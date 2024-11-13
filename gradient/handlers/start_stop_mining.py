from aiogram import Router, types, F, Bot
from database import (
    get_user_accounts,
    get_user_proxies,
    get_user_captcha_service_and_key,
)
from keyboards import main_menu_keyboard
from BotManager import BotManager
from config import CHANNEL_ID
from shared import user_bot_managers, user_tasks
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

router = Router()

async def is_subscribed(bot: Bot, channel_username, user_id):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        if member.status.lower() in ["member", "administrator", "creator"]:
            return True
    except Exception:
        return False

@router.callback_query(F.data == 'action_mining')
async def start_stop_mining(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id

    if user_id in user_tasks:
        bot_manager = user_bot_managers[user_id]
        bot_manager.stop()
        task = user_tasks[user_id]
        task.cancel()
        del user_tasks[user_id]
        del user_bot_managers[user_id]
        await callback_query.message.answer("Фарминг остановлен.")
    else:
        
        # subscribed = await is_subscribed(bot, CHANNEL_ID, user_id)

        subscribed = True

        if not subscribed:
            builder = InlineKeyboardBuilder()
            builder.row(
                types.InlineKeyboardButton(
                    text="Yes", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"
                ),
                types.InlineKeyboardButton(
                    text="No", callback_data="no_subscribe"
                )
            )
            await callback_query.message.answer(
                "Do you want to subscribe to Web3 Enjoyer Club?",
                reply_markup=builder.as_markup()
            )
            return

        accounts = get_user_accounts(user_id)
        proxies = get_user_proxies(user_id)
        captcha_service, captcha_api_key = get_user_captcha_service_and_key(user_id)

        if not accounts:
            await callback_query.message.answer(
                "У вас нет добавленных аккаунтов. Пожалуйста, добавьте аккаунты сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if not proxies:
            await callback_query.message.answer(
                "У вас нет добавленных прокси. Пожалуйста, добавьте прокси сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if len(proxies) < len(accounts):
            await callback_query.message.answer(
                "Количество прокси меньше количества аккаунтов. Пожалуйста, добавьте больше прокси."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        if not captcha_service or not captcha_api_key:
            await callback_query.message.answer(
                "Не указан сервис капчи или API ключ. Пожалуйста, установите их сначала."
            )
            await callback_query.message.answer(
                "Выберите следующее действие:", reply_markup=main_menu_keyboard()
            )
            return

        bot_manager = BotManager(
            accounts, proxies, captcha_service, captcha_api_key, user_id
        )
        user_bot_managers[user_id] = bot_manager
        task = asyncio.create_task(bot_manager.start_mining())
        user_tasks[user_id] = task
        await callback_query.message.answer("Фарминг запущен.")

    await callback_query.message.answer(
        "Выберите следующее действие:", reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "no_subscribe")
async def process_no_subscribe(callback_query: types.CallbackQuery):
    await callback_query.answer("Wrong answer. Try again.", show_alert=True)
