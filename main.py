import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
import asyncio

from dotenv import load_dotenv

load_dotenv('.env')
API_TOKEN = os.getenv("API_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

WEATHER_EMOJIS = {
    "ясно": "☀️",
    "облачно с прояснениями": "🌤️",
    "пасмурно": "☁️",
    "дождь": "🌧️",
    "небольшой дождь": "🌦️",
    "ливень": "🌧️",
    "гроза": "⛈️",
    "снег": "❄️",
    "туман": "🌫️",
    "морось": "🌧️",
}

def get_weather_emoji(description: str) -> str:
    for key in WEATHER_EMOJIS:
        if key in description.lower():
            return WEATHER_EMOJIS[key]
    return "🌡️"

async def get_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                weather_description = data['weather'][0]['description']
                emoji = get_weather_emoji(weather_description)
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                return (f"<b>Погода в {city}:</b>\n"
                        f"{emoji} {weather_description.capitalize()}\n"
                        f"Температура: <i>{temp}°C</i> (ощущается как {feels_like}°C)\n"
                        f"Влажность: {humidity}%\n"
                        f"Скорость ветра: {wind_speed} м/с")
            else:
                return "Не удалось получить данные. Проверьте название места."

async def get_forecast(city: str) -> str:
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(geo_url) as geo_resp:
            if geo_resp.status != 200:
                return "Не удалось найти координаты места."
            geo_data = await geo_resp.json()
            if not geo_data:
                return "Город не найден."
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']

        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&lang=ru&appid={OPENWEATHER_API_KEY}"
        async with session.get(forecast_url) as forecast_resp:
            if forecast_resp.status != 200:
                return "Не удалось получить прогноз."
            data = await forecast_resp.json()

            result = f"<b>Прогноз погоды в {city.title()} на ближайшие 3 дня:</b>\n"
            days_collected = set()

            for entry in data['list']:
                date = entry['dt_txt'].split(" ")[0]
                if date not in days_collected:
                    weather = entry['weather'][0]['description']
                    emoji = get_weather_emoji(weather)
                    temp = entry['main']['temp']
                    result += f"<b>{date}</b>: {emoji} {weather.capitalize()}, <i>{temp}°C</i>\n"
                    days_collected.add(date)
                if len(days_collected) >= 3:
                    break
            return result

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я погодный бот.\nНапиши название места, и я расскажу, какая там погода.\nДобавь слово 'прогноз', чтобы получить погоду на 3 дня. Используй /help для справки.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Поддерживаемые команды:\n/start - приветствие и информация о боте\n/help - список команд\nВведите название места - получите текущую погоду\nДобавьте слово 'прогноз' - получите прогноз на 3 дня")

@dp.message()
async def handle_message(message: Message):
    city = message.text.strip()
    if city.lower().endswith("прогноз"):
        city_name = city.lower().replace("прогноз", "").strip()
        weather_info = await get_forecast(city_name)
    else:
        weather_info = await get_weather(city)
    await message.answer(weather_info, parse_mode=ParseMode.HTML)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())