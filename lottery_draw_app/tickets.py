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
INVALID_TICKET_RANGE_ORDER_MESSAGE = "Ο αρχικός λαχνός πρέπει να είναι μικρότερος ή ίσος του τελικού λαχνού"
INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE = (
    "Οι εξαιρούμενοι λαχνοί πρέπει να είναι διαχωρισμένοι με κόμμα και κάθε τιμή να είναι "
    "είτε ένας λαχνός είτε ένα διάστημα λαχνών (π.χ. Α10, Β15, Δ12-Δ25)."
)
INVALID_EXCLUDED_RANGE_ORDER_MESSAGE = (
    "Στους εξαιρούμενους λαχνούς, η αρχή του διαστήματος πρέπει να είναι μικρότερη ή ίση του τέλους "
    "(π.χ. Δ12-Δ25)."
)


class TicketValidationError(ValueError):
    """Raised when a ticket is not valid."""


class TicketRangeOrderError(TicketValidationError):
    """Raised when a ticket range start comes after its end."""


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
        raise TicketRangeOrderError(INVALID_TICKET_RANGE_ORDER_MESSAGE)

    return [serial_to_ticket(serial) for serial in range(start_serial, end_serial + 1)]


def parse_excluded_tickets(raw_text: str) -> list[str]:
    """Parse and validate excluded tickets from comma-separated text."""
    if not raw_text.strip():
        return []

    if any(separator in raw_text for separator in ("\n", ";", "\t")):
        raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE)

    pieces = [part.strip() for part in raw_text.split(",")]
    if any(not part for part in pieces):
        raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE)

    deduplicated: list[str] = []
    seen = set()

    for piece in pieces:
        expanded_tickets: list[str] = []
        if "-" in piece:
            if piece.count("-") != 1:
                raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE)

            start_text, end_text = (part.strip() for part in piece.split("-", 1))
            if not start_text or not end_text:
                raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE)

            try:
                expanded_tickets = generate_ticket_range(start_text, end_text)
            except TicketRangeOrderError as exc:
                raise TicketValidationError(INVALID_EXCLUDED_RANGE_ORDER_MESSAGE) from exc
            except TicketValidationError as exc:
                raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE) from exc
        else:
            try:
                letter, number = parse_ticket(piece)
            except TicketValidationError as exc:
                raise TicketValidationError(INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE) from exc
            expanded_tickets = [_format_ticket(letter, number)]

        for normalized_ticket in expanded_tickets:
            if normalized_ticket not in seen:
                seen.add(normalized_ticket)
                deduplicated.append(normalized_ticket)

    return deduplicated


def filter_excluded_in_range(tickets: Iterable[str], excluded: Iterable[str]) -> list[str]:
    """Remove excluded tickets that fall inside selected range."""
    excluded_set = set(excluded)
    return [ticket for ticket in tickets if ticket not in excluded_set]
