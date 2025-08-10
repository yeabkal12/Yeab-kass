# database_models/manager.py - The final and correct version with URL fix

import os
from sqlalchemy import (Column, BigInteger, String, DECIMAL, JSON, Integer, Text)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Get the standard database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("FATAL ERROR: DATABASE_URL environment variable is not set.")

# 2. THE BULLETPROOF FIX:
# Manually ensure the driver is asyncpg.
# The standard URL from Render is "postgresql://...". We replace it.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 3. Create the engine with the corrected URL
engine = create_async_engine(DATABASE_URL)

# --- The rest of the file remains the same ---
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)

class Game(Base):
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
    __tablename__ = "transactions"
    tx_ref = Column(Text, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default="pending")