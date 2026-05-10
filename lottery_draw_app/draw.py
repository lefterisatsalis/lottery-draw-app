"""Prize draw orchestration."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class DrawResult:
    prize: str
    drawn_ticket: str


def run_draw(prizes: list[str], available_tickets: list[str]) -> list[DrawResult]:
    """Assign each prize to a unique random ticket."""
    cleaned_prizes = [prize.strip() for prize in prizes if prize and prize.strip()]
    if not cleaned_prizes:
        raise ValueError("At least one prize is required")

    if len(cleaned_prizes) > len(available_tickets):
        raise ValueError(
            f"Not enough available tickets for draw: prizes={len(cleaned_prizes)}, tickets={len(available_tickets)}"
        )

    winners = random.sample(available_tickets, len(cleaned_prizes))
    return [DrawResult(prize=prize, drawn_ticket=ticket) for prize, ticket in zip(cleaned_prizes, winners)]
