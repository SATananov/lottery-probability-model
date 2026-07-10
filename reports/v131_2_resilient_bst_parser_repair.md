# Step 131.2 — Resilient BST 6/49 Parser & HTML Variant Fallback

This repair strengthens the shared BST 6/49 index parser used by Steps 123, 126, 129 and 131.

Supported candidate strategies:

- standard and absolute `/results/6x49/YYYY-DRAW` links;
- escaped SPA/JSON URLs;
- visible `Тираж N - YYYY` selector text;
- visible `Тираж N - DD.MM.YYYY` main-result text;
- structured script payloads containing 6/49 context and draw year/number.

When no candidate is recognized, the detection report records the HTML SHA-256, response size and marker diagnostics. The behavior remains fail-closed and does not change production draw data.
