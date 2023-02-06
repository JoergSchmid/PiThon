import unittest
from web import *


class TestPi(unittest.TestCase):

    def test_pi_get_digit_at_index(self):
        self.assertEqual(pi_get_digit_at_index(0), "3")  # pi = 3.141592...
        self.assertEqual(pi_get_digit_at_index(4), "5")  # 4th index should not be rounded up

    def test_pi_get_next_ten_digits_from_index(self):
        self.assertEqual(pi_get_next_ten_digits_from_index(0), "3.141592653")
        self.assertEqual(pi_get_next_ten_digits_from_index(1), "1415926535")

    def test_pi_get_last_ten_digits(self):  # tests the pi() and pi_reset() functions
        pi_reset()
        self.assertEqual(pi_get_last_ten_digits(), "3.141592653")
        self.assertEqual(pi_get_last_ten_digits(), "8979323846")
        pi_reset()
        self.assertEqual(pi_get_last_ten_digits(), "3.141592653")


if __name__ == "__main__":
    unittest.main()
