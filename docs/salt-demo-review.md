# SEG/EAGE salt demonstration review

Prepared 2026-10-07. Entry point: `site/salt.html`, linked from the geophysics primer and reading-order navigation. Serve `site/` over HTTP; the viewer needs no build step or external CDN at runtime.

## Implemented

- Interactive Three.js viewer with mouse/touch orbit controls, keyboard rotation, zoom buttons, four camera presets and reset.
- Salt surface visibility and opacity; movable X, Y and horizontal velocity sections on physically scaled coordinates.
- Two schematic acquisition layouts with equal marker counts. No illumination, uncertainty or reconstruction score is asserted.
- Responsive light/dark layout, static model and reference sections, disabled controls when unavailable, load retry and WebGL context-loss recovery.
- Reproducible asset builder, source and binary checksums, explicit transformations, CC BY 4.0 data attribution, and vendored Three.js MIT notice.

## Material change from the initial plan

The original SEG/EAGE archive still returned HTTP 403. The implemented preview uses the recoverable interior of the documented, checksum-verified EMsig derivative. Its overwritten water/air and deep basement are excluded. The retained original depth samples are 15–183 (0.30–3.66 km), over the full horizontal sample extent (0–13.50 km on both axes).

The published transform is reversed only in that interval. The forward/inverse round-trip relative error is 2.22e-16. Restored float32 velocities in this source are already integer m/s, so the additional uint16 quantization error is zero. This does not substitute for a direct comparison against the unavailable complete original velocity file.

The displayed volume is 170 × 170 × 85 samples. The unsmoothed salt mesh has 28,246 vertices and 56,544 triangles. Binary volume and mesh assets total 5,930,480 bytes; previews, metadata and the local Three.js library bring the complete page assets to approximately 7.6 MB before HTTP compression.

The builder accepts `SALTF.ZIP` or raw `Saltf@@` for a future full-volume import. That original-data path has not been validated against an actual original file here. Static provenance text and image alternatives must be updated when switching to it, as documented in the asset README.

## Verification completed

- `node scripts/test_salt.mjs`: source-independent non-cubic slice/stride tests; asset hashes; model bounds; colour endpoints; survey directions and equal marker counts.
- `venv/bin/python -m pytest tests/test_salt_assets.py -q`: 2 tests passed, checking physical mesh/volume boundary alignment, nondegenerate faces, provenance, crop and asset checksums.
- `NODE_PATH=/tmp/jt/node_modules node scripts/smoke_site.js`: all 11 pages ran without errors; existing segmented controls and slider checks passed.
- `scripts/test_salt_browser.cjs`: passed in Chromium using software WebGL, covering render calls, camera presets, keyboard and mouse rotation, zoom controls, slices and coordinate readouts, opacity/visibility, survey switching, reset, light/dark and mobile layout, context loss and recovery, failed volume download and retry, no-WebGL fallback and no-JavaScript content.
- Visual review of desktop model, full desktop page and mobile screenshots. Screenshots saved locally under `out/salt-review/` (git-ignored).
- All local HTML references resolve; `git diff --check` passes. Asset rebuild reproduced identical binary checksums.

Browser tests were run with Playwright and Chromium installed under `/tmp`; missing browser libraries were extracted to a temporary folder, without installing system packages. Mobile layout was tested at 390 × 844 pixels; physical-device touch performance and Safari/Firefox were not tested.

No deployment or external publication was performed. No seismic propagation or inversion experiment was added.
