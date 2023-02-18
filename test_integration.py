import http
import web
from database import get_password, create_connection, DB_PATH
from werkzeug.security import check_password_hash

status = http.HTTPStatus
USER_JOERG = ("joerg", "elsa")
USER_FELIX = ("felix", "mady")


def test_client():
    with web.app.test_client() as c:
        web.innit_app()
        test_standard_endpoints(c)
        test_get(c)
        test_delete(c)
        test_admin(c)


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


def test_admin(c):  # Testing the admin functions. Should only be accessible by admin (joerg)
    test_admin_get_users(c)
    test_admin_post_new_user(c)
    test_admin_patch_new_password(c)
    test_admin_delete_test_user(c)


def test_admin_get_users(c):
    assert c.get("/admin/users").status_code == status.UNAUTHORIZED  # Unauthorized, no auth
    assert c.get("/admin/users", auth=USER_FELIX).status_code == status.FORBIDDEN  # Forbidden, not admin (joerg)
    assert c.get("/admin/users", auth=USER_JOERG).status_code == status.OK


def test_admin_post_new_user(c):
    c.delete("/admin/users?user=test_user", auth=USER_JOERG)  # Delete test_user in case they exist

    assert c.post("/admin/users").status_code == status.UNAUTHORIZED
    assert c.post("/admin/users", auth=USER_FELIX).status_code == status.UNSUPPORTED_MEDIA_TYPE  # No json
    assert c.post("/admin/users", auth=USER_FELIX,
                  json={"username": "test_user", "password": "wrong_password"}).status_code == status.FORBIDDEN
    assert c.post("/admin/users", auth=USER_JOERG,
                  json={"username": "test_user", "password": "test_password"}).status_code == status.CREATED


def test_admin_patch_new_password(c):
    assert c.patch("/admin/users?user=test_user").status_code == status.UNAUTHORIZED
    assert c.patch("/admin/users?user=test_user", auth=USER_FELIX).status_code == status.UNSUPPORTED_MEDIA_TYPE
    assert c.patch("/admin/users?user=test_user", auth=USER_FELIX,
                   json={"password": "wrong_password"}).status_code == status.FORBIDDEN
    assert c.patch("/admin/users?user=test_user", auth=USER_JOERG,
                   json={"password": "new_test_password"}).status_code == status.CREATED
    assert check_password_hash(get_password(create_connection(DB_PATH), "test_user"), "new_test_password")


def test_admin_delete_test_user(c):
    assert c.delete("/admin/users?user=test_user").status_code == status.UNAUTHORIZED
    assert c.delete("/admin/users?user=test_user", auth=USER_FELIX).status_code == status.FORBIDDEN
    assert c.delete("/admin/users?user=test_user", auth=USER_JOERG).status_code == status.OK


if __name__ == "__main__":
    test_client()
