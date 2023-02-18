import http
import web
from database import get_password, create_connection, DB_PATH
from werkzeug.security import check_password_hash

status = http.HTTPStatus
USER_JOERG = ("joerg", "elsa")
USER_FELIX = ("felix", "mady")


def test_client():
    with web.app.test_client() as c:
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


def test_admin(c):
    assert c.get("/admin/users").status_code == 401  # Unauthorized, no auth
    assert c.get("/admin/users", auth=("felix", "mady")).status_code == 403  # Forbidden, not admin (joerg)
    assert c.get("/admin/users", auth=("joerg", "elsa")).status_code == 200

    c.delete("/admin/users?user=test_user", auth=("joerg", "elsa"))  # Delete test_user in case they exist

    assert c.post("/admin/users").status_code == 401
    assert c.post("/admin/users", auth=("felix", "mady")).status_code == 415  # No json
    assert c.post("/admin/users", auth=("felix", "mady"),
                  json={"username": "test_user", "password": "wrong_password"}).status_code == 403
    assert c.post("/admin/users", auth=("joerg", "elsa"),
                  json={"username": "test_user", "password": "test_password"}).status_code == 201

    assert c.patch("/admin/users?user=test_user").status_code == 401
    assert c.patch("/admin/users?user=test_user", auth=("felix", "mady")).status_code == 415
    assert c.patch("/admin/users?user=test_user", auth=("felix", "mady"),
                   json={"password": "wrong_password"}).status_code == 403
    assert c.patch("/admin/users?user=test_user", auth=("joerg", "elsa"),
                   json={"password": "new_test_password"}).status_code == 201
    assert check_password_hash(get_password(create_connection(DB_PATH), "test_user"), "new_test_password")
    c.patch()

    assert c.delete("/admin/users?user=test_user").status_code == 401
    assert c.delete("/admin/users?user=test_user", auth=("felix", "mady")).status_code == 403
    assert c.delete("/admin/users?user=test_user", auth=("joerg", "elsa")).status_code == 200


if __name__ == "__main__":
    test_client()
