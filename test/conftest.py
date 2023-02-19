import pytest

from web import create_app


# https://docs.pytest.org/en/7.2.x/explanation/fixtures.html#about-fixtures
# tmp_path is an integrated pytest fixture
# This assures that each test receives a separate database and is not impacted by other tests
@pytest.fixture
def app(tmp_path):
    app = create_app(tmp_path)
    return app


# The yield is included to allow for cleanup steps after the client is no longer needed.
# pytest automatically calls the generator again to finish any cleanup steps
@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
    # Future cleanup steps
