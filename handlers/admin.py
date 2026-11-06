from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from config import ADMIN_IDS
from database import (
    create_operation,
    create_patient,
    find_patient_by_phone,
    get_operation_categories,
    get_operation_types_by_category,
)
from keyboards import admin_keyboard
from states import AdminAddOperation, AdminAddPatient


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


async def admin_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к админ-панели.")
        return

    await message.answer("Панель администратора.", reply_markup=admin_keyboard)


async def add_patient_start_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа.")
        return

    await state.set_state(AdminAddPatient.waiting_for_full_name)
    await message.answer("Введите ФИО пациента.", reply_markup=ReplyKeyboardRemove())


async def admin_patient_full_name_handler(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(AdminAddPatient.waiting_for_phone)
    await message.answer("Введите телефон пациента.")


async def admin_patient_phone_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data["full_name"]
    phone = message.text

    await create_patient(full_name=full_name, phone=phone)

    await state.clear()
    await message.answer("Пациент добавлен.", reply_markup=admin_keyboard)


async def add_operation_start_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа.")
        return

    await state.set_state(AdminAddOperation.waiting_for_patient_phone)
    await message.answer("Введите телефон пациента.", reply_markup=ReplyKeyboardRemove())


async def operation_patient_phone_handler(message: Message, state: FSMContext):
    patient = await find_patient_by_phone(message.text)

    if patient is None:
        await message.answer("Пациент с таким телефоном не найден.", reply_markup=admin_keyboard)
        await state.clear()
        return

    await state.update_data(patient_id=patient["id"], patient_name=patient["full_name"])

    categories = await get_operation_categories()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{category['id']}. {category['name']}")]
            for category in categories
        ],
        resize_keyboard=True,
    )

    await state.set_state(AdminAddOperation.waiting_for_category)
    await message.answer("Выберите направление операции.", reply_markup=keyboard)


async def operation_category_handler(message: Message, state: FSMContext):
    category_id_text = message.text.split(".")[0]

    if not category_id_text.isdigit():
        await message.answer("Выберите категорию кнопкой.")
        return

    category_id = int(category_id_text)

    await state.update_data(category_id=category_id)

    operation_types = await get_operation_types_by_category(category_id)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{operation_type['id']}. {operation_type['name']}")]
            for operation_type in operation_types
        ],
        resize_keyboard=True,
    )

    await state.set_state(AdminAddOperation.waiting_for_operation_type)
    await message.answer("Выберите тип операции.", reply_markup=keyboard)


async def operation_type_handler(message: Message, state: FSMContext):
    operation_type_id_text = message.text.split(".")[0]

    if not operation_type_id_text.isdigit():
        await message.answer("Выберите операцию кнопкой.")
        return

    operation_type_id = int(operation_type_id_text)

    await state.update_data(operation_type_id=operation_type_id)
    await state.set_state(AdminAddOperation.waiting_for_operation_date)
    await message.answer(
        "Введите дату операции в формате ГГГГ-ММ-ДД.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def operation_date_handler(message: Message, state: FSMContext):
    try:
        operation_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД.")
        return

    await state.update_data(operation_date=operation_date)
    await state.set_state(AdminAddOperation.waiting_for_arrival_time)
    await message.answer("Введите время прихода в формате ЧЧ:ММ.")


async def operation_arrival_time_handler(message: Message, state: FSMContext):
    try:
        arrival_time = datetime.strptime(message.text, "%H:%M").time()
    except ValueError:
        await message.answer("Неверный формат времени. Введите время в формате ЧЧ:ММ.")
        return

    data = await state.get_data()

    await create_operation(
        patient_id=data["patient_id"],
        operation_type_id=data["operation_type_id"],
        operation_date=data["operation_date"],
        arrival_time=arrival_time,
    )

    await state.clear()
    await message.answer("Операция назначена.", reply_markup=admin_keyboard)
