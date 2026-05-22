import asyncio
import logging
import math
import os
import re
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import create_pool, get_latest_vdot, init_db, save_latest_vdot


DISTANCES_KM = {
    "полумарафон": 21.0975,
    "полумарафонa": 21.0975,
    "half": 21.0975,
    "halfmarathon": 21.0975,
    "hm": 21.0975,
    "марафон": 42.195,
    "marathon": 42.195,
}


@dataclass(frozen=True)
class RaceResult:
    distance_km: float
    total_seconds: int


@dataclass(frozen=True)
class PendingVdot:
    result: RaceResult
    vdot: float
    source_text: str


PENDING_VDOTS: dict[int, PendingVdot] = {}
VDOT_EPSILON = 0.05


def parse_time(value: str) -> int:
    parts = value.strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError("time must be mm:ss or h:mm:ss")

    numbers = [int(part) for part in parts]
    if any(number < 0 for number in numbers):
        raise ValueError("time cannot contain negative numbers")

    if len(numbers) == 2:
        minutes, seconds = numbers
        hours = 0
    else:
        hours, minutes, seconds = numbers

    if minutes >= 60 and hours > 0:
        raise ValueError("minutes must be less than 60")
    if seconds >= 60:
        raise ValueError("seconds must be less than 60")

    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError("time must be positive")
    return total_seconds


def parse_result(text: str) -> RaceResult:
    normalized = text.strip().lower().replace(",", ".")
    normalized = re.sub(r"\s+", " ", normalized)

    time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", normalized)
    if not time_match:
        raise ValueError("time not found")
    total_seconds = parse_time(time_match.group(1))

    distance_km = None
    for name, value in DISTANCES_KM.items():
        if re.search(rf"\b{re.escape(name)}\b", normalized):
            distance_km = value
            break

    if distance_km is None:
        km_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:км|km|k)\b", normalized)
        if not km_match:
            raise ValueError("distance not found")
        distance_km = float(km_match.group(1))

    if distance_km <= 0:
        raise ValueError("distance must be positive")

    return RaceResult(distance_km=distance_km, total_seconds=total_seconds)


def calculate_vdot(distance_km: float, total_seconds: int) -> float:
    """Daniels/Gilbert race-performance VDOT formula."""
    minutes = total_seconds / 60
    velocity_m_per_min = distance_km * 1000 / minutes

    vo2 = (
        -4.60
        + 0.182258 * velocity_m_per_min
        + 0.000104 * velocity_m_per_min**2
    )
    percent_vo2_max = (
        0.8
        + 0.1894393 * math.exp(-0.012778 * minutes)
        + 0.2989558 * math.exp(-0.1932605 * minutes)
    )
    return vo2 / percent_vo2_max


def velocity_for_vo2(vo2: float) -> float:
    """Return meters per minute for the Daniels VO2 velocity equation."""
    a = 0.000104
    b = 0.182258
    c = -4.60 - vo2
    discriminant = b**2 - 4 * a * c
    return (-b + math.sqrt(discriminant)) / (2 * a)


def pace_for_vdot_fraction(vdot: float, fraction: float) -> int:
    velocity_m_per_min = velocity_for_vo2(vdot * fraction)
    seconds_per_km = round(60_000 / velocity_m_per_min)
    return seconds_per_km


def format_pace_seconds(seconds_per_km: int) -> str:
    minutes, seconds = divmod(seconds_per_km, 60)
    return f"{minutes}:{seconds:02d}/км"


def format_pace_range(first_seconds: int, second_seconds: int) -> str:
    faster, slower = sorted((first_seconds, second_seconds))
    return (
        f"{format_pace_seconds(faster).removesuffix('/км')}"
        f"-{format_pace_seconds(slower)}"
    )


def training_paces(vdot: float) -> dict[str, str]:
    """Approximate training paces derived from VDOT intensity fractions."""
    return {
        "Easy": format_pace_range(
            pace_for_vdot_fraction(vdot, 0.65),
            pace_for_vdot_fraction(vdot, 0.74),
        ),
        "Marathon": format_pace_seconds(pace_for_vdot_fraction(vdot, 0.84)),
        "Threshold": format_pace_seconds(pace_for_vdot_fraction(vdot, 0.88)),
        "Interval": format_pace_seconds(pace_for_vdot_fraction(vdot, 1.00)),
        "Repetition": format_pace_seconds(pace_for_vdot_fraction(vdot, 1.08)),
    }


def format_duration(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def pace_per_km(distance_km: float, total_seconds: int) -> str:
    return format_pace_seconds(pace_seconds_per_km(distance_km, total_seconds))


def pace_seconds_per_km(distance_km: float, total_seconds: int) -> int:
    return round(total_seconds / distance_km)


HELP_TEXT = (
    "Пришли результат забега, например:\n"
    "5 км за 24:30\n"
    "10 км за 52:10\n"
    "полумарафон за 1:55:00\n\n"
    "Я посчитаю VDOT по формуле Daniels.\n"
    "Команда /my_vdot покажет твой сохраненный VDOT."
)


def training_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Рассчитать тренировку",
                    callback_data="training:calculate",
                )
            ]
        ]
    )


def save_decision_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, изменить",
                    callback_data="vdot_save:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Нет, оставить предыдущее",
                    callback_data="vdot_save:no",
                )
            ],
        ]
    )


def format_training_paces(vdot: float) -> str:
    paces = training_paces(vdot)
    return (
        "Тренировочные темпы:\n"
        f"Easy: {paces['Easy']}\n"
        f"Marathon: {paces['Marathon']}\n"
        f"Threshold: {paces['Threshold']}\n"
        f"Interval: {paces['Interval']}\n"
        f"Repetition: {paces['Repetition']}"
    )


def format_result(result: RaceResult, vdot: float) -> str:
    return (
        "VDOT: "
        f"{vdot:.1f}\n"
        f"Дистанция: {result.distance_km:g} км\n"
        f"Время: {format_duration(result.total_seconds)}\n"
        f"Темп: {pace_per_km(result.distance_km, result.total_seconds)}"
    )


async def start(message: Message) -> None:
    await message.answer(HELP_TEXT)


async def my_vdot(message: Message, db_pool) -> None:
    if not message.from_user:
        return

    saved_vdot = await get_latest_vdot(db_pool, message.from_user.id)
    if not saved_vdot:
        await message.answer(
            "У тебя пока нет сохраненного VDOT.\n\n"
            "Пришли результат забега, например: 5 км за 24:30"
        )
        return

    await message.answer(
        "Твой сохраненный VDOT: "
        f"{saved_vdot['last_vdot']:.1f}\n"
        f"Последний результат: {saved_vdot['distance_km']:g} км "
        f"за {format_duration(saved_vdot['total_seconds'])}",
        reply_markup=training_keyboard(),
    )


async def handle_result(message: Message, db_pool) -> None:
    try:
        result = parse_result(message.text or "")
        vdot = calculate_vdot(result.distance_km, result.total_seconds)
    except ValueError:
        await message.answer(
            "Не смог разобрать результат.\n\n"
            "Формат: дистанция за время\n"
            "Например: 5 км за 24:30"
        )
        return

    if not message.from_user:
        await message.answer(format_result(result, vdot))
        return

    saved_vdot = await get_latest_vdot(db_pool, message.from_user.id)
    if not saved_vdot:
        await save_latest_vdot(
            pool=db_pool,
            user=message.from_user,
            vdot=vdot,
            distance_km=result.distance_km,
            total_seconds=result.total_seconds,
            race_pace_seconds=pace_seconds_per_km(
                result.distance_km,
                result.total_seconds,
            ),
            source_text=message.text or "",
        )
        await message.answer(
            f"{format_result(result, vdot)}\n\n"
            "Я запомнил твой текущий VDOT.\n"
            "Могу сразу рассчитать тренировочные темпы.",
            reply_markup=training_keyboard(),
        )
        return

    previous_vdot = float(saved_vdot["last_vdot"])
    if abs(vdot - previous_vdot) <= VDOT_EPSILON:
        await message.answer(
            f"{format_result(result, vdot)}\n\n"
            "VDOT совпадает с сохраненным значением. Можно сразу перейти "
            "к тренировочным темпам.",
            reply_markup=training_keyboard(),
        )
        return

    PENDING_VDOTS[message.from_user.id] = PendingVdot(
        result=result,
        vdot=vdot,
        source_text=message.text or "",
    )
    if vdot > previous_vdot:
        reaction = (
            "Класс, VDOT вырос: "
            f"{previous_vdot:.1f} -> {vdot:.1f}."
        )
    else:
        reaction = (
            "VDOT стал ниже: "
            f"{previous_vdot:.1f} -> {vdot:.1f}. Бывает, форма тоже ходит "
            "волнами."
        )

    await message.answer(
        f"{format_result(result, vdot)}\n\n"
        f"{reaction}\n"
        "Пересохранить VDOT для тебя?",
        reply_markup=save_decision_keyboard(),
    )


async def handle_save_decision(callback: CallbackQuery, db_pool) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    decision = (callback.data or "").split(":", maxsplit=1)[-1]
    pending = PENDING_VDOTS.pop(callback.from_user.id, None)
    if not pending:
        await callback.answer("Нет нового VDOT для сохранения.", show_alert=True)
        return

    if decision == "yes":
        await save_latest_vdot(
            pool=db_pool,
            user=callback.from_user,
            vdot=pending.vdot,
            distance_km=pending.result.distance_km,
            total_seconds=pending.result.total_seconds,
            race_pace_seconds=pace_seconds_per_km(
                pending.result.distance_km,
                pending.result.total_seconds,
            ),
            source_text=pending.source_text,
        )
        if isinstance(callback.message, Message):
            await callback.message.answer(
                f"Готово, я запомнил новый VDOT: {pending.vdot:.1f}.\n"
                "Могу сразу рассчитать тренировочные темпы.",
                reply_markup=training_keyboard(),
            )
        await callback.answer("VDOT обновлен")
        return

    if isinstance(callback.message, Message):
        await callback.message.answer(
            "Хорошо, оставляю предыдущее значение VDOT.",
            reply_markup=training_keyboard(),
        )
    await callback.answer("Оставил прежний VDOT")


async def handle_training(callback: CallbackQuery, db_pool) -> None:
    saved_vdot = await get_latest_vdot(db_pool, callback.from_user.id)
    if not saved_vdot:
        await callback.answer("Сначала пришли результат забега.", show_alert=True)
        return

    vdot = float(saved_vdot["last_vdot"])
    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"Расчет по сохраненному VDOT {vdot:.1f}:\n\n"
            f"{format_training_paces(vdot)}"
        )
    await callback.answer()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Set DATABASE_URL environment variable")

    bot = Bot(token=token)
    db_pool = await create_pool(database_url)
    await init_db(db_pool)

    dispatcher = Dispatcher()
    dispatcher["db_pool"] = db_pool
    dispatcher.message.register(start, CommandStart())
    dispatcher.message.register(my_vdot, Command("my_vdot"))
    dispatcher.callback_query.register(
        handle_save_decision,
        F.data.startswith("vdot_save:"),
    )
    dispatcher.callback_query.register(handle_training, F.data == "training:calculate")
    dispatcher.message.register(handle_result, F.text)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
