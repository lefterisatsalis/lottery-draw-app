import unittest

from lottery_draw_app.draw import run_draw


class DrawTests(unittest.TestCase):
    def test_run_draw_returns_unique_tickets(self):
        prizes = ["Gift A", "Gift B", "Gift C"]
        tickets = ["Α01", "Α02", "Α03", "Α04"]

        results = run_draw(prizes, tickets)

        self.assertEqual(len(results), 3)
        self.assertEqual({result.prize for result in results}, set(prizes))
        self.assertEqual(len({result.drawn_ticket for result in results}), 3)

    def test_run_draw_raises_when_not_enough_tickets(self):
        with self.assertRaises(ValueError):
            run_draw(["Gift A", "Gift B"], ["Α01"])


if __name__ == "__main__":
    unittest.main()
