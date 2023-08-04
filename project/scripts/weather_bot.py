import requests
import telebot
import pytz
import psycopg2
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ElementTree

conn = ""
curs = ""
DB_CONNECTION_LINK = ""
BOT = telebot.TeleBot("your_bot_token")
API = ""
HELP_COMMAND = "Бот выводит погодные условия введенного города," \
               "а также местную дату и время"

py_logger = logging.getLogger("weather_bot")
py_logger.setLevel(logging.INFO)

date_fmt = "%Y-%m-%d %H:%M:%S"
str_fmt = "%(asctime)s : [%(levelname)s] : %(name)s : %(message)s"

py_handler = logging.FileHandler(f"../../weather_bot.log", mode="a", encoding="utf8")
py_formatter = logging.Formatter(fmt=str_fmt, datefmt=date_fmt)

py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)


@BOT.message_handler(commands=["start"])
def start(message):
    BOT.send_message(message.chat.id, "Привет, напиши название города и страну"
                                      "в таком формате:\n\nПариж, Франция")


@BOT.message_handler(commands=["help"])
def help(message):
    BOT.send_message(message.chat.id, HELP_COMMAND)


@BOT.message_handler(content_types=["text"])
def get_weather(message):
    city_and_country = message.text.strip().split(",")

    try:
        city = city_and_country[0].strip()
        country = city_and_country[1].strip()
        country_code = get_country_code(country)
        weather = requests.get("https://api.openweathermap.org/data/2.5"
                               "/weather?q="
                               f"{city + ', ' + country_code}&appid="
                               f"{API}&units=metric&"
                               "lang=ru&mode=xml")
    except Exception:
        py_logger.warning("Неверный ввод", exc_info=True)
        BOT.reply_to(message, "Ведите в таком формате\n\nПариж, Франция")
        return

    # successful request
    if weather.status_code == 200:
        rt = ElementTree.fromstring(weather.text)
        weather_code = int(rt.find("weather").get("number"))
        weather_picture = get_weather_picture(weather_code)
        utc = pytz.utc

        # work with current date and time
        timezone_value = int(rt.find("city").find("timezone").text)
        datetime_now_utc = datetime.now(tz=utc)
        datetime_now = timedelta(seconds=timezone_value) + datetime_now_utc

        weather_code_clear = 800
        # day or night we see only in clear weather
        if weather_code == weather_code_clear:
            weather_pictures = weather_picture.split(":")
            day_or_night = get_day_or_night(rt, datetime_now_utc)
            if day_or_night == "d":
                weather_picture = weather_pictures[0]
            else:
                weather_picture = weather_pictures[1]

        BOT.reply_to(message,
                     "Местные дата и время: "
                     f"{datetime_now.strftime('%d/%m/%y')}🕰️"
                     f"{datetime_now.strftime('%H:%M')}" +
                     "\nТемпература: "
                     f"{round(float(rt.find('temperature').get('value')))} С°" +
                     "\nОщущается как: "
                     f"{round(float(rt.find('feels_like').get('value')))} С°" +
                     "\nВлажность: "
                     f"{rt.find('humidity').get('value')}%" +
                     "\nОблачность: "
                     f"{rt.find('clouds').get('value')}%" +
                     "\nСкорость ветра: "
                     f"{rt.find('wind').find('speed').get('value')} м/с" +
                     "\nПогодные условия: "
                     f"{rt.find('weather').get('value')} {weather_picture}")

    else:
        BOT.reply_to(message, "Город указан неверно")


def get_day_or_night(rt, datetime_now_utc):
    rise = rt.find("city").find("sun").get("rise").split("T")
    rise_time = rise[1].split(":")
    rise_date = rise[0].split("-")
    set = rt.find("city").find("sun").get("set").split("T")
    set_time = set[1].split(":")
    set_date = set[0].split("-")

    datetime_rise = datetime(int(rise_date[0]), int(rise_date[1]),
                             int(rise_date[2]),
                             int(rise_time[0]), int(rise_time[1]),
                             int(rise_time[2]))
    datetime_rise = datetime_rise.replace(tzinfo=pytz.utc)

    datetime_set = datetime(int(set_date[0]), int(set_date[1]),
                            int(set_date[2]),
                            int(set_time[0]), int(set_time[1]),
                            int(set_time[2]))
    datetime_set = datetime_set.replace(tzinfo=pytz.utc)

    return "d" if datetime_rise < datetime_now_utc < datetime_set else "n"


def get_connection_with_db():
    global conn, curs

    conn = psycopg2.connect(DB_CONNECTION_LINK)
    curs = conn.cursor()


def get_country_code(country):
    country_code = ''

    try:
        get_connection_with_db()
        curs.execute("SELECT code "
                     "FROM countries "
                     "WHERE name='%s' or english='%s'" % (country, country))

        country_code = curs.fetchone()[0]
    except psycopg2.Error:
        py_logger.warning("Ошибка при работе с PostgreSQL", exc_info=True)

    return country_code


def get_weather_picture(weather_code):
    weather_picture = ''

    try:
        curs.execute("SELECT picture "
                     "FROM weather_code "
                     "WHERE id='%d'" % weather_code)

        weather_picture = curs.fetchone()[0]
    except psycopg2.Error:
        py_logger.warning("Ошибка при работе с PostgreSQL", exc_info=True)
    finally:
        if conn:
            curs.close()
            conn.close()
            py_logger.info("Соединение с PostgresSQL")

    return weather_picture


BOT.polling(none_stop=True)
