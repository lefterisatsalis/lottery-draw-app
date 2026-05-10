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
        raise TicketValidationError(f"Invalid ticket format: {ticket}")

    letter, number_text = match.groups()
    if letter not in LETTER_TO_INDEX:
        raise TicketValidationError(f"Invalid Greek uppercase letter in ticket: {ticket}")

    number = int(number_text)
    if not 1 <= number <= 100:
        raise TicketValidationError(f"Ticket number must be between 1 and 100: {ticket}")

    return letter, number


def ticket_to_serial(ticket: str) -> int:
    """Convert ticket to sortable serial number (1-based)."""
    letter, number = parse_ticket(ticket)
    return LETTER_TO_INDEX[letter] * 100 + number


def serial_to_ticket(serial: int) -> str:
    """Convert serial number back to formatted ticket text."""
    if serial < 1:
        raise TicketValidationError("Ticket serial must be positive")

    serial_zero_based = serial - 1
    letter_index = serial_zero_based // 100
    number = (serial_zero_based % 100) + 1

    if letter_index >= len(GREEK_CAPITALS):
        raise TicketValidationError("Ticket serial exceeds supported Greek alphabet range")

    letter = GREEK_CAPITALS[letter_index]
    return _format_ticket(letter, number)


def generate_ticket_range(start_ticket: str, end_ticket: str) -> list[str]:
    """Generate inclusive ticket range between start and end."""
    start_serial = ticket_to_serial(start_ticket)
    end_serial = ticket_to_serial(end_ticket)

    if start_serial > end_serial:
        raise TicketValidationError("Start ticket must be less than or equal to end ticket")

    return [serial_to_ticket(serial) for serial in range(start_serial, end_serial + 1)]


def parse_excluded_tickets(raw_text: str) -> list[str]:
    """Parse excluded tickets from comma/newline/space separated text."""
    if not raw_text.strip():
        return []

    pieces = [part.strip() for part in re.split(r"[\n,;\s]+", raw_text) if part.strip()]
    deduplicated: list[str] = []
    seen = set()

    for piece in pieces:
        letter, number = parse_ticket(piece)
        normalized_ticket = _format_ticket(letter, number)
        if normalized_ticket not in seen:
            seen.add(normalized_ticket)
            deduplicated.append(normalized_ticket)

    return deduplicated


def filter_excluded_in_range(tickets: Iterable[str], excluded: Iterable[str]) -> list[str]:
    """Remove excluded tickets that fall inside selected range."""
    excluded_set = set(excluded)
    return [ticket for ticket in tickets if ticket not in excluded_set]
