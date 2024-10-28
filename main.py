import telebot
import psycopg2
import random
from telebot import types
from psycopg2 import Error
from datetime import datetime


TOKEN = '7643476199:AAF4XuhcewqYHXYc7plyJrf6DtQ_GUAuAPc'

bot = telebot.TeleBot(TOKEN)

chars = '+-/*!&$#?=@<>abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

# Глобальный словарь для хранения данных пользователя
user_data = {}


def create_login(message):
    login_user = message.text
    user_data[message.chat.id] = login_user  # Сохраняем логин в словаре
    bot.send_message(message.chat.id,
                     f"Добро пожаловать, {login_user}, на наш сайт! Осталось создать пароль для регистрации.")
    bot.send_message(message.chat.id, "Выберите длину пароля: ", reply_markup=password_length_markup())


def password_length_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Пароль длины 6 символов", callback_data="password_6"))
    markup.add(types.InlineKeyboardButton("Пароль длины 8 символов", callback_data="password_8"))
    markup.add(types.InlineKeyboardButton("Пароль длины 10 символов", callback_data="password_10"))
    return markup


def generate_password(length):
    return ''.join(random.choice(chars) for _ in range(length))


@bot.callback_query_handler(func=lambda call: call.data.startswith("password_"))
def callback_password_length(call):
    length = int(call.data.split("_")[1])  # Получаем длину пароля из callback_data
    password = generate_password(length)

    # Получаем логин из словаря
    login_user = user_data.get(call.message.chat.id)

    if login_user:  # Проверка на случай, если логин не был сохранен
        bot.send_message(call.message.chat.id, f"Ваш сгенерированный пароль: {password}")
        bot.send_message(call.message.chat.id,
                         "Вы зарегистрированы на наш сайт, используйте логин и пароль при авторизации!")

        # Сохраняем пользователя в базе данных
        create_user_db(call.message.chat.id, login_user, password)

        # Удаляем данные из словаря после использования
        del user_data[call.message.chat.id]
    else:
        bot.send_message(call.message.chat.id, "Ошибка: логин не найден, попробуйте снова.")


def create_user_db(user_id, login, password):
    try:
        # подключиться к существующей базе данных
        connection = psycopg2.connect(user="postgres",
                                      # пароль, который указали при установке PostgreSQL
                                      password="admin",
                                      host="127.0.0.1",
                                      port="5432")
        cursor = connection.cursor()
        created_at = datetime.now()
        cursor.execute(
            "INSERT INTO users (user_id, login, password, created_at) VALUES (%s, %s, %s, %s)",
            (user_id, login, password, created_at)
        )
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при вставке данных: ", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с postgresql закрыто")

@bot.message_handler(commands=['start'])
def send_message(message):
    sent = bot.reply_to(message, "Привет! Я бот для регистрации пользователей. Введите свой логин: ")
    bot.register_next_step_handler(sent, create_login)


@bot.message_handler(commands=['about'])
def send_help(message):
    bot.reply_to(message,
                 "Этот бот создан, для регистрации пользователей на сайте Store21, для запуска регистрации нажмите или напишите /start")


bot.polling()
