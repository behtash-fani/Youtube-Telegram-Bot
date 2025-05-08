import logging
from aiogram.types import Update, Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from db.database import BotDB
from keyboard.keys import get_user_keyboard
from typing import Callable, Awaitable, Dict, Any

db = BotDB()

class AutoKeyboardMiddleware(BaseMiddleware):
    """Middleware for automatically adding a keyboard to user messages."""
    
    async def __call__(
        self, 
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]], 
        event: Update, 
        data: Dict[str, Any]
    ) -> Any:
        # Skip if not a message
        if not event.message:
            return await handler(event, data)

        # Get user keyboard
        user_id = event.message.from_user.id
        keyboard = await get_user_keyboard(user_id)
        
        # Store keyboard in data for handlers to use
        data['reply_markup'] = keyboard
        
        # Call handler
        result = await handler(event, data)
        
        # If handler returns a Message object, ensure it has the keyboard
        if isinstance(result, Message):
            if not result.reply_markup:
                await result.edit_reply_markup(reply_markup=keyboard)
        
        return result