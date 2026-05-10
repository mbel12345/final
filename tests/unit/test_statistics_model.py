import logging

from datetime import date

from app.models import CalcsPerDay
from app.models import User
from tests.conftest import get_unique_user_data

logger = logging.getLogger(__name__)


def test_calcs_per_day_repr():

    # Test that CalcsPerDay.__repr__ works

    data = {
        'user_id': 'fake_user',
        'type': 'addition',
        'calc_date': date.today(),
        'count': 5,
    }
    actual = str(CalcsPerDay(**data))
    expected = f"<CalcsPerDay(user_id={data['user_id']}, type={data['type']}, calc_date={data['calc_date']}, count={data['count']})>"
    assert actual == expected


def test_calcs_per_day_create(db_session):

    # Test that CalcsPerDay can be imported into DB

    user_data = get_unique_user_data()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()

    calcs_per_day_data = {
        'user_id': user.id,
        'type': 'addition',
        'calc_date': date.today(),
        'count': 10,
    }
    calcs_per_day = CalcsPerDay(**calcs_per_day_data)
    db_session.add(calcs_per_day)
    db_session.commit()
    db_session.refresh(calcs_per_day)
    row = db_session.query(CalcsPerDay).filter_by(
        user_id=calcs_per_day_data['user_id']
    ).first()

    assert row.user_id == calcs_per_day_data['user_id']
    assert row.type == calcs_per_day_data['type']
    assert row.calc_date == calcs_per_day_data['calc_date']
    assert row.count == calcs_per_day_data['count']


def test_calcs_per_day_update(db_session):

    # Test that CalcsPerDay can be updated in DB

    user_data = get_unique_user_data()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()

    calcs_per_day_data = {
        'user_id': user.id,
        'type': 'addition',
        'calc_date': date.today(),
        'count': 10,
    }
    calcs_per_day = CalcsPerDay(**calcs_per_day_data)
    db_session.add(calcs_per_day)
    db_session.commit()
    db_session.refresh(calcs_per_day)
    row = db_session.query(CalcsPerDay).filter_by(
        user_id=calcs_per_day_data['user_id']
    ).first()

    assert row.user_id == calcs_per_day_data['user_id']
    assert row.type == calcs_per_day_data['type']
    assert row.calc_date == calcs_per_day_data['calc_date']
    assert row.count == calcs_per_day_data['count']

    # Do update and verify

    calcs_per_day.count = 50
    db_session.commit()
    db_session.refresh(calcs_per_day)
    row = db_session.query(CalcsPerDay).filter_by(
        user_id=calcs_per_day_data['user_id']
    ).first()

    assert row.user_id == calcs_per_day_data['user_id']
    assert row.type == calcs_per_day_data['type']
    assert row.calc_date == calcs_per_day_data['calc_date']
    assert row.count == 50
