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
site/          static web pages (no build step): overview, ideas, geophysics primer, experiments, literature, method
src/wmt/       library: SPZ reader, tile rasterizer (illumination, Fisher), ICP, stand-in generator, benchmark, per-experiment code
experiments/   one folder per experiment: runners and analysis scripts
prereg/        hypotheses and success criteria written before each run, with dated amendments
results/       write-ups (WP*.md), raw JSON, plots, recorded hashes; see results/README.md
docs/literature/  verified literature maps (also rendered on the site's Literature page)
scripts/       data fetch, site-data build, smoke tests
tests/         pytest suite
```

## Quick start

```
python3 -m venv venv && venv/bin/pip install -e ".[dev,depth]"   # depth = torch + transformers (CPU)
venv/bin/python scripts/fetch_data.py                            # public example exports, SHA-256 verified
venv/bin/python -m pytest -q
```

No GPU is needed. Data and intermediate outputs (`data/`, `out/`) are git-ignored.

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
python3 -m http.server -d site 8000      # then open http://localhost:8000 (opening site/index.html directly also works)
```

`scripts/smoke_site.js` loads every page in jsdom (`npm install jsdom`), exercises the controls and checks for errors; `scripts/test_primer.js` tests the geophysics illustrations' compute code (`node scripts/test_primer.js`). Neither can judge visual appearance, so review the pages in a browser.

## Limits and provenance

- All experiments use a **stand-in generator** (a public depth network plus a room-box rule), not Marble. Any use of Marble itself would need paid API credits and, first, a careful reading of World Labs' terms and their agreement.
- World Labs and Spark data files are **not** redistributed, and no images derived from World Labs content are included; `scripts/fetch_data.py` downloads public example files on demand from their public locations (check World Labs' terms before reusing them). See [`NOTICE.md`](NOTICE.md) for attributions and third-party licences.
- Samples are small (12 cases from 3 worlds) and intervals are indicative. Hypotheses and success criteria were written down before each run, but not committed beforehand, so the record is self-attested. Post-hoc changes are labelled exploratory.

## Licences

- Code: MIT License ([`LICENSE`](LICENSE)).
- Text, documentation, results write-ups, site content and original figures: Creative Commons Attribution 4.0 International ([`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt)).
- Third-party material (short quotations from public pages, and the components listed in [`NOTICE.md`](NOTICE.md)) is not covered by either licence and remains under its owners' terms.

To request a change or removal of anything referenced here, open an issue.
