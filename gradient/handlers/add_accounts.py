from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_menu_keyboard, cancel_keyboard
from database import add_accounts_to_user, delete_user_accounts
import re

router = Router()

class AddAccountsStates(StatesGroup):
    waiting_for_accounts = State()

@router.callback_query(F.data == 'data_accounts')
async def add_accounts_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer(
        "Пожалуйста, отправьте ваши аккаунты в формате:\nemail:password\nemail:password\nemail:password:imap_password",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddAccountsStates.waiting_for_accounts)

@router.callback_query(AddAccountsStates.waiting_for_accounts, F.data == 'cancel')
async def cancel_add_accounts(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Добавление аккаунтов отменено.")
    await state.clear()

@router.message(AddAccountsStates.waiting_for_accounts)
async def accounts_received(message: types.Message, state: FSMContext):
    accounts_text = message.text
    accounts_list = accounts_text.strip().split('\n')
    parsed_accounts = []
    password_pattern = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
    for account in accounts_list:
        if ':' in account:
            parts = account.strip().split(':')
            email = parts[0].strip()
            password = parts[1].strip()
            imap_pass = parts[2].strip() if len(parts) > 2 else None

            # if not password_pattern.match(password):
                # await message.answer(
                #     f"Пароль для {email} не соответствует требованиям. Пожалуйста, убедитесь, что пароль содержит не менее 8 символов, включая строчные и заглавные буквы, цифры и специальные символы."
                # )
                # await state.clear()
                # return
            parsed_accounts.append((email, password, imap_pass))
        else:
            await message.answer(
                "Ошибка в формате аккаунтов. Добавление аккаунтов отменено."
            )
            await state.clear()
            return
    user_id = message.from_user.id
    delete_user_accounts(user_id)
    add_accounts_to_user(user_id, parsed_accounts)
    await message.answer(f"Аккаунты успешно добавлены: {len(parsed_accounts)}")
    await message.answer(
        "Выберите следующее действие:", reply_markup=main_menu_keyboard()
    )
    await state.clear()
