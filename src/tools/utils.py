from tools.logger import logger
from aiogram.types import FSInputFile
import os
from config import IMAGE_DIR

def get_payment_image(name: str):
    image_path = os.path.join(IMAGE_DIR, name)
    return FSInputFile(image_path)