"""Excel import/export helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelDataError(ValueError):
    """Raised when data loaded from Excel is invalid."""


def load_prizes_from_excel(file_path: str | Path) -> list[str]:
    """Load one prize per row from the first column of an Excel file."""
    path = Path(file_path)
    if not path.exists():
        raise ExcelDataError(f"Prize file does not exist: {file_path}")

    try:
        dataframe = pd.read_excel(path, header=None, engine="openpyxl")
    except Exception as exc:
        raise ExcelDataError(f"Failed to read Excel prize file: {exc}") from exc

    if dataframe.empty:
        raise ExcelDataError("Excel file is empty")

    first_column = dataframe.iloc[:, 0]
    prizes = [str(value).strip() for value in first_column if pd.notna(value) and str(value).strip()]

    if not prizes:
        raise ExcelDataError("No valid prizes found in first column")

    return prizes


def save_results_to_excel(results: list[dict[str, str]], file_path: str | Path) -> None:
    """Save draw results in exactly two columns: Prize, Drawn Ticket."""
    if not results:
        raise ExcelDataError("No draw results available to export")

    normalized_results = [
        {
            "Prize": row["Prize"],
            "Drawn Ticket": row["Drawn Ticket"],
        }
        for row in results
    ]

    dataframe = pd.DataFrame(normalized_results, columns=["Prize", "Drawn Ticket"])
    output_path = Path(file_path)

    try:
        dataframe.to_excel(output_path, index=False, engine="openpyxl")
    except Exception as exc:
        raise ExcelDataError(f"Failed to save results to Excel: {exc}") from exc
