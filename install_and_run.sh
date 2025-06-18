#!/usr/bin/env bash
set -euo pipefail

# 1. создаём и активируем окружение
python3 -m venv D.I.T.H.
source D.I.T.H./bin/activate

# 2. зависимости
python3 -m pip install --upgrade pip
pip install vizdoom onnxruntime numpy pyyaml

# 3. клонируем репо
[ -d coNNquest ] || git clone https://github.com/dolganin/coNNquest.git

# 4. PYTHONPATH
export PYTHONPATH="$PWD"

# 5. запускаем игрока-хоста (сервер)
python3 players/host.py &
HOST_PID=$!

# 6. пауза и запуск клиента
sleep 1
python3 players/bot.py &
BOT_PID=$!

# 7. ждём, пока любой завершится, и убиваем второй
wait -n
kill $HOST_PID $BOT_PID 2>/dev/null || true
wait

# 8. деактивируем окружение
deactivate

