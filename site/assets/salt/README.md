# SEG/EAGE salt demonstration assets

These are derived assets from the SEG/EAGE 3D Salt Model, not a newly generated salt shape or an inversion result.

## Source and access

- Original model: Aminzadeh, F., Brac, J., and Kunz, T. (1997), *SEG/EAGE 3-D Salt and Overthrust Models*, Society of Exploration Geophysicists. Copyright 1997 Society of Exploration Geophysicists; CC BY 4.0.
- Original archive: https://s3.amazonaws.com/open.source.geoscience/open_data/seg_eage_models_cd/Salt_Model_3D.tar.gz (returned HTTP 403 on 2026-10-07).
- Source used: Dieter Werthmüller / EMsig, https://raw.githubusercontent.com/emsig/data/2021-05-21/emg3d/models/SEG-EAGE-Salt-Model.h5
- SHA-256: `6ee10663de588d445332ba7cc1c0dc3d6f9c50d1965f797425cebc64f9c71de6` (matches the published recipe).
- Conversion and licence documentation: https://github.com/emsig/emg3d-gallery/blob/89997efe7ee5a7fceba1b9b559e5fac3fd9c0bef/examples/models/SEG-EAGE_3D_salt_model.py
- Independent original-volume layout and salt-membership reference: https://github.com/pyvista/show-room/blob/master/seg-eage-3d-salt-model.ipynb (Bane Sullivan and Dieter Werthmüller). That notebook also explicitly identifies the model licence as CC BY 4.0. No notebook code or rendered assets were copied into this demo.

## What is retained

The EMsig file is a resistivity derivative, not the original velocity archive. Its code transforms velocity as `rho = (v / 1700) ** 3.88`, inserts an air layer, replaces shallow water and deep basement, and reverses depth ordering. Only its unchanged interior is reversible. The builder checks the exact file hash and uses HDF5 indices 26 through 194 inclusive, reversed: original velocity depth indices 15 through 183 inclusive, or 300–3660 m under the original sample-coordinate convention. No overwritten values are inferred or filled in.

Within this crop, `v = 1700 * rho ** (1 / 3.88)` recovers the original float32 velocity values. The numerical forward/inverse round-trip error is recorded in `metadata.json`. This is an interior crop of the SEG/EAGE model, not the full original volume. The original velocity volume was not available for a direct full-volume byte comparison.

The builder samples every fourth X/Y point and every second depth point, and retains final endpoints. The display volume has 170 × 170 × 85 samples. Horizontal sample coordinates span 0–13.50 km, with depth spanning 0.30–3.66 km. The final X/Y interval is 60 m rather than the usual 80 m; the viewer uses the explicit coordinate arrays. Coordinates refer to grid samples, not cell-boundary extents.

Velocities are rounded to unsigned 16-bit integer m/s. Salt membership is computed before rounding, with absolute tolerance 0.01 m/s around the documented salt velocity 4482 m/s. Marching cubes extracts the 0.5 boundary of this binary mask. There is no mesh smoothing, guessed continuation, or artificial cap at the crop boundary. Thin features can disappear through subsampling. The displayed mesh has no vertical exaggeration.

## Files

- `velocity.bin`: little-endian uint16, shape from metadata, XYZ in C order (Z fastest).
- `vertices.bin`: little-endian float32 XYZ coordinates, depth positive down, kilometres.
- `triangles.bin`: little-endian uint32 triangle indices.
- `metadata.json`: source checksum, coordinate axes, transformations, counts, and binary hashes.
- `preview.png`, `sections.png`: original renders of these derived data, available without WebGL or JavaScript.
- `LICENSE.txt`: data attribution and the full CC BY 4.0 licence. Keep it with these assets.

## Rebuild

From the repository root:

```sh
venv/bin/pip install -e '.[salt]'
mkdir -p data/seg-eage
curl -fL https://raw.githubusercontent.com/emsig/data/2021-05-21/emg3d/models/SEG-EAGE-Salt-Model.h5 -o data/seg-eage/SEG-EAGE-Salt-Model.h5
MPLCONFIGDIR=/tmp/wmt-matplotlib venv/bin/python scripts/build_salt_assets.py --source data/seg-eage/SEG-EAGE-Salt-Model.h5 --kind emsig-interior
```

The original grid is supported when available:

```sh
venv/bin/python scripts/build_salt_assets.py --source data/seg-eage/SALTF.ZIP --kind original
```

This path also accepts uncompressed `Saltf@@` and records its checksum. Before publishing a rebuild from the complete grid, update this README and the static source/crop text and image alternatives in `site/salt.html` to match the new asset provenance. Runtime labels already read the metadata, but the static/no-JavaScript content also needs review.

## Interpretation

The amber surface represents salt membership; slice colours represent P-wave velocity. Survey markers are schematic and use an equal number of positions in both layouts. No wavefield, ray trace, seismic illumination, reconstruction, or uncertainty calculation is performed. These assets do not evaluate World Labs or another product.
