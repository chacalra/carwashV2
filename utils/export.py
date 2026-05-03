"""Utilidades para exportacion de datos."""

from io import BytesIO

import pandas as pd


def build_export_filename(prefix, start_date, end_date, extension):
    """Construye un nombre de archivo simple y consistente."""
    return f"{prefix}_{start_date}_a_{end_date}.{extension}"


def export_dataframe_to_csv(df):
    """Convierte un DataFrame a CSV en bytes."""
    return df.to_csv(index=False).encode("utf-8")


def export_dataframe_to_excel(df_dict):
    """Convierte uno o varios DataFrames a un archivo Excel en memoria."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, dataframe in df_dict.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    return output.getvalue()
