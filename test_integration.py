import web


def test_client():
    with web.app.test_client() as c:
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"
        assert c.get("/pi").data == b"5897932384"
        c.get("/pi_reset")
        assert c.get("/pi").data == b"3.141592653"

        c.delete("/pi?user=joerg")
        assert c.post("/post", json={'user': 'joerg'}).get_data(True) == "3.141592653"
        assert c.post("/post", json={'user': 'joerg'}).get_data(True) == "5897932384"
        c.delete("/pi?user=joerg")
        assert c.post("/post", json={'user': 'joerg'}).get_data(True) == "3.141592653"

        assert c.post("/post", json={'index': '0'}).get_data(True) == "3"
        assert c.post("/post", json={'index': '4'}).get_data(True) == "5"

        assert c.post("/post", json={'upto': '4'}).get_data(True) == "3.1415"

        c.get("/pi_reset")
        assert c.post("/post", json={'getfile': 'true'}).get_data(True) == "empty"
        c.get("/pi")
        assert c.post("/post", json={'getfile': 'true'}).get_data(True) == "3.141592653"

        c.delete("/pi")
        assert c.get("/pi").data == b"3.141592653"
        c.delete("/pi")
        assert c.get("/pi").data == b"3.141592653"

        c.delete("/pi?user=felix")
        assert c.get("/pi?user=felix").data == b"3.141592653"
        c.delete("/pi?user=felix")
        assert c.get("/pi?user=felix").data == b"3.141592653"


if __name__ == "__main__":
    test_client()
