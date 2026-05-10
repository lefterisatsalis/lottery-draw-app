import unittest

from lottery_draw_app.tickets import (
    TicketValidationError,
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
        excluded = parse_excluded_tickets("Α01, Α1\nΑ02")
        self.assertEqual(excluded, ["Α01", "Α02"])


if __name__ == "__main__":
    unittest.main()
