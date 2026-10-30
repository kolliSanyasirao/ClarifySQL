"""Download and safely extract the public SPIDER dataset for ClarifySQL."""

from __future__ import annotations

import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import requests

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / ".vscode" / "combined_data_all" / "spider"
DOWNLOAD_URL = (
    "https://huggingface.co/datasets/"
    "sanyasirao87/clarifysql-spider-data/resolve/main/spider_data.zip?download=true"
)


def download_archive(archive_path: Path) -> None:
    print("Downloading SPIDER dataset from Hugging Face...")
    with requests.get(
        DOWNLOAD_URL,
        stream=True,
        allow_redirects=True,
        timeout=(30, 180),
    ) as response:
        response.raise_for_status()
        total_bytes = 0
        with archive_path.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
                    total_bytes += len(chunk)
                    print(
                        f"\rDownloaded {total_bytes / (1024 * 1024):.1f} MB",
                        end="",
                        flush=True,
                    )
    print("\nDownload complete.")


def extract_archive(archive_path: Path) -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    destination_root = DESTINATION.resolve()
    extracted_files = 0

    print(f"Extracting SPIDER dataset into {DESTINATION}...")
    with zipfile.ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            parts = member.parts

            # The uploaded ZIP has a top-level spider_data/ directory.
            # Ignore macOS metadata and any files outside spider_data/.
            if not parts or parts[0] != "spider_data":
                continue
            relative_parts = parts[1:]
            if not relative_parts:
                continue
            if "__MACOSX" in relative_parts or ".DS_Store" in relative_parts:
                continue
            if any(part in ("", ".", "..") for part in relative_parts):
                raise ValueError(f"Unsafe archive path: {info.filename}")

            # Do not extract symbolic links from the ZIP.
            unix_mode = info.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                continue

            target = DESTINATION.joinpath(*relative_parts).resolve()
            try:
                target.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError(
                    f"Archive path escapes destination: {info.filename}"
                ) from exc

            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            extracted_files += 1

    tables_file = DESTINATION / "tables.json"
    database_dir = DESTINATION / "database"
    if not tables_file.is_file():
        raise RuntimeError(f"tables.json is missing after extraction: {tables_file}")
    if not database_dir.is_dir():
        raise RuntimeError(f"database/ is missing after extraction: {database_dir}")

    database_count = sum(1 for item in database_dir.iterdir() if item.is_dir())
    print("SPIDER dataset is ready.")
    print(f"Extracted files: {extracted_files}")
    print(f"Database folders: {database_count}")
    print(f"Dataset path: {DESTINATION}")
    return extracted_files


def main() -> None:
    tables_file = DESTINATION / "tables.json"
    database_dir = DESTINATION / "database"
    if tables_file.is_file() and database_dir.is_dir():
        print(f"SPIDER dataset already exists at {DESTINATION}")
        return

    with tempfile.TemporaryDirectory(prefix="clarifysql-spider-") as temp_dir:
        archive_path = Path(temp_dir) / "spider_data.zip"
        download_archive(archive_path)
        extract_archive(archive_path)


if __name__ == "__main__":
    main()
