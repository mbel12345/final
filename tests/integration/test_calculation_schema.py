import pytest

from datetime import datetime
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.calculation import (
    CalculationBase,
    CalculationCreate,
    CalculationRead,
    CalculationResponse,
    CalculationUpdate,
)

def test_calculation_create_valid():

    # Test creating a valid CalculationCreate schema

    data = {
        'type': 'addition',
        'inputs': [10.5, 5],
        'user_id': uuid4(),
    }

    calc = CalculationCreate(**data)
    assert calc.type == data['type']
    assert calc.inputs == data['inputs']
    assert calc.user_id is not None

def test_calculation_create_missing_type():

    # Test CalculationCreate fails if 'type' is missing

    data = {
        'inputs': [10.5, 5],
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match='required'):
        CalculationCreate(**data)

def test_calculation_create_missing_inputs():

    # Test CalculationCreate fails if 'inputs' is missing

    data = {
        'type': 'addition',
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match='required'):
        CalculationCreate(**data)

def test_calculation_create_missing_user_id():

    # Test CalculationCreate fails if 'user_id' is missing

    data = {
        'type': 'addition',
        'inputs': [10.5, 5],
    }

    with pytest.raises(ValidationError, match='required'):
        CalculationCreate(**data)

def test_calculation_create_invalid_inputs():

    # Test that CalculationCreate fails if 'inputs' is not a list of floats

    data =  {
        'type': 'division',
        'inputs': 'not-a-list',
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match=r'1 validation error for CalculationCreate[\s\S]*inputs[\s\S]*Input should be a valid list') as e:
        CalculationCreate(**data)

def test_short_inputs_fail():

    # Test that validation fails if inputs is a single-item list

    data = {
        'type': 'addition',
        'inputs': [10.5],
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match=r'1 validation error for CalculationBase[\s\S]*inputs[\s\S]*List should have at least 2 items'):
        CalculationBase(**data)

def test_calculation_create_unsupported_type():

    # Test CalculationCreate fails if an unsupported calculation type is provided

    data = {
        'type': 'modulus',
        'inputs': [25, 2],
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match=r'1 validation error[\s\S]*one of.*addition'):
        CalculationCreate(**data)

def test_calculation_update_valid():

    # Test a valid partial update

    data = {
        'inputs': [49, 7],
    }
    calc_update = CalculationUpdate(**data)
    assert calc_update.inputs == data['inputs']

def test_calculation_update_no_fields():

    # Test that an empty update is allowed (i.e. no fields)

    calc_update = CalculationUpdate()
    assert calc_update.inputs is None

def test_calculation_response_valid():

    # Test creating a valid CalculationResponse schema

    data = {
        'id': uuid4(),
        'user_id': uuid4(),
        'type': 'subtraction',
        'inputs': [20, 5],
        'result': 15,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }

    response = CalculationResponse(**data)
    assert response.id is not None
    assert response.user_id is not None
    assert response.type == data['type']
    assert response.inputs == data['inputs']
    assert response.result == data['result']

def test_calculation_read_valid():

    # Test creating a valid CalculationRead schema

    data = {
        'id': uuid4(),
        'user_id': uuid4(),
        'type': 'subtraction',
        'inputs': [20, 5],
        'result': 15,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }

    response = CalculationRead(**data)
    assert response.id is not None
    assert response.user_id is not None
    assert response.type == data['type']
    assert response.inputs == data['inputs']
    assert response.result == data['result']

def test_calculation_divide_by_zero():

    # Test creating a valid CalculationCreate schema

    data = {
        'type': 'division',
        'inputs': [10.5, 5, 0, 5],
        'user_id': uuid4(),
    }

    with pytest.raises(ValidationError, match=r'1 validation error for CalculationCreate[\s\S]*Cannot divide by zero'):
        CalculationCreate(**data)
