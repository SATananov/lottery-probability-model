from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "docs/PROJECT_CONTEXT.md",
    ROOT / "reports" / "RESEARCH_NOTE_NEURAL_DYNAMICAL_SYSTEMS_REFERENCE.md",
    ROOT / "reports" / "STEP_143_1_PERSONAL_PROJECT_DOCUMENTATION_LANGUAGE_AND_RELEASE_INTEGRITY.md",
]
for path in required:
    assert path.is_file(), f"Missing required Step 143.1 file: {path.relative_to(ROOT)}"

readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "личен експериментален проект" in readme.lower()
assert "Стефан Тананов" in readme

verify_122 = (ROOT / "scripts" / "verify_step_122.py").read_text(encoding="utf-8")
assert "build_freshness_report(write_outputs=False)" in verify_122
assert "build_freshness_report(write_outputs=True)" not in verify_122

step_125 = (ROOT / "src" / "v125_unified_downstream_refresh_engine.py").read_text(encoding="utf-8")
assert "stage['kind'] == 'internal' and runner is None" in step_125

forbidden_fragments = [
    "историческа проверкаing",
    "Advanced Statistical Комбиниран анализ Model",
    "Lottery ML Extensions Комбиниран анализ",
    "statistical оптимизаторът",
    "not a гаранция",
    "статистическа референция portfolio",
]
for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".py", ".md", ".txt", ".json"}:
        continue
    if path.name in {"release-manifest.json", "verify_step_143_1.py"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for fragment in forbidden_fragments:
        assert fragment not in text, f"Malformed mixed-language fragment remains in {path.relative_to(ROOT)}: {fragment}"

for json_path in ROOT.rglob("*.json"):
    json.loads(json_path.read_text(encoding="utf-8"))

research = required[1].read_text(encoding="utf-8")
assert "no claim is made that the illustrated method has been implemented" in research
assert "No continuous neural dynamical-system code" in research

print("STEP_143_1_VERIFY_OK")
