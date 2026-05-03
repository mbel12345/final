import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, func, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, mapped_column, relationship

from app.database import Base

class AbstractCalculation:

    # Abstract base class for calculations

    @declared_attr
    def __tablename__(cls):

        return 'calculations'

    @declared_attr
    def id(cls):

        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )

    @declared_attr
    def user_id(cls):

        return Column(
            UUID(as_uuid=True),
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        )

    @declared_attr
    def type(cls):

        return Column(
            String(50),
            nullable=False,
            index=True,
        )

    @declared_attr
    def inputs(cls):

        return Column(
            JSON,
            nullable=False,
        )

    @declared_attr
    def result(cls):

        return Column(
            Float,
            nullable=True,
        )

    @declared_attr
    def created_at(cls):

        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):

        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )

    @declared_attr
    def user(cls):

        return relationship('User', back_populates='calculations')

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: list[float]):

        # Factory method, to create calculations

        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(f'Unsupported calculation type: {calculation_type}')
        return calculation_class(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:

        # Method to compute calculation result

        raise NotImplementedError

    def validate_inputs(self) -> None:

        # Check the inputs before doing the calculation

        if not isinstance(self.inputs, list):
            raise ValueError('Inputs must be a list of numbers.')
        if len(self.inputs) < 2:
            raise ValueError('Inputs must be a list with at least two numbers.')

    def __repr__(self):

        # str representation of the calculation

        return f'<Calculation(type={self.type}, inputs={self.inputs})>'

class Calculation(Base, AbstractCalculation):

    # Base calculation model

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'calculation',
    }

class Addition(Calculation):

    # Addition calculation

    __mapper_args__ = {
        'polymorphic_identity': 'addition'
    }

    def get_result(self) -> float:

        self.validate_inputs()
        return sum(self.inputs)

class Subtraction(Calculation):

    # Subtraction calculation

    __mapper_args__ = {
        'polymorphic_identity': 'subtraction'
    }

    def get_result(self) -> float:

        self.validate_inputs()
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result

class Multiplication(Calculation):

    # Multiplication calculation

    __mapper_args__ = {
        'polymorphic_identity': 'multiplication'
    }

    def get_result(self) -> float:

        self.validate_inputs()
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result *= value
        return result

class Division(Calculation):

    # Division calculation

    __mapper_args__ = {
        'polymorphic_identity': 'division'
    }

    def get_result(self) -> float:

        self.validate_inputs()
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError('Cannot divide by zero.')
            result /= value
        return result
