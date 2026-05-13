import unittest

from lottery_draw_app.tickets import (
    TicketValidationError,
    filter_excluded_in_range,
    generate_ticket_range,
    parse_excluded_tickets,
    parse_ticket,
)


class TicketTests(unittest.TestCase):
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

        self.assertIn("αρχή του διαστήματος", str(error.exception))

    def test_parse_excluded_rejects_non_comma_separator(self):
        with self.assertRaises(TicketValidationError) as error:
            parse_excluded_tickets("Α01 Β02")

        self.assertIn("διαχωρισμένοι με κόμμα", str(error.exception))

    def test_filter_excluded_in_range_ignores_exclusions_outside_selected_range(self):
        tickets = generate_ticket_range("Α10", "Α15")
        excluded = parse_excluded_tickets("Α08-Α11, Α13, Β01")

        available = filter_excluded_in_range(tickets, excluded)

        self.assertEqual(available, ["Α12", "Α14", "Α15"])


if __name__ == "__main__":
    unittest.main()
