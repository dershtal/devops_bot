# Импорт библиотек
import logging, re, paramiko, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext)
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error

# Регистрация логгера
logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Параметры SSH
HOST = os.getenv('RM_HOST')
SSH_PORT = os.getenv('RM_PORT')
USERNAME = os.getenv('RM_USER')
PASSWORD = os.getenv('RM_PASSWORD')

# Параметры SSH для базы данных
DB_NAME = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Токен из .env файла
BOT_TOKEN = os.getenv('TOKEN')

# Стадии разговора
CHOOSING, GET_PACKAGE_INFO, INPUT_TEXT_PHONE, CONFIRM_SAVE_PHONE, INPUT_TEXT_EMAIL, CONFIRM_SAVE_EMAIL, VERIFY_PASSWORD = range(7)

def start(update, context):
    update.message.reply_text(f'Привет {update.effective_user.full_name}! Используй /help чтобы увидеть доступные команды.')

def help_command(update: Update, _: CallbackContext) -> None:
    help_text = "Этот бот создан для выполнения практического задания 5 модуля PT Start 2024. Связаться с владельцем @dershtal Доступные команды:\n"
    help_text += "/start - Запуск Бота\n"
    help_text += "/help - Помощь по Боту\n"
    help_text += "/cancel - Отмена\n"
    help_text += "/find_phone_numbers - Поиск телефонных номеров в тексте\n"
    help_text += "/find_email_address - Поиск эл. адресов в тексте\n"
    help_text += "/verify_password - Проверка сложности пароля\n"
    help_text += "/get_release - Информация о релизе\n"
    help_text += "/get_uname - Информация об архитектуры процессора, имени хоста системы и версии ядра\n"
    help_text += "/get_uptime - Информация о овремени работы\n"
    help_text += "/get_df - Информация о состоянии файловой системы\n"
    help_text += "/get_free - Информация о состоянии оперативной памяти\n"
    help_text += "/get_mpstat - Информация о производительности системы\n"
    help_text += "/get_w - Информация о работающих в данной системе пользователях\n"
    help_text += "/get_auths - Информация о последние 10 входов в систему\n"
    help_text += "/get_critical - Информация о последние 5 критических события\n"
    help_text += "/get_ps - Информация о запущенных процессах\n"
    help_text += "/get_ss - Информация об используемых портах\n"
    help_text += "/get_apt_list - Информация об установленных пакетах\n"
    help_text += "/get_services - Информация о запущенных сервисах\n"
    help_text += "/get_repl_logs - Вывод логов о репликации\n"
    help_text += "/get_emails - Вывод эл. адресов почты из таблицы\n"
    help_text += "/get_phone_numbers - Вывод телефонных номеров из таблицы\n"
    update.message.reply_text(help_text)

#-----------------------------------------------------------------------------------------
# Поиск Номера Телефона
#-----------------------------------------------------------------------------------------
# Регулярное выражение для поиска номеров телефона
PHONE_REGEX = r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|\+?7[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}|8[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}"

def find_phone_numbers(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Пожалуйста, отправьте текст для поиска номеров телефона.")
    return INPUT_TEXT_PHONE

# Обработка введенного текста
def input_text_pn(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    phone_numbers = re.findall(PHONE_REGEX, text)
    if not phone_numbers:
        update.message.reply_text("В введенном тексте номера телефона не найдены.")
        return ConversationHandler.END
    else:
        context.user_data['phone_numbers'] = phone_numbers
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="yes")],
            [InlineKeyboardButton("Нет", callback_data="no")]
        ])
        update.message.reply_text(f"Найдены номера: {' '.join(phone_numbers)}. Хотите сохранить их в базу данных?", reply_markup=reply_markup)
        return CONFIRM_SAVE_PHONE

# Обработка подтверждения
def confirm_savepn(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    if query.data == "yes":
        phone_numbers = context.user_data['phone_numbers']
        save_phone_numbers(phone_numbers)
        query.edit_message_text(text="Номера телефона сохранены успешно.")
    else:
        query.edit_message_text(text="Сохранение отменено.")
    return ConversationHandler.END

# Сохранение номеров телефона в базу данных
def save_phone_numbers(phone_numbers):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    for number in phone_numbers:
        cur.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s) ON CONFLICT DO NOTHING", (number,))
    conn.commit()
    cur.close()
    conn.close()
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Поиск Адреса почты
#-----------------------------------------------------------------------------------------
# Регулярное выражение для поиска Адреса почты
EMAIL_REGEX = r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'

def find_email_address(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Пожалуйста, отправьте текст для поиска адреса электронной почты.")
    return INPUT_TEXT_EMAIL

# Обработка введенного текста
def input_text_em(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    email_address = re.findall(EMAIL_REGEX, text)
    if not email_address:
        update.message.reply_text("В введенном тексте адреса электронной почты не найдены.")
        return ConversationHandler.END
    else:
        context.user_data['email_address'] = email_address
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="yes")],
            [InlineKeyboardButton("Нет", callback_data="no")]
        ])
        update.message.reply_text(f"Найдены адреса: {' '.join(email_address)}. Хотите сохранить их в базу данных?", reply_markup=reply_markup)
        return CONFIRM_SAVE_EMAIL

# Обработка подтверждения
def confirm_savepn(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    if query.data == "yes":
        email_address = context.user_data['email_address']
        save_email_address(email_address)
        query.edit_message_text(text="Адреса электронной почты сохранены успешно.")
    else:
        query.edit_message_text(text="Сохранение отменено.")
    return ConversationHandler.END

# Сохранение номеров телефона в базу данных
def save_email_address(email_address):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    for number in email_address:
        cur.execute("INSERT INTO email (email) VALUES (%s) ON CONFLICT DO NOTHING", (number,))
    conn.commit()
    cur.close()
    conn.close()
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Проверка Пароля
#-----------------------------------------------------------------------------------------
def verify_passwordCommand(update, context):
    update.message.reply_text('Введите пароль для проверки:')
    return VERIFY_PASSWORD

def verify_password(update, context):
    password_input = update.message.text
    if re.search(r'[=+\-_\/\\|]', password_input):
        update.message.reply_text('Пароль содержит не корректные символы.')
    elif re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$', password_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Функция эхо
#-----------------------------------------------------------------------------------------
def echo(update: Update, context):
    update.message.reply_text(update.message.text)
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Подключение SSH
#-----------------------------------------------------------------------------------------
def execute_ssh_command(update, command, message_prefix):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=SSH_PORT, username=USERNAME, password=PASSWORD)
    stdin, stdout, stderr = ssh.exec_command(command)
    result = stdout.read().decode('utf-8')
    ssh.close()
    update.message.reply_text(message_prefix + result)
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Функции для работы с базой данных
#-----------------------------------------------------------------------------------------
def get_db_data(update: Update, context: CallbackContext, query):
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        if rows:
            message_text = "\n".join(f"{row[0]}: {row[1]}" for row in rows)
        else:
            message_text = "Данные не найдены."
        update.message.reply_text(message_text)
        cur.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Database error: {error}")
        update.message.reply_text('Ошибка базы данных.')
#-----------------------------------------------------------------------------------------

    # Команды для вывода данных
def get_emails(update: Update, context: CallbackContext):
    get_db_data(update, context, "SELECT id, email FROM email")

def get_phone_numbers(update: Update, context: CallbackContext):
    get_db_data(update, context, "SELECT id, phone_number FROM phone_numbers")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Сбор информации об установленных пакетах.
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def get_apt_list(update, context):
    keyboard = [
        [InlineKeyboardButton("Все установленные пакеты", callback_data='get_apt_list1')],
        [InlineKeyboardButton("Поиск пакета", callback_data='get_apt_list2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)
    return CHOOSING

def button(update, context):
    query = update.callback_query
    query.answer()
    # Изменено
    match query.data:
        case 'get_apt_list1':
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(HOST, port=SSH_PORT, username=USERNAME, password=PASSWORD)
            command = 'dpkg-query -f \'${binary:Package}\\n\' -W'
            stdin, stdout, stderr = ssh.exec_command(command)
            packages = stdout.read().decode('utf-8').strip().split('\n')
            ssh.close()

            # Отправить по 50 пакетов в сообщении
            for i in range(0, len(packages), 50):
                message_text = "\n".join(packages[i:i+50])
                query.message.reply_text(f"Установленные пакеты:\n{message_text}")
            return ConversationHandler.END
        
        case 'get_apt_list2':
            query.edit_message_text(text='Введите название пакета:')
            return GET_PACKAGE_INFO

def get_package_info(update, context):
    text = update.message.text
    command = f"apt-cache show {text}"
    execute_ssh_command(update, command, f"Информация о пакете {text}:\n")
    return ConversationHandler.END
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Сбор информации о релизе.
def get_release(update, context):
    command = "lsb_release -a"
    execute_ssh_command(update, command, "Информация о релизе:\n")

    # Сбор информации об архитектуры процессора, имени хоста системы и версии ядра.
def get_uname(update, context):
    command = "uname -a"
    execute_ssh_command(update, command, "Информация об архитектуры процессора, имени хоста системы и версии ядра:\n")

    # Сбор информации о времени работы.
def get_uptime(update, context):
    command = "uptime -p"
    execute_ssh_command(update, command, "Информация о времени работы:\n")

    # Сбор информации о состоянии файловой системы.
def get_df(update, context):
    command = "df -h"
    execute_ssh_command(update, command, "Информация о состоянии файловой системы:\n")

    # Сбор информации о состоянии оперативной памяти.
def get_free(update, context):
    command = "free -h"
    execute_ssh_command(update, command, "Информация о состоянии оперативной памяти:\n")

    # Сбор информации о производительности системы. 
def get_mpstat(update, context):
    command = "mpstat"
    execute_ssh_command(update, command, "Информация о производительности системы:\n")

    # Сбор информации о работающих в данной системе пользователях.
def get_w(update, context):
    command = "w"
    execute_ssh_command(update, command, "Работающие в данной системе пользователи:\n")

    # Последние 10 входов в систему.
def get_auths(update, context):
    command = "last -n 10"
    execute_ssh_command(update, command, "Последние 10 входов в систему:\n")

    # Последние 5 критических событий.
def get_critical(update, context):
    command = "journalctl -p crit -n 5 --no-pager"
    execute_ssh_command(update, command, "Последние 5 критических событий:\n")

    # Сбор информации о запущенных процессах.
def get_ps(update, context):
    command = "ps -eo comm --no-headers"
    execute_ssh_command(update, command, "Запущенные процессы:\n")
    
    # Сбор информации об используемых портах.
def get_ss(update, context):
    command = "ss -tuln"
    execute_ssh_command(update, command, "Используемые порты:\n")

    # Сбор информации о запущенных сервисах. 
def get_services(update, context):
    command = "systemctl list-units --type=service --state=running --no-legend | awk '{print $1}'"
    execute_ssh_command(update, command, "Информация о запущенных сервисах:\n")

    # Получения логов PostgreSQL
def get_repl_logs(update, context):
    command = "cat /var/log/postgresql/postgresql-15-main.log | head -10"
    execute_ssh_command(update, command, "PostgreSQL logs:\n")


# chmod 777 /var/log/postgresql/postgresql-15-main.log - для пользователя чей логин используем в запросе

def cancel(update, context):
    update.message.reply_text('Операция отменена.')
    return ConversationHandler.END
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# основная функция, которая запускается самой первой
#-----------------------------------------------------------------------------------------
def main():
    # Создаем Updater и передаем ему токен вашего бота.
    updater = Updater(BOT_TOKEN, use_context=True)
    # Получаем диспетчера для регистрации обработчиков
    dp = updater.dispatcher

    #-------------------------------------------------------------------------------------
    # Обработчики диалогов
    #-------------------------------------------------------------------------------------

    # Обработчик номеров телефонов
    conv_handler_find_phone_numbers = ConversationHandler(
        # Здесь строится логика разговора
        # Точка входа в разговор
        entry_points=[CommandHandler('find_phone_numbers', find_phone_numbers)],
        states={
            # Этапы разговора
            INPUT_TEXT_PHONE: [MessageHandler(Filters.text & ~Filters.command, input_text_pn)],
            CONFIRM_SAVE_PHONE: [CallbackQueryHandler(confirm_savepn)]
        },
        # Точка выхода из разговора
        fallbacks=[CommandHandler('start', start)]
    )

    # Обработчик электронных почт 
    conv_handler_find_email_address = ConversationHandler(
        entry_points=[CommandHandler('find_email_address', find_email_address)],
        states={
            INPUT_TEXT_EMAIL: [MessageHandler(Filters.text & ~Filters.command, input_text_em)],
            CONFIRM_SAVE_EMAIL: [CallbackQueryHandler(confirm_savepn)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    # Обработчик верификации паролей
    conv_handler_verify_password = ConversationHandler(
        entry_points=[CommandHandler('verify_password',verify_passwordCommand)],
        states={
            VERIFY_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Команды линукс которой надо 2 раза что-то сказать
    # Сбор информации об установленных пакетах
    conv_handler_get_apt_list = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list)],
        states={
            CHOOSING: [CallbackQueryHandler(button)],
            GET_PACKAGE_INFO: [MessageHandler(Filters.text & ~Filters.command, get_package_info)],
        },
        
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Регистрируем обработчики команд
    # Обработчики текста
    dp.add_handler(conv_handler_find_phone_numbers)
    dp.add_handler(conv_handler_find_email_address)
    dp.add_handler(conv_handler_verify_password)
    
    # Обработчики команд для взаимодействия с удалённым Linux сервером
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('get_ps', get_ps))
    dp.add_handler(CommandHandler('get_ss', get_ss))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(conv_handler_get_apt_list)

    # Обработчики команд для взаимодействия с Базой данных
    dp.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    dp.add_handler(CommandHandler('get_emails', get_emails))
    dp.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))

    # Регистрируем обработчик текстовых сообщений (эхо режим)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()
    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
