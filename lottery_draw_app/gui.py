"""CustomTkinter desktop application UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from lottery_draw_app.draw import DrawResult, run_draw
from lottery_draw_app.excel_io import ExcelDataError, load_prizes_from_excel, save_results_to_excel
from lottery_draw_app.tickets import (
    TicketValidationError,
    filter_excluded_in_range,
    generate_ticket_range,
    parse_excluded_tickets,
)


class LotteryDrawApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Lottery Draw App")
        self.geometry("980x640")
        self.minsize(900, 560)

        self.prizes: list[str] = []
        self.draw_results: list[DrawResult] = []

        self._build_ui()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, corner_radius=12)
        container.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(container, text="Raffle / Lottery Draw", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        left_panel = ctk.CTkFrame(container, fg_color="transparent")
        left_panel.grid(row=1, column=0, rowspan=4, padx=(16, 10), pady=8, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_panel, text="Prizes Excel file", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )

        self.prize_file_var = tk.StringVar(value="No file selected")
        ctk.CTkLabel(left_panel, textvariable=self.prize_file_var, wraplength=360, justify="left").grid(
            row=1, column=0, pady=(4, 8), sticky="w"
        )

        ctk.CTkButton(left_panel, text="Import prizes from Excel", command=self._import_prizes).grid(
            row=2, column=0, pady=(0, 12), sticky="ew"
        )

        ctk.CTkLabel(left_panel, text="Start ticket", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w")
        self.start_entry = ctk.CTkEntry(left_panel, placeholder_text="e.g. Α01")
        self.start_entry.grid(row=4, column=0, pady=(4, 8), sticky="ew")
        self.start_entry.insert(0, "Α01")

        ctk.CTkLabel(left_panel, text="End ticket", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w")
        self.end_entry = ctk.CTkEntry(left_panel, placeholder_text="e.g. Η23")
        self.end_entry.grid(row=6, column=0, pady=(4, 8), sticky="ew")
        self.end_entry.insert(0, "Α100")

        ctk.CTkLabel(left_panel, text="Excluded tickets (comma / space / newline separated)", font=ctk.CTkFont(weight="bold")).grid(
            row=7, column=0, sticky="w"
        )
        self.excluded_text = ctk.CTkTextbox(left_panel, height=95)
        self.excluded_text.grid(row=8, column=0, pady=(4, 10), sticky="nsew")

        stats_frame = ctk.CTkFrame(left_panel)
        stats_frame.grid(row=9, column=0, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)

        self.prize_count_var = tk.StringVar(value="Prizes: 0")
        self.ticket_count_var = tk.StringVar(value="Available tickets: 0")
        ctk.CTkLabel(stats_frame, textvariable=self.prize_count_var).grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(stats_frame, textvariable=self.ticket_count_var).grid(row=0, column=1, padx=8, pady=8, sticky="e")

        right_panel = ctk.CTkFrame(container)
        right_panel.grid(row=1, column=1, rowspan=4, padx=(10, 16), pady=8, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(right_panel, text="Draw actions", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 8), sticky="w"
        )

        actions = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(actions, text="Run draw", command=self._confirm_and_draw).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Export results to Excel", command=self._export_results).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        ctk.CTkLabel(right_panel, text="Results (Prize → Drawn Ticket)", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=12, pady=(8, 4), sticky="w"
        )

        self.results_table = ctk.CTkTextbox(right_panel)
        self.results_table.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.results_table.configure(state="disabled")

        self.status_var = tk.StringVar(value="Status: Ready")
        ctk.CTkLabel(container, textvariable=self.status_var, anchor="w").grid(
            row=5, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew"
        )

    def _set_results_text(self, lines: list[str]) -> None:
        self.results_table.configure(state="normal")
        self.results_table.delete("1.0", "end")
        self.results_table.insert("1.0", "\n".join(lines) if lines else "No draw results yet.")
        self.results_table.configure(state="disabled")

    def _import_prizes(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select prizes Excel file",
            filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*")),
        )
        if not file_path:
            return

        try:
            self.prizes = load_prizes_from_excel(file_path)
        except ExcelDataError as exc:
            messagebox.showerror("Prize Import Error", str(exc))
            return

        self.prize_file_var.set(file_path)
        self.prize_count_var.set(f"Prizes: {len(self.prizes)}")
        self.status_var.set(f"Status: Imported {len(self.prizes)} prizes")

    def _build_available_tickets(self) -> list[str]:
        start_ticket = self.start_entry.get().strip()
        end_ticket = self.end_entry.get().strip()

        tickets = generate_ticket_range(start_ticket, end_ticket)
        excluded_raw = self.excluded_text.get("1.0", "end").strip()
        excluded = parse_excluded_tickets(excluded_raw) if excluded_raw else []

        available = filter_excluded_in_range(tickets, excluded)
        self.ticket_count_var.set(f"Available tickets: {len(available)}")
        return available

    def _confirm_and_draw(self) -> None:
        if not self.prizes:
            messagebox.showerror("Missing Data", "Please import prizes from Excel before drawing.")
            return

        if not messagebox.askyesno(
            "Confirm Draw",
            "Are you sure you want to run the draw? This will replace current results.",
        ):
            return

        try:
            available_tickets = self._build_available_tickets()
            self.draw_results = run_draw(self.prizes, available_tickets)
        except (TicketValidationError, ValueError) as exc:
            messagebox.showerror("Draw Error", str(exc))
            return

        lines = [f"{index}. {result.prize} -> {result.drawn_ticket}" for index, result in enumerate(self.draw_results, start=1)]
        self._set_results_text(lines)
        self.status_var.set(f"Status: Draw completed for {len(self.draw_results)} prizes")

    def _export_results(self) -> None:
        if not self.draw_results:
            messagebox.showerror("No Results", "Run a draw first, then export the results.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save draw results",
            defaultextension=".xlsx",
            filetypes=(("Excel files", "*.xlsx"),),
        )
        if not file_path:
            return

        export_rows = [{"Prize": result.prize, "Drawn Ticket": result.drawn_ticket} for result in self.draw_results]

        try:
            save_results_to_excel(export_rows, file_path)
        except ExcelDataError as exc:
            messagebox.showerror("Export Error", str(exc))
            return

        self.status_var.set(f"Status: Results exported to {file_path}")
        messagebox.showinfo("Export Complete", "Draw results were exported successfully.")


def run_app() -> None:
    app = LotteryDrawApp()
    app.mainloop()
