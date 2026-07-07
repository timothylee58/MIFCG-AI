"""
Shared pytest fixtures.

Router-level auth (``get_current_user`` / ``require_admin``) is applied to
every business router. Existing tests exercise business logic, not auth, so
we override both dependencies for the whole test session to act as an
authenticated admin user. Tests that specifically want to exercise auth
failure paths can override these again locally (dependency_overrides is a
plain dict, so per-test overrides + cleanup still work).
"""

import pytest

from app.core.auth import get_current_user, require_admin
from app.main import app

_TEST_USER = {"id": "00000000-0000-0000-0000-000000000001", "role": "admin"}


@pytest.fixture(autouse=True)
def _override_auth():
    app.dependency_overrides[get_current_user] = lambda: _TEST_USER
    app.dependency_overrides[require_admin] = lambda: _TEST_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def real_auth():
    """
    Remove the auth override for a single test so it exercises the real
    get_current_user/require_admin dependencies instead of the stubbed
    admin user. Restores the override afterwards.
    """
    saved_user = app.dependency_overrides.pop(get_current_user, None)
    saved_admin = app.dependency_overrides.pop(require_admin, None)
    yield
    if saved_user is not None:
        app.dependency_overrides[get_current_user] = saved_user
    if saved_admin is not None:
        app.dependency_overrides[require_admin] = saved_admin
