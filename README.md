# TELEGRAM WEATHER BOT #

It's a simple telegram bot that returns the user the weather and local time in 
the entered city.

## STARTING THE WEATHER BOT ##

In the script at the address `project/scripts/weather_bot.py`
```python
DB_CONNECTION_LINK = ""
BOT = telebot.TeleBot("your_bot_token")
API = ""
```
variable `DB_CONNECTION_LINK` assign a link to the database, variable `BOT` — your 
telegram bot token, which can be created by [the link](https://t.me/BotFather),
variable `API` — your [API key](https://home.openweathermap.org/api_keys), to get 
the API key you need to register. You can read weather [API documentation.](https://openweathermap.org/current)

Even before starting, you need to execute a sql query from a file `init.sql` in 
your chosen DBMS (I used PostgreSQL)

Project logs will be kept in file `weather_bot.log`.

