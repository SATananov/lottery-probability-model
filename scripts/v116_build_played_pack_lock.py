from __future__ import annotations

import importlib.util
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION_PATH = ROOT / "src" / "v116_played_pack_lock_section.py"
SCRIPT_PATH = ROOT / "scripts" / "v116_build_played_pack_lock.py"


def _bad_markers() -> list[str]:
    markers = []
    for rel in ["src/v116_played_pack_lock_section.py", "scripts/v116_build_played_pack_lock.py"]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        if ("?" * 4) in text or chr(0xFFFD) in text:
            markers.append(rel)
    return markers


def main() -> int:
    failures: list[str] = []
    report = {}
    for path, label in [(SECTION_PATH, "section"), (SCRIPT_PATH, "script")]:
        if not path.exists():
            failures.append(f"Липсва {label}: {path}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            failures.append(f"Compile error {label}: {exc}")

    if not failures:
        try:
            spec = importlib.util.spec_from_file_location("v116_played_pack_lock_section", SECTION_PATH)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)
            report = module.build_report()
        except Exception as exc:
            failures.append(f"Report build error: {exc}")

    bad = _bad_markers()
    if bad:
        failures.append("Съмнителна кирилица: " + ", ".join(bad))

    status = "PLAYED_PACK_LOCK_READY" if not failures else "CHECK_REQUIRED"
    print(f"STEP_116_STATUS {status}")
    print(f"BLOCKING_FAILURES {len(failures)}")
    if report:
        print(f"REPORT_STATUS {report.get('status')}")
        print(f"TICKETS {report.get('ticket_count', 0)}")
        print(f"LINES {report.get('line_count', 0)}")
        print(f"TOTAL_PRICE_EUR {report.get('total_price_eur', 0)}")
    print(f"BAD_COUNT {len(bad)}")
    for failure in failures:
        print("FAILURE", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
