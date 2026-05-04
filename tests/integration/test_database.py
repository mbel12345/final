import importlib
import pytest
import sys

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import MagicMock, patch

from app.database import engine
from app.database import get_db
from app.database.database_init import drop_db
from app.database.database_init import init_db

DATABASE_MODULE = 'app.database'
@pytest.fixture
def mock_settings(monkeypatch):

    # Mock the settings of DATABASE_URL

    mock_url = 'postgresql://user:password@localhost:5432/test_db'
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = mock_url
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    monkeypatch.setattr(f'{DATABASE_MODULE}.settings', mock_settings)
    return mock_settings

def reload_database_module():

    # Helper function to reload the database module after patches

    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    return importlib.import_module(DATABASE_MODULE)

def test_base_declaration():

    # Test that Base is an instance of declarative_base

    database = reload_database_module()
    Base = database.Base
    assert isinstance(Base, database.declarative_base().__class__)

def test_get_engine_succes():

    # Test that get_engine returns a valid engine

    database = reload_database_module()
    engine = database.get_engine()
    assert isinstance(engine, Engine)

def test_get_engine_failure():

    # Test that get_engine raises an error if the engine cannot be created

    database = reload_database_module()
    with patch('app.database.create_engine', side_effect=SQLAlchemyError('Engine error')):
        with pytest.raises(SQLAlchemyError, match='Engine error'):
            database.get_engine()

def test_get_sessionmaker():

    # Test that get_sessionmaker returns a valid sessionmaker

    database = reload_database_module()
    engine = database.get_engine()
    SessionLocal = database.get_sessionmaker(engine)
    assert isinstance(SessionLocal, sessionmaker)

def test_get_db():

    # Test get_db method

    db_gen = get_db()
    db = next(db_gen)

    assert isinstance(db, Session)

    try:
        next(db_gen)
    except StopIteration:
        pass

def test_drop_db_and_init_db():

    # Test drop_db (table deletion) and init_db (table creation)
    # Combined into one test so that drop_db testing doesn't result in subsequent tests failing

    drop_db(engine)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        assert result.scalar() == 1

    init_db(engine)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        assert result.scalar() == 1
