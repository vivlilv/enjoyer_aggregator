from aiogram import Router, types
from aiogram.filters import CommandStart
from keyboards import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    username = message.from_user.username or "User"

    await message.answer(
        f"👋 Добро пожаловать, {username}! Выберите действие из меню ниже:",
        reply_markup=main_menu_keyboard()
    )
