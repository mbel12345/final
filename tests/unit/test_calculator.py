import pytest
import uuid

from typing import Union

from app.models.calculation import (
    Addition,
    Subtraction,
    Multiplication,
    Division,
)

Number = Union[int, float]

def dummy_user_id():

    return uuid.uuid4()

#################################################
# Addition
#################################################
@pytest.mark.parametrize(
    'inputs, expected',
    [
        ([2, 4, 5], 11),     # positive ints
        ([2, 4, -5], 1),     # mixed-sign ints
        ([2.5, 4, 2], 8.5),  # ints and floats
        ([2.5, 4, -2], 4.5), # mixed-sign ints and floats
        ([6, 0, 0], 6),      # zeros
    ],
    ids=[
        'add_positive_ints',
        'add_mixed_sign_ints',
        'add_ints_and_floats',
        'add_mixed_sign_ints_and_float',
        'add_zeros',
    ],
)
def test_add(inputs: list[Number], expected: Number) -> None:

    # Test calculation.add

    calc = Addition(user_id=dummy_user_id(), inputs=inputs)
    actual = calc.get_result()
    assert actual == expected

#################################################
# Subtraction
#################################################
@pytest.mark.parametrize(
    'inputs, expected',
    [
        ([2, 4, 5], -7),     # positive ints
        ([2, 4, -5], 3),     # mixed-sign ints
        ([2.5, 4, 2], -3.5), # ints and floats
        ([2.5, 4, -2], 0.5), # mixed-sign ints and floats
        ([6, 0, 0], 6),      # zeros
    ],
    ids=[
        'subtract_positive_ints',
        'subtract_mixed_sign_ints',
        'subtract_ints_and_floats',
        'subtract_mixed_sign_ints_and_float',
        'subtract_zeros',
    ],
)
def test_subtraction(inputs: list[Number], expected: Number) -> None:

    # Test calculation.subtraction

    calc = Subtraction(user_id=dummy_user_id(), inputs=inputs)
    actual = calc.get_result()
    assert actual == expected

#################################################
# Multiplication
#################################################
@pytest.mark.parametrize(
    'inputs, expected',
    [
        ([2, 4, 5], 40),     # positive ints
        ([2, 4, -5], -40),   # mixed-sign ints
        ([2.5, 4, 2], 20),   # ints and floats
        ([2.5, 4, -2], -20), # mixed-sign ints and floats
        ([6, 0, 0], 0),      # zeros
    ],
    ids=[
        'multiply_positive_ints',
        'multiply_mixed_sign_ints',
        'multiply_ints_and_floats',
        'multiply_mixed_sign_ints_and_float',
        'multiply_zeros',
    ],
)
def test_multiplication(inputs: list[Number], expected: Number) -> None:

    # Test calculation.multiplication

    calc = Multiplication(user_id=dummy_user_id(), inputs=inputs)
    actual = calc.get_result()
    assert actual == expected


#################################################
# Division
#################################################
@pytest.mark.parametrize(
    'inputs, expected',
    [
        ([2, 4, 5], 0.1),        # positive ints
        ([2, 4, -5], -0.1),      # mixed-sign ints
        ([2.5, 4, 2], 0.3125),   # ints and floats
        ([2.5, 4, -2], -0.3125), # mixed-sign ints and floats
        ([0, 1, 2], 0),          # zeros
    ],
    ids=[
        'divide_positive_ints',
        'divide_mixed_sign_ints',
        'divide_ints_and_floats',
        'divide_mixed_sign_ints_and_float',
        'divide_zeros',
    ],
)
def test_division(inputs: list[Number], expected: Number) -> None:

    # Test calculation.division

    calc = Division(user_id=dummy_user_id(), inputs=inputs)
    actual = calc.get_result()
    assert actual == expected

#################################################
# Division by Zero
#################################################
@pytest.mark.parametrize(
    'inputs',
    [
        ([2, 1, 0]),
    ],
    ids=[
        'divide_zeros_fail',
    ],
)
def test_division_by_zero_fail(inputs: list[Number]) -> None:

    # Test calculation.division by zero

    calc = Division(user_id=dummy_user_id(), inputs=inputs)
    with pytest.raises(ValueError, match='Cannot divide by zero.'):
        calc.get_result()
