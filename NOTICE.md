# NOTICE

world-model-trust is an independent research project. Copyright (c) 2026 the world-model-trust authors.

## Independence and sources

This project is not affiliated with, sponsored by, or endorsed by World Labs Technologies, Inc. or any other company or project named here. It is built only from public information: public web pages and documentation, public example files, and published papers. The views expressed are the author's own.

"World Labs", "Marble", "Atlas", "RTFM" and "Spark" and other product names are trademarks or names of their respective owners and are used only to refer to those products and publications. No logos are used. Short quotations from public pages are attributed and used for commentary and research; they remain the property of their owners.

The project starts from open problems that World Labs describes on its own public pages and offers complementary ideas from geophysics. It does not evaluate or compare any company's products.

## What is not included

- No World Labs or Spark data files, and no images or renders derived from World Labs content, are included in this repository. `scripts/fetch_data.py` downloads public example files from their public locations on demand; check World Labs' terms before reusing them.
- No model weights are included.

## Third-party code

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
