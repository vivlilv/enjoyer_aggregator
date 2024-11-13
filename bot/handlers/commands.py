from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from .core.project_manager import project_manager

router = Router()

@router.message(Command("mode"))
async def show_mode_selection(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Dawn Mode", callback_data="dawn_mode"),
            InlineKeyboardButton(text="Gradient Mode", callback_data="gradient_mode")
        ]
    ])
    
    await message.answer("Please select a mode:", reply_markup=keyboard)

@router.callback_query(F.data == "dawn_mode")
async def set_dawn_mode(callback_query: types.CallbackQuery):
    # Add your mode switching logic here
    await callback_query.answer("Switched to Dawn mode")
    await callback_query.message.edit_text("Dawn mode activated!")

@router.callback_query(F.data == "gradient_mode")
async def set_gradient_mode(callback_query: types.CallbackQuery):
    # Add your mode switching logic here
    await callback_query.answer("Switched to Gradient mode")
    await callback_query.message.edit_text("Gradient mode activated!")