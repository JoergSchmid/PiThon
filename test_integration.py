import web


def test_client():
    with web.app.test_client() as c:
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"
        assert c.get("/pi").data == b"5897932384"
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"


if __name__ == "__main__":
    test_client()
