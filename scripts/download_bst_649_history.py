from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_importer import import_bst_history


def main() -> None:
    result = import_bst_history()

    print("BST 6/49 official data import")
    print("-" * 40)
    print(f"Archive links discovered/generated: {result['links_discovered']}")
    print(f"Fresh imported rows: {result['fresh_imported_rows']}")
    print(f"Backup rows considered: {result['backup_rows_considered']}")
    print(f"Final rows imported: {result['rows_imported']}")
    print(f"Year range: {result['year_min']} to {result['year_max']}")
    print(f"Missing years 1958-2025: {result['missing_years']}")
    print(f"CSV saved to: {result['csv_path']}")
    print(f"Report saved to: {result['report_path']}")

    warnings = result.get("warnings", [])
    if warnings:
        print("Warnings:")
        for warning in warnings[:20]:
            print(f"- {warning}")
        if len(warnings) > 20:
            print(f"... plus {len(warnings) - 20} more warnings")


if __name__ == "__main__":
    main()
