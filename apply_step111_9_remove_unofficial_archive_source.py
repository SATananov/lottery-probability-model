from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path.cwd()
PATCH_ROOT = ROOT / "step111_9_remove_unofficial_archive_source_patch_files"

FILES = {
    "scripts/v111_9_remove_unofficial_archive_source.py": "scripts/v111_9_remove_unofficial_archive_source.py",
}


def main() -> None:
    if not (ROOT / "streamlit_app.py").exists():
        raise RuntimeError("Не открих streamlit_app.py. Стартирай patch-а от основната папка на проекта.")
    if not PATCH_ROOT.exists():
        raise RuntimeError(f"Липсва папка с patch файлове: {PATCH_ROOT}")
    for src_rel, dst_rel in FILES.items():
        src = PATCH_ROOT / src_rel
        dst = ROOT / dst_rel
        if not src.exists():
            raise RuntimeError(f"Липсва patch файл: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    subprocess.run([sys.executable, "scripts/v111_9_remove_unofficial_archive_source.py"], check=True)
    print("STEP_111_9_PATCH_APPLIED")
    print("Next: python -m compileall -q streamlit_app.py src scripts")
    print(r"Next: python .\scripts\v111_9_remove_unofficial_archive_source.py")


if __name__ == "__main__":
    main()
