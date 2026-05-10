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

        self.title("Εφαρμογή Κλήρωσης Λαχνών")
        self.geometry("1200x780")
        self.minsize(1000, 680)

        self.prizes: list[str] = []
        self.draw_results: list[DrawResult] = []

        self._build_ui()
        self.after(0, self._maximize_on_windows)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, corner_radius=12)
        container.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(container, text="Κλήρωση Λαχνών", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        left_panel = ctk.CTkFrame(container, fg_color="transparent")
        left_panel.grid(row=1, column=0, padx=(16, 10), pady=8, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(left_panel, text="Αρχείο Excel δώρων", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w"
        )

        self.prize_file_var = tk.StringVar(value="Δεν έχει επιλεγεί αρχείο")
        ctk.CTkLabel(left_panel, textvariable=self.prize_file_var, wraplength=360, justify="left").grid(
            row=1, column=0, pady=(4, 8), sticky="w"
        )

        ctk.CTkButton(left_panel, text="Εισαγωγή δώρων από Excel", command=self._import_prizes).grid(
            row=2, column=0, pady=(0, 12), sticky="ew"
        )

        ctk.CTkLabel(left_panel, text="Αρχικός λαχνός", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w")
        self.start_ticket_var = tk.StringVar(value="Α01")
        self.start_entry = ctk.CTkEntry(left_panel, placeholder_text="π.χ. Α01", textvariable=self.start_ticket_var)
        self.start_entry.grid(row=4, column=0, pady=(4, 8), sticky="ew")

        ctk.CTkLabel(left_panel, text="Τελικός λαχνός", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="w")
        self.end_ticket_var = tk.StringVar(value="Α100")
        self.end_entry = ctk.CTkEntry(left_panel, placeholder_text="π.χ. Η23", textvariable=self.end_ticket_var)
        self.end_entry.grid(row=6, column=0, pady=(4, 8), sticky="ew")

        ctk.CTkLabel(left_panel, text="Εξαιρούμενοι λαχνοί (μόνο με κόμμα)", font=ctk.CTkFont(weight="bold")).grid(
            row=7, column=0, sticky="w"
        )
        self.excluded_tickets_var = tk.StringVar(value="")
        self.excluded_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="π.χ. Α05, Β12, Η03",
            textvariable=self.excluded_tickets_var,
        )
        self.excluded_entry.grid(row=8, column=0, pady=(4, 4), sticky="ew")
        ctk.CTkLabel(
            left_panel,
            text="π.χ. Α05, Β12, Η03",
            text_color=("gray40", "gray70"),
            font=ctk.CTkFont(size=12),
        ).grid(row=9, column=0, pady=(0, 10), sticky="w")

        stats_frame = ctk.CTkFrame(left_panel)
        stats_frame.grid(row=10, column=0, sticky="ew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)

        self.prize_count_var = tk.StringVar(value="Δώρα: 0")
        self.ticket_count_var = tk.StringVar(value="Διαθέσιμοι λαχνοί: 0")
        ctk.CTkLabel(
            stats_frame,
            textvariable=self.prize_count_var,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(
            stats_frame,
            textvariable=self.ticket_count_var,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1, padx=10, pady=10, sticky="e")

        right_panel = ctk.CTkFrame(container)
        right_panel.grid(row=1, column=1, padx=(10, 16), pady=8, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(right_panel, text="Ενέργειες κλήρωσης", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 8), sticky="w"
        )

        actions = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        action_button_font = ctk.CTkFont(size=16, weight="bold")
        ctk.CTkButton(
            actions,
            text="Κλήρωση",
            command=self._confirm_and_draw,
            font=action_button_font,
            height=42,
        ).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(
            actions,
            text="Εξαγωγή αποτελεσμάτων σε Excel",
            command=self._export_results,
            font=action_button_font,
            height=42,
        ).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        ctk.CTkLabel(right_panel, text="Αποτελέσματα (Δώρο → Κληρωθείς λαχνός)", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=12, pady=(4, 4), sticky="w"
        )

        self.results_table = ctk.CTkTextbox(right_panel, font=ctk.CTkFont(size=14))
        self.results_table.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.results_table.configure(state="disabled")

        self.status_var = tk.StringVar(value="Κατάσταση: Έτοιμο")
        ctk.CTkLabel(container, textvariable=self.status_var, anchor="w").grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew"
        )

        for var in (self.start_ticket_var, self.end_ticket_var, self.excluded_tickets_var):
            var.trace_add("write", self._refresh_available_ticket_count)
        self._refresh_available_ticket_count()

    def _set_results_text(self, lines: list[str]) -> None:
        self.results_table.configure(state="normal")
        self.results_table.delete("1.0", "end")
        self.results_table.insert("1.0", "\n".join(lines) if lines else "Δεν υπάρχουν ακόμη αποτελέσματα κλήρωσης.")
        self.results_table.configure(state="disabled")

    def _import_prizes(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Επιλογή αρχείου Excel δώρων",
            filetypes=(("Αρχεία Excel", "*.xlsx *.xls"), ("Όλα τα αρχεία", "*.*")),
        )
        if not file_path:
            return

        try:
            self.prizes = load_prizes_from_excel(file_path)
        except ExcelDataError as exc:
            messagebox.showerror("Σφάλμα εισαγωγής δώρων", str(exc))
            return

        self.prize_file_var.set(file_path)
        self.prize_count_var.set(f"Δώρα: {len(self.prizes)}")
        self.status_var.set(f"Κατάσταση: Εισήχθησαν {len(self.prizes)} δώρα")

    def _build_available_tickets(self) -> list[str]:
        start_ticket = self.start_ticket_var.get().strip()
        end_ticket = self.end_ticket_var.get().strip()

        tickets = generate_ticket_range(start_ticket, end_ticket)
        excluded_raw = self.excluded_tickets_var.get().strip()
        excluded = parse_excluded_tickets(excluded_raw) if excluded_raw else []

        available = filter_excluded_in_range(tickets, excluded)
        self.ticket_count_var.set(f"Διαθέσιμοι λαχνοί: {len(available)}")
        return available

    def _refresh_available_ticket_count(self, *_args: object) -> None:
        start_ticket = self.start_ticket_var.get().strip()
        end_ticket = self.end_ticket_var.get().strip()

        if not start_ticket or not end_ticket:
            self.ticket_count_var.set("Διαθέσιμοι λαχνοί: -")
            return

        try:
            tickets = generate_ticket_range(start_ticket, end_ticket)
            excluded_raw = self.excluded_tickets_var.get().strip()
            excluded = parse_excluded_tickets(excluded_raw) if excluded_raw else []
            available = filter_excluded_in_range(tickets, excluded)
        except TicketValidationError:
            self.ticket_count_var.set("Διαθέσιμοι λαχνοί: -")
            return

        self.ticket_count_var.set(f"Διαθέσιμοι λαχνοί: {len(available)}")

    def _confirm_and_draw(self) -> None:
        if not self.prizes:
            messagebox.showerror("Ελλιπή δεδομένα", "Παρακαλώ εισάγετε πρώτα τα δώρα από αρχείο Excel.")
            return

        if not messagebox.askyesno(
            "Επιβεβαίωση κλήρωσης",
            "Θέλετε σίγουρα να γίνει η κλήρωση; Τα τρέχοντα αποτελέσματα θα αντικατασταθούν.",
        ):
            return

        try:
            available_tickets = self._build_available_tickets()
            self.draw_results = run_draw(self.prizes, available_tickets)
        except (TicketValidationError, ValueError) as exc:
            messagebox.showerror("Σφάλμα κλήρωσης", str(exc))
            return

        lines = [
            f"{index}. {result.prize} → {result.drawn_ticket}"
            for index, result in enumerate(self.draw_results, start=1)
        ]
        self._set_results_text(lines)
        self.status_var.set(f"Κατάσταση: Η κλήρωση ολοκληρώθηκε για {len(self.draw_results)} δώρα")

    def _export_results(self) -> None:
        if not self.draw_results:
            messagebox.showerror("Δεν υπάρχουν αποτελέσματα", "Κάντε πρώτα κλήρωση και μετά εξαγωγή αποτελεσμάτων.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Αποθήκευση αποτελεσμάτων κλήρωσης",
            defaultextension=".xlsx",
            filetypes=(("Αρχεία Excel", "*.xlsx"),),
        )
        if not file_path:
            return

        export_rows = [{"Prize": result.prize, "Drawn Ticket": result.drawn_ticket} for result in self.draw_results]

        try:
            save_results_to_excel(export_rows, file_path)
        except ExcelDataError as exc:
            messagebox.showerror("Σφάλμα εξαγωγής", str(exc))
            return

        self.status_var.set(f"Κατάσταση: Τα αποτελέσματα εξήχθησαν στο {file_path}")
        messagebox.showinfo("Η εξαγωγή ολοκληρώθηκε", "Τα αποτελέσματα της κλήρωσης εξήχθησαν επιτυχώς.")

    def _maximize_on_windows(self) -> None:
        if self.tk.call("tk", "windowingsystem") != "win32":
            return

        try:
            self.state("zoomed")
        except tk.TclError:
            pass


def run_app() -> None:
    app = LotteryDrawApp()
    app.mainloop()
