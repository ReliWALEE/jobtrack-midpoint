"""Package allowlisted repository files for the AWS bootstrap's JobTrack/ path."""
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "JobTrack-source.zip"
DIRECTORIES = ("web", "extension", "tests", "deploy", "docs", "presentation", ".github")
FILES = ("jobs.py", "account_factory.py", ".env.example", "server.py", "seed_demo.py", "requirements.txt", "README.md", "Dockerfile", ".gitignore", ".dockerignore")

def main():
    selected = [ROOT / name for name in FILES if (ROOT / name).is_file()]
    for directory in DIRECTORIES:
        selected.extend(p for p in (ROOT / directory).rglob("*")
                        if p.is_file() and not p.is_symlink()
                        and "__pycache__" not in p.parts
                        and p.suffix not in (".pyc", ".sqlite3")
                        and p.name != ".env")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(selected):
            info = zipfile.ZipInfo.from_file(path, Path("JobTrack") / path.relative_to(ROOT))
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(f"Created {OUTPUT} with {len(selected)} files")

if __name__ == "__main__":
    main()
