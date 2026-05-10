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
        raise ExcelDataError(f"Το αρχείο δώρων δεν υπάρχει: {file_path}")

    try:
        dataframe = pd.read_excel(path, header=None, engine="openpyxl")
    except Exception as exc:
        raise ExcelDataError(f"Αποτυχία ανάγνωσης αρχείου Excel δώρων: {exc}") from exc

    if dataframe.empty:
        raise ExcelDataError("Το αρχείο Excel είναι κενό")

    first_column = dataframe.iloc[:, 0]
    prizes = [str(value).strip() for value in first_column if pd.notna(value) and str(value).strip()]

    if not prizes:
        raise ExcelDataError("Δεν βρέθηκαν έγκυρα δώρα στην πρώτη στήλη")

    return prizes


def save_results_to_excel(results: list[dict[str, str]], file_path: str | Path) -> None:
    """Save draw results in exactly two columns: Prize, Drawn Ticket."""
    if not results:
        raise ExcelDataError("Δεν υπάρχουν αποτελέσματα κλήρωσης για εξαγωγή")

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
        raise ExcelDataError(f"Αποτυχία αποθήκευσης αποτελεσμάτων σε Excel: {exc}") from exc
