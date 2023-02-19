def test_e_can_be_reset(client):
    client.get("/e/reset")
    assert client.get("/e").data == b"2.718281828"
    assert client.get("/e").data == b"8459045235"
    client.get("/e/reset")
    assert client.get("/e").data == b"2.718281828"


def test_users_can_query_digits_independently(client):
    # Make requests without user to validate that there is no connection between the user and the default
    client.get("/e")
    client.get("/e")
    assert client.get("/e/get/joerg").data == b"2.718281828"
    assert client.get("/e/get/joerg").data == b"4590452353"
    client.delete("/e/joerg")
    assert client.get("/e/get/joerg").data == b"2.718281828"
    assert client.get("/e/get/felix").data == b"2.718281828"


def test_get_special_options(client):
    assert client.get("/e/get/0").data == b"2"
    assert client.get("/e/get/2").data == b"1"

    assert client.get("/e/get/upto4").data == b"2.7182"

    client.get("/e/reset")
    assert client.get("/e/get/getfile").data == b"empty"
    client.get("/e")
    assert client.get("/e/get/getfile").data == b"2.718281828"


def test_delete_resets_index(client):
    assert client.get("/e").data == b"2.718281828"
    client.get("/e/reset")
    assert client.get("/e").data == b"2.718281828"

    client.delete("/e/felix")
    assert client.get("/e/felix").data == b"2.718281828"
    client.delete("/e/felix")
    assert client.get("/e/felix").data == b"2.718281828"
