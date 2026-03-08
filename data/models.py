from .db import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    TIMESTAMP,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    idp = Column(String,nullable=False)
    external_id = Column(String, nullable=False)
    email = Column(String, nullable=True)
    alias = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("id", "idp", "external_id", name="uq_user_idp"),
        # Needed for composite foreign keys
        {"sqlite_autoincrement": True},
    )