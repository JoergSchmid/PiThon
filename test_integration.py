import web


def test_client():
    with web.app.test_client() as c:
        test_standard_endpoints(c)
        test_post(c)
        test_delete(c)


def test_standard_endpoints(c):
    c.get("/pi_reset")
    assert c.get("/pi").data == b"3.141592653"
    assert c.get("/pi").data == b"5897932384"
    c.get("/pi_reset")
    assert c.get("/pi").data == b"3.141592653"


def test_get(c):
    c.delete("/pi?user=joerg")
    assert c.get("/get?user=joerg").data == b"3.141592653"
    assert c.get("/get?user=joerg").data == b"5897932384"
    c.delete("/pi?user=joerg")
    assert c.get("/get?user=joerg").data == b"3.141592653"

    assert c.get("/get?index=0").data == b"3"
    assert c.get("/get?index=4").data == b"5"

    assert c.get("/get?upto=4").data == b"3.1415"

    c.get("/pi_reset")
    assert c.get("/get?getfile=true").data == b"empty"
    c.get("/pi")
    assert c.get("/get?getfile=true").data == b"3.141592653"


def test_delete(c):
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
