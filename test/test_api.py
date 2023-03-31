import http
import pytest
from database import TEST_USER_STD

PI_FIRST_10 = b"3.1415926535"
PI_NEXT_10 = b"8979323846"
E_FIRST_10 = b"2.7182818284"
E_NEXT_10 = b"5904523536"
SQRT2_FIRST_10 = b"1.4142135623"
SQRT2_NEXT_10 = b"7309504880"
status = http.HTTPStatus


@pytest.mark.parametrize("number,first_ten,next_ten", [("pi", PI_FIRST_10, PI_NEXT_10),
                                                       ("e", E_FIRST_10, E_NEXT_10),
                                                       ("sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_num_can_be_reset_without_auth(client, number, first_ten, next_ten):
    client.delete(f"api?number={number}")
    assert client.get(f"api?number={number}&amount=10").data == first_ten
    assert client.get(f"api?number={number}").data == first_ten
    client.delete(f"api?number={number}")
    assert client.get(f"api?number={number}").data == b""


@pytest.mark.parametrize("number,first_ten,next_ten", [("pi", PI_FIRST_10, PI_NEXT_10),
                                                       ("e", E_FIRST_10, E_NEXT_10),
                                                       ("sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_num_get_index_and_amount_without_auth(client, number, first_ten, next_ten):
    assert client.get(f"api?number={number}&index=0").data == first_ten[0:1]
    assert client.get(f"api?number={number}&index=2").data == first_ten[3:4]
    assert client.get(f"api?number={number}&amount=0").data == first_ten[0:1]
    assert client.get(f"api?number={number}&amount=20").data == first_ten + next_ten
    assert client.get(f"api?number={number}&index=0&amount=10").data == first_ten
    assert client.get(f"api?number={number}&index=5&amount=13").data == first_ten[7:12] + next_ten[0:8]


@pytest.mark.parametrize("number,first_ten,next_ten", [("pi", PI_FIRST_10, PI_NEXT_10),
                                                       ("e", E_FIRST_10, E_NEXT_10),
                                                       ("sqrt2", SQRT2_FIRST_10, SQRT2_NEXT_10)])
def test_user_indices_can_be_reset(client, number, first_ten, next_ten):
    client.post(f"api/user?number={number}&index=0", auth=TEST_USER_STD)
    assert client.get(f"api/user?number={number}", auth=TEST_USER_STD).data == first_ten
    assert client.get(f"api/user?number={number}", auth=TEST_USER_STD).data == next_ten
    client.post(f"api/user?number={number}&index=0", auth=TEST_USER_STD)
    assert client.get(f"api/user?number={number}", auth=TEST_USER_STD).data == first_ten


@pytest.mark.parametrize("endpoint,first_ten", [("/pi", PI_FIRST_10),
                                                ("/e", E_FIRST_10),
                                                ("/sqrt2", SQRT2_FIRST_10)])
def test_db_number_digit(client, endpoint, first_ten):
    assert client.get(f"/db{endpoint}/0").data == first_ten[0:1]
    for i in range(2, 5):
        assert client.get(f"/db{endpoint}/{i}").data == first_ten[i + 1:i + 2]


def test_users_can_be_created_and_deleted(client):
    tmp_user = "tmp_user"
    tmp_pw = "tmp_password"

    client.delete("api/user", json={"confirm_deletion": True}, auth=(tmp_user, tmp_pw))
    assert client.post("api", json={"username": tmp_user, "password": tmp_pw}).status_code == status.CREATED
    assert client.delete("api/user", json={"confirm_deletion": True},
                         auth=(tmp_user, tmp_pw)).status_code == status.OK


def test_if_no_cache_is_set_correctly(client):
    assert client.get("/e").headers['Cache-Control'] == "no-store, max-age=0"
    assert client.get("/admin/users").headers['Cache-Control'] == "no-store, max-age=0"


