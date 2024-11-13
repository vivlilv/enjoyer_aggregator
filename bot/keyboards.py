from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_mode_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Dawn Mode", callback_data="dawn_mode"),
            InlineKeyboardButton(text="Gradient Mode", callback_data="gradient_mode")
        ]
    ])
    return keyboard
