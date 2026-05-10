import uuid

from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, mapped_column

from app.database import Base

class CalcsPerDay(Base):

    # Cache for calculations per user per day

    @declared_attr
    def __tablename__(cls):

        return 'calcs_per_day'

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
            nullable=True,
            index=True,
        )

    @declared_attr
    def calc_date(cls):

        return mapped_column(
            Date,
            nullable=False,
        )

    @declared_attr
    def count(cls):

        return Column(
            Integer,
            nullable=True,
        )

    def __repr__(self):

        # str representation of the calcs_per_day

        return f'<CalcsPerDay(user_id={self.user_id}, type={self.type}, calc_date={self.calc_date}, count={self.count})>'
