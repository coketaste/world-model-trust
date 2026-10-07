"""WP1: floor-plane grid construction, Dijkstra planning and execution checks (see prereg/RQ1.md)."""
import heapq

import numpy as np
from scipy.ndimage import binary_closing, binary_dilation

CELL = 0.1
HALF = 6.0
N = int(round(2 * HALF / CELL))
OBST_LO, OBST_HI = 0.15, 1.0
FLOOR_TOL = 0.08
MIN_OBST_SPLATS = 2
S3 = np.ones((3, 3), bool)
SQRT2 = float(np.sqrt(2.0))
MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, SQRT2), (1, -1, SQRT2), (-1, 1, SQRT2), (-1, -1, SQRT2)]


def floor_height(P):
    """Mode of the y histogram (y is down) over 0.3<y<3, |x|,|z|<5."""
    m = (P[:, 1] > 0.3) & (P[:, 1] < 3.0) & (np.abs(P[:, 0]) < 5) & (np.abs(P[:, 2]) < 5)
    h, e = np.histogram(P[m, 1], bins=np.arange(0.3, 3.0, 0.05))
    i = int(h.argmax())
    return float(0.5 * (e[i] + e[i + 1]))


def cell_index(P):
    ix = np.floor((P[:, 0] + HALF) / CELL).astype(int)
    iz = np.floor((P[:, 2] + HALF) / CELL).astype(int)
    ok = (ix >= 0) & (ix < N) & (iz >= 0) & (iz < N)
    return ix, iz, ok


def floor_grid(P, y_f, mask=None):
    """Binary floor evidence (3x3 closed). `mask` selects which splats may contribute."""
    sel = np.abs(P[:, 1] - y_f) <= FLOOR_TOL
    if mask is not None:
        sel &= mask
    ix, iz, ok = cell_index(P[sel])
    g = np.zeros((N, N), bool)
    g[ix[ok], iz[ok]] = True
    return binary_closing(g, structure=S3)


def obstacle_grid(P, y_f):
    """Uninflated obstacle evidence: >= MIN_OBST_SPLATS splats at height above floor in [OBST_LO, OBST_HI]."""
    h = y_f - P[:, 1]
    sel = (h >= OBST_LO) & (h <= OBST_HI)
    ix, iz, ok = cell_index(P[sel])
    cnt = np.zeros((N, N), int)
    np.add.at(cnt, (ix[ok], iz[ok]), 1)
    return cnt >= MIN_OBST_SPLATS


def inflate(obst):
    return binary_dilation(obst, structure=S3)


START = (int(HALF / CELL), int(HALF / CELL))  # cell containing the origin


def dijkstra(free, start=START):
    """Shortest-path tree on an 8-connected grid without diagonal corner cutting.
    Returns (dist, parent) with parent encoded as flat index (-1 = none)."""
    dist = np.full(free.shape, np.inf)
    parent = np.full(free.shape, -1, dtype=np.int64)
    dist[start] = 0.0
    heap = [(0.0, start[0], start[1])]
    while heap:
        d, x, z = heapq.heappop(heap)
        if d > dist[x, z]:
            continue
        for dx, dz, c in MOVES:
            nx, nz = x + dx, z + dz
            if not (0 <= nx < free.shape[0] and 0 <= nz < free.shape[1]) or not free[nx, nz]:
                continue
            if dx and dz and not (free[x + dx, z] and free[x, z + dz]):
                continue
            nd = d + c
            if nd < dist[nx, nz]:
                dist[nx, nz] = nd
                parent[nx, nz] = x * free.shape[1] + z
                heapq.heappush(heap, (nd, nx, nz))
    return dist, parent


def extract_path(parent, goal, shape):
    path = [goal]
    while parent[path[-1]] != -1:
        p = int(parent[path[-1]])
        path.append((p // shape[1], p % shape[1]))
    return path[::-1]


def path_length(path):
    return float(sum(np.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(path[:-1], path[1:])) * CELL)


def execute(path, truth_floor, truth_obst_infl):
    """Walk the path in the truth map. Returns None if it succeeds, else 'collision' or 'fall' at the first violation."""
    for (x, z) in path[1:]:
        if truth_obst_infl[x, z]:
            return "collision"
        if not truth_floor[x, z]:
            return "fall"
    return None


def wedge_los(obst, yaw_deg, hfov_deg, r_max=np.inf, cand=None, start=START):
    """Cells inside the camera's horizontal FOV wedge, within r_max of the start, whose 2D line of sight
    to the start (sampled every 0.05) crosses no uninflated obstacle cell. `cand` optionally restricts cells."""
    ii, jj = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    dx = (ii - start[0]) * CELL
    dz = (jj - start[1]) * CELL
    yaw = np.radians(yaw_deg)
    fwd = np.array([np.sin(yaw), np.cos(yaw)])
    r = np.hypot(dx, dz)
    cosang = (dx * fwd[0] + dz * fwd[1]) / np.maximum(r, 1e-9)
    ok = ((cosang >= np.cos(np.radians(hfov_deg / 2))) | (r < CELL * 0.5)) & (r <= r_max)
    if cand is not None:
        ok &= cand
    free = np.zeros_like(ok)
    for x, z in zip(*np.nonzero(ok)):
        n = max(int(np.ceil(r[x, z] / 0.05)), 1)
        t = np.linspace(0, 1, n + 1)[:-1]
        px = np.floor(start[0] + t * (x - start[0])).astype(int)
        pz = np.floor(start[1] + t * (z - start[1])).astype(int)
        if not obst[px, pz].any():
            free[x, z] = True
    free[start] = True
    return free


def wedge_free(obst, floor_any, yaw_deg, hfov_deg, start=START):
    """Unknown=obstacle map: inside the FOV wedge, clear 2D line of sight to the start, with floor evidence,
    and not an inflated obstacle."""
    return wedge_los(obst, yaw_deg, hfov_deg, cand=floor_any & ~inflate(obst), start=start)


def blind_radius(floor_y, hfov_deg, aspect=0.75):
    """Distance within which the floor is below the camera's vertical FOV (camera at height floor_y, level gaze)."""
    half_v = np.arctan(np.tan(np.radians(hfov_deg / 2)) * aspect)
    return float(floor_y / np.tan(half_v))


def disc(r, start=START):
    ii, jj = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    return np.hypot(ii - start[0], jj - start[1]) * CELL <= r
