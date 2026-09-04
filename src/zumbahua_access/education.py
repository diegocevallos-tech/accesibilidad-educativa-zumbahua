from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

EXPECTED_HISTORY_COLUMNS = {
    "Anio_lectivo",
    "Provincia",
    "Canton",
    "Parroquia",
    "AMIE",
    "Total_Docentes",
    "Total_Estudiantes",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in text if not unicodedata.combining(char)).upper().strip()


def load_history(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";", low_memory=False)
    missing = EXPECTED_HISTORY_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Columnas ausentes: {sorted(missing)}")
    return frame


def filter_zumbahua(frame: pd.DataFrame) -> pd.DataFrame:
    province = frame["Provincia"].map(normalize_text)
    canton = frame["Canton"].map(normalize_text)
    parish = frame["Parroquia"].map(normalize_text)
    mask = (
        province.eq("COTOPAXI")
        & canton.eq("PUJILI")
        & parish.eq("ZUMBAHUA")
    )
    return frame.loc[mask].copy()


def summarize_history(frame: pd.DataFrame) -> pd.DataFrame:
    local = filter_zumbahua(frame)
    for column in ("Total_Docentes", "Total_Estudiantes"):
        local[column] = pd.to_numeric(local[column], errors="coerce")

    summary = (
        local.groupby("Anio_lectivo", sort=False)
        .agg(
            instituciones=("AMIE", "nunique"),
            estudiantes=("Total_Estudiantes", "sum"),
            docentes=("Total_Docentes", "sum"),
        )
        .reset_index()
        .rename(columns={"Anio_lectivo": "periodo"})
    )
    return summary


def compare_periods(summary: pd.DataFrame, baseline: str, current: str) -> pd.DataFrame:
    indexed = summary.set_index("periodo")
    if baseline not in indexed.index or current not in indexed.index:
        raise KeyError("Los periodos solicitados no están presentes en la serie")

    rows = []
    for indicator in ("instituciones", "estudiantes", "docentes"):
        old = float(indexed.loc[baseline, indicator])
        new = float(indexed.loc[current, indicator])
        rows.append(
            {
                "indicador": indicator,
                "baseline": old,
                "actual": new,
                "cambio_absoluto": new - old,
                "cambio_relativo": (new / old - 1) if old else pd.NA,
            }
        )
    return pd.DataFrame(rows)

