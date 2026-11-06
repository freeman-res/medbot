from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import save_patient, save_user
from states import PatientRegistration


async def registration_start_handler(message: Message, state: FSMContext):
    print(message.from_user.id)
    await save_user(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
    )

    await state.set_state(PatientRegistration.waiting_for_full_name)
    await message.answer("Здравствуйте! Я бот клиники. Напишите ваше ФИО.")


async def full_name_handler(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(PatientRegistration.waiting_for_phone)
    await message.answer("Спасибо. Теперь напишите ваш номер телефона.")


async def phone_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data["full_name"]
    phone = message.text

    await save_patient(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone=phone,
    )

    await state.clear()
    await message.answer("Готово, вы зарегистрированы как пациент клиники.")
