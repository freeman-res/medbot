from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить пациента")],
        [KeyboardButton(text="Назначить операцию")],
    ],
    resize_keyboard=True,
)
