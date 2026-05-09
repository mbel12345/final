import pytest

from pydantic import ValidationError

from app.schemas.statistics import TotalCalculations


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
