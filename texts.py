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
            "/my_vdot покажет твой сохраненный VDOT.\n"
            "/trains покажет текущие тренировки.\n"
            "/language позволит сменить язык."
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
        "back_to_trainings_button": "Назад к тренировкам",
        "workout_names": {
            "easy": "Легкий бег",
            "marathon": "Марафонский темп",
            "threshold": "Пороговая тренировка",
            "interval": "Интервалы",
            "repetition": "Повторения",
        },
        "workout_descriptions": {
            "easy": (
                "{name}\n"
                "Темп: {pace}\n\n"
                "Как выполнять:\n"
                "Беги спокойно, без борьбы за темп. Дыхание должно оставаться "
                "комфортным, разговорным. Такая тренировка развивает аэробную "
                "базу и помогает восстановлению.\n\n"
                "Пример: 30-60 минут ровного бега в указанном диапазоне."
            ),
            "marathon": (
                "{name}\n"
                "Темп: {pace}\n\n"
                "Как выполнять:\n"
                "Это контролируемый устойчивый темп, близкий к соревновательному "
                "марафонскому усилию. Начинай после легкой разминки и не "
                "разгоняйся в первые минуты.\n\n"
                "Пример: 15 минут легко, затем 2 x 15 минут в марафонском темпе "
                "с 5 минутами легкого бега между отрезками."
            ),
            "threshold": (
                "{name}\n"
                "Темп: {pace}\n\n"
                "Как выполнять:\n"
                "Беги мощно, но контролируемо: это усилие, которое можно держать "
                "примерно 40-60 минут на соревновании. Не превращай отрезки в "
                "максимальную работу.\n\n"
                "Пример: 10-15 минут разминки, затем 3 x 8 минут в пороговом "
                "темпе с 2 минутами легкого бега."
            ),
            "interval": (
                "{name}\n"
                "Темп: {pace}\n\n"
                "Как выполнять:\n"
                "Интервалы выполняются короткими отрезками с восстановлением. "
                "Цель - качественная работа на высокой скорости, а не финиш "
                "любой ценой.\n\n"
                "Пример: 10-15 минут разминки, затем 5 x 3 минуты в интервальном "
                "темпе с 2-3 минутами легкого бега."
            ),
            "repetition": (
                "{name}\n"
                "Темп: {pace}\n\n"
                "Как выполнять:\n"
                "Короткие быстрые отрезки на хорошей технике и полном контроле. "
                "Восстановление должно быть достаточно длинным, чтобы каждый "
                "повтор был качественным.\n\n"
                "Пример: 10-15 минут разминки, затем 8 x 200 м в темпе повторений "
                "с легким восстановлением 200 м."
            ),
        },
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
            "/my_vdot shows your saved VDOT.\n"
            "/trains shows your current training paces.\n"
            "/language changes the language."
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
        "back_to_trainings_button": "Back to trainings",
        "workout_names": {
            "easy": "Easy",
            "marathon": "Marathon",
            "threshold": "Threshold",
            "interval": "Interval",
            "repetition": "Repetition",
        },
        "workout_descriptions": {
            "easy": (
                "{name}\n"
                "Pace: {pace}\n\n"
                "How to run it:\n"
                "Keep the effort relaxed and conversational. Do not chase the "
                "fast end of the range. This run builds aerobic base and helps "
                "recovery.\n\n"
                "Example: 30-60 minutes of steady running in the suggested range."
            ),
            "marathon": (
                "{name}\n"
                "Pace: {pace}\n\n"
                "How to run it:\n"
                "Run a controlled, sustainable effort close to marathon race "
                "intensity. Warm up first and avoid starting too fast.\n\n"
                "Example: 15 minutes easy, then 2 x 15 minutes at marathon pace "
                "with 5 minutes easy between reps."
            ),
            "threshold": (
                "{name}\n"
                "Pace: {pace}\n\n"
                "How to run it:\n"
                "Run strong but controlled, around the effort you could sustain "
                "for roughly 40-60 minutes in a race. Do not turn it into an "
                "all-out interval session.\n\n"
                "Example: 10-15 minutes warm-up, then 3 x 8 minutes at threshold "
                "pace with 2 minutes easy jog."
            ),
            "interval": (
                "{name}\n"
                "Pace: {pace}\n\n"
                "How to run it:\n"
                "Run short fast reps with recovery. The goal is high-quality "
                "speed at a hard but repeatable effort.\n\n"
                "Example: 10-15 minutes warm-up, then 5 x 3 minutes at interval "
                "pace with 2-3 minutes easy jog."
            ),
            "repetition": (
                "{name}\n"
                "Pace: {pace}\n\n"
                "How to run it:\n"
                "Run short quick reps with clean technique and full control. "
                "Recover long enough that every rep stays sharp.\n\n"
                "Example: 10-15 minutes warm-up, then 8 x 200 m at repetition "
                "pace with 200 m easy recovery."
            ),
        },
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
