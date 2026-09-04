import pandas as pd

from zumbahua_access.education import compare_periods, filter_zumbahua, summarize_history


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Anio_lectivo": "2017-2018 Inicio",
                "Provincia": "COTOPAXI",
                "Canton": "PUJILÍ",
                "Parroquia": "ZUMBAHUA",
                "AMIE": "A",
                "Total_Docentes": 10,
                "Total_Estudiantes": 100,
            },
            {
                "Anio_lectivo": "2024-2025 Inicio",
                "Provincia": "COTOPAXI",
                "Canton": "PUJILI",
                "Parroquia": "ZUMBAHUA",
                "AMIE": "A",
                "Total_Docentes": 8,
                "Total_Estudiantes": 60,
            },
            {
                "Anio_lectivo": "2024-2025 Inicio",
                "Provincia": "PICHINCHA",
                "Canton": "QUITO",
                "Parroquia": "ZUMBAHUA",
                "AMIE": "X",
                "Total_Docentes": 99,
                "Total_Estudiantes": 999,
            },
        ]
    )


def test_filter_zumbahua_handles_accented_canton() -> None:
    filtered = filter_zumbahua(sample_frame())
    assert len(filtered) == 2
    assert set(filtered["AMIE"]) == {"A"}


def test_summary_and_comparison() -> None:
    summary = summarize_history(sample_frame())
    assert summary["estudiantes"].tolist() == [100, 60]
    comparison = compare_periods(summary, "2017-2018 Inicio", "2024-2025 Inicio")
    students = comparison.loc[comparison["indicador"] == "estudiantes"].iloc[0]
    assert students["cambio_absoluto"] == -40
    assert students["cambio_relativo"] == -0.4

