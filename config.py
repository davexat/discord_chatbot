import os
from dotenv import load_dotenv

load_dotenv()

TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")
if not TOKEN_DISCORD:
    raise ValueError("DISCORD_TOKEN no está definido en el archivo .env")

TOKEN_API_KEY = os.getenv("GEMINI_API_KEY")
if not TOKEN_API_KEY:
    raise ValueError("GEMINI_API_KEY no está definido en el archivo .env")
