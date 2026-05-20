# VDOT Telegram Bot

Telegram bot на aiogram, который принимает результат бега и отвечает рассчитанным VDOT.

## Формат сообщений

```text
5 км за 24:30
10 км за 52:10
полумарафон за 1:55:00
```

Также поддерживаются `km`, `k`, `марафон`, `marathon`, `half`, `hm`.

## Запуск

Перед запуском добавьте токен в окружение:

```bash
export BOT_TOKEN=123456:telegram-token
docker compose up --build
```

Или создайте локальный `.env`:

```env
BOT_TOKEN=123456:telegram-token
```

Затем:

```bash
docker compose up --build
```

## Расчет VDOT

Используется формула Daniels/Gilbert:

```text
VO2 = -4.60 + 0.182258 * v + 0.000104 * v^2
fraction = 0.8 + 0.1894393 * e^(-0.012778 * t) + 0.2989558 * e^(-0.1932605 * t)
VDOT = VO2 / fraction
```

где `v` — скорость в метрах в минуту, `t` — время в минутах.
