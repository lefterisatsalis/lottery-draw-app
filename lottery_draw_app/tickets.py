"""Greek ticket parsing and range generation helpers."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

GREEK_CAPITALS = (
    "Α",
    "Β",
    "Γ",
    "Δ",
    "Ε",
    "Ζ",
    "Η",
    "Θ",
    "Ι",
    "Κ",
    "Λ",
    "Μ",
    "Ν",
    "Ξ",
    "Ο",
    "Π",
    "Ρ",
    "Σ",
    "Τ",
    "Υ",
    "Φ",
    "Χ",
    "Ψ",
    "Ω",
)
LETTER_TO_INDEX = {letter: idx for idx, letter in enumerate(GREEK_CAPITALS)}
TICKET_RE = re.compile(r"^([Α-Ω])\s*(\d{1,3})$")
ACCENTED_UPPER_MAP = str.maketrans({"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω", "Ϊ": "Ι", "Ϋ": "Υ"})


class TicketValidationError(ValueError):
    """Raised when a ticket is not valid."""


def _normalize_ticket_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.strip().upper())
    return normalized.translate(ACCENTED_UPPER_MAP)


def _format_ticket(letter: str, number: int) -> str:
    if number == 100:
        return f"{letter}100"
    return f"{letter}{number:02d}"


def parse_ticket(ticket: str) -> tuple[str, int]:
    """Parse and validate a ticket like Α01, Β99, Η100."""
    normalized = _normalize_ticket_text(ticket)
    match = TICKET_RE.match(normalized)
    if not match:
        raise TicketValidationError(f"Μη έγκυρη μορφή λαχνού: {ticket}")

    letter, number_text = match.groups()
    if letter not in LETTER_TO_INDEX:
        raise TicketValidationError(f"Μη έγκυρο ελληνικό κεφαλαίο γράμμα στον λαχνό: {ticket}")

    number = int(number_text)
    if not 1 <= number <= 100:
        raise TicketValidationError(f"Ο αριθμός λαχνού πρέπει να είναι από 1 έως 100: {ticket}")

    return letter, number


def ticket_to_serial(ticket: str) -> int:
    """Convert ticket to sortable serial number (1-based)."""
    letter, number = parse_ticket(ticket)
    return LETTER_TO_INDEX[letter] * 100 + number


def serial_to_ticket(serial: int) -> str:
    """Convert serial number back to formatted ticket text."""
    if serial < 1:
        raise TicketValidationError("Ο σειριακός αριθμός λαχνού πρέπει να είναι θετικός")

    serial_zero_based = serial - 1
    letter_index = serial_zero_based // 100
    number = (serial_zero_based % 100) + 1

    if letter_index >= len(GREEK_CAPITALS):
        raise TicketValidationError("Ο σειριακός αριθμός λαχνού υπερβαίνει το υποστηριζόμενο ελληνικό αλφάβητο")

    letter = GREEK_CAPITALS[letter_index]
    return _format_ticket(letter, number)


def generate_ticket_range(start_ticket: str, end_ticket: str) -> list[str]:
    """Generate inclusive ticket range between start and end."""
    start_serial = ticket_to_serial(start_ticket)
    end_serial = ticket_to_serial(end_ticket)

    if start_serial > end_serial:
        raise TicketValidationError("Ο αρχικός λαχνός πρέπει να είναι μικρότερος ή ίσος του τελικού λαχνού")

    return [serial_to_ticket(serial) for serial in range(start_serial, end_serial + 1)]


def parse_excluded_tickets(raw_text: str) -> list[str]:
    """Parse excluded tickets from comma-separated text."""
    if not raw_text.strip():
        return []

    invalid_format_message = "Οι εξαιρούμενοι λαχνοί πρέπει να χωρίζονται μόνο με κόμμα (π.χ. Α05, Β12, Η03)."
    if any(separator in raw_text for separator in ("\n", ";", "\t")):
        raise TicketValidationError(invalid_format_message)

    pieces = [part.strip() for part in raw_text.split(",")]
    if any(not part for part in pieces):
        raise TicketValidationError(invalid_format_message)

    deduplicated: list[str] = []
    seen = set()

    for piece in pieces:
        try:
            letter, number = parse_ticket(piece)
        except TicketValidationError as exc:
            if "," not in raw_text and any(character.isspace() for character in raw_text.strip()):
                raise TicketValidationError(invalid_format_message) from exc
            raise
        normalized_ticket = _format_ticket(letter, number)
        if normalized_ticket not in seen:
            seen.add(normalized_ticket)
            deduplicated.append(normalized_ticket)

    return deduplicated


def filter_excluded_in_range(tickets: Iterable[str], excluded: Iterable[str]) -> list[str]:
    """Remove excluded tickets that fall inside selected range."""
    excluded_set = set(excluded)
    return [ticket for ticket in tickets if ticket not in excluded_set]
