# NOTICE

world-model-trust is an independent research project. Copyright (c) 2026 the world-model-trust authors.

## Independence and sources

This project is not affiliated with, sponsored by, or endorsed by World Labs Technologies, Inc. or any other company or project named here. It is built only from public information: public web pages and documentation, public example files, and published papers. The views expressed are the author's own.

"World Labs", "Marble", "Atlas", "RTFM" and "Spark" and other product names are trademarks or names of their respective owners and are used only to refer to those products and publications. No logos are used. Short quotations from public pages are attributed and used for commentary and research; they remain the property of their owners.

The project starts from open problems that World Labs describes on its own public pages and offers complementary ideas from geophysics. It does not evaluate or compare any company's products.

## What is not included

- No World Labs or Spark data files, and no images or renders derived from World Labs content, are included in this repository. `scripts/fetch_data.py` downloads public example files from their public locations on demand; check World Labs' terms before reusing them.
- No model weights are included.
- Figures include inline SVG drawn in `site/assets/*.js`, plots from this project's own results, renders of a procedurally generated synthetic room, and the SEG/EAGE-derived salt visualisations credited below. The site's icons are drawn for this project; no logos are used.

## Third-party code

### Three.js 0.160.1

`site/assets/vendor/three.module.js` and `OrbitControls.js` are vendored from Three.js 0.160.1 (MIT, copyright 2010–2023 Three.js Authors). The OrbitControls import path is changed to the local module; otherwise these files are unmodified. The complete notice is in `site/assets/vendor/THREE-LICENSE.txt`. Sources: https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js and https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/controls/OrbitControls.js.

## SEG/EAGE salt model data and derived figures

`site/assets/salt/` contains a reduced interior volume, an extracted salt mesh and figures derived from the SEG/EAGE 3D Salt Model. Copyright 1997 Society of Exploration Geophysicists; licensed under CC BY 4.0. Credit the SEG/EAGE 3-D Modeling committee and Aminzadeh, Brac & Kunz (1997), *SEG/EAGE 3-D Salt and Overthrust Models*.

The source used is the checksum-verified EMsig derivative by Dieter Werthmüller, https://github.com/emsig/data/blob/2021-05-21/emg3d/models/SEG-EAGE-Salt-Model.h5. The original SEG archive returned HTTP 403 during preparation. We reverse the published velocity-to-resistivity transform only in the unchanged interior (0.30–3.66 km under the sample-coordinate convention), exclude overwritten layers, subsample, quantize velocities, and extract a salt-membership surface. This is not a copy of the complete original volume. Processing and source references are in `site/assets/salt/README.md` and `metadata.json`; the full licence and attribution are in `site/assets/salt/LICENSE.txt`. Keep these notices with redistributed assets. No endorsement is implied.

## Other third-party code

### Spark SPZ decoder (`src/wmt/spz_io.py`)

Parts of `src/wmt/spz_io.py` are a Python port of the SPZ decoder in Spark (https://github.com/sparkjsdev/spark, `rust/spark-lib/src/spz.rs`), which is licensed under the MIT License:

    The MIT License

    Copyright © 2025 WORLD LABS TECHNOLOGIES, INC.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

The SPZ file format was created by Niantic Labs (https://github.com/nianticlabs/spz, MIT License, Copyright (c) 2024 Niantic Labs).

### Methods implemented independently (no code copied)

- `src/wmt/raster.py`: an independent NumPy implementation of the tile-based Gaussian splat rendering method of Kerbl et al., "3D Gaussian Splatting for Real-Time Radiance Field Rendering" (ACM Transactions on Graphics, 2023; arXiv:2308.04079). It contains no code from the authors' reference implementation.
- `src/wmt/align.py`: similarity alignment after Umeyama (1991) and iterative closest point.

## Third-party dependencies (installed by the user, not redistributed)

| Package | Licence |
|---|---|
| numpy | BSD-3-Clause (with 0BSD, MIT, Zlib, CC0-1.0 components) |
| scipy | BSD-3-Clause |
| matplotlib | Matplotlib licence (PSF-style) |
| pillow | MIT-CMU |
| torch (optional) | BSD-style, with Apache-2.0 components |
| transformers (optional) | Apache-2.0 |
| open3d, libusb-package (optional, for one experiment) | MIT; Apache-2.0 |
| pytest (development) | MIT |
| scikit-image, h5py (optional salt asset preparation) | BSD-3-Clause |

Licences were read from package metadata; check each project for the current terms.

## Models and data used but not redistributed

- Depth Anything V2 Metric Indoor Small (Hugging Face: `depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf`), downloaded on demand. The model card states no licence. The project's repository (https://github.com/DepthAnything/Depth-Anything-V2) states that the Small model is Apache-2.0 and the Base, Large and Giant models are CC-BY-NC-4.0; the metric-depth checkpoints are not addressed there. The indoor metric model was fine-tuned on the Hypersim dataset (CC BY-SA 3.0). Check the current licence terms before any reuse.
- Public example files (splats, collider meshes, panoramas) listed at https://docs.worldlabs.ai/marble/export/specs and downloaded by `scripts/fetch_data.py`. They are World Labs content; no licence is stated for them, and they are not included here.

## Licences of this project

- Code (`src/`, `experiments/`, `scripts/`, `tests/`, and the JavaScript and CSS in `site/assets/`): MIT License, see `LICENSE`.
- Text, documentation, results write-ups, site content and original figures: Creative Commons Attribution 4.0 International, see `LICENSE-CC-BY-4.0.txt`.
- Third-party material described in this file, including short quotations from public pages, is not covered by either licence and remains under its owners' terms.

## Contact and removal requests

If you own material referenced here and want it changed or removed, please open an issue at https://github.com/coketaste/world-model-trust/issues and it will be handled promptly.
