#!/usr/bin/env python3
# coding: utf-8

import telebot
from telebot import types
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TOKEN")
KEY_FILE = os.getenv("KEY_FILE")
USED_FILE = os.getenv("USED_FILE")
USER_DATA_FILE = os.getenv("USER_DATA_FILE")
OWNER_ID = int(os.getenv("OWNER_ID"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "0000 0000 0000 0000")
CARD_HOLDER = os.getenv("CARD_HOLDER", "Получатель")
import json
from datetime import datetime, timedelta


# === Настройки ===


bot = telebot.TeleBot(TOKEN)

# === Загрузка данных ===
def load_keys():
    return [line.strip() for line in open(KEY_FILE, "r", encoding="utf-8")] if os.path.exists(KEY_FILE) else []

def load_user_data():
    return json.load(open(USER_DATA_FILE, "r", encoding="utf-8")) if os.path.exists(USER_DATA_FILE) else {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_free_vless_link():
    if not os.path.exists(KEY_FILE):
        return None
    all_keys = [line.strip() for line in open(KEY_FILE, "r", encoding="utf-8") if line.strip()]
    used_keys = [line.strip() for line in open(USED_FILE, "r", encoding="utf-8")] if os.path.exists(USED_FILE) else []
    free_keys = [k for k in all_keys if k not in used_keys]
    if not free_keys:
        return None
    selected = free_keys[0]
    with open(USED_FILE, "a", encoding="utf-8") as f:
        f.write(selected + "\n")
    return selected

def generate_vpn_keys(count):
    result = []
    for _ in range(count):
        link = get_free_vless_link()
        if link:
            result.append(link)
    return result


# === Старт ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("✅ Купить доступ"),
        types.KeyboardButton("🎁 Получить пробный доступ"),
        types.KeyboardButton("👤 Мой профиль"),
        types.KeyboardButton("❓ Как это работает"),
        types.KeyboardButton("📘 FAQ"),
        types.KeyboardButton("📜 Правила использования")
    )
    bot.send_message(message.chat.id, "👋 Добро пожаловать!\n\nВыберите нужный пункт ниже:", reply_markup=markup)

    bot.send_message(
        message.chat.id,
        "👋 *Добро пожаловать в BlokaNet!*\n\n"
        "🌐 Независимый VPN-сервис для свободного, безопасного интернета.\n\n"
        "🔒 Каждый получает уникальный защищённый ключ\n"
        "⚡️ Протокол: *Xray REALITY*\n"
        "📱 Android, iOS, Windows, macOS, мобильные сети — всё работает.",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
@bot.message_handler(commands=["debugkey"])
def debug_key(message):
    link = get_free_vless_link()
    if link:
        bot.send_message(message.chat.id, f"✅ test: `{link}`", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ нет ключей", parse_mode="Markdown")


@bot.message_handler(func=lambda msg: msg.text == "❓ Как это работает")
def how_it_works(message):
    caption = (
        "🤔 *Как это работает — пошагово:*\n\n"
        "1️⃣ Нажмите кнопку *«Купить доступ»*\n"
        "2️⃣ Получите реквизиты для перевода\n"
        "3️⃣ Оплатите и отправьте скрин перевода\n"
        "4️⃣ Бот автоматически подтвердит оплату и выдаст вам VPN-ключ\n\n"
        "📲 *Дальнейшие шаги для подключения:*\n"
        "1️⃣ Установите приложение *Amnezia VPN* из Google Play или App Store\n"
        "2️⃣ Откройте приложение → нажмите *Let's get started*\n"
        "3️⃣ Вставьте выданный ключ в поле\n"
        "4️⃣ Нажмите кнопку *Connect* — и VPN активируется\n\n"
        "🔒 Всё просто: без регистрации, логинов и технической головной боли\n"
        "💬 Если возникнут вопросы — напишите: @BlokaNet"
    )

    with open("/root/logo.png", "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption=caption, parse_mode="Markdown")

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    user_id = str(message.contact.user_id)
    phone = message.contact.phone_number
    users = load_user_data()
    users.setdefault(user_id, {})["phone"] = phone
    save_user_data(users)
    bot.send_message(message.chat.id, "📞 Номер сохранён. Теперь можете нажать «Купить доступ».", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "✅ Купить доступ")
def buy_access(message):
    from datetime import datetime

    def has_tariff(packages, target_tariff):
        return any(pkg.get("tariff") == target_tariff for pkg in packages)

    user_id = str(message.from_user.id)
    username = message.from_user.username
    users = load_user_data()
    user_info = users.get(user_id, {})
    packages = user_info.get("packages", [])

    # 🔘 Формируем выбор тарифов
    markup = types.InlineKeyboardMarkup()

    if not has_tariff(packages, "1"):
        markup.add(types.InlineKeyboardButton("📍 Пакет №1 — 1 ключ за 159₽", callback_data="start_new_tariff_1"))
    if not has_tariff(packages, "2"):
        markup.add(types.InlineKeyboardButton("📦 Пакет №2 — 2 ключа за 199₽", callback_data="start_new_tariff_2"))
    if not has_tariff(packages, "3"):
        markup.add(types.InlineKeyboardButton("📦 Пакет №3 — 3 ключа за 259₽", callback_data="start_new_tariff_3"))

    # Если все три тарифа уже покупались
    if not markup.to_dict().get("inline_keyboard"):
        bot.send_message(
            message.chat.id,
            "⚠️ Вы уже приобрели все доступные тарифы.\n\n🛠 Теперь вы можете только *продлевать* их из раздела *Мой профиль*.",
            parse_mode="Markdown"
        )
        return

    # 📋 Показываем список пакетов
    text = "*💼 Ваши VPN-пакеты:*\n\n"
    now = datetime.now()
    for i, pkg in enumerate(packages):
        tariff = pkg.get("tariff", "1")
        expires = pkg.get("expires", "не указано")
        try:
            exp = datetime.strptime(expires, "%Y-%m-%d")
            status = "✅ активен" if exp >= now else "🕒 истёк"
        except:
            status = "❓ неизвестен"

        name = (
            "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)" if tariff == "3" else
            f"Пакет с тарифом `{tariff}`"
        )

        text += f"{name} → срок: `{expires}` — {status}\n"

    text += "\n📎 Вы можете купить только тот тариф, который ещё *не покупался*.\n\n"
    text += "*1 🔑 = 1 устройство*\n\n"
    text += "📦 Выберите доступный тариф ниже:"

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def select_tariff(call):
    user_id = str(call.from_user.id)
    tariff = call.data.split("_")[1]
    users = load_user_data()
    users.setdefault(user_id, {})["tariff"] = tariff
    save_user_data(users)

    price = "*159₽*" if tariff == "1" else "*259₽*" if tariff == "3" else "*неизвестно*"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Я оплатил", callback_data="confirm_payment"))

    bot.send_message(
        call.message.chat.id,
        f"✅ Вы выбрали тариф: {price}\n\n"
        "👉 Переведите на карту Сбербанка:\n"
        f"`{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n\n"
        "❗️ Без комментария к переводу.",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_extend_"))
def approve_extension_package(call):
    print(f"🔥 Обработка продления: {call.data}")
    parts = call.data.split("_")
    user_id, index = parts[2], int(parts[3])
    users = load_user_data()
    now = datetime.now()

    if user_id not in users or index >= len(users[user_id].get("packages", [])):
        bot.send_message(call.message.chat.id, "❌ Пользователь или пакет не найден.")
        return

    package = users[user_id]["packages"][index]
    try:
        old_exp = datetime.strptime(package.get("expires", ""), "%Y-%m-%d")
        new_exp = old_exp + timedelta(days=30) if old_exp > now else now + timedelta(days=30)
    except:
        new_exp = now + timedelta(days=30)

    package["expires"] = new_exp.strftime("%Y-%m-%d")

    # 👁 Получаем тариф и количество ключей
    tariff = package.get("tariff", "1")
    count = 3 if tariff == "3" else 1

    # 🎯 Обновляем активность
    for i, p in enumerate(users[user_id]["packages"]):
        p["active"] = (i == index)

    save_user_data(users)

    # 📩 Отправляем уведомления
    identity = users[user_id].get("username", user_id)

    bot.send_message(
        int(user_id),
        f"✅ Ваш пакет #{index} продлён!\n🔐 Тариф: `{tariff}`\n📆 До: `{new_exp.strftime('%Y-%m-%d')}`",
        parse_mode="Markdown"
    )
    bot.send_message(
        call.message.chat.id,
        f"🔁 Продление: `{identity}` → #{index}\n📦 Тариф: `{tariff}`\n🔐 Ключей: {count}\n📆 До: `{new_exp.strftime('%Y-%m-%d')}`",
        parse_mode="Markdown"
    )

    
@bot.message_handler(func=lambda msg: msg.text == "🔁 Продлить доступ")
def extend_access(message):
    from datetime import datetime

    def is_package_expired(pkg):
        try:
            expires = datetime.strptime(pkg.get("expires", "1970-01-01"), "%Y-%m-%d")
            return expires < datetime.now()
        except:
            return True

    user_id = str(message.from_user.id)
    users = load_user_data()

    packages = users.get(user_id, {}).get("packages", [])
    if not packages:
        bot.send_message(
            message.chat.id,
            "🔐 У вас нет VPN-пакетов.\nСначала нужно *купить доступ*.\n\n👉 Нажмите «Купить доступ».",
            parse_mode="Markdown"
        )
        return

    # 🔍 Находим последний по времени пакет
    try:
        latest_index = max(
            range(len(packages)),
            key=lambda i: datetime.strptime(packages[i].get("expires", "1970-01-01"), "%Y-%m-%d")
        )
    except:
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось определить актуальный пакет. Напишите /admin.",
            parse_mode="Markdown"
        )
        return

    package = packages[latest_index]
    expires_str = package.get("expires", "не указано")
    tariff = package.get("tariff", "1")

    # 💳 Цена по тарифу
    price = "259₽" if tariff == "3" else "199₽" if tariff == "2" else "159₽"

    # 🧾 Формируем сообщение о продлении
    try:
        expires = datetime.strptime(expires_str, "%Y-%m-%d")
        now = datetime.now()
        if expires > now:
            days_left = (expires - now).days
            msg = (
                f"🔐 Ваш текущий тариф: `{tariff}` ключ(ей)\n"
                f"⏳ Действует до: `{expires_str}` (*ещё {days_left} дн.*)\n\n"
                f"💬 После оплаты *{price}* он будет продлён на +30 дней."
            )
        else:
            msg = (
                f"⌛ Тариф `{tariff}` истёк `{expires_str}`\n\n"
                f"💬 После оплаты *{price}* он снова будет активен на 30 дней."
            )
    except:
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось распознать срок действия. Напишите /admin.",
            parse_mode="Markdown"
        )
        return

    # 💳 Реквизиты
    msg += (
        "\n\nРеквизиты для оплаты:\n"
        f"`{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n"
        "❗️ Без комментария к переводу."
    )

    # 🔘 Кнопка подтверждения
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "💳 Я оплатил",
            callback_data=f"extend_confirm_{user_id}_{latest_index}"
        )
    )

    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def confirm_payment(call):
    user_id = str(call.from_user.id)
    users = load_user_data()

    selected_tariff = users.get(user_id, {}).get("tariff", "1")
    users.setdefault(user_id, {})["tariff"] = selected_tariff
    save_user_data(users)

    price = "259₽" if selected_tariff == "3" else "159₽"
    requisites = (
        f"💰 *Оплата: {price}*\n\n"
        "💳 *Реквизиты:*\n"
        f"Сбербанк: `{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n"
        "❗️ Без комментария к переводу."
    )
    bot.send_message(user_id, requisites, parse_mode="Markdown")

    bot.send_message(
        user_id,
        "📸 Пришлите *скриншот перевода* сюда сообщением.\n"
        "После проверки — получите VPN-ключ.",
        parse_mode="Markdown"
    )
    
@bot.callback_query_handler(func=lambda call: call.data == "start_new_purchase")
def start_new_package_purchase(call):
    user_id = str(call.from_user.id)
    users = load_user_data()
    users.setdefault(user_id, {})["purchase_mode"] = "new"  # 👈 метка: это новая покупка
    save_user_data(users)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📍 Тариф 1 ключ — 159₽", callback_data="new_tariff_1"),
        types.InlineKeyboardButton("📦 Тариф 3 ключа — 259₽", callback_data="new_tariff_3")
    )

    bot.send_message(
        call.message.chat.id,
        "📦 *Новая покупка*\n\nВыберите тариф для нового VPN-пакета:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_new_tariff_"))
def handle_start_new_tariff(call):
    user_id = str(call.from_user.id)
    tariff = call.data.split("_")[-1]

    users = load_user_data()
    users.setdefault(user_id, {})["purchase_mode"] = "new"
    users[user_id]["tariff_temp"] = tariff
    save_user_data(users)

    # 💰 Цена по тарифу
    price = "259₽" if tariff == "3" else "199₽" if tariff == "2" else "159₽"

    # 📦 Название пакета
    pkg_name = (
        "Пакет №1 — 1 ключ 🔑" if tariff == "1" else
        "Пакет №2 — 2 ключа 🔑🔑" if tariff == "2" else
        "Пакет №3 — 3 ключа 🔑🔑🔑"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Я оплатил", callback_data="confirm_payment_new"))

    bot.send_message(
        call.message.chat.id,
        f"✅ Вы выбрали: *{pkg_name} → {price}*\n\n"
        "💳 Оплатите на карту Сбербанка:\n"
        f"`{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n"
        "❗️ Без комментария к переводу.",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("new_tariff_"))
def select_new_tariff(call):
    user_id = str(call.from_user.id)
    tariff = call.data.split("_")[2]

    users = load_user_data()
    users.setdefault(user_id, {})["tariff_temp"] = tariff  # 👈 временно сохраняем выбранный тариф
    save_user_data(users)

    price = "259₽" if tariff == "3" else "159₽"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 Я оплатил", callback_data="confirm_payment_new"))

    bot.send_message(
        call.message.chat.id,
        f"✅ Тариф выбран: `{tariff}` ключ(ей) → *{price}*\n\n"
        "💳 Переведите по реквизитам:\n"
        f"`{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n"
        "❗️ Без комментария к переводу.",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment_new")
def confirm_new_package_payment(call):
    user_id = str(call.from_user.id)
    users = load_user_data()

    selected_tariff = users.get(user_id, {}).get("tariff_temp", "1")
    users[user_id]["tariff_temp"] = selected_tariff
    save_user_data(users)

    bot.send_message(
        user_id,
        "📸 Пришлите *скриншот перевода* сюда сообщением.\n"
        "После подтверждения — получите ключи.",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=["photo"])
def handle_payment_photo(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "unknown"
    now = datetime.now()

    # 📂 Путь для логов
    folder = os.path.join("/root/payments/logs", now.strftime('%Y-%m/%d'), username)
    os.makedirs(folder, exist_ok=True)
    filename = f"{message.message_id}.jpg"
    filepath = os.path.join(folder, filename)

    # 📸 Сохраняем фото
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_data = bot.download_file(file_info.file_path)
        with open(filepath, "wb") as f:
            f.write(photo_data)
    except:
        bot.send_message(message.chat.id, "❌ Не удалось сохранить скрин. Попробуйте ещё раз.")
        return

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        bot.send_message(message.chat.id, "❌ Скриншот повреждён. Попробуйте снова.")
        return

    users = load_user_data()
    user_info = users.get(user_id, {})
    has_packages = bool(user_info.get("packages"))
    purchase_mode = user_info.get("purchase_mode", "")
    meta_path = os.path.join(folder, "meta.json")

    # 🧠 Определение типа заявки
    if purchase_mode == "new":
        selected_tariff = user_info.get("tariff_temp", "1")
        key_count = "3" if selected_tariff == "3" else "2" if selected_tariff == "2" else "1"
        pkg_name = (
            "Пакет №1 (1 ключ 🔑)" if selected_tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if selected_tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)"
        )
        callback_ok = f"approve_new_{user_id}"
        callback_fail = f"reject_new_{user_id}"
        caption_type = (
            f"🆕 Новая покупка\n"
            f"📦 {pkg_name}\n"
            f"🔐 Ожидается выдача: `{key_count}` ключей"
        )
        req_type = "purchase"

    elif has_packages:
        packages = user_info.get("packages", [])
        latest_index = int(user_info.get("last_package_index", 0))
        if latest_index >= len(packages):
            latest_index = len(packages) - 1
        current_package = packages[latest_index]
        tariff = current_package.get("tariff", "1")
        key_count = "3" if tariff == "3" else "2" if tariff == "2" else "1"

        pkg_name = (
            "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)"
        )

        callback_ok = f"approve_extend_{user_id}_{latest_index}"
        callback_fail = f"reject_extend_{user_id}_{latest_index}"
        caption_type = f"🔁 Продление {pkg_name}"
        req_type = "extension"

    else:
        tariff = user_info.get("tariff", "1")
        key_count = "3" if tariff == "3" else "2" if tariff == "2" else "1"
        pkg_name = (
            "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)"
        )
        callback_ok = f"approve_{user_id}"
        callback_fail = f"reject_{user_id}"
        caption_type = (
            f"🆕 Покупка\n📦 {pkg_name}\n"
            f"🔐 Ожидается выдача: `{key_count}` ключей"
        )
        req_type = "purchase"

    # 🧾 meta.json
    entry = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "type": req_type,
        "status": "pending"
    }
    try:
        meta = []
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        meta.append(entry)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except:
        pass

    # 📤 Заявка админу
    caption = (
        f"{caption_type}\n\n"
        f"👤 @{username}\n"
        f"🆔 `{user_id}`\n"
        f"📸 `{filename}`\n"
        f"📂 `{now.strftime('%Y-%m/%d')}/{username}`"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=callback_ok),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=callback_fail)
    )

    try:
        with open(filepath, "rb") as photo:
            bot.send_photo(OWNER_ID, photo, caption=caption, parse_mode="Markdown", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Скриншот принят. Заявка отправлена.")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка при отправке. Попробуйте снова.")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_extend_"))
def reject_extension(call):
    parts = call.data.split("_")
    user_id, index = parts[2], parts[3]
    identity = bot.get_chat(user_id).username or user_id
    pkg_number = int(index) + 1  # 👈 сначала определяем

    # 🛑 Клиенту
    bot.send_message(
        int(user_id),
        f"❌ Ваша заявка на продление *Пакета №{pkg_number}* отклонена.\n\n"
        "💬 Если уверены, что всё верно — напишите: @BlokaNet",
        parse_mode="Markdown"
    )

    # 👤 Админу
    bot.send_message(
        call.message.chat.id,
        f"⛔️ Заявка на продление @{identity} *Пакета №{pkg_number}* отклонена.",
        parse_mode="Markdown"
    )

    # ✏️ Обновление meta.json и payments.json — по желанию
    
@bot.message_handler(func=lambda msg: msg.text == "👤 Мой профиль")
def show_profile_button(msg):
    user_profile(msg)  # вызывает функцию профиля

@bot.callback_query_handler(func=lambda call: call.data.startswith("extend_confirm_"))
def confirm_extension_payment(call):
    parts = call.data.split("_")
    user_id = parts[2]
    package_index = int(parts[3])

    users = load_user_data()
    users.setdefault(user_id, {})["last_package_index"] = package_index
    users[user_id]["purchase_mode"] = "extend"
    save_user_data(users)

    packages = users.get(user_id, {}).get("packages", [])
    if not packages or package_index >= len(packages):
        bot.send_message(int(user_id), "⚠️ Пакет не найден. Напишите /admin.", parse_mode="Markdown")
        return

    current_package = packages[package_index]
    tariff = current_package.get("tariff", "1")

    # 💳 Цена по тарифу
    price = "259₽" if tariff == "3" else "199₽" if tariff == "2" else "159₽"

    # 📦 Название пакета
    pkg_name = (
        "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
        "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
        "Пакет №3 (3 ключа 🔑🔑🔑)" if tariff == "3" else
        f"Пакет с тарифом `{tariff}`"
    )

    requisites = (
        f"📦 {pkg_name}\n"
        f"💰 *Оплата: {price}*\n\n"
        "💳 *Реквизиты:*\n"
        f"Сбербанк: `{CARD_NUMBER}`\n"
        f"📍 Получатель: `{CARD_HOLDER}`\n"
        "❗️ Без комментария к переводу."
    )

    bot.send_message(int(user_id), requisites, parse_mode="Markdown")

    bot.send_message(
        int(user_id),
        "📸 Пришлите *скриншот перевода* сюда сообщением.\n"
        "Мы сверим и активируем продление.",
        parse_mode="Markdown"
    )
    
@bot.message_handler(func=lambda msg: msg.text == "🎁 Получить пробный доступ")
def trial_access(message):
    user_id = str(message.from_user.id)
    users = load_user_data()

    # 🔐 Проверка: уже был пробный доступ?
    for pkg in users.get(user_id, {}).get("packages", []):
        if pkg.get("tariff") == "trial":
            bot.send_message(
                message.chat.id,
                "⛔️ Вы уже использовали пробный доступ.\n\n"
                "💬 Если хотите продолжить — выберите платный тариф.",
                parse_mode="Markdown"
            )
            return

    # ✅ Генерация ключа
    trial_keys = generate_vpn_keys(1)
    if not trial_keys:
        bot.send_message(
            message.chat.id,
            "❌ Нет доступных пробных ключей.\nНапишите: @BlokaNet",
            parse_mode="Markdown"
        )
        return

    expires = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    trial_package = {
        "tariff": "trial",
        "expires": expires,
        "vless": trial_keys
    }

    users.setdefault(user_id, {})["username"] = message.from_user.username or user_id
    users.setdefault(user_id, {}).setdefault("packages", []).append(trial_package)
    save_user_data(users)

    # 📩 Сообщение клиенту с инструкцией
    text = (
        "🎁 *Пробный доступ активирован!*\n\n"
        f"🔑 Ваш ключ:\n`{trial_keys[0]}`\n\n"
        f"⏳ *Срок действия: до {expires}*\n\n"
        "📘 *Как подключиться:*\n"
        "1️⃣ Установите приложение *Amnezia VPN*\n"
        "2️⃣ Откройте его → нажмите *Let's get started*\n"
        "3️⃣ Вставьте ключ\n"
        "4️⃣ Нажмите *Connect*\n\n"
        "📌 Пробный доступ работает на одном устройстве\n"
        "💬 Вопросы? Напишите: @BlokaNet"
    )

    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") and not call.data.startswith("approve_extend_") and not call.data.startswith("approve_new_"))
def approve_payment(call):
    try:
        print(f"📩 Обработка approve_payment: {call.data}")
        user_id = call.data.split("_")[1]
        chat = bot.get_chat(user_id)
        identity = chat.username or chat.first_name or user_id
        now = datetime.now()

        # 📂 Путь к логам
        folder = f"/root/payments/logs/{now.strftime('%Y-%m')}/{now.strftime('%d')}/{identity}"
        filename = sorted([f for f in os.listdir(folder) if f.endswith(".jpg")], reverse=True)[0]
        meta_path = os.path.join(folder, "meta.json")
        payments_log = "/root/payments/payments.json"

        # 📝 Обновление meta.json
        try:
            meta = []
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            meta.append({
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "filename": filename,
                "type": "purchase",
                "status": "approved"
            })
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta[-100:], f, indent=2, ensure_ascii=False)
            print(f"✅ meta.json обновлён")
        except Exception as e:
            print(f"❌ Ошибка обновления meta.json: {e}")

        # 📘 Обновление payments.json
        try:
            payments = []
            if os.path.exists(payments_log):
                with open(payments_log, "r", encoding="utf-8") as f:
                    payments = json.load(f)
            for p in reversed(payments):
                if p["user_id"] == user_id and p["status"] == "pending":
                    p["status"] = "approved"
                    break
            with open(payments_log, "w", encoding="utf-8") as f:
                json.dump(payments[-1000:], f, indent=2, ensure_ascii=False)
            print(f"✅ payments.json обновлён")
        except Exception as e:
            print(f"❌ Ошибка обновления payments.json: {e}")

        # 🔐 Генерация ключей
        users = load_user_data()
        tariff = users.get(user_id, {}).get("tariff", "1")
        count = 3 if tariff == "3" else 2 if tariff == "2" else 1
        expires = (now + timedelta(days=30)).strftime("%Y-%m-%d")

        vless_links = []
        for _ in range(count):
            link = get_free_vless_link()
            if link:
                vless_links.append(link)

        if not vless_links:
            bot.send_message(int(user_id), "❌ Нет доступных VPN-ключей. Напишите @BlokaNet.")
            bot.send_message(call.message.chat.id, f"⚠️ У @{identity} нет доступных ключей.")
            print("⚠️ Не удалось выдать ключи — список пуст")
            return

        print(f"✅ Выдаём {len(vless_links)} ключей пользователю {user_id}")

        # 📦 Обновление user_keys.json
        new_package = {
            "tariff": tariff,
            "expires": expires,
            "vless": vless_links
        }

        users.setdefault(user_id, {})["username"] = identity
        users.setdefault(user_id, {}).setdefault("packages", []).append(new_package)
        save_user_data(users)
        print(f"✅ user_keys.json обновлён")

        # 📘 Инструкция подключения
        instructions = (
            "📘 *Как подключиться:*\n"
            "1️⃣ Скачайте *Amnezia VPN*\n"
            "2️⃣ Нажмите *Let's get started*\n"
            "3️⃣ Вставьте ключ\n"
            "4️⃣ Нажмите *Connect*\n\n"
            "💬 Поддержка: @BlokaNet"
        )

        # 📩 Сообщение пользователю
        msg = "🎉 *Оплата подтверждена!*\n\n🔑 *Ваши ключи:*\n\n"
        for idx, link in enumerate(vless_links, start=1):
            msg += f"🔑 Ключ №{idx}:\n`{link}`\n\n"

        msg += f"⏳ *Срок действия: до {expires}*\n\n{instructions}"

        # 📦 Название пакета для админа
        pkg_name = (
            "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)" if tariff == "3" else
            f"Тариф `{tariff}`"
        )

        # 📩 Уведомление админу
        try:
            bot.send_message(int(user_id), msg, parse_mode="Markdown")
            print("✅ Ключи отправлены пользователю")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            bot.send_message(call.message.chat.id, f"⚠️ Не удалось отправить ключи @{identity}")

        bot.send_message(
            call.message.chat.id,
            f"📦 Новый пакет для `{identity}`\n"
            f"{pkg_name}\n"
            f"🔐 Ключей: `{count}`\n"
            f"📆 До: `{expires}`\n"
            f"🗂 Всего пакетов: `{len(users[user_id]['packages'])}`",
            parse_mode="Markdown"
        )
        print("📤 Уведомление админу отправлено")

    except Exception as e:
        print(f"❌ Общая ошибка approve_payment: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при обработке. Напишите @BlokaNet.")
        
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_new_"))
def approve_new_package(call):
    try:
        print(f"🔥 Вход в approve_new_package: {call.data}")

        user_id = call.data.split("_")[2]
        print(f"🧠 user_id: {user_id}")

        chat = bot.get_chat(user_id)
        identity = chat.username or chat.first_name or chat.last_name or f"user_{user_id}"
        print(f"🧠 Имя пользователя: {identity}")

        users = load_user_data()
        selected_tariff = users.get(user_id, {}).get("tariff_temp", "1")
        print(f"🧠 Выбран тариф: {selected_tariff}")

        key_count = 3 if selected_tariff == "3" else 2 if selected_tariff == "2" else 1
        print(f"🧠 Количество ключей: {key_count}")

        generated_keys = generate_vpn_keys(key_count)
        print(f"🧠 Сгенерировано ключей: {len(generated_keys)} → {generated_keys}")

        if not generated_keys:
            bot.send_message(call.message.chat.id, f"❌ Нет свободных ключей для @{user_id}.")
            print(f"❌ Ключи не найдены для пользователя {user_id}")
            return

        # 📦 Новый VPN-пакет
        new_package = {
            "tariff": selected_tariff,
            "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "vless": generated_keys
        }

        # 📘 Обновим payments.json
        payments_log = "/root/payments/payments.json"
        entry = {
            "user_id": user_id,
            "username": identity,
            "type": "purchase",
            "status": "approved",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            payments = []
            if os.path.exists(payments_log):
                with open(payments_log, "r", encoding="utf-8") as f:
                    payments = json.load(f)
            payments.append(entry)
            with open(payments_log, "w", encoding="utf-8") as f:
                json.dump(payments[-1000:], f, indent=2, ensure_ascii=False)
            print("📘 payments.json обновлён")
        except Exception as e:
            print(f"❌ Ошибка записи в payments.json: {e}")

        # ✅ Обновляем user_keys.json
        users.setdefault(user_id, {})["username"] = identity
        users.setdefault(user_id, {}).setdefault("packages", []).append(new_package)
        users[user_id]["purchase_mode"] = ""
        users[user_id]["tariff_temp"] = ""
        save_user_data(users)
        print(f"✅ Новый пакет сохранён для {user_id}")

        # 📘 Инструкция подключения
        instructions = (
            "📘 *Как подключиться:*\n"
            "1️⃣ Скачайте *Amnezia VPN*\n"
            "2️⃣ Нажмите *Let's get started*\n"
            "3️⃣ Вставьте ключ\n"
            "4️⃣ Нажмите *Connect*\n\n"
            "💬 Поддержка: @BlokaNet"
        )

        # 📦 Название пакета по тарифу
        pkg_name = (
            "Пакет №1 (1 ключ 🔑)" if selected_tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if selected_tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)" if selected_tariff == "3" else
            f"Тариф `{selected_tariff}`"
        )

        # 📩 Отправка ключей клиенту
        message_text = (
            f"🎉 *{pkg_name} активирован!*\n\n"
            f"📦 Тариф: `{selected_tariff}`\n"
            f"🗓 Срок: 30 дней\n\n"
            f"🔑 *Ключи:*\n\n"
        )
        for idx, link in enumerate(generated_keys, start=1):
            message_text += f"🔑 Ключ №{idx}:\n`{link}`\n\n"

        message_text += instructions

        bot.send_message(int(user_id), message_text, parse_mode="Markdown")
        print(f"📩 Ключи отправлены пользователю {user_id}")

        bot.send_message(call.message.chat.id, f"✅ {pkg_name} выдан @{identity}", parse_mode="Markdown")
        print(f"📩 Подтверждение отправлено админу")
        print("✅ approve_new_package завершён")

    except Exception as e:
        print(f"❌ Ошибка в approve_new_package: {e}")
        bot.send_message(call.message.chat.id, "❌ Произошла ошибка при выдаче ключей.")
        

    
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject"))
def reject_payment(call):
    try:
        print(f"⛔️ Обработка отклонения: {call.data}")
        
        # 🧠 Извлекаем user_id из call.data — ищем любое число ≥ 6 символов
        import re
        match = re.search(r"_([0-9]{6,})", call.data)
        user_id = match.group(1) if match else None

        if not user_id:
            bot.send_message(call.message.chat.id, "❌ Не удалось определить пользователя.")
            return

        users = load_user_data()
        identity = users.get(user_id, {}).get("username") or user_id
        now = datetime.now()

        # 💬 Клиенту
        bot.send_message(
            int(user_id),
            "❌ Ваша заявка *отклонена*.\n\n"
            "🚫 Причины:\n"
            "- Неверный скрин\n"
            "- Оплата не найдена\n\n"
            "Если уверены, что всё верно — напишите: @BlokaNet",
            parse_mode="Markdown"
        )

        # 👤 Админу
        bot.send_message(
            call.message.chat.id,
            f"⛔️ Заявка от @{identity} отклонена.",
            parse_mode="Markdown"
        )

        # 📝 meta.json → статус "rejected"
        folder = f"/root/payments/logs/{now.strftime('%Y-%m')}/{now.strftime('%d')}/{identity}"
        meta_path = os.path.join(folder, "meta.json")
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta:
                    meta[-1]["status"] = "rejected"
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка записи meta.json: {e}")

        # 🧾 payments.json → статус "rejected"
        payments_path = "/root/payments/payments.json"
        try:
            payments = []
            if os.path.exists(payments_path):
                with open(payments_path, "r", encoding="utf-8") as f:
                    payments = json.load(f)
            for p in reversed(payments):
                if p["user_id"] == user_id and p["status"] == "pending":
                    p["status"] = "rejected"
                    break
            with open(payments_path, "w", encoding="utf-8") as f:
                json.dump(payments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка записи payments.json: {e}")

        print(f"⛔️ Отклонение заявки завершено: {user_id}")
    except Exception as e:
        print(f"❌ Ошибка reject_payment: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при отклонении. Напишите @BlokaNet.")

@bot.message_handler(func=lambda msg: msg.text == "📘 FAQ")
def show_faq(message):
    faq_text = (
        "📘 *FAQ — часто задаваемые вопросы:*\n\n"

        "**— Как получить доступ❓**\n"
        "👉 Нажмите «Купить доступ», переведите *указанную сумму*, отправьте скрин.\n\n"

        "**— Срок ключа❓**\n"
        "⏳ 30 дней с момента активации.\n\n"

        "**— Как узнать, когда истекает❓**\n"
        "📆 Бот предупредит за 3 дня до окончания.\n\n"

        "**— Как продлить❓**\n"
        "🔁 Нажмите «Продлить доступ», оплатите, получите продление.\n\n"

        "**— Сколько пакетов я могу купить❓**\n"
        "📦 Всего доступно *3 пакета*:\n"
        "- Пакет №1 — 1 ключ\n"
        "- Пакет №2 — 2 ключа\n"
        "- Пакет №3 — 3 ключа\n\n"
        "✅ Можно купить сразу все три. Каждый работает независимо.\n"
        "📌 Вы можете продлевать нужные пакеты или просто перестать их продлевать.\n"
        "🎯 Хотите сменить тариф? Купите новый пакет и продлевайте только его.\n\n"

        "**— Что делать, если приходит уведомление о временной блокировке❓**\n"
        "🔒 VPN может зафиксировать смену IP, если вы переключаетесь между Wi-Fi и мобильной связью.\n"
        "🕒 Это воспринимается как мульти-подключение, и доступ временно блокируется — но только на несколько секунд.\n\n"
        "📌 Чтобы избежать подобных уведомлений:\n"
        "- Используйте одну стабильную сеть: Wi-Fi *или* мобильную\n"
        "- Отключите вторую сеть, если замечаете перебои\n\n"
        "💬 Работоспособность ключа при этом не страдает — просто нужно дождаться стабильного соединения.\n\n"

        "**— Где находятся серверы❓**\n"
        "🌍 Сейчас — Германия. В будущем — будут добавлены другие страны.\n\n"

        "**— Что делать при полной блокировке❓**\n"
        "📩 Напишите в поддержку: @BlokaNet"
    )

    bot.send_message(message.chat.id, faq_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📜 Правила использования")
def show_rules(message):
    rules_text = (
        "📜 *Правила использования:*\n\n"
        "1️⃣ Один ключ — один пользователь, одно устройство.\n"
        "2️⃣ Множественное подключение — автоматическая блокировка.\n"
        "3️⃣ Блокировка снимается при стабилизации IP.\n"
        "4️⃣ Уведомление перед окончанием доступа.\n\n"
        "⚠️ Нарушение — блокировка без компенсации.\n"
        "💬 Вопросы? → @BlokaNet"
    )
    bot.send_message(message.chat.id, rules_text, parse_mode="Markdown")

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "⛔️ Нет доступа.")
        return

    users = load_user_data()
    total_keys = len(load_keys())
    used_keys = sum(len(pkg.get("vless", [])) for u in users.values() for pkg in u.get("packages", []))
    available_keys = total_keys - used_keys

    # 🧠 Подсчёт уникальных пользователей по никам
    usernames = set()
    for u in users.values():
        name = u.get("username")
        if name:
            usernames.add(name)
    real_users = len(usernames)

    report = (
        f"🔐 *Админ-панель BlokaNet*\n\n"
        f"👥 Пользователей: `{real_users}`\n"
        f"🔑 Всего ключей: `{total_keys}`\n"
        f"📤 Выдано: `{used_keys}`\n"
        f"🟢 Осталось: `{available_keys}`"
    )
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

@bot.message_handler(commands=["profile"])
def user_profile(message):
    user_id = str(message.from_user.id)
    users = load_user_data()

    if user_id not in users or not users[user_id].get("packages"):
        bot.send_message(
            message.chat.id,
            "🔐 У вас нет активных VPN-пакетов.\nНажмите «Купить доступ».",
            parse_mode="Markdown"
        )
        return

    now = datetime.now()

    for i, pkg in enumerate(users[user_id]["packages"]):
        tariff = pkg.get("tariff", "1")

        # 🎁 Пробный доступ: краткий формат с датой и статусом
        if tariff == "trial":
            trial_key = pkg.get("vless", ["— ключ не найден —"])[0]
            expires = pkg.get("expires", "не указано")

            try:
                exp = datetime.strptime(expires, "%Y-%m-%d")
                status = "✅ активен" if exp >= now else "🕒 истёк"
            except:
                status = "❓ неизвестен"

            trial_text = (
                "🎁 Тариф: *Trial*\n"
                f"📆 Срок действия: `{expires}`\n"
                f"📊 Статус: {status}\n\n"
                f"🔑 Ключ:\n`{trial_key}`"
            )

            bot.send_message(message.chat.id, trial_text, parse_mode="Markdown")
            continue

        # 📦 Платные пакеты
        pkg_number = i + 1
        expires = pkg.get("expires", "не указано")

        try:
            exp = datetime.strptime(expires, "%Y-%m-%d")
            status = "✅ активен" if exp >= now else "🕒 истёк"
        except:
            status = "❓ неизвестен"

        vless_list = pkg.get("vless", [])

        name = (
            "Пакет №1 (1 ключ 🔑)" if tariff == "1" else
            "Пакет №2 (2 ключа 🔑🔑)" if tariff == "2" else
            "Пакет №3 (3 ключа 🔑🔑🔑)" if tariff == "3" else
            f"Тариф `{tariff}`"
        )

        text = (
            f"{name}\n"
            f"📦 Пакет #{pkg_number}\n"
            f"🔐 Ключей: `{len(vless_list)}`\n"
            f"📆 Срок: `{expires}`\n"
            f"📊 Статус: {status}\n\n"
            f"🔑 *Ключи:*\n\n"
        )

        for idx, link in enumerate(vless_list, start=1):
            text += f"🔑 Ключ №{idx}:\n`{link}`\n\n"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔁 Продлить",
                callback_data=f"extend_confirm_{user_id}_{i}"
            )
        )

        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
# === Запуск бота ===
print("✅ Бот запущен.")
print("🟢 Polling запущен")


bot.infinity_polling()
