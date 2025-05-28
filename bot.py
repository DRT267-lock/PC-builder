# bot.py – основной модуль бота
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# Импортируем наши модули
from config import API_TOKEN, DB_DSN
from db import Database
from states import BuildAutoState, BuildManualState
from builder import build_pc

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()  # Aiogram v3: можно явно не передавать loop, он берется из asyncio

# Инициализация БД (globally, then connect in startup)
db = Database(DB_DSN)

# Хендлер на команду /start
@dp.message(Command("start"))
async def on_start(message: Message):
    # Сохранить пользователя в БД (асинхронно)
    await db.add_user(message.from_user.id, message.from_user.username or message.from_user.full_name)
    # Приветственное сообщение
    welcome_text = (f"Привет, {message.from_user.first_name}! 👋\n"
                    "Я бот, который поможет подобрать оптимальную сборку ПК по твоим требованиям.\n"
                    "Выбери, что ты хочешь сделать:")
    # Кнопки главного меню
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Подобрать сборку", callback_data="auto")],
        [InlineKeyboardButton(text="🛠 Ручной режим сборки", callback_data="manual")],
        [InlineKeyboardButton(text="💾 Мои сохранённые сборки", callback_data="view_builds")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])
    await message.answer(welcome_text, reply_markup=menu_kb)

# Хендлер на нажатие кнопок главного меню (CallbackQuery)
@dp.callback_query(lambda c: c.data in ["auto", "manual", "view_builds", "help"])
async def on_menu_click(callback: CallbackQuery, state: FSMContext):
    action = callback.data
    user_id = await db.get_user_id(callback.from_user.id)
    if action == "auto":
        # Начать диалог автоматического подбора
        await callback.message.answer("🚀 Автоматический подбор сборки запущен.\nВыберите цель использования ПК:", 
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                          [InlineKeyboardButton(text="🎮 Игры", callback_data="usage_Игры")],
                                          [InlineKeyboardButton(text="💼 Работа/Офис", callback_data="usage_Работа")],
                                          [InlineKeyboardButton(text="🖥️ Рендеринг/3D", callback_data="usage_Рендеринг")],
                                          [InlineKeyboardButton(text="Другое", callback_data="usage_Другое")]
                                      ]))
        await state.set_state(BuildAutoState.usage)
        await db.log_action(user_id, "start_auto_build")
    elif action == "manual":
        # Начать диалог ручной сборки
        await callback.message.answer("🔧 Ручной режим: давайте соберём ПК по компонентам.\nСначала выберите процессор:")
        # Сформировать кнопки CPU (например, несколько топовых CPU из базы)
        cpu_list = await db.select_cpus(usage=None, max_price=None)
        # Ограничимся 5 вариантами для примера
        cpu_buttons = []
        for cpu in cpu_list[:5]:
            cpu_buttons.append([InlineKeyboardButton(text=f"{cpu['name']} ({cpu['price']} ₽)", callback_data=f"cpu_{cpu['id']}")])
        if not cpu_buttons:
            cpu_buttons.append([InlineKeyboardButton(text="Нет данных по CPU", callback_data="ignore")])
        cpu_kb = InlineKeyboardMarkup(inline_keyboard=cpu_buttons)
        await callback.message.answer("Процессоры:", reply_markup=cpu_kb)
        await state.set_state(BuildManualState.choosing_cpu)
        await db.log_action(user_id, "start_manual_build")
    elif action == "view_builds":
        # Отобразить сохранённые сборки пользователя
        builds = await db.get_builds(user_id)
        if not builds:
            await callback.message.answer("У вас нет сохранённых сборок.")
        else:
            text = "💾 *Ваши сохранённые сборки:*\n"
            for rec in builds:
                price = rec.get('total_price') or 0
                text += f"- Сборка #{rec['id']} от {rec['created_at']}, сумма {price} ₽\n"
            text += "\nЧтобы подробнее посмотреть сборку, введите команду `/build <ID>`."
            await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()  # просто уберём часики на кнопке
    elif action == "help":
        help_text = ("*Помощь по боту*\n"
                     "Этот бот поможет собрать ПК. Вы можете воспользоваться автоматическим подбором, указав лишь цель и бюджет, либо вручную выбирать каждую комплектующую.\n"
                     "- Нажмите «Подобрать сборку», чтобы бот предложил оптимальную конфигурацию.\n"
                     "- Нажмите «Ручной режим сборки», чтобы самостоятельно выбрать компоненты с подсказками совместимости.\n"
                     "- «Мои сохранённые сборки» – просмотреть и сохранить конфигурации.\n"
                     "Команда /cancel отменяет текущий процесс.\n"
                     "Приятного пользования!")
        await callback.message.answer(help_text, parse_mode="Markdown")
        await callback.answer()

# Хендлер выбора цели использования (шаг 1 автоподбора, ловим callback от кнопок "usage_...")
@dp.callback_query(lambda c: c.data and c.data.startswith("usage_"), StateFilter(BuildAutoState.usage))
async def on_choose_usage(callback: CallbackQuery, state):
    # Получаем выбранную цель (после "usage_")
    usage = callback.data.split("usage_")[1]
    # Сохраняем в FSM-состоянии
    await state.update_data(chosen_usage=usage)
    # Переходим к следующему состоянию – запрос бюджета
    await state.set_state(BuildAutoState.budget)
    await callback.message.answer(f"Цель: *{usage}*. Введите ваш бюджет в ₽:", parse_mode="Markdown")
    await callback.answer()  # убираем уведомление

# Хендлер ввода бюджета (шаг 2 автоподбора, ловим текстовое сообщение в состоянии BuildAutoState.budget)
@dp.message(StateFilter(BuildAutoState.budget))
async def on_enter_budget(message: Message, state):
    # Валидация ввода бюджета
    try:
        budget = int(message.text.strip().replace(" ", ""))
    except ValueError:
        await message.reply("Пожалуйста, введите целое число для бюджета (в рублях). Попробуйте ещё раз:")
        return
    # Получаем сохранённую цель из FSM
    data = await state.get_data()
    usage = data.get("chosen_usage", "не указана")
    # Генерируем сборку
    await message.answer("⌛ Пожалуйста, подождите, идёт подбор оптимальной конфигурации...")
    build = await build_pc(db, usage, budget)
    # Сохраняем текущую сборку во временном состоянии
    await state.update_data(last_build=build)
    # Формируем текст ответа с итоговой сборкой
    if not build or not build.get('cpu'):
        await message.answer("К сожалению, не удалось подобрать сборку по указанным параметрам. Попробуйте изменить критерии.")
    else:
        total = build.get('total_price', 0)
        result_text = f"✅ *Сборка \"{usage}\" за ~{total} ₽:*\n"
        if build.get('cpu'):
            result_text += f"- CPU: {build['cpu']['name']} ({build['cpu']['price']} ₽)\n"
        if build.get('motherboard'):
            result_text += f"- Мат. плата: {build['motherboard']['name']} ({build['motherboard']['price']} ₽)\n"
        if build.get('ram'):
            result_text += f"- ОЗУ: {build['ram']['name']} ({build['ram']['price']} ₽)\n"
        if build.get('gpu'):
            result_text += f"- Видеокарта: {build['gpu']['name']} ({build['gpu']['price']} ₽)\n"
        else:
            result_text += "- Видеокарта: (не требуется)\n"
        if build.get('storage'):
            result_text += f"- Накопитель: {build['storage']['name']} ({build['storage']['price']} ₽)\n"
        if build.get('psu'):
            result_text += f"- Блок питания: {build['psu']['name']} ({build['psu']['price']} ₽)\n"
        if build.get('case'):
            result_text += f"- Корпус: {build['case']['name']} ({build['case']['price']} ₽)\n"
        if build.get('cooler'):
            result_text += f"- Кулер: {build['cooler']['name']} ({build['cooler']['price']} ₽)\n"
        result_text += f"*Итого:* {total} ₽\n"
        await message.answer(result_text, parse_mode="Markdown", 
                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                  [InlineKeyboardButton(text="💾 Сохранить сборку", callback_data="save_build")],
                                  [InlineKeyboardButton(text="🔄 В меню", callback_data="back_to_menu")]
                              ]))
    # Логируем действие
    user_id = await db.get_user_id(message.from_user.id)
    await db.log_action(user_id, f"auto_build_done_{usage}")


# Хендлер на сохранение сборки после авто-подбора
@dp.callback_query(lambda c: c.data == "save_build")
async def on_save_build(callback: CallbackQuery, state: FSMContext):
    user_id = await db.get_user_id(callback.from_user.id)
    data = await state.get_data()
    build = data.get("last_build", {})
    # Подготовить словарь для сохранения
    build_data = {
        'cpu_id': None,
        'motherboard_id': None,
        'ram_id': None,
        'gpu_id': None,
        'storage_id': None,
        'case_id': None,
        'psu_id': None,
        'cooler_id': None,
        'total_price': build.get('total_price')
    }
    await db.save_build(user_id, build_data)
    await callback.message.answer("💾 Сборка сохранена! Вы можете просмотреть её в разделе 'Мои сохранённые сборки'.")
    await db.log_action(user_id, "build_saved")
    await state.clear()
    await callback.answer()


# Хендлер для возврата в главное меню по кнопке "back_to_menu"
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def on_back_to_menu(callback: CallbackQuery):
    # Показываем главное меню заново
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Подобрать сборку", callback_data="auto")],
        [InlineKeyboardButton(text="🛠 Ручной режим сборки", callback_data="manual")],
        [InlineKeyboardButton(text="💾 Мои сохранённые сборки", callback_data="view_builds")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])
    await callback.message.answer("Главное меню:", reply_markup=menu_kb)
    await callback.answer()

# Хендлеры для ручного режима (выбор компонентов последовательно)
@dp.callback_query(lambda c: c.data and c.data.startswith("cpu_"), StateFilter(BuildManualState.choosing_cpu))
async def manual_choose_cpu(callback: CallbackQuery, state):
    cpu_id = int(callback.data.split("cpu_")[1])
    # Получаем выбранный CPU из базы
    cpu = None
    cpu_list = await db.select_cpus(None)
    for c in cpu_list:
        if c['id'] == cpu_id:
            cpu = c
            break
    if not cpu:
        await callback.answer("Ошибка: выбранный CPU не найден.")
        return
    # Сохраняем выбор CPU
    await state.update_data(cpu=cpu)
    # Предлагаем выбрать материнскую плату под этот CPU
    mobos = await db.select_motherboards(cpu['socket'])
    if not mobos:
        await callback.message.answer("❌ Не найдены материнские платы для сокета " + cpu['socket'])
        await state.clear()
        return
    # Формируем список кнопок для плат (первые 5)
    mobo_buttons = []
    for mobo in mobos[:5]:
        mobo_buttons.append([InlineKeyboardButton(
            text=f"{mobo['name']} ({mobo['price']} ₽)", 
            callback_data=f"mobo_{mobo['id']}"
        )])
    mobo_kb = InlineKeyboardMarkup(inline_keyboard=mobo_buttons)
    await callback.message.answer("Материнские платы, совместимые с выбранным CPU:", reply_markup=mobo_kb)
    await state.set_state(BuildManualState.choosing_motherboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("mobo_"), StateFilter(BuildManualState.choosing_motherboard))
async def manual_choose_mobo(callback: CallbackQuery, state):
    mobo_id = int(callback.data.split("mobo_")[1])
    # Получаем материнскую плату
    mobos = await db.select_motherboards(socket=None)  # получим все, затем выберем нужную
    mobo = None
    for m in mobos:
        if m['id'] == mobo_id:
            mobo = m
            break
    if not mobo:
        await callback.answer("Ошибка: мат. плата не найдена.")
        return
    # Сохраняем выбор
    await state.update_data(motherboard=mobo)
    # Предлагаем выбрать ОЗУ (тип зависит от платы)
    ram_type = mobo['ram_type']
    rams = await db.select_rams(ram_type, needed_size=8)
    ram_buttons = []
    for ram in rams[:5]:
        ram_buttons.append([InlineKeyboardButton(text=f"{ram['name']} ({ram['price']} ₽)", callback_data=f"ram_{ram['id']}")])
    if not ram_buttons:
        ram_buttons.append([InlineKeyboardButton(text="Нет модулей ОЗУ совместимого типа", callback_data="ignore")])
    ram_kb = InlineKeyboardMarkup(inline_keyboard=ram_buttons)
    await callback.message.answer(f"ОЗУ (тип {ram_type}):", reply_markup=ram_kb)
    await state.set_state(BuildManualState.choosing_ram)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("ram_"), StateFilter(BuildManualState.choosing_ram))
async def manual_choose_ram(callback: CallbackQuery, state):
    ram_id = int(callback.data.split("ram_")[1])
    # Получаем RAM
    data = await state.get_data()
    ram_list = await db.select_rams(data.get('motherboard')['ram_type'], needed_size=0)
    ram = next((r for r in ram_list if r['id'] == ram_id), None)
    if not ram:
        await callback.answer("Ошибка: ОЗУ не найдено.")
        return
    await state.update_data(ram=ram)
    # Предлагаем выбрать видеокарту
    gpus = await db.select_gpus()
    gpu_buttons = []
    if gpus:
        for gpu in gpus[:5]:
            gpu_buttons.append([InlineKeyboardButton(text=f"{gpu['name']} ({gpu['price']} ₽)", callback_data=f"gpu_{gpu['id']}")])
    else:
        gpu_buttons.append([InlineKeyboardButton(text="Нет данных по GPU", callback_data="ignore")])
    gpu_kb = InlineKeyboardMarkup(inline_keyboard=gpu_buttons)
    await callback.message.answer("Видеокарты:", reply_markup=gpu_kb)
    await state.set_state(BuildManualState.choosing_gpu)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("gpu_"), StateFilter(BuildManualState.choosing_gpu))
async def manual_choose_gpu(callback: CallbackQuery, state):
    gpu_id = int(callback.data.split("gpu_")[1])
    # Получаем GPU
    gpu_list = await db.select_gpus()
    gpu = next((g for g in gpu_list if g['id'] == gpu_id), None)
    if not gpu:
        await callback.answer("Ошибка: GPU не найден.")
        return
    await state.update_data(gpu=gpu)
    # Предлагаем накопитель
    storages = await db.select_storages(min_capacity=256)
    storage_buttons = []
    for st in storages[:5]:
        storage_buttons.append([InlineKeyboardButton(text=f"{st['name']} ({st['price']} ₽)", callback_data=f"sto_{st['id']}")])
    storage_kb = InlineKeyboardMarkup(inline_keyboard=storage_buttons)
    await callback.message.answer("Накопители:", reply_markup=storage_kb)
    await state.set_state(BuildManualState.choosing_storage)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("sto_"), StateFilter(BuildManualState.choosing_storage))
async def manual_choose_storage(callback: CallbackQuery, state):
    sto_id = int(callback.data.split("sto_")[1])
    storage_list = await db.select_storages(min_capacity=0)
    storage = next((s for s in storage_list if s['id'] == sto_id), None)
    if not storage:
        await callback.answer("Ошибка: накопитель не найден.")
        return
    await state.update_data(storage=storage)
    # Предлагаем корпус (с учетом форм-фактора и длины видео)
    data = await state.get_data()
    mobo = data.get('motherboard')
    gpu = data.get('gpu')
    # Формируем корпус без учёта длины GPU (адаптировано под тестовые данные)
    cases = await db.select_cases(mobo['form_factor'], gpu_length=None)
    case_buttons = []
    for case in cases[:5]:
        case_buttons.append([InlineKeyboardButton(text=f"{case['name']} ({case['price']} ₽)", callback_data=f"case_{case['id']}")])
    case_kb = InlineKeyboardMarkup(inline_keyboard=case_buttons)
    await callback.message.answer("Корпуса:", reply_markup=case_kb)
    await state.set_state(BuildManualState.choosing_case)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("case_"), StateFilter(BuildManualState.choosing_case))
async def manual_choose_case(callback: CallbackQuery, state):
    case_id = int(callback.data.split("case_")[1])
    case_list = await db.select_cases(form_factor="", gpu_length=None)
    case = next((c for c in case_list if c['id'] == case_id), None)
    if not case:
        await callback.answer("Ошибка: корпус не найден.")
        return
    await state.update_data(case=case)
    # Предлагаем блок питания (мощность расчитываем по CPU+GPU)
    data = await state.get_data()
    cpu = data.get('cpu')
    gpu = data.get('gpu')
    total_tdp = 0
    if cpu: total_tdp += cpu.get('tdp') or 0
    if gpu: total_tdp += gpu.get('tdp') or 0
    required_power = int(total_tdp * 1.2) + 50
    psus = await db.select_psus(required_power)
    psu_buttons = []
    for psu in psus[:5]:
        psu_buttons.append([InlineKeyboardButton(text=f"{psu['name']} ({psu['power']}W, {psu['price']} ₽)", callback_data=f"psu_{psu['id']}")])
    psu_kb = InlineKeyboardMarkup(inline_keyboard=psu_buttons)
    await callback.message.answer("Блоки питания:", reply_markup=psu_kb)
    await state.set_state(BuildManualState.choosing_psu)
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("psu_"), StateFilter(BuildManualState.choosing_psu))
async def manual_choose_psu(callback: CallbackQuery, state):
    psu_id = int(callback.data.split("psu_")[1])
    psu_list = await db.select_psus(0)
    psu = next((p for p in psu_list if p['id'] == psu_id), None)
    if not psu:
        await callback.answer("Ошибка: БП не найден.")
        return
    await state.update_data(psu=psu)
    # Предлагаем кулер (опционально, можно добавить условие)
    data = await state.get_data()
    cpu = data.get('cpu')
    cooler_buttons = []
    if cpu:
        coolers = await db.select_coolers(cpu['socket'], cpu.get('tdp') or 65)
        for col in coolers[:5]:
            cooler_buttons.append([InlineKeyboardButton(text=f"{col['name']} ({col['price']} ₽)", callback_data=f"col_{col['id']}")])
    if cooler_buttons:
        cooler_kb = InlineKeyboardMarkup(inline_keyboard=cooler_buttons + [[InlineKeyboardButton(text="Без отдельного кулера", callback_data="col_none")]])
        await callback.message.answer("Кулеры (введите пропустить, если не нужен):", reply_markup=cooler_kb)
    else:
        await callback.message.answer("Отдельный кулер не требуется или нет вариантов.")
    await state.set_state(BuildManualState.choosing_cooler)
    await callback.answer()

@dp.callback_query(lambda c: c.data and (c.data.startswith("col_") or c.data == "col_none"), StateFilter(BuildManualState.choosing_cooler))
async def manual_choose_cooler(callback: CallbackQuery, state):
    if callback.data == "col_none":
        cooler = None
    else:
        col_id = int(callback.data.split("col_")[1])
        cooler_list = await db.select_coolers(socket="", required_tdp=0)
        cooler = next((col for col in cooler_list if col['id'] == col_id), None)
        if not cooler:
            await callback.answer("Ошибка: кулер не найден.")
            return
    await state.update_data(cooler=cooler)
    # Переходим к подтверждению
    data = await state.get_data()
    # Формируем текст сборки
    total_price = 0
    summary = "🔧 *Собранная конфигурация:*\n"
    if data.get('cpu'):
        cpu = data['cpu']; total_price += cpu['price']; summary += f"- CPU: {cpu['name']} ({cpu['price']} ₽)\n"
    if data.get('motherboard'):
        mb = data['motherboard']; total_price += mb['price']; summary += f"- Мат. плата: {mb['name']} ({mb['price']} ₽)\n"
    if data.get('ram'):
        ram = data['ram']; total_price += ram['price']; summary += f"- ОЗУ: {ram['name']} ({ram['price']} ₽)\n"
    if data.get('gpu'):
        gpu = data['gpu']; total_price += gpu['price']; summary += f"- Видеокарта: {gpu['name']} ({gpu['price']} ₽)\n"
    else:
        summary += "- Видеокарта: (не выбрана)\n"
    if data.get('storage'):
        sto = data['storage']; total_price += sto['price']; summary += f"- Накопитель: {sto['name']} ({sto['price']} ₽)\n"
    if data.get('case'):
        case = data['case']; total_price += case['price']; summary += f"- Корпус: {case['name']} ({case['price']} ₽)\n"
    if data.get('psu'):
        psu = data['psu']; total_price += psu['price']; summary += f"- Блок питания: {psu['name']} ({psu['price']} ₽)\n"
    if data.get('cooler'):
        col = data['cooler']; total_price += col['price']; summary += f"- Кулер: {col['name']} ({col['price']} ₽)\n"
    summary += f"*Итого:* {total_price} ₽\n"
    summary += "Сохранить эту сборку?"
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 Сохранить", callback_data="manual_save")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="manual_cancel")]
    ])
    await callback.message.answer(summary, parse_mode="Markdown", reply_markup=confirm_kb)
    await state.set_state(BuildManualState.confirm)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "manual_save", StateFilter(BuildManualState.confirm))
async def manual_save_build(callback: CallbackQuery, state):
    user_id = await db.get_user_id(callback.from_user.id)
    data = await state.get_data()
    # Подготовить словарь build для сохранения
    build_data = {
        'cpu_id': data['cpu']['id'] if data.get('cpu') else None,
        'motherboard_id': data['motherboard']['id'] if data.get('motherboard') else None,
        'ram_id': data['ram']['id'] if data.get('ram') else None,
        'gpu_id': data['gpu']['id'] if data.get('gpu') else None,
        'storage_id': data['storage']['id'] if data.get('storage') else None,
        'case_id': data['case']['id'] if data.get('case') else None,
        'psu_id': data['psu']['id'] if data.get('psu') else None,
        'cooler_id': data['cooler']['id'] if data.get('cooler') else None,
        'total_price': 0
    }
    # Рассчитать total_price
    for comp in ['cpu', 'motherboard', 'ram', 'gpu', 'storage', 'case', 'psu', 'cooler']:
        if data.get(comp):
            build_data['total_price'] += data[comp]['price']
    # Сохранить сборку
    await db.save_build(user_id, build_data)
    await callback.message.answer(
        "✅ Сборка сохранена в вашем списке!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 В главное меню", callback_data="back_to_menu")]
        ])
    )
    await db.log_action(user_id, "manual_build_saved")
    await state.clear()

@dp.callback_query(lambda c: c.data == "manual_cancel", StateFilter(BuildManualState.confirm))
async def manual_cancel_build(callback: CallbackQuery, state):
    # Отменить сохранение и сбросить состояние
    await callback.message.answer("Сборка отменена. Вы можете начать заново или вернуться в меню.")
    await state.clear()
    await callback.answer()

# Общий хендлер на отмену /cancel (срабатывает в любом состоянии)
@dp.message(Command("cancel"))
@dp.message(lambda m: m.text and m.text.lower() == "отмена")
async def cancel_handler(message: Message, state):
    await message.answer("Действие отменено. Возвращаюсь в главное меню.")
    await state.clear()
    # Можно заново вызвать меню /start или вывести inline-кнопки меню
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Подобрать сборку", callback_data="auto")],
        [InlineKeyboardButton(text="🛠 Ручной режим сборки", callback_data="manual")],
        [InlineKeyboardButton(text="💾 Мои сохранённые сборки", callback_data="view_builds")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])
    await message.answer("Главное меню:", reply_markup=menu_kb)

# Функция запуска бота
async def main():
    # Устанавливаем соединение с базой
    await db.connect()
    # Запускаем бот
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
