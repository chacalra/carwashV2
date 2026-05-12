"""Tests para helpers de ui/dashboard.py."""

import pandas as pd

from frontend.streamlit.ui.dashboard import _donut_chart


def test_donut_chart_handles_zero_total_without_nan():
    df, spec = _donut_chart(
        pd.DataFrame(
            [
                {"name": "Lavado", "total": 0},
                {"name": "Perfume", "total": 0},
            ]
        ),
        "Item",
    )

    assert df["pct"].tolist() == [0, 0]
    assert spec["mark"]["type"] == "arc"
