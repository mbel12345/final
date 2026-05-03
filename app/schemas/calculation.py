import uuid

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional

class CalculationType(str, Enum):

    # Valid calculation types

    ADDITION = 'addition'
    SUBTRACTION = 'subtraction'
    MULTIPLICATION = 'multiplication'
    DIVISION = 'division'

class CalculationBase(BaseModel):

    type: CalculationType = Field(
        ...,
        description='Type of calculation (addition, subtraction, multiplication, division)',
        example='addition',
    )

    inputs: list[float] = Field(
        ...,
        description='List of numeric inputs for the calculation',
        example=[10.5, 5, -2],
        min_items=2,
    )

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):

        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")

        return v.lower()

    @field_validator('inputs', mode='before')
    @classmethod
    def check_inputs_is_list(cls, v):

        if not isinstance(v, list):
            raise ValueError('Input should be a valid list')

        return v

    @model_validator(mode='after')
    def validate_inputs(self) -> 'CalculationBase':

        # No need to check length, as this is done the field definition itself
        # If I added it, it would be dead code.

        if self.type == CalculationType.DIVISION:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError('Cannot divide by zero')

        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'examples': [
                {'type': 'addition', 'inputs': [10.5, 3, 2]},
                {'type': 'division', 'inputs': [100, 2]}
            ]
        }
    )

class CalculationCreate(CalculationBase):

    # Schema for creating a new Calculation

    user_id: uuid.UUID = Field(
        ...,
        description='UUID of the user who owns this calculation',
        example='123e4567-e89b-12d3-a456-426614174000',
    )

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'type': 'addition',
                'inputs': [10.5, 5, -2],
                'user_id': '123e4567-e89b-12d3-a456-426614174000',
            }
        }
    )

class CalculationUpdate(BaseModel):

    # Schema for updating an existing calculation

    inputs: Optional[list[float]] = Field(
        None,
        description='Updated list of numeric inputs',
        example=[40, 8],
        min_items=2,
    )

    @model_validator(mode='after')
    def validate_inputs(self) -> 'CalculationUpdate':

        # No need to check length, as this is done the field definition itself
        # If I added it, it would be dead code.

        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'inputs': [40, 8],
            }
        },
    )

class CalculationResponse(CalculationBase):

    id: uuid.UUID = Field(
        ...,
        description='Unique UUID of the calculation',
        example='123e4567-e89b-12d3-a456-426614174999',
    )

    user_id: uuid.UUID = Field(
        ...,
        description='UUID of the user who owns this calculation',
        example='123e4567-e89b-12d3-a456-426614174000',
    )

    created_at: datetime = Field(
        ...,
        description='Time when the calculation was created',
    )

    updated_at: datetime = Field(
        ...,
        description='Time when the calculation was updated',
    )

    result: float = Field(
        ...,
        description='Result of the calculation',
        example=13.5,
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {
                'id': '123e4567-e89b-12d3-a456-426614174999',
                'user_id': '123e4567-e89b-12d3-a456-426614174000',
                'type': 'addition',
                'inputs': [10.5, 5, -2],
                'result': 13.5,
                'created_at': '2025-01-01T00:00:00',
                'updated_at': '2025-01-01T00:00:00'
            }
        }
    )

class CalculationRead(CalculationResponse):

    pass
