# docs/literature/

Verified literature maps used by this project.

| File | What it is |
|---|---|
| `LITERATURE-IMAGING.md` | Seismic-imaging concepts paired with their existing counterparts in vision, graphics and imaging, with verified references and a machine-readable JSON block. |
| `LITERATURE-PHYSICAL-AI.md` | Short attributed excerpts of what World Labs' public pages describe, with URLs, and the physical-AI literature around a geophysicist's skills, also with a JSON block. |

`scripts/build_site_data.py` reads the last fenced `json` block of each file to build `site/assets/lit.js` for the Literature page; keep that block valid if you edit them.

Verification limits: no general web search was available, so references were checked through the arXiv, Crossref and Semantic Scholar interfaces; "not found in this search" never means "does not exist". World Labs excerpts came through a summarising fetch tool, so re-check any quotation against the primary page before reusing it.
