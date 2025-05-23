#!/usr/bin/env bash
set -e

# 1. создаём и активируем окружение
python3 -m venv D.I.T.H.
source D.I.T.H./bin/activate

# 2. зависимости
python -m pip install --upgrade pip
pip install vizdoom onnxruntime numpy pyyaml

# 3. клонируем репо
[ -d coNNquest ] || git clone https://github.com/dolganin/coNNquest.git

# 4. выставляем PYTHONPATH
export PYTHONPATH="$(pwd)"

# 5. запускаем игрока-хоста (сервер)
python players/host.py &
HOST_PID=$!

# 6. пауза перед запуском клиента
sleep 1

# 7. запускаем адаптивного бота
python players/bot.py &
BOT_PID=$!

# 8. ждём завершения обоих
wait "$HOST_PID"
wait "$BOT_PID"

# 9. выключаем окружение
deactivate
