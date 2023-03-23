import http
import pytest

from test_api import PI_FIRST_10, PI_NEXT_10, E_NEXT_10, E_FIRST_10, SQRT2_FIRST_10, \
    SQRT2_NEXT_10


@pytest.mark.parametrize("number,first_twenty", [("pi", PI_FIRST_10 + PI_NEXT_10),
                                                 ("e", E_FIRST_10 + E_NEXT_10),
                                                 ("sqrt2", SQRT2_FIRST_10 + SQRT2_NEXT_10)])
def test_download_returns_file(client, number, first_twenty):
    client.get(f"api?number={number}&amount=20")
    download = client.get(f"/digits/{number}")
    assert download.data == first_twenty
    # This header is what triggers the browser to start a download and not display it
    assert download.headers.get("content-disposition") == f"attachment; filename={number}.txt"


@pytest.mark.parametrize("number", ["pi", "e", "sqrt2"])
def test_download_of_empty_file_fails(client, number):
    download = client.get(f"/digits/{number}")
    assert download.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("number", ["cat", "a", "four"])
def test_download_of_unknown_numbers_fails(client, number):
    download = client.get(f"/digits/{number}")
    assert download.status_code == http.HTTPStatus.NOT_FOUND
