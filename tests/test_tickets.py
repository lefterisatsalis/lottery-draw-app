import unittest

from lottery_draw_app.tickets import (
    INVALID_EXCLUDED_RANGE_ORDER_MESSAGE,
    INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE,
    TicketValidationError,
    filter_excluded_in_range,
    generate_ticket_range,
    parse_excluded_tickets,
    parse_ticket,
)


class TicketTests(unittest.TestCase):
    def test_excluded_error_messages_match_expected_greek_text(self):
        self.assertEqual(
            INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE,
            "Οι εξαιρούμενοι λαχνοί πρέπει να είναι διαχωρισμένοι με κόμμα και κάθε τιμή να είναι "
            "είτε ένας λαχνός είτε ένα διάστημα λαχνών (π.χ. Α10, Β15, Δ12-Δ25).",
        )
        self.assertEqual(
            INVALID_EXCLUDED_RANGE_ORDER_MESSAGE,
            "Στους εξαιρούμενους λαχνούς, η αρχή του διαστήματος πρέπει να είναι μικρότερη ή ίση του τέλους "
            "(π.χ. Δ12-Δ25).",
        )

    def test_parse_ticket_accepts_greek(self):
        letter, number = parse_ticket("Β07")
        self.assertEqual((letter, number), ("Β", 7))

    def test_generate_ticket_range_inclusive_cross_letter(self):
        tickets = generate_ticket_range("Α99", "Β02")
        self.assertEqual(tickets, ["Α99", "Α100", "Β01", "Β02"])

    def test_invalid_ticket_number_raises(self):
        with self.assertRaises(TicketValidationError):
            parse_ticket("Α101")

    def test_parse_excluded_deduplicates(self):
        excluded = parse_excluded_tickets("Α01, Α1, Α02")
        self.assertEqual(excluded, ["Α01", "Α02"])

    def test_parse_excluded_expands_ranges_and_deduplicates(self):
        excluded = parse_excluded_tickets("Α01, Α02-Α03, Α03, Α02-Α04")
        self.assertEqual(excluded, ["Α01", "Α02", "Α03", "Α04"])

    def test_parse_excluded_expands_cross_letter_range(self):
        excluded = parse_excluded_tickets("Α99-Β02")
        self.assertEqual(excluded, ["Α99", "Α100", "Β01", "Β02"])

    def test_parse_excluded_rejects_reversed_range(self):
        with self.assertRaises(TicketValidationError) as error:
            parse_excluded_tickets("Δ25-Δ12")

        self.assertEqual(str(error.exception), INVALID_EXCLUDED_RANGE_ORDER_MESSAGE)

    def test_parse_excluded_rejects_non_comma_separator(self):
        with self.assertRaises(TicketValidationError) as error:
            parse_excluded_tickets("Α01 Β02")

        self.assertEqual(str(error.exception), INVALID_EXCLUDED_TICKETS_FORMAT_MESSAGE)

    def test_filter_excluded_in_range_ignores_exclusions_outside_selected_range(self):
        tickets = generate_ticket_range("Α10", "Α15")
        excluded = parse_excluded_tickets("Α08-Α11, Α13, Β01")

        available = filter_excluded_in_range(tickets, excluded)

        self.assertEqual(available, ["Α12", "Α14", "Α15"])


if __name__ == "__main__":
    unittest.main()
