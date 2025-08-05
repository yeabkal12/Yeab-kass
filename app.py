# app.py (Final, API-Only Version)

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware # <-- CRITICAL NEW IMPORT
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

from bot.handlers import setup_handlers
from database_models.manager import get_db_session, games, users
from sqlalchemy import select

# --- 1. SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- 2. LIFESPAN LOGIC ---
bot_app: Application | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... (The lifespan function remains exactly the same as before)
    pass # For brevity, this is unchanged

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

# --- CRITICAL FIX: Add CORS Middleware ---
# This tells your API that it is okay to accept requests from your new frontend website.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, you can restrict this to your static site's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- (The rest of the file is the same, but WITHOUT the app.mount line) ---

# ... (all your @app.post and @app.get endpoints for /api/telegram/webhook, /api/games, /health)
# ... (all the bot initialization logic)

# CRITICAL: We REMOVE the following line. The API will no longer serve the frontend files.
# app.mount("/", StaticFiles(directory="frontend"), name="frontend")