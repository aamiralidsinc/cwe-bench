"""Fixtures for the hidden security and functional suites.

The application is built exactly as the project's own test suite builds it, against
the database named by SQLALCHEMY_DATABASE_URI.
"""
import os

import pytest
from sqlalchemy.sql import text

import lemur
from lemur import create_app
from lemur.database import db as _db
from lemur.tests.factories import (
    ApiKeyFactory,
    RoleFactory,
    RotationPolicyFactory,
    UserFactory,
)
from lemur.tests.vectors import VALID_ADMIN_HEADER_TOKEN, VALID_USER_HEADER_TOKEN

CONF_PATH = os.path.join(os.path.dirname(os.path.realpath(lemur.__file__)), "tests", "conf.py")


@pytest.fixture(scope="session")
def app():
    application = create_app(config_path=CONF_PATH)
    ctx = application.app_context()
    ctx.push()
    yield application
    ctx.pop()


@pytest.fixture(scope="session")
def db(app):
    _db.drop_all()
    try:
        _db.engine.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    except Exception:
        pass
    _db.create_all()
    _db.app = app

    UserFactory()
    admin_role = RoleFactory(name="admin")
    admin_user = UserFactory(roles=[admin_role])
    read_only_role = RoleFactory(name="read-only")
    UserFactory(roles=[read_only_role])
    RoleFactory(name="joe@example.com")
    RotationPolicyFactory(name="default")
    ApiKeyFactory(user=admin_user)

    _db.session.commit()
    yield _db
    _db.session.remove()
    _db.drop_all()


@pytest.fixture
def session(db):
    db.session.begin_nested()
    yield db.session
    db.session.rollback()
    db.session.remove()


@pytest.fixture
def client(app, session):
    return app.test_client()


@pytest.fixture
def admin_token():
    return VALID_ADMIN_HEADER_TOKEN


@pytest.fixture
def user_token():
    return VALID_USER_HEADER_TOKEN


@pytest.fixture
def canary():
    from support import _Canary

    server = _Canary()
    try:
        yield server
    finally:
        server.close()
