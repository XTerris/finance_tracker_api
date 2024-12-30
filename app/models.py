from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    login = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    done_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    user = relationship("User")
