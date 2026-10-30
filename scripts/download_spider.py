"""Download and extract the public SPIDER dataset for ClarifySQL."""

from __future__ import annotations

import os
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from huggingface_hub import hf_hub_download


ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / ".vscode" / "combined_data_all" / "spider"
REPOSITORY_ID = os.getenv(
    "SPIDER_HF_REPO",
    "sanyasirao87/clarifysql-spider-data",
)
ARCHIVE_NAME = "spider_data.zip"


def main() -> None:
    tables_file = DESTINATION / "tables.json"
    database_dir = DESTINATION / "database"

    if tables_file.is_file() and database_dir.is_dir():
        print(f"SPIDER dataset already exists at {DESTINATION}")
        return

    print(f"Downloading {ARCHIVE_NAME} from {REPOSITORY_ID}...")
    archive_path = hf_hub_download(
        repo_id=REPOSITORY_ID,
        filename=ARCHIVE_NAME,
        repo_type="dataset",
    )

    DESTINATION.mkdir(parents=True, exist_ok=True)
    destination_root = DESTINATION.resolve()
    extracted_files = 0

    print(f"Extracting SPIDER dataset into {DESTINATION}...")

    with zipfile.ZipFile(archive_path, "r") as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            parts = member.parts

            # The uploaded archive has a top-level spider_data/ directory.
            # Ignore __MACOSX metadata and anything outside spider_data/.
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

    if not tables_file.is_file():
        raise RuntimeError(
            f"SPIDER extraction finished, but tables.json is missing: {tables_file}"
        )

    if not database_dir.is_dir():
        raise RuntimeError(
            f"SPIDER extraction finished, but database/ is missing: {database_dir}"
        )

    database_count = sum(1 for item in database_dir.iterdir() if item.is_dir())
    print("SPIDER dataset is ready.")
    print(f"Extracted files: {extracted_files}")
    print(f"Database folders: {database_count}")
    print(f"Dataset path: {DESTINATION}")


if __name__ == "__main__":
    main()
