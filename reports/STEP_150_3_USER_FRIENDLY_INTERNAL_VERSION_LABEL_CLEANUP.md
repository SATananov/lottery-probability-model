# Step 150.3 — User-Friendly Internal Version Label Cleanup

## Purpose

Step 150.3 removes internal labels such as `V1`, `v41`, `v94` and similar development identifiers from the normal user interface. These values describe internal generations of modules, workflows or stored artifacts. They are useful for maintenance, but they do not explain anything meaningful to a normal user.

## User-facing behavior

In normal Bulgarian mode:

- `V1 работен процес` becomes `работният процес`;
- `V1 lock` becomes `финалното заключване`;
- `V94 активен <timestamp>` becomes `Активният план е наличен`;
- labels such as `Последни прогнози — v41` become `Последни прогнози`;
- ranges such as `v41 → v71` become a plain description of the full model chain;
- internal version suffixes are removed from cards, metrics, table cells, explanations and status messages;
- file paths, model identifiers and exact version numbers remain available only when technical details are enabled.

## Scope

The cleanup is applied globally through the Streamlit display layer, so it covers:

- all active modules and pages;
- metrics, banners, captions and explanatory text;
- tables and nested JSON values;
- dynamic values loaded from model and report files;
- status codes and workflow descriptions.

## Safety boundaries

- Display-only change.
- No training or scoring logic changed.
- No historical result changed.
- No prospective lock changed.
- No personal journal data used or packaged.
- Exact internal versions remain available in technical-details mode.

## Verification

The Step 150.3 audit scans Python UI literals and dynamic JSON/CSV values containing internal version labels. Every candidate is rendered through the normal-mode cleanup and checked to confirm that no internal `Vxx` token remains. Separate regression cases cover the exact text reported in the browser screenshots.
