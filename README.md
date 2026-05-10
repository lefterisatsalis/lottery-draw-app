# Lottery Draw App

A polished Python desktop application for raffle/lottery draws with Greek ticket support, Excel prize import, and Excel result export.

## Features

- Import prizes from an Excel file (`.xlsx`, one prize per row in the first column)
- Define an inclusive draw range using Greek uppercase ticket format (`Α01` to `Ω100`)
- Exclude specific tickets from the draw (optional)
- Confirmation dialog before running the draw
- Unique winners (no duplicate winning tickets)
- Export results to Excel with exactly 2 columns:
  - `Prize`
  - `Drawn Ticket`
- Modern desktop UI built with `customtkinter`

## Ticket format rules

- Ticket format is: **one Greek uppercase letter + number**
- Valid examples: `Α01`, `Β99`, `Η23`, `Ω100`
- Number range per letter is `1` to `100`
- Draw range is inclusive across letters
  - Example `Α99` to `Β02` includes: `Α99`, `Α100`, `Β01`, `Β02`

## Prize Excel input format

Use a single-column Excel file (first column used):

| Prize |
|---|
| Gift Basket |
| Smart Watch |
| Weekend Trip |

> If additional columns exist, they are ignored.

## Install (Windows / macOS / Linux)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Run locally

```bash
python app.py
```

## Build a Windows `.exe` with PyInstaller

Run these commands on a Windows machine:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

pyinstaller --name LotteryDrawApp --onefile --windowed app.py
```

The executable will be created in:

- `dist\LotteryDrawApp.exe`

## Project structure

```text
app.py
lottery_draw_app/
  __init__.py
  draw.py
  excel_io.py
  gui.py
  tickets.py
requirements.txt
tests/
```

## Run tests

```bash
python -m unittest discover -s tests -v
```
