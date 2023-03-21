import http

import pytest
from werkzeug.security import check_password_hash

from database import TEST_USER_STD, TEST_USER_ADMIN, db_get_password, create_connection
from test_irrational_number_endpoints import PI_FIRST_10, E_FIRST_10, SQRT2_FIRST_10
from web import CONFIG_DB_PATH

status = http.HTTPStatus


@pytest.fixture
def client_with_test_user(client):
    client.post("/admin/users", auth=TEST_USER_ADMIN, json={"username": "test_user", "password": "test_password"})
    return client


def test_login_needed(client):
    assert client.post("/admin/users").status_code == http.HTTPStatus.UNAUTHORIZED


def test_only_admin_can_get_users(client):
    assert client.get("/admin/users").status_code == status.UNAUTHORIZED  # Unauthorized, no auth
    assert client.get("/admin/users",
                      auth=TEST_USER_STD).status_code == status.FORBIDDEN  # Forbidden, not admin (joerg)
    assert client.get("/admin/users", auth=TEST_USER_ADMIN).status_code == status.OK


def test_only_admin_can_post_new_user(client):
    client.delete("/admin/users/test_user", auth=TEST_USER_ADMIN)  # Delete test_user in case they exist
    assert client.post("/admin/users",
                       json={"username": "test_user", "password": "test_password"}).status_code == status.UNAUTHORIZED
    assert client.post("/admin/users", auth=TEST_USER_ADMIN).status_code == status.UNSUPPORTED_MEDIA_TYPE  # No json
    assert client.post("/admin/users", auth=TEST_USER_STD,
                       json={"username": "test_user", "password": "wrong_password"}).status_code == status.FORBIDDEN
    assert client.post("/admin/users", auth=TEST_USER_ADMIN,
                       json={"username": "test_user", "password": "test_password"}).status_code == status.CREATED


def test_only_admin_can_patch_new_password(app, client_with_test_user):
    client = client_with_test_user
    assert client.patch("/admin/users/test_user",
                        json={"password": "new_test_password"}).status_code == status.UNAUTHORIZED
    assert client.patch("/admin/users/test_user", auth=TEST_USER_ADMIN).status_code == status.UNSUPPORTED_MEDIA_TYPE
    assert client.patch("/admin/users/test_user", auth=TEST_USER_STD,
                        json={"password": "wrong_password"}).status_code == status.FORBIDDEN
    assert client.patch("/admin/users/test_user", auth=TEST_USER_ADMIN,
                        json={"password": "new_test_password"}).status_code == status.CREATED
    assert check_password_hash(db_get_password(create_connection(app.config[CONFIG_DB_PATH]), "test_user"),
                               "new_test_password")


def test_only_admin_can_delete_test_user(client_with_test_user):
    client = client_with_test_user

    assert client.delete("/admin/users/test_user").status_code == status.UNAUTHORIZED
    assert client.delete("/admin/users/test_user", auth=TEST_USER_STD).status_code == status.FORBIDDEN
    assert client.delete("/admin/users/test_user", auth=TEST_USER_ADMIN).status_code == status.OK


def test_admin_can_reset_all_user_indices(client_with_test_user):
    client = client_with_test_user

    client.get(f"/pi/{TEST_USER_STD[0]}")
    client.get(f"/e/{TEST_USER_ADMIN[0]}")
    client.get(f"/sqrt2/test_user")
    assert client.delete("/admin/reset_all_indices", auth=TEST_USER_ADMIN).status_code == status.OK
    assert client.get(f"/pi/{TEST_USER_STD[0]}").data == PI_FIRST_10
    assert client.get(f"/e/{TEST_USER_ADMIN[0]}").data == E_FIRST_10
    assert client.get("/sqrt2/test_user").data == SQRT2_FIRST_10
