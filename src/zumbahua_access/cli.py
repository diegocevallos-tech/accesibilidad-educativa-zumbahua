from __future__ import annotations

import argparse
from pathlib import Path

from zumbahua_access.download import download_education
from zumbahua_access.education import compare_periods, load_history, summarize_history

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
TABLE_DIR = ROOT / "reports" / "tables"
HISTORY_FILE = RAW_DIR / "registro-administrativo-historico_2009-2024-inicio.csv"


def command_download(overwrite: bool) -> None:
    for path in download_education(RAW_DIR, overwrite=overwrite):
        print(path)


def command_summary() -> None:
    frame = load_history(HISTORY_FILE)
    summary = summarize_history(frame)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    output = TABLE_DIR / "enrollment_trend.csv"
    summary.to_csv(output, index=False)
    print(summary.to_string(index=False))
    print()
    print(
        compare_periods(summary, "2017-2018 Inicio", "2024-2025 Inicio").to_string(
            index=False
        )
    )
    print(f"\nGuardado: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accesibilidad educativa en Zumbahua")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Descargar fuentes educativas")
    download.add_argument("dataset", choices=["education"])
    download.add_argument("--overwrite", action="store_true")

    subparsers.add_parser("summary", help="Reproducir la serie administrativa")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "download":
        command_download(args.overwrite)
    elif args.command == "summary":
        command_summary()

