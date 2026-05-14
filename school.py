import logging
import requests
from datetime import datetime
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
from telegram.ext import Application
import config

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
OPENWEATHER_API_KEY = config.OPENWEATHER_API_KEY


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_current_weather(city):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json(), response.status_code


def get_5day_forecast(city):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params, timeout=10)
    return response.json(), response.status_code


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌤 Привет! Я бот погоды.\n\n"
        "Используй:\n"
        "/weather Москва — текущая погода\n"
        "/forecast Воронеж — прогноз на 5 дней"
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите город, например: /weather Москва")
        return

    city = " ".join(context.args)
    try:
        data, status = get_current_weather(city)
        if status == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            desc = data["weather"][0]["description"].capitalize()
            humidity = data["main"]["humidity"]
            city_name = data["name"]
            country = data["sys"]["country"]

            msg = (
                f"📍 *{city_name}, {country}*\n"
                f"🌡 {temp:.1f}°C (ощущается как {feels_like:.1f}°C)\n"
                f"☁️ {desc}\n"
                f"💧 Влажность: {humidity}%"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            error = data.get("message", "Город не найден")
            await update.message.reply_text(f"❌ Ошибка: {error}")
    except Exception as e:
        logger.error(f"Ошибка при запросе погоды: {e}")
        await update.message.reply_text("⚠️ Не удалось получить погоду. Попробуйте позже.")


async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите город, например: /forecast Токио")
        return

    city = " ".join(context.args)
    try:
        data, status = get_5day_forecast(city)
        if status != 200:
            error = data.get("message", "Город не найден")
            await update.message.reply_text(f"❌ Ошибка: {error}")
            return

        # Группируем прогноз по датам (игнорируем сегодня, если нужно — можно оставить)
        daily = defaultdict(list)
        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            daily[date].append(item)


        forecast_days = list(daily.items())[:5]

        if not forecast_days:
            await update.message.reply_text("Нет данных для прогноза.")
            return

        city_name = data["city"]["name"]
        country = data["city"]["country"]
        msg = f"📅 *Прогноз погоды на 5 дней для {city_name}, {country}:*\n\n"

        for date_str, entries in forecast_days:

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = date_obj.strftime("%a")
            readable_date = date_obj.strftime("%d.%m")


            temps = [e["main"]["temp"] for e in entries]
            avg_temp = sum(temps) / len(temps)
            description = entries[0]["weather"][0]["description"].capitalize()

            msg += f"*{readable_date} ({day_name})*: {avg_temp:.1f}°C, {description}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при запросе прогноза: {e}")
        await update.message.reply_text("⚠️ Не удалось получить прогноз. Попробуйте позже.")


def main():
    PROXY_URL = "https://80.241.251.54:8080"  # пример
    httpx_client = httpx.AsyncClient(proxy=PROXY_URL)
    application = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .httpx_client(httpx_client) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("forecast", forecast))

    print("✅ Бот с прогнозом погоды запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()