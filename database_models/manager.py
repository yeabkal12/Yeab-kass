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
# This is the section that was causing the error. All models are now correctly defined here.

class User(Base):
    """
    Defines the 'users' table in the database.
    This model stores user-specific information.
    """
    __tablename__ = "users"
    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)


class Game(Base):
    """
    Defines the 'games' table in the database.
    This is the class that the ImportError was complaining about.
    It stores information about each Ludo game lobby and session.
    """
    __tablename__ = "games"
    id = Column(String, primary_key=True) # A unique ID for each game
    creator_id = Column(BigInteger, nullable=False)
    opponent_id = Column(BigInteger, nullable=True)
    stake = Column(DECIMAL(10, 2), nullable=False)
    win_condition = Column(Integer, nullable=False) # e.g., 1, 2, or 4
    status = Column(String, default="waiting") # "waiting", "active", "finished"
    game_state = Column(JSON, nullable=True) # For storing the live board state
    message_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)


class Transaction(Base):
    """
    Defines the 'transactions' table in the database.
    This model logs all financial activities like deposits and withdrawals.
    """
    __tablename__ = "transactions"
    tx_ref = Column(Text, primary_key=True) # The unique reference from the payment gateway
    user_id = Column(BigInteger, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(String, nullable=False) # 'deposit' or 'withdrawal'
    status = Column(String, default="pending") # 'pending', 'completed', 'failed'


@asynccontextmanager
async def get_db_session():
    """Provides a safe way to interact with the database session."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()