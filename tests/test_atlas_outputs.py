from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_geocoded_inventory_is_complete_and_inside_study_bbox() -> None:
    schools = pd.read_csv(ROOT / "atlas" / "data" / "instituciones_educativas_2024_2025.csv")
    assert len(schools) == 19
    assert schools["codigo_amie"].nunique() == 19
    assert schools["longitud"].between(-78.9933325, -78.8079605).all()
    assert schools["latitud"].between(-1.0708598, -0.8601922).all()
    assert schools["confianza_coordenada"].value_counts().to_dict() == {
        "alta": 18,
        "media": 1,
    }


def test_network_coverage_is_monotonic() -> None:
    coverage = pd.read_csv(ROOT / "atlas" / "data" / "cobertura_longitud_red_preliminar.csv")
    for _, group in coverage.groupby("nivel"):
        ordered = group.sort_values("umbral_min")["red_cubierta_pct"]
        assert ordered.is_monotonic_increasing
        assert ordered.between(0, 100).all()
