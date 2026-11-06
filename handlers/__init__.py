from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart

from handlers.admin import (
    add_operation_start_handler,
    add_patient_start_handler,
    admin_handler,
    admin_patient_full_name_handler,
    admin_patient_phone_handler,
    operation_arrival_time_handler,
    operation_category_handler,
    operation_date_handler,
    operation_patient_phone_handler,
    operation_type_handler,
)
from handlers.patient import full_name_handler, phone_handler, registration_start_handler
from states import AdminAddOperation, AdminAddPatient, PatientRegistration


def register_handlers(dp: Dispatcher):
    dp.message.register(registration_start_handler, CommandStart())
    dp.message.register(admin_handler, Command("admin"))

    dp.message.register(add_patient_start_handler, F.text == "Добавить пациента")
    dp.message.register(admin_patient_full_name_handler, AdminAddPatient.waiting_for_full_name)
    dp.message.register(admin_patient_phone_handler, AdminAddPatient.waiting_for_phone)

    dp.message.register(full_name_handler, PatientRegistration.waiting_for_full_name)
    dp.message.register(phone_handler, PatientRegistration.waiting_for_phone)

    dp.message.register(add_operation_start_handler, F.text == "Назначить операцию")
    dp.message.register(operation_patient_phone_handler, AdminAddOperation.waiting_for_patient_phone)
    dp.message.register(operation_category_handler, AdminAddOperation.waiting_for_category)
    dp.message.register(operation_type_handler, AdminAddOperation.waiting_for_operation_type)
    dp.message.register(operation_date_handler, AdminAddOperation.waiting_for_operation_date)
    dp.message.register(operation_arrival_time_handler, AdminAddOperation.waiting_for_arrival_time)
