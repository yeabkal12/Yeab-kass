# database_models/manager.py - The Final and Correct Version

import os
from contextlib import asynccontextmanager

from sqlalchemy import (Column, BigInteger, String, DECIMAL, JSON, Integer, Text)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure the DATABASE_URL is set in the environment, otherwise fail fast.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("FATAL ERROR: The DATABASE_URL environment variable is not set.")

# The engine is the main entry point to our database.
engine = create_async_engine(DATABASE_URL)

# The sessionmaker provides a factory for creating database sessions.
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# This is the base class that all our database models will inherit from.
Base = declarative_base()


# --- ORM MODEL DEFINITIONS ---
class User(Base):
    """Defines the 'users' table in the database."""
    __tablename__ = "users"
    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)


class Game(Base):
    """Defines the 'games' table in the database."""
    __tablename__ = "games"
    id = Column(String, primary_key=True)
    creator_id = Column(BigInteger, nullable=False)
    opponent_id = Column(BigInteger, nullable=True)
    stake = Column(DECIMAL(10, 2), nullable=False)
    win_condition = Column(Integer, nullable=False)
    status = Column(String, default="waiting")
    game_state = Column(JSON, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)


class Transaction(Base):
    """Defines the 'transactions' table in the database."""
    __tablename__ = "transactions"
    tx_ref = Column(Text, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default="pending")


@asynccontextmanager
async def get_db_session():
    """Provides a safe way to interact with the database session."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()