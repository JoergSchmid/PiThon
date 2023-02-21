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
def test_num_can_be_reset(client, endpoint, first_ten, next_ten):
    client.get(f"{endpoint}/reset")
    assert client.get(endpoint).data == first_ten
    assert client.get(endpoint).data == next_ten
    client.get(f"{endpoint}/reset")
    assert client.get(endpoint).data == first_ten


@pytest.mark.parametrize("endpoint,first_ten,next_ten", [("/pi", PI_FIRST_10, PI_NEXT_10),
                                                         ("/e", E_FIRST_10, E_NEXT_10),
                                                         ("/sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_users_can_query_digits_independently(client, endpoint, first_ten, next_ten):
    # Make requests without user to validate that there is no connection between the user and the default
    client.get(endpoint)
    client.get(endpoint)
    assert client.get(f"{endpoint}/get/joerg").data == first_ten
    assert client.get(f"{endpoint}/get/joerg").data == next_ten
    client.delete(f"{endpoint}/joerg")
    assert client.get(f"{endpoint}/get/joerg").data == first_ten
    assert client.get(f"{endpoint}/get/felix").data == first_ten


def test_pi_get_special_options(client):
    assert client.get("/pi/get/0").data == b"3"
    assert client.get("/pi/get/4").data == b"5"

    assert client.get("/pi/get/upto4").data == b"3.1415"

    client.get("/pi/reset")
    assert client.get("/pi/get/getfile").data == b"empty"
    client.get("/pi")
    assert client.get("/pi/get/getfile").data == PI_FIRST_10


def test_e_get_special_options(client):
    assert client.get("/e/get/0").data == b"2"
    assert client.get("/e/get/2").data == b"1"

    assert client.get("/e/get/upto3").data == b"2.718"

    client.get("/e/reset")
    assert client.get("/e/get/getfile").data == b"empty"
    client.get("/e")
    assert client.get("/e/get/getfile").data == b"2.7182818284"


def test_sqrt2_get_special_options(client):
    assert client.get("/sqrt2/get/0").data == b"1"
    assert client.get("/sqrt2/get/7").data == b"5"

    assert client.get("/sqrt2/get/upto4").data == b"1.4142"

    client.get("/sqrt2/reset")
    assert client.get("/sqrt2/get/getfile").data == b"empty"
    client.get("/sqrt2")
    assert client.get("/sqrt2/get/getfile").data == b"1.4142135623"


@pytest.mark.parametrize("endpoint,first_ten,next_ten", [("/pi", PI_FIRST_10, PI_NEXT_10),
                                                         ("/e", E_FIRST_10, E_NEXT_10),
                                                         ("/sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_delete_resets_index(client, endpoint, first_ten, next_ten):
    assert client.get(endpoint).data == first_ten
    client.get(f"{endpoint}/reset")
    assert client.get(endpoint).data == first_ten

    client.delete(f"{endpoint}/felix")
    assert client.get(f"{endpoint}/felix").data == first_ten
    client.delete(f"{endpoint}/felix")
    assert client.get(f"{endpoint}/felix").data == first_ten
