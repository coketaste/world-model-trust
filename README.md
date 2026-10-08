# world-model-trust

An independent brainstorm and proof-of-concept project on how methods from seismic imaging (illumination and resolution analysis, tomography, migration, imaging with multiples, full-waveform inversion, uncertainty quantification) could contribute to **spatial intelligence and physical AI**: generating 3D worlds that people and robots can trust. Ideas are tried on small experiments where the right answer is known, and each is checked against verified prior work.

This project starts from open problems that World Labs describes on its own public pages (for example, as its taxonomy post puts it, that "AI-generated geometry can look correct while containing self-intersections or wrong scale that produce nonsensical physics", or that "object shape, weight, and friction may be uncertain") and asks whether ideas from geophysics (seismic imaging, tomography, migration, imaging with multiples, full-waveform inversion, uncertainty analysis) could complement that work. It uses public information and small stand-in experiments only; it does not evaluate or compare any company's products. Much of the relevant prior work comes from the vision and robotics communities, which the literature page credits. The ideas are hypotheses to examine, and comments or corrections from World Labs or anyone else are welcome.

Not affiliated with World Labs. Nothing here tests World Labs' Marble itself (see *Limits and provenance*).

**Status:** the planned proof-of-concept experiments are done and reviewed. See [`site/index.html`](site/index.html) for the readable version, [`results/`](results/) for write-ups, and [`prereg/`](prereg/) for the specifications written before each run.

## What was found

| Experiment | Question | Result |
|---|---|---|
| Illumination (`results/WP0.md`) | Which parts of a rebuilt 3D world does the photo constrain? | A seismic-style illumination score is practically equal to plain visibility and clearly beats an in-frame test. |
| Robots (`results/WP1.md`, `WP1-sensitivity.md`) | Does a trust map keep a simulated robot safer? | Inconclusive: underpowered; no policy beat "unknown = obstacle". |
| Alignment (`results/WP2.md`, `WP2-sensitivity.md`) | Does an optimal-transport misfit line up generated and real geometry better than ICP? | Success criterion not met. The first run's clear negative was largely a compute artefact; at matched compute the comparison is inconclusive. |
| Shadows (`results/WP3.md`) | Can a cast shadow resolve the depth–size ambiguity? | Yes in an idealised simulation, if the shadow is in view; weak on textured floors. |

Almost every idea has verified prior work in vision, graphics or robotics ([`docs/literature/`](docs/literature/)). The contribution sought is discipline (what the data constrain, blind tests, calibration, honest negatives), not new algorithms.

## Repository layout

```
site/          static web pages (no build step): overview, ideas, geophysics primer, experiments, literature, method;
               assets/ holds the shared JS/CSS, SVG figure toolkit and rendered figures (assets/figs/)
src/wmt/       library: SPZ reader, tile rasterizer (illumination, Fisher), ICP, stand-in generator, benchmark, per-experiment code
experiments/   one folder per experiment: runners and analysis scripts
prereg/        hypotheses and success criteria written before each run, with dated amendments
results/       write-ups (WP*.md), raw JSON, plots, recorded hashes; see results/README.md
docs/literature/  verified literature maps (also rendered on the site's Literature page)
scripts/       data fetch, site-data build, figure generation (make_figures.py), smoke tests
tests/         pytest suite
```

## Quick start

```
python3 -m venv venv && venv/bin/pip install -e ".[dev,depth]"   # depth = torch + transformers (CPU)
venv/bin/python scripts/fetch_data.py                            # public example exports, SHA-256 verified
venv/bin/python -m pytest -q
```

No GPU is needed. Data and intermediate outputs (`data/`, `out/`) are git-ignored.

## Interactive SEG/EAGE salt demonstration

[`site/salt.html`](site/salt.html), linked from the geophysics primer, displays an actual SEG/EAGE salt-model interior with orbit controls, movable X/Y/depth velocity sections, surface opacity, and schematic survey layouts. Browser assets are included; serve `site/` over HTTP for the interactive viewer. Static previews also work without JavaScript or WebGL.

The original archive was unavailable, so this preview recovers only the unchanged interior of a published EMsig derivative: 0.30–3.66 km depth. It does not invent the overwritten water or basement. The crop and transformation are visible on the page. See [`site/assets/salt/README.md`](site/assets/salt/README.md) for the source, CC BY 4.0 attribution, checksums, and rebuild instructions. `scripts/build_salt_assets.py` also supports the original `SALTF.ZIP` or `Saltf@@` when available. Preparing assets requires the `salt` extra; viewing requires no Python dependencies.

Validation: `node scripts/test_salt.mjs`, `venv/bin/python -m pytest tests/test_salt_assets.py -q`, and browser interaction tests in `scripts/test_salt_browser.cjs` (Playwright; instructions in that file). The viewer presents model geometry and schematic measurement positions, not a seismic simulation or uncertainty result.

## Reproducing the experiments

```
venv/bin/python experiments/wp0_baseline/reproduce.py                  # ~5 min; also caches the 12 cases in out/cases/ that the others use
OMP_NUM_THREADS=4 venv/bin/python experiments/wp1_robot_benchmark/run.py            # as specified; add --amended for the exploratory run
venv/bin/python experiments/wp2_ot_alignment/run.py tune                            # then: run.py eval --variants A C B, then analyze.py (~45 min)
PYTHONPATH=src OMP_NUM_THREADS=4 venv/bin/python experiments/wp3_shadows/run_wp3.py # then analyze_wp3.py and stress_wp3.py
```

The post-hoc sensitivity runs are `experiments/wp1_robot_benchmark/run_sensitivity.py` and `experiments/wp2_ot_alignment/run_sensitivity.py`. WP2 needs the `wp2` extra (`pip install -e ".[wp2]"`) and a `libusb` shim for open3d; see `results/WP2.md` section 8. Per-job run caches are not committed; rerunning regenerates them.

## Web pages

```
python3 scripts/build_site_data.py       # refresh site/assets/data.js and lit.js from results/ and docs/literature/
python3 scripts/make_figures.py         # regenerate the synthetic-room figures in site/assets/figs/ (about a minute, CPU)
python3 -m http.server -d site 8000      # then open http://localhost:8000 (opening site/index.html directly also works)
```

`scripts/smoke_site.js` loads every page in jsdom (`npm install jsdom`), exercises the controls and exits unsuccessfully on errors; `scripts/test_primer.js` tests the geophysics illustrations' compute code (`node scripts/test_primer.js`). Neither can judge visual appearance.

`scripts/test_site_browser.cjs` uses Playwright/Chromium against a running local server (default `http://127.0.0.1:8765`, override with `SITE_BASE_URL`). It checks every page at desktop and mobile widths, exercises controls and chart/table switches, checks images, anchors and overflow, and verifies that primer rays are visible and section jumps clear the sticky navigation. It saves primer screenshots under `/tmp/wmt-site-review` for visual inspection. Install Playwright separately and run `node scripts/test_site_browser.cjs`; the focused salt-browser suite additionally checks WebGL failure and recovery.

### Publish with GitHub Pages

GitHub Pages' **Deploy from a branch** source only supports `/` and `/docs`.
Use **GitHub Actions** to publish the existing `site/` directory with
[the Pages workflow](.github/workflows/pages.yml); no build step is required.

1. In the repository's **Settings → Pages → Build and deployment**, set
   **Source** to **GitHub Actions**.
2. Commit and push the workflow and all site files to `main`, including
   `site/assets/salt/` and `site/assets/vendor/`. The generated assets must be
   included; the workflow does not download or regenerate them.
3. Open **Actions → Deploy site to GitHub Pages** and check that the run succeeds.
   If the files were already pushed before enabling Pages, select **Run workflow**
   on `main` to deploy manually.

The published home page is <https://coketaste.github.io/world-model-trust/>.
The workflow publishes the contents of `site/` at that URL, so the salt demo is
<https://coketaste.github.io/world-model-trust/salt.html>. Do not add `/site/`
to these URLs. Relative links and assets support the repository URL prefix.
Subsequent pushes that change `site/` or the workflow deploy automatically.

### Figures

Figures are generated by this project, including salt visualisations derived from the credited SEG/EAGE model.

- **Diagrams and icons** are inline SVG drawn in JavaScript: `site/assets/viz.js` (`V.diagram`, `V.figure`), `icons.js` (themed icons), `analogy.js` (geophysics-to-vision maps, literature status matrix) and per-page code. Colours come from theme tokens in `style.css`/`figures.css`, so they follow light and dark mode.
- **Rendered figures** in `site/assets/figs/`: `synthetic-room_*.png` come from `scripts/make_figures.py`, which builds a procedural room (no third-party assets) and renders it with `src/wmt/raster.py`; the other PNGs are plots and schematics from this project's experiments. The synthetic room is an illustration, not a World Labs or Marble output.
- **Salt visualisations** in `site/assets/salt/` derive from the SEG/EAGE model interior recovered from the EMsig derivative; see [the asset provenance and licence](site/assets/salt/README.md).
- Text alternatives or captions accompany each figure; when adding one, check it in light and dark mode and with the keyboard.

## Limits and provenance

- All experiments use a **stand-in generator** (a public depth network plus a room-box rule), not Marble. Any use of Marble itself would need paid API credits and, first, a careful reading of World Labs' terms and their agreement.
- World Labs and Spark data files are **not** redistributed, and no images derived from World Labs content are included; `scripts/fetch_data.py` downloads public example files on demand from their public locations (check World Labs' terms before reusing them). See [`NOTICE.md`](NOTICE.md) for attributions and third-party licences.
- Samples are small (12 cases from 3 worlds) and intervals are indicative. Hypotheses and success criteria were written down before each run, but not committed beforehand, so the record is self-attested. Post-hoc changes are labelled exploratory.

## Licences

- Code: MIT License ([`LICENSE`](LICENSE)).
- Text, documentation, results write-ups, site content and original figures: Creative Commons Attribution 4.0 International ([`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt)).
- Third-party material (short quotations from public pages, and the components listed in [`NOTICE.md`](NOTICE.md)) is not covered by either licence and remains under its owners' terms.

To request a change or removal of anything referenced here, open an issue.
