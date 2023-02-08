import unittest
from unittest.mock import patch
from web import *


class TestPi(unittest.TestCase):

    def test_pi_get_digit_at_index(self):
        self.assertEqual(pi_get_digit_at_index(0), "3")  # pi = 3.141592...
        self.assertEqual(pi_get_digit_at_index(4), "5")  # 4th index should not be rounded up

    def test_pi_get_next_ten_digits_from_index(self):
        self.assertEqual(pi_get_next_ten_digits_from_index(0), "3.141592653")
        self.assertEqual(pi_get_next_ten_digits_from_index(1), "1415926535")

    def test_pi(self):  # Mock-tests pi() and pi_reset()
        with patch("web.pi_get_user_and_index") as mock_request:
            mock_request.return_value = None, None
            pi_reset()
            self.assertEqual(pi(), "3.141592653")

            mock_request.return_value = None, None
            self.assertEqual(pi(), "5897932384")

            pi_reset()
            mock_request.return_value = None, None
            self.assertEqual(pi(), "3.141592653")

            mock_request.return_value = None, 0
            self.assertEqual(pi(), "3")

            mock_request.return_value = None, 4
            self.assertEqual(pi(), "5")


if __name__ == "__main__":
    unittest.main()
