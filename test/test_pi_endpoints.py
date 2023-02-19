def test_pi_can_be_reset(client):
    client.get("/pi_reset")
    assert client.get("/pi").data == b"3.141592653"
    assert client.get("/pi").data == b"5897932384"
    client.get("/pi_reset")
    assert client.get("/pi").data == b"3.141592653"


def test_users_can_query_digits_independently(client):
    # Make requests without user to validate that there is no connection between the user and the default
    client.get("/pi")
    client.get("/pi")
    assert client.get("/get/joerg").data == b"3.141592653"
    assert client.get("/get/joerg").data == b"5897932384"
    client.delete("/pi/joerg")
    assert client.get("/get/joerg").data == b"3.141592653"
    assert client.get("/get/felix").data == b"3.141592653"


def test_get_special_options(client):
    assert client.get("/get/0").data == b"3"
    assert client.get("/get/4").data == b"5"

    assert client.get("/get/upto4").data == b"3.1415"

    client.get("/pi_reset")
    assert client.get("/get/getfile").data == b"empty"
    client.get("/pi")
    assert client.get("/get/getfile").data == b"3.141592653"


def test_delete_resets_index(client):
    assert client.get("/pi").data == b"3.141592653"
    client.get("/pi_reset")
    assert client.get("/pi").data == b"3.141592653"

    client.delete("/pi/felix")
    assert client.get("/pi/felix").data == b"3.141592653"
    client.delete("/pi/felix")
    assert client.get("/pi/felix").data == b"3.141592653"
