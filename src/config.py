import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')
DOMAIN = os.getenv('DOMAIN')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS").split(",")]