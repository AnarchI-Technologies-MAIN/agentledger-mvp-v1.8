from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

RELEASE_VERSION = "0.1.0"
ARCHIVE_NAME = f"Stewardence-Collector-Windows-x64-v{RELEASE_VERSION}.zip"
FIXED_ZIP_TIME = (2026, 9, 4, 0, 0, 0)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode()


def write_deterministic_zip(destination: Path, release_files: dict[str, Path]):
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, source in sorted(release_files.items()):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def build_executable(repository: Path, destination: Path):
    entrypoint = destination.parent / "collector-entrypoint.py"
    entrypoint.write_text(
        "from collector.__main__ import main\n\nmain()\n",
        encoding="utf-8",
    )
    subprocess.run(  # noqa: S603 - fixed interpreter and build arguments.
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--noupx",
            "--onefile",
            "--console",
            "--name",
            destination.stem,
            "--paths",
            str(repository),
            "--distpath",
            str(destination.parent),
            "--workpath",
            str(destination.parent / "build"),
            "--specpath",
            str(destination.parent),
            str(entrypoint),
        ],
        cwd=repository,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    collector = repository / "collector"
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    private_key = serialization.load_pem_private_key(
        args.private_key.read_bytes(), password=None
    )
    public_key_path = collector / "collector-profile-public.pem"
    tracked_public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if private_key.public_key().public_numbers() != tracked_public_key.public_numbers():
        raise ValueError("Private key does not match the tracked Collector public key")

    with tempfile.TemporaryDirectory(dir=output) as temporary_name:
        temporary = Path(temporary_name)
        executable = temporary / "Stewardence-Collector.exe"
        build_executable(repository, executable)

        manifest = collector / "collector-modules.json"
        public_der = tracked_public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        profile = {
            "artifact": {
                "name": executable.name,
                "sha256": sha256(executable),
            },
            "collector_version": RELEASE_VERSION,
            "enabled_modules": ["windows.installed_programs"],
            "module_manifest": {
                "name": manifest.name,
                "sha256": sha256(manifest),
                "version": "1",
            },
            "profile_id": "stewardence-windows-one-shot-mvp",
            "profile_schema_version": 1,
            "public_key_sha256": hashlib.sha256(public_der).hexdigest(),
            "release_version": RELEASE_VERSION,
        }
        profile_path = temporary / "collector-profile.json"
        profile_path.write_bytes(canonical_json(profile))
        signature = private_key.sign(
            profile_path.read_bytes(), padding.PKCS1v15(), hashes.SHA256()
        )
        signature_path = temporary / "collector-profile.sig"
        signature_path.write_text(base64.b64encode(signature).decode() + "\n")

        archive_path = output / ARCHIVE_NAME
        write_deterministic_zip(
            archive_path,
            {
                executable.name: executable,
                "Stewardence-Collector.ps1": collector / "Stewardence-Collector.ps1",
                "README.txt": collector / "RELEASE_README.txt",
                manifest.name: manifest,
                profile_path.name: profile_path,
                "collector-profile-public.pem": public_key_path,
                signature_path.name: signature_path,
            },
        )
        metadata = {
            "archive_name": ARCHIVE_NAME,
            "archive_sha256": sha256(archive_path),
            "artifact_sha256": profile["artifact"]["sha256"],
            "profile_sha256": sha256(profile_path),
            "public_key_sha256": profile["public_key_sha256"],
            "release_version": RELEASE_VERSION,
        }
        (output / "release-metadata.json").write_bytes(canonical_json(metadata))
        print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
