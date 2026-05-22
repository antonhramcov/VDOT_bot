DEFAULT_LANGUAGE = "en"


LANGUAGES = {
    "ru": {
        "flag": "🇷🇺",
        "native_name": "Русский",
        "start": (
            "Пришли результат забега, например:\n"
            "5 км за 24:30\n"
            "10 км за 52:10\n"
            "полумарафон за 1:55:00\n\n"
            "Я посчитаю VDOT по формуле Daniels.\n"
            "Команда /my_vdot покажет твой сохраненный VDOT."
        ),
        "language_button": "Language",
        "language_prompt": "Choose your language:",
        "pace_suffix": "/км",
        "training_button": "Рассчитать тренировку",
        "save_yes_button": "Да, изменить",
        "save_no_button": "Нет, оставить предыдущее",
        "no_saved_vdot": (
            "У тебя пока нет сохраненного VDOT.\n\n"
            "Пришли результат забега, например: 5 км за 24:30"
        ),
        "saved_vdot": "Твой сохраненный VDOT: {vdot:.1f}\n",
        "last_result": "Последний результат: {distance:g} км за {duration}",
        "parse_error": (
            "Не смог разобрать результат.\n\n"
            "Формат: дистанция за время\n"
            "Например: 5 км за 24:30"
        ),
        "result": (
            "VDOT: {vdot:.1f}\n"
            "Дистанция: {distance:g} км\n"
            "Время: {duration}\n"
            "Темп: {pace}"
        ),
        "remembered_vdot": (
            "Я запомнил твой текущий VDOT.\n"
            "Могу сразу рассчитать тренировочные темпы."
        ),
        "same_vdot": (
            "VDOT совпадает с сохраненным значением. Можно сразу перейти "
            "к тренировочным темпам."
        ),
        "vdot_improved": "Класс, VDOT вырос: {previous:.1f} -> {current:.1f}.",
        "vdot_declined": (
            "VDOT стал ниже: {previous:.1f} -> {current:.1f}. Бывает, форма "
            "тоже ходит волнами."
        ),
        "ask_save_vdot": "Пересохранить VDOT для тебя?",
        "no_pending_vdot": "Нет нового VDOT для сохранения.",
        "saved_new_vdot": (
            "Готово, я запомнил новый VDOT: {vdot:.1f}.\n"
            "Могу сразу рассчитать тренировочные темпы."
        ),
        "vdot_updated_alert": "VDOT обновлен",
        "kept_previous_vdot": "Хорошо, оставляю предыдущее значение VDOT.",
        "kept_previous_alert": "Оставил прежний VDOT",
        "send_result_first": "Сначала пришли результат забега.",
        "training_paces": "Тренировочные темпы:",
        "training_by_vdot": "Расчет по сохраненному VDOT {vdot:.1f}:",
    },
    "en": {
        "flag": "🇬🇧",
        "native_name": "English",
        "start": (
            "Send me a race result, for example:\n"
            "5 km in 24:30\n"
            "10 km in 52:10\n"
            "half marathon in 1:55:00\n\n"
            "I will calculate your VDOT with the Daniels formula.\n"
            "Use /my_vdot to see your saved VDOT."
        ),
        "language_button": "Language",
        "language_prompt": "Choose your language:",
        "pace_suffix": "/km",
        "training_button": "Calculate training",
        "save_yes_button": "Yes, update",
        "save_no_button": "No, keep previous",
        "no_saved_vdot": (
            "You do not have a saved VDOT yet.\n\n"
            "Send me a race result, for example: 5 km in 24:30"
        ),
        "saved_vdot": "Your saved VDOT: {vdot:.1f}\n",
        "last_result": "Last result: {distance:g} km in {duration}",
        "parse_error": (
            "I could not understand the result.\n\n"
            "Format: distance in time\n"
            "Example: 5 km in 24:30"
        ),
        "result": (
            "VDOT: {vdot:.1f}\n"
            "Distance: {distance:g} km\n"
            "Time: {duration}\n"
            "Pace: {pace}"
        ),
        "remembered_vdot": (
            "I saved your current VDOT.\n"
            "I can calculate training paces right away."
        ),
        "same_vdot": (
            "This VDOT matches your saved value. You can go straight to "
            "training paces."
        ),
        "vdot_improved": "Nice, your VDOT improved: {previous:.1f} -> {current:.1f}.",
        "vdot_declined": (
            "Your VDOT went down: {previous:.1f} -> {current:.1f}. That happens; "
            "fitness moves in waves."
        ),
        "ask_save_vdot": "Save this VDOT for you?",
        "no_pending_vdot": "There is no new VDOT to save.",
        "saved_new_vdot": (
            "Done, I saved your new VDOT: {vdot:.1f}.\n"
            "I can calculate training paces right away."
        ),
        "vdot_updated_alert": "VDOT updated",
        "kept_previous_vdot": "Okay, I will keep your previous VDOT.",
        "kept_previous_alert": "Kept previous VDOT",
        "send_result_first": "Send me a race result first.",
        "training_paces": "Training paces:",
        "training_by_vdot": "Calculation by saved VDOT {vdot:.1f}:",
    },
}


def supported_language_codes() -> tuple[str, ...]:
    return tuple(LANGUAGES)


def normalize_language(language_code: str | None) -> str:
    if language_code in LANGUAGES:
        return language_code
    return DEFAULT_LANGUAGE


def text(language_code: str | None, key: str, **kwargs) -> str:
    language = normalize_language(language_code)
    template = LANGUAGES[language][key]
    if kwargs:
        return template.format(**kwargs)
    return template
