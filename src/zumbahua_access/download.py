from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

USER_AGENT = (
    "zumbahua-accessibility-research/0.1 "
    "(https://github.com/diegocevallos-tech/accesibilidad-educativa-zumbahua)"
)


@dataclass(frozen=True)
class Source:
    key: str
    filename: str
    url: str


SOURCES = {
    "mineduc_history": Source(
        key="mineduc_history",
        filename="registro-administrativo-historico_2009-2024-inicio.csv",
        url=(
            "https://www.datosabiertos.gob.ec/dataset/"
            "5d1838d2-4efb-44a3-8c36-eebb5a8f798a/resource/"
            "59db7bb5-eb6b-4a7a-a06a-d1f93ac7506a/download/"
            "registro-administrativo-historico_2009-2024-inicio.csv"
        ),
    ),
    "mineduc_typologies": Source(
        key="mineduc_typologies",
        filename="registros-administrativos_2024-2025_tipologias.xlsx",
        url=(
            "https://educacion.gob.ec/wp-content/uploads/downloads/2025/04/"
            "Registros-administrativos_2024-2025_Tipologias.xlsx"
        ),
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_source(source: Source, raw_dir: Path, overwrite: bool = False) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / source.filename
    if destination.exists() and not overwrite:
        return destination

    request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
    partial = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)
    partial.replace(destination)

    metadata = {
        **asdict(source),
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "sha256": sha256(destination),
        "bytes": destination.stat().st_size,
    }
    destination.with_suffix(destination.suffix + ".metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return destination


def download_education(raw_dir: Path, overwrite: bool = False) -> list[Path]:
    return [download_source(source, raw_dir, overwrite) for source in SOURCES.values()]

