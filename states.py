# states.py – описание состояний (FSM)
from aiogram.fsm.state import State, StatesGroup

class BuildAutoState(StatesGroup):
    usage = State()    # пользователь выбирает цель использования ПК
    budget = State()   # пользователь вводит бюджет

class BuildManualState(StatesGroup):
    choosing_cpu = State()
    choosing_motherboard = State()
    choosing_ram = State()
    choosing_gpu = State()
    choosing_storage = State()
    choosing_case = State()
    choosing_psu = State()
    choosing_cooler = State()
    confirm = State()  # финальное подтверждение сборки
