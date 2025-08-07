import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

# --- Make sure all necessary components are imported ---
# These would be in your project's local folders
from bot.handlers import setup_handlers
from database_models.manager import get_db_session, games, users
from sqlalchemy import select

# --- 1. Setup & Configuration ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment variables for configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# --- 2. Global Application Instances ---
# The Telegram bot application instance is stored globally
bot_app: Application | None = None


# --- 3. Lifespan Management for Startup/Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles critical startup and shutdown events for the FastAPI application."""
    logger.info("Application startup...")
    global bot_app
    if bot_app:
        await bot_app.initialize()
        if WEBHOOK_URL:
            # Construct the full webhook URL for Telegram
            webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
            try:
                # Set the webhook with Telegram's servers
                await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
                logger.info(f"Successfully set webhook to: {webhook_full_url}")
            except RetryAfter:
                logger.warning("Could not set webhook due to flood control. Another worker likely succeeded.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while setting webhook: {e}")
        else:
            # This is a fatal error for a production environment
            logger.error("FATAL: WEBHOOK_URL environment variable is not set!")
    
    yield  # --- The application is now running and ready to handle requests ---
    
    logger.info("Application shutdown...")
    if bot_app:
        # Gracefully shut down the bot application
        await bot_app.shutdown()


# --- 4. Main FastAPI Application Initialization ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

# --- Initialize the Telegram Bot ---
if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot functionality will be disabled.")
else:
    # Build the Python Telegram Bot application
    ptb_application_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    ptb_application = ptb_application_builder.build()
    
    # Attach all the defined handlers (e.g., /start, button clicks)
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")


# --- 5. API Endpoints ---

# Webhook endpoint for receiving updates from Telegram
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Main webhook to receive and process updates from Telegram."""
    if not bot_app:
        # If the bot isn't initialized, service is unavailable
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        # Acknowledge receipt of the update to Telegram
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- INJECTED ENDPOINT TO FIX THE ERROR ---
@app.get("/api/games")
async def get_open_games():
    """Endpoint for the web app to fetch open game lobbies."""
    live_games = []
    try:
        # Use an async session to query the database
        async with get_db_session() as session:
            # SQL statement to select game data, joining with the users table to get the creator's name
            stmt = select(games.c.id, games.c.stake, games.c.pot, users.c.username).\
                   join(users, games.c.creator_id == users.c.telegram_id).\
                   where(games.c.status == 'lobby').order_by(games.c.created_at.desc())
            
            result = await session.execute(stmt)
            
            # Format the data for the frontend
            for row in result.fetchall():
                live_games.append({
                    "id": row.id,
                    "creator_name": row.username or "Player",  # Fallback name
                    "creator_avatar": f"https://i.pravatar.cc/40?u={row.id}", # Placeholder avatar
                    "stake": float(row.stake),
                    "prize": float(row.pot * 0.9), # Assuming a 10% commission
                })
    except Exception as e:
        logger.error(f"Failed to fetch open games from database: {e}")
        # Return an empty list on failure so the frontend doesn't break
        return {"games": []}
        
    # Return the list of games as a JSON response
    return {"games": live_games}

# Health check endpoint for monitoring services (e.g., Render)
@app.get("/health")
async def health_check():
    """A simple health check endpoint that returns a success status."""
    return {"status": "healthy"}


# --- 6. Mount Static Files for the Web App ---
# This crucial line tells FastAPI to serve the frontend's HTML, CSS, and JS files.
# It assumes your frontend build files are located in a folder named 'frontend'.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")