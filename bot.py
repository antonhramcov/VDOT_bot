import asyncio
import logging
import math
import os
import re
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db import (
    create_pool,
    ensure_user,
    get_latest_vdot,
    init_db,
    save_latest_vdot,
    set_user_language,
)
from texts import LANGUAGES, DEFAULT_LANGUAGE, supported_language_codes, text


DISTANCES_KM = {
    "полумарафон": 21.0975,
    "полумарафонa": 21.0975,
    "half": 21.0975,
    "half marathon": 21.0975,
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
TRAINING_ZONES = (
    ("easy", 0.65, 0.74),
    ("marathon", 0.84, None),
    ("threshold", 0.88, None),
    ("interval", 1.00, None),
    ("repetition", 1.08, None),
)


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


def format_pace_seconds(
    seconds_per_km: int,
    language_code: str | None = None,
) -> str:
    minutes, seconds = divmod(seconds_per_km, 60)
    pace_suffix = text(language_code, "pace_suffix")
    return f"{minutes}:{seconds:02d}{pace_suffix}"


def format_pace_range(
    first_seconds: int,
    second_seconds: int,
    language_code: str | None = None,
) -> str:
    faster, slower = sorted((first_seconds, second_seconds))
    pace_suffix = text(language_code, "pace_suffix")
    return (
        f"{format_pace_seconds(faster, language_code).removesuffix(pace_suffix)}"
        f"-{format_pace_seconds(slower, language_code)}"
    )


def training_paces(vdot: float, language_code: str | None = None) -> dict[str, str]:
    """Approximate training paces derived from VDOT intensity fractions."""
    paces = {}
    for zone_id, first_fraction, second_fraction in TRAINING_ZONES:
        if second_fraction is None:
            paces[zone_id] = format_pace_seconds(
                pace_for_vdot_fraction(vdot, first_fraction),
                language_code,
            )
        else:
            paces[zone_id] = format_pace_range(
                pace_for_vdot_fraction(vdot, first_fraction),
                pace_for_vdot_fraction(vdot, second_fraction),
                language_code,
            )
    return paces


def format_duration(total_seconds: int) -> str:
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def pace_per_km(
    distance_km: float,
    total_seconds: int,
    language_code: str | None = None,
) -> str:
    return format_pace_seconds(
        pace_seconds_per_km(distance_km, total_seconds),
        language_code,
    )


def pace_seconds_per_km(distance_km: float, total_seconds: int) -> int:
    return round(total_seconds / distance_km)


def start_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text(language_code, "language_button"),
                    callback_data="language:open",
                )
            ]
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for language_code in supported_language_codes():
        language = LANGUAGES[language_code]
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{language['flag']} {language['native_name']}",
                    callback_data=f"language:set:{language_code}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def training_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text(language_code, "training_button"),
                    callback_data="training:calculate",
                )
            ]
        ]
    )


def training_details_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    workout_names = text(language_code, "workout_names")
    buttons = []
    for zone_id, _, _ in TRAINING_ZONES:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=workout_names[zone_id],
                    callback_data=f"training:details:{zone_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_trainings_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text(language_code, "back_to_trainings_button"),
                    callback_data="training:calculate",
                )
            ]
        ]
    )


def save_decision_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text(language_code, "save_yes_button"),
                    callback_data="vdot_save:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text(language_code, "save_no_button"),
                    callback_data="vdot_save:no",
                )
            ],
        ]
    )


def format_training_paces(vdot: float, language_code: str | None = None) -> str:
    paces = training_paces(vdot, language_code)
    workout_names = text(language_code, "workout_names")
    lines = [text(language_code, "training_paces")]
    for zone_id, _, _ in TRAINING_ZONES:
        lines.append(f"{workout_names[zone_id]}: {paces[zone_id]}")
    return "\n".join(lines)


def format_training_detail(
    vdot: float,
    zone_id: str,
    language_code: str | None = None,
) -> str:
    paces = training_paces(vdot, language_code)
    workout_names = text(language_code, "workout_names")
    workout_descriptions = text(language_code, "workout_descriptions")
    return workout_descriptions[zone_id].format(
        name=workout_names[zone_id],
        pace=paces[zone_id],
    )


def format_result(
    result: RaceResult,
    vdot: float,
    language_code: str | None = None,
) -> str:
    return text(
        language_code,
        "result",
        vdot=vdot,
        distance=result.distance_km,
        duration=format_duration(result.total_seconds),
        pace=pace_per_km(
            result.distance_km,
            result.total_seconds,
            language_code,
        ),
    )


async def resolve_language(db_pool, user) -> str:
    if not user:
        return DEFAULT_LANGUAGE
    return await ensure_user(db_pool, user)


async def start(message: Message, db_pool) -> None:
    language_code = await resolve_language(db_pool, message.from_user)
    await message.answer(
        text(language_code, "start"),
        reply_markup=start_keyboard(language_code),
    )


async def my_vdot(message: Message, db_pool) -> None:
    if not message.from_user:
        return

    language_code = await resolve_language(db_pool, message.from_user)
    saved_vdot = await get_latest_vdot(db_pool, message.from_user.id)
    if not saved_vdot:
        await message.answer(text(language_code, "no_saved_vdot"))
        return

    await message.answer(
        text(language_code, "saved_vdot", vdot=saved_vdot["last_vdot"])
        + text(
            language_code,
            "last_result",
            distance=saved_vdot["distance_km"],
            duration=format_duration(saved_vdot["total_seconds"]),
        ),
        reply_markup=training_keyboard(language_code),
    )


async def handle_result(message: Message, db_pool) -> None:
    language_code = await resolve_language(db_pool, message.from_user)
    try:
        result = parse_result(message.text or "")
        vdot = calculate_vdot(result.distance_km, result.total_seconds)
    except ValueError:
        await message.answer(text(language_code, "parse_error"))
        return

    if not message.from_user:
        await message.answer(format_result(result, vdot, language_code))
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
            f"{format_result(result, vdot, language_code)}\n\n"
            f"{text(language_code, 'remembered_vdot')}",
            reply_markup=training_keyboard(language_code),
        )
        return

    previous_vdot = float(saved_vdot["last_vdot"])
    if abs(vdot - previous_vdot) <= VDOT_EPSILON:
        await message.answer(
            f"{format_result(result, vdot, language_code)}\n\n"
            f"{text(language_code, 'same_vdot')}",
            reply_markup=training_keyboard(language_code),
        )
        return

    PENDING_VDOTS[message.from_user.id] = PendingVdot(
        result=result,
        vdot=vdot,
        source_text=message.text or "",
    )
    if vdot > previous_vdot:
        reaction = text(
            language_code,
            "vdot_improved",
            previous=previous_vdot,
            current=vdot,
        )
    else:
        reaction = text(
            language_code,
            "vdot_declined",
            previous=previous_vdot,
            current=vdot,
        )

    await message.answer(
        f"{format_result(result, vdot, language_code)}\n\n"
        f"{reaction}\n"
        f"{text(language_code, 'ask_save_vdot')}",
        reply_markup=save_decision_keyboard(language_code),
    )


async def handle_save_decision(callback: CallbackQuery, db_pool) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    language_code = await resolve_language(db_pool, callback.from_user)
    decision = (callback.data or "").split(":", maxsplit=1)[-1]
    pending = PENDING_VDOTS.pop(callback.from_user.id, None)
    if not pending:
        await callback.answer(
            text(language_code, "no_pending_vdot"),
            show_alert=True,
        )
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
                text(language_code, "saved_new_vdot", vdot=pending.vdot),
                reply_markup=training_keyboard(language_code),
            )
        await callback.answer(text(language_code, "vdot_updated_alert"))
        return

    if isinstance(callback.message, Message):
        await callback.message.answer(
            text(language_code, "kept_previous_vdot"),
            reply_markup=training_keyboard(language_code),
        )
    await callback.answer(text(language_code, "kept_previous_alert"))


async def handle_training(callback: CallbackQuery, db_pool) -> None:
    language_code = await resolve_language(db_pool, callback.from_user)
    saved_vdot = await get_latest_vdot(db_pool, callback.from_user.id)
    if not saved_vdot:
        await callback.answer(
            text(language_code, "send_result_first"),
            show_alert=True,
        )
        return

    vdot = float(saved_vdot["last_vdot"])
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f"{text(language_code, 'training_by_vdot', vdot=vdot)}\n\n"
            f"{format_training_paces(vdot, language_code)}",
            reply_markup=training_details_keyboard(language_code),
        )
    await callback.answer()


async def handle_training_detail(callback: CallbackQuery, db_pool) -> None:
    language_code = await resolve_language(db_pool, callback.from_user)
    saved_vdot = await get_latest_vdot(db_pool, callback.from_user.id)
    if not saved_vdot:
        await callback.answer(
            text(language_code, "send_result_first"),
            show_alert=True,
        )
        return

    zone_id = (callback.data or "").split(":", maxsplit=2)[-1]
    valid_zone_ids = {item[0] for item in TRAINING_ZONES}
    if zone_id not in valid_zone_ids:
        await callback.answer()
        return

    vdot = float(saved_vdot["last_vdot"])
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_training_detail(vdot, zone_id, language_code),
            reply_markup=back_to_trainings_keyboard(language_code),
        )
    await callback.answer()


async def open_language_menu(callback: CallbackQuery, db_pool) -> None:
    if callback.from_user:
        await ensure_user(db_pool, callback.from_user)

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text("en", "language_prompt"),
            reply_markup=language_keyboard(),
        )
    await callback.answer()


async def select_language(callback: CallbackQuery, db_pool) -> None:
    if not callback.from_user:
        await callback.answer()
        return

    language_code = (callback.data or "").split(":", maxsplit=2)[-1]
    if language_code not in supported_language_codes():
        language_code = DEFAULT_LANGUAGE
    saved_language = await set_user_language(
        db_pool,
        callback.from_user,
        language_code,
    )

    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text(saved_language, "start"),
            reply_markup=start_keyboard(saved_language),
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
    dispatcher.callback_query.register(open_language_menu, F.data == "language:open")
    dispatcher.callback_query.register(
        select_language,
        F.data.startswith("language:set:"),
    )
    dispatcher.callback_query.register(
        handle_save_decision,
        F.data.startswith("vdot_save:"),
    )
    dispatcher.callback_query.register(
        handle_training_detail,
        F.data.startswith("training:details:"),
    )
    dispatcher.callback_query.register(handle_training, F.data == "training:calculate")
    dispatcher.message.register(handle_result, F.text)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
