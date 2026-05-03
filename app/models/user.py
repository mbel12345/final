import uuid

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, relationship

from app.database import Base

class User(Base):

    __tablename__ = 'users'

    @declared_attr
    def id(cls):

        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4, unique=True,
            index=True,
        )

    calculations = relationship('Calculation', back_populates='user', cascade='all, delete-orphan')
