import pytest
from database import TEST_USER_STD

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


@pytest.mark.parametrize("endpoint,first_ten", [("/pi", PI_FIRST_10),
                                                ("/e", E_FIRST_10),
                                                ("/sqrt2", SQRT2_FIRST_10)])
def test_get_special_options(client, endpoint, first_ten):
    assert client.get(f"{endpoint}/get/0").data == first_ten[0:1]
    for i in range(1, 11):
        assert client.get(f"{endpoint}/get/{i}").data == first_ten[i + 1:i + 2]  # byte strings have different indexing
    assert client.get(f"{endpoint}/get/upto4").data == first_ten[:6]
    client.get(f"{endpoint}/reset")
    assert client.get(f"{endpoint}/get/getfile").data == b"empty"
    client.get(f"{endpoint}")
    assert client.get(f"{endpoint}/get/getfile").data == first_ten


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


@pytest.mark.parametrize("endpoint,first_ten", [("/pi", PI_FIRST_10),
                                                ("/e", E_FIRST_10),
                                                ("/sqrt2", SQRT2_FIRST_10)])
def test_db_number_digit(client, endpoint, first_ten):
    assert client.get(f"/db{endpoint}/0").data == first_ten[0:1]
    for i in range(2, 5):
        assert client.get(f"/db{endpoint}/{i}").data == first_ten[i+1:i+2]


def test_if_no_cache_is_set_correctly(client):
    assert client.get("/e").headers['Cache-Control'] == "no-store, max-age=0"
    assert client.get("/admin/users").headers['Cache-Control'] == "no-store, max-age=0"


def test_all_user_indices_get_reset(client):
    client.get(f"/pi/{TEST_USER_STD[0]}")
    client.get(f"/e/{TEST_USER_STD[0]}")
    client.get(f"/sqrt2/{TEST_USER_STD[0]}")
    client.delete(f"/reset/{TEST_USER_STD[0]}")
    assert client.get(f"/pi/{TEST_USER_STD[0]}").data == PI_FIRST_10
    assert client.get(f"/e/{TEST_USER_STD[0]}").data == E_FIRST_10
    assert client.get(f"/sqrt2/{TEST_USER_STD[0]}").data == SQRT2_FIRST_10
