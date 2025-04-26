from dotenv import load_dotenv
import os

load_dotenv()   # Busca y lee .env
DATABASE_URL = os.getenv("DATABASE_URL")
SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SHEET_KEY     = os.getenv("GSPREAD_SHEET_KEY")
SECRET_KEY    = os.getenv("SECRET_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")