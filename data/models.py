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
    admin = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("id", "idp", "external_id", name="uq_user_idp"),
        # Needed for composite foreign keys
        {"sqlite_autoincrement": True},
    )


class AuthCode(Base):
    """
        Table to store authorisation codes
        This is for people who sign in without the option of setting a cookie
    """
    __tablename__ = "auth_codes"

    code = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    used = Column(Boolean, default=False)

    user = relationship("Users", backref="user_auth_codes")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship so you can easily access the user from feedback
    user = relationship("Users", backref="feedback_entries")