import pytest

from datetime import date
from pydantic import ValidationError

from app.schemas import CalcsPerDayResponse
from app.schemas import TotalCalculations


def test_schema_total_statistics_valid():

    # Test creating a valid TotalStatistics schema

    data = {
        'type': 'addition',
        'count': 50,
    }

    calc = TotalCalculations(**data)
    assert calc.type == data['type']
    assert calc.count == data['count']


def test_schema_total_statistics_missing_type():

    # Test TotalStatistics fails if 'type' is missing

    data = {
        'count': 50,
    }

    with pytest.raises(ValidationError, match='required'):
        TotalCalculations(**data)


def test_schema_total_statistics_missing_count():

    # Test TotalStatistics fails if 'count' is missing

    data = {
        'type': 'addition',
    }

    with pytest.raises(ValidationError, match='required'):
        TotalCalculations(**data)


def test_schema_total_statistics_invalid_type():

    # Test TotalStatistics fails if 'type' is invalid

    data = {
        'type': 'modulus',
        'count': 50,
    }

    with pytest.raises(ValidationError, match='Type must be one of'):
        TotalCalculations(**data)


def test_schema_calcs_per_day_valid():

    # Test creating a valid CalcsPerDayResponse schema

    data = {
        'type': 'addition',
        'calc_date': date.today(),
        'count': 50,
    }

    calc = CalcsPerDayResponse(**data)
    assert calc.type == data['type']
    assert calc.calc_date == data['calc_date']
    assert calc.count == data['count']


def test_schema_calcs_per_day_type_is_none():

    # Test CalcsPerDayResponse passes if type is None

    data = {
        'type': None,
        'calc_date': date.today(),
        'count': 50,
    }

    calc = CalcsPerDayResponse(**data)
    assert calc.type == data['type']
    assert calc.calc_date == data['calc_date']
    assert calc.count == data['count']


def test_schema_calcs_per_day_missing_calc_date():

    # Test CalcsPerDayResponse fails if 'calc_date' is missing

    data = {
        'type': 'addition',
        'count': 50,
    }

    with pytest.raises(ValidationError, match='required'):
        CalcsPerDayResponse(**data)


def test_schema_calcs_per_day_missing_count():

    # Test CalcsPerDayResponse fails if 'count' is missing

    data = {
        'type': 'addition',
        'calc_date': date.today(),
    }

    with pytest.raises(ValidationError, match='required'):
        CalcsPerDayResponse(**data)


def test_schema_calcs_per_day_invalid_type():

    # Test CalcsPerDayResponse fails if 'type' is invalid

    data = {
        'type': 'modulus',
        'calc_date': date.today(),
        'count': 50,
    }

    with pytest.raises(ValidationError, match='Type must be one of'):
        CalcsPerDayResponse(**data)
