from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

from app.schemas.calculation import CalculationType

class TotalCalculations(BaseModel):

    type: CalculationType = Field(
        ...,
        description='Type of calculation (addition, subtraction, multiplication, division)',
        example='addition',
    )

    count: int = Field(
        ...,
        description='Number of occurrences of the calculation type',
        example=15,
    )

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):

        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")

        return v.lower()

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'examples': [
                {'type': 'addition', 'count': 150},
                {'type': 'subtraction', 'count': 50},
            ],
        },
    )

class CalcsPerDayResponse(BaseModel):

    type: Optional[CalculationType] = Field(
        None,
        description='Type of calculation (addition, subtraction, multiplication, division)',
        example='addition',
    )

    calc_date: date = Field(
        ...,
        description='Calendar Date (YYYY-MM-DD)',
        example='2026-05-09',
    )

    count: int = Field(
        ...,
        description='Number of occurrences of the calculation type',
        example=15,
    )

    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v):

        if v is None:
            return None

        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")

        return v.lower()

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'examples': [
                {'type': 'addition', 'calc_date': '2026-05-09', 'count': 150},
                {'type': 'subtraction', 'calc_date': '2026-05-09', 'count': 50},
            ],
        },
    )
