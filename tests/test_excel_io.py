import tempfile
import unittest
from pathlib import Path

import pandas as pd

from lottery_draw_app.excel_io import load_prizes_from_excel, save_results_to_excel


class ExcelIoTests(unittest.TestCase):
    def test_load_prizes_reads_first_column(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "prizes.xlsx"
            pd.DataFrame({0: ["Gift 1", "Gift 2"], 1: ["ignore", "ignore"]}).to_excel(
                path, index=False, header=False
            )

            prizes = load_prizes_from_excel(path)
            self.assertEqual(prizes, ["Gift 1", "Gift 2"])

    def test_save_results_creates_two_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.xlsx"
            save_results_to_excel(
                [{"Prize": "Gift 1", "Drawn Ticket": "Α01"}, {"Prize": "Gift 2", "Drawn Ticket": "Β11"}],
                path,
            )

            dataframe = pd.read_excel(path, engine="openpyxl")
            self.assertEqual(list(dataframe.columns), ["Prize", "Drawn Ticket"])
            self.assertEqual(len(dataframe), 2)


if __name__ == "__main__":
    unittest.main()
