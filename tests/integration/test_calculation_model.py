import pytest
import uuid

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)

def dummy_user_id():

    # Create a dummy user_id for testing

    return uuid.uuid4()

def test_addition_get_result():

    # Test that Addition.get_result returns the correct sum

    inputs = [9, 4, -0.75]
    operation = Addition(user_id=dummy_user_id(), inputs=inputs)
    actual = operation.get_result()
    expected = 12.25
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_subtraction_get_result():

    # Test that Subtraction.get_result returns the correct difference

    inputs = [9, 4, -0.75]
    operation = Subtraction(user_id=dummy_user_id(), inputs=inputs)
    actual = operation.get_result()
    expected = 5.75
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_multiplication_get_result():

    # Test that Multiplication.get_result returns the correct difference

    inputs = [9, 4, -0.75]
    operation = Multiplication(user_id=dummy_user_id(), inputs=inputs)
    actual = operation.get_result()
    expected = -27
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_division_get_result():

    # Test that Division.get_result returns the correct difference

    inputs = [9, 4, -0.75]
    operation = Division(user_id=dummy_user_id(), inputs=inputs)
    actual = operation.get_result()
    expected = -3
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_division_by_zero():

    # Test that Division.get_result raises ValueError when dividing by zero.

    inputs = [4, 0, 4]
    operation = Division(user_id=dummy_user_id(), inputs=inputs)
    with pytest.raises(ValueError, match='Cannot divide by zero.'):
        operation.get_result()

def test_calculation_factory_addition():

    # Test Calculation.create method for addition

    inputs = [2, 4, 8]
    calc = Calculation.create(
        calculation_type='addition',
        user_id=dummy_user_id(),
        inputs=inputs,
    )

    # Check that the returned instance is an Addition and the result is correct
    assert isinstance(calc, Addition), 'Factory did not return an Addition instance.'
    actual = calc.get_result()
    expected = 14
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_calculation_factory_subtraction():

    # Test Calculation.create method for subtraction

    inputs = [2, 4, 8]
    calc = Calculation.create(
        calculation_type='subtraction',
        user_id=dummy_user_id(),
        inputs=inputs,
    )

    # Check that the returned instance is a Subtraction and the result is correct
    assert isinstance(calc, Subtraction), 'Factory did not return a Subtraction instance.'
    actual = calc.get_result()
    expected = -10
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_calculation_factory_multiplication():

    # Test Calculation.create method for multiplication

    inputs = [2, 4, 8]
    calc = Calculation.create(
        calculation_type='multiplication',
        user_id=dummy_user_id(),
        inputs=inputs,
    )

    # Check that the returned instance is a Multiplication and the result is correct
    assert isinstance(calc, Multiplication), 'Factory did not return a Multiplication instance.'
    actual = calc.get_result()
    expected = 64
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_calculation_factory_division():

    # Test Calculation.create method for division

    inputs = [2, 4, 8]
    calc = Calculation.create(
        calculation_type='division',
        user_id=dummy_user_id(),
        inputs=inputs,
    )

    # Check that the returned instance is a Division and the result is correct
    assert isinstance(calc, Division), 'Factory did not return a Division instance.'
    actual = calc.get_result()
    expected = 0.0625
    assert actual == expected, f'Expected {expected}, got {actual}'

def test_calculation_factory_invalid_type():

    # Test that Calculation.create raises a ValueError for an unsupported calculation type

    with pytest.raises(ValueError, match='Unsupported calculation type'):
        Calculation.create(
            calculation_type='modulus',
            user_id=dummy_user_id(),
            inputs=[10, 3],
        )

def test_invalid_inputs_for_addition():

    # Test that providing non-list inputs to Addition.get_result raises a ValueError

    calc = Addition(user_id=dummy_user_id(), inputs='not-a-list')
    with pytest.raises(ValueError, match='Inputs must be a list of numbers.'):
        calc.get_result()

def test_invalid_inputs_for_subtraction():

    # Test that providing fewer than two numbers to Subtraction.get_result raises a ValueError

    calc = Subtraction(user_id=dummy_user_id(), inputs=[20])
    with pytest.raises(ValueError, match='Inputs must be a list with at least two numbers.'):
        calc.get_result()

def test_invalid_inputs_for_multiplication():

    # Test that providing fewer than two numbers to Multiplication.get_result raises a ValueError

    calc = Multiplication(user_id=dummy_user_id(), inputs=[20])
    with pytest.raises(ValueError, match='Inputs must be a list with at least two numbers.'):
        calc.get_result()


def test_invalid_inputs_for_division():

    # Test that providing fewer than two numbers to Division.get_result raises a ValueError

    calc = Division(user_id=dummy_user_id(), inputs=[20])
    with pytest.raises(ValueError, match='Inputs must be a list with at least two numbers.'):
        calc.get_result()

def test_unimplemented_get_result():

    # Test that a Calculation class without get_result() defined throws an error

    class Modulus(Calculation):

        __mapper_args__ = {
            'polymorphic_identity': 'modulus',
        }

    calc = Modulus(user_id=dummy_user_id(), inputs=[23, 3])
    with pytest.raises(NotImplementedError, match=''):
        calc.get_result()

def test_calculation_repr():

    # Test __repr__ for the Calculation class

    calc = Addition(user_id=dummy_user_id(), inputs=[3, 3])
    actual = str(calc)
    expected = '<Calculation(type=addition, inputs=[3, 3])>'
    assert actual == expected, f'Expected {expected}, got {actual}'
