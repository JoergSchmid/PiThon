import pytest

PI_FIRST_10 = b"3.1415926535"
PI_NEXT_10 = b"8979323846"
E_FIRST_10 = b"2.7182818284"
E_NEXT_10 = b"5904523536"
SQRT2_FIRST_10 = b"1.4142135623"
SQRT2_NEXT_10 = b"7309504880"


@pytest.mark.parametrize("endpoint,first_ten,next_ten", [("/pi", PI_FIRST_10, PI_NEXT_10),
                                                         ("/e", E_FIRST_10, E_NEXT_10),
                                                         ("/sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_pi_can_be_reset(client, endpoint, first_ten, next_ten):
    client.get(f"{endpoint}/reset")
    assert client.get(endpoint).data == first_ten
    assert client.get(endpoint).data == next_ten
    client.get(f"{endpoint}/reset")
    assert client.get(endpoint).data == first_ten


def test_users_can_query_digits_independently(client):
    # Make requests without user to validate that there is no connection between the user and the default
    client.get("/pi")
    client.get("/pi")
    assert client.get("/pi/get/joerg").data == PI_FIRST_10
    assert client.get("/pi/get/joerg").data == PI_NEXT_10
    client.delete("/pi/joerg")
    assert client.get("/pi/get/joerg").data == PI_FIRST_10
    assert client.get("/pi/get/felix").data == PI_FIRST_10


def test_get_special_options(client):
    assert client.get("/pi/get/0").data == b"3"
    assert client.get("/pi/get/4").data == b"5"

    assert client.get("/pi/get/upto4").data == b"3.1415"

    client.get("/pi/reset")
    assert client.get("/pi/get/getfile").data == b"empty"
    client.get("/pi")
    assert client.get("/pi/get/getfile").data == PI_FIRST_10


def test_delete_resets_index(client):
    assert client.get("/pi").data == PI_FIRST_10
    client.get("/pi/reset")
    assert client.get("/pi").data == PI_FIRST_10

    client.delete("/pi/felix")
    assert client.get("/pi/felix").data == PI_FIRST_10
    client.delete("/pi/felix")
    assert client.get("/pi/felix").data == PI_FIRST_10
