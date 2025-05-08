import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')
DOMAIN = os.getenv('DOMAIN')