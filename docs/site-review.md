# Site regression review — 2026-10-07

Reviewed the local site after adding the Geophysics subnavigation. Fixed the following issues:

- **Section headings covered by navigation.** The new second row increased the sticky header to 98 CSS pixels, but primer widgets still used a 72-pixel scroll margin. Shared navigation now measures its actual height (including resizing and touch layout), and root scroll padding keeps anchor targets clear. The old widget-specific offset is removed.
- **Invisible ray paths.** `V.el` set SVG fill/stroke through inline styles, then replaced the entire style attribute when opacity was provided. It now merges authored CSS without erasing colours. Tomography rays and primary paths in the multiples schematic are visibly restored.
- **Broken toolkit citations.** Nested child arrays were flattened only one level, converting anchors to `[object HTMLAnchorElement]` strings. The builder now recursively flattens child arrays while retaining real DOM nodes. This also removes the primer's remaining narrow-screen text overflow.
- **Incorrect button names.** Segmented button groups were wrapped in a label, which implicitly labelled only the first button with the entire group's text. They now use a non-label wrapper and the existing group accessible name, preserving each button's own name.
- **Mobile overflow.** Long status badges, tags and control groups now wrap. Grid tracks can shrink within narrow containers. Touch subnavigation has enough height for its controls. Wide data tables remain horizontally scrollable inside their existing containers.
- **Smoke-test reporting.** The jsdom smoke runner now exits with failure for detected errors or missing pages, instead of only printing a message.

## Validation

- All 11 pages passed Chromium browser checks at 1440, 390 and 320 pixels: **33 page/viewport cases**. Mobile cases include touch media emulation.
- Exercised segmented groups, sliders, checkboxes, chart/table switches, literature search, primer aperture and multiple-path controls. Checked navigation states, same-page anchor targets, loaded assets/images, rendered DOM text and page overflow.
- Explicit rendering regressions verify computed ray strokes and opacity, nested citation links, and section positions below the actual sticky header. Primer screenshots reviewed in light and dark themes; review images are in git-ignored `out/site-review/`.
- All 11 jsdom page smoke tests passed; all **18 primer numerical tests** passed; salt asset checks passed.
- The focused salt-browser suite passed, including camera/slice controls, mobile layout, missing-asset retry, WebGL context loss/recovery, and static fallbacks.
- Local HTML page/asset paths resolve and `git diff --check` passes.

Browser suite: `scripts/test_site_browser.cjs`. Run against a local HTTP server with Playwright installed; see its header and the repository README. Chromium used software WebGL in this environment. This review does not certify Safari/Firefox or the availability of external literature websites. No deployment was performed.
