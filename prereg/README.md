# prereg/

Historical, time-stamped specifications for the experiments: the hypothesis, baselines, metrics and a numeric success criterion for each research question, written before the corresponding run.

- `RQ1.md` robot benchmark, `RQ2.md` alignment, `RQ3.md` shadows.
- Each file's SHA-256 and a timestamp were recorded locally before the run (see `results/wp*_prereg_hash.txt`). They were not committed beforehand, so the record is self-attested.
- **Please do not edit these files.** Editing them would invalidate the recorded hashes. The only exception so far: on 2026-10-06 a few descriptive sentences and the author lines were reworded for tone and clarity, with an "Editorial change" note at the end of each file and the new hash recorded; nothing about the hypotheses, criteria or analyses changed. Their wording about other systems (for example, shorthand such as "hallucinated geometry" for content produced by this project's own stand-in generator) is working language written at the time, not a statement about any product.
- Changes made after a run began are listed as dated amendments inside each file, and the results write-ups (`results/WP*.md`) and the post-hoc sensitivity reports (`results/WP1-sensitivity.md`, `results/WP2-sensitivity.md`) say which analyses were exploratory or post hoc.
- References to `PROPOSAL.md` inside these files point to the original project plan, which is not published; each file states its own hypothesis and success criterion.
- The template for new specifications is `docs/PREREGISTRATION-TEMPLATE.md`.
