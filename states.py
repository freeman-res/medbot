from aiogram.fsm.state import State, StatesGroup


class PatientRegistration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()


class AdminAddPatient(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()


class AdminAddOperation(StatesGroup):
    waiting_for_patient_phone = State()
    waiting_for_category = State()
    waiting_for_operation_type = State()
    waiting_for_operation_date = State()
    waiting_for_arrival_time = State()
