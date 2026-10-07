"""
Read .spz Gaussian-splat files (the format Marble / the World API
exports, and Spark.js loads) in pure numpy.

Attribution: this decoder is a Python port of the SPZ decoder in Spark
(https://github.com/sparkjsdev/spark, rust/spark-lib/src/spz.rs), which is MIT licensed,
Copyright (c) 2025 WORLD LABS TECHNOLOGIES, INC. The SPZ format was created by Niantic Labs
(MIT, Copyright (c) 2024 Niantic Labs). The full MIT notice is reproduced in NOTICE.md and
must accompany copies or substantial portions of this file.

Decode is a vectorized port of Spark's own parser
(`spark/rust/spark-lib/src/spz.rs`, `poll_sections`), checked line by line:
  header   16 bytes: magic "NGSP", version, num_splats, sh_degree, fractional_bits, flags, reserved
  centers  v1: 3 x f16; v2/v3: 3 x signed int24 / 2^fractional_bits
  alphas   u8 / 255 (x2 if the LoD-tree flag 0x80 is set)
  rgb      (u8/255 - 0.5) * (SH_C0/0.15) + 0.5      (SH DC term baked to a color)
  scales   exp(u8/16 - 10)
  quats    v1/v2: xyz as u8/127.5 - 1, w = sqrt(1 - |xyz|^2); v3: "smallest three" packed u32
  sh       skipped here (we only use the view-independent DC color)
Quaternions are returned in xyzw order, same as Spark.
"""
import gzip
import struct

import numpy as np

SPZ_MAGIC = 0x5053474E
SH_C0 = 0.28209479177387814
RGB_SCALE = SH_C0 / 0.15


def read_spz(path):
    raw = gzip.open(path, "rb").read()
    magic, version, n = struct.unpack("<III", raw[:12])
    sh_degree, frac_bits, flags = raw[12], raw[13], raw[14]
    if magic != SPZ_MAGIC:
        raise ValueError(f"bad SPZ magic 0x{magic:08x}")
    if not 1 <= version <= 3:
        raise ValueError(f"unsupported SPZ version {version}")
    buf = np.frombuffer(raw, dtype=np.uint8, offset=16)
    off = 0

    def take(nbytes):
        nonlocal off
        out = buf[off:off + nbytes]
        off += nbytes
        return out

    if version == 1:
        centers = take(n * 6).view("<f2").reshape(n, 3).astype(np.float32)
    else:
        b = take(n * 9).reshape(n, 3, 3).astype(np.int32)
        v = b[..., 0] | (b[..., 1] << 8) | (b[..., 2] << 16)
        v = np.where(v >= 1 << 23, v - (1 << 24), v)  # sign-extend int24
        centers = (v / float(1 << frac_bits)).astype(np.float32)

    opacity = take(n).astype(np.float32) / 255.0 * (2.0 if flags & 0x80 else 1.0)
    rgb = (take(n * 3).reshape(n, 3).astype(np.float32) / 255.0 - 0.5) * RGB_SCALE + 0.5
    scales = np.exp(take(n * 3).reshape(n, 3).astype(np.float32) / 16.0 - 10.0)

    if version == 3:
        comp = take(n * 4).view("<u4").astype(np.uint64)
        largest = (comp >> 30).astype(np.int64)
        quats = np.zeros((n, 4), dtype=np.float32)
        rem = comp.copy()
        mask = (1 << 9) - 1
        sum_sq = np.zeros(n, dtype=np.float32)
        for j in (3, 2, 1, 0):  # same reverse order as spz.rs
            is_small = largest != j
            val = (rem & mask).astype(np.float32)
            sign = ((rem >> 9) & 1).astype(bool)
            q = np.float32(1 / np.sqrt(2)) * val / mask
            q = np.where(sign, -q, q)
            quats[:, j] = np.where(is_small, q, quats[:, j])
            sum_sq += np.where(is_small, q * q, 0)
            rem = np.where(is_small, rem >> 10, rem)
        quats[np.arange(n), largest] = np.sqrt(np.clip(1 - sum_sq, 0, None))
    else:
        xyz = take(n * 3).reshape(n, 3).astype(np.float32) / 127.5 - 1.0
        w = np.sqrt(np.clip(1 - (xyz ** 2).sum(1), 0, None))
        quats = np.concatenate([xyz, w[:, None]], axis=1)

    return dict(centers=centers, opacity=opacity, rgb=rgb, scales=scales, quats=quats,
                header=dict(version=version, n=n, sh_degree=sh_degree, frac_bits=frac_bits, flags=flags))

