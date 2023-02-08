import requests
import unittest
import web

ENDPOINT_PI = "http://127.0.0.1:5000/pi"
ENDPOINT_PI_RESET = "http://127.0.0.1:5000/pi_reset"


# class TestPiIntegration(unittest.TestCase):
#     def test_pi(self):
#         requests.get(ENDPOINT_PI_RESET)
#
#         data = requests.get(ENDPOINT_PI).json()
#         self.assertEqual(data, 3.141592653)
#         data = requests.get(ENDPOINT_PI).json()
#         self.assertEqual(data, 5897932384)
#
#         requests.get(ENDPOINT_PI_RESET)
#
#         data = requests.get(ENDPOINT_PI).json()
#         self.assertEqual(data, 3.141592653)


def test_client():
    with web.app.test_client() as c:
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"
        assert c.get("/pi").data == b"5897932384"
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"


if __name__ == "__main__":
    # unittest.main()
    test_client()
