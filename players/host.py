# players/host.py — запуск deathmatch на test.wad без зависимостей от ConquestWrapper

import os, time, json, math, socket
from vizdoom import DoomGame, GameVariable, Mode

# --- init DoomGame ---
game = DoomGame()
game.load_config("my_scenario.cfg")                    # минимальный .cfg
game.set_doom_scenario_path("maps/statistics.wad")                # путь к WAD-файлу
game.add_game_args("-host 2 +deathmatch +timelimit 0 +sv_forcerespawn 1 +sv_nocrouch 1")
game.set_window_visible(True)
game.set_mode(Mode.PLAYER)
game.init()

# --- init UDP socket ---
UDP_ADDR = ("127.0.0.1", 50007)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- track ---
prev_frags = game.get_game_variable(GameVariable.FRAGCOUNT)
prev_time  = time.time()
dmg_total  = 0.0
HP_PER_KILL = 100

# --- loop ---
while True:
    game.advance_action()

    vx = game.get_game_variable(GameVariable.VELOCITY_X)
    vy = game.get_game_variable(GameVariable.VELOCITY_Y)
    vz = game.get_game_variable(GameVariable.VELOCITY_Z)
    speed = math.sqrt(vx*vx + vy*vy + vz*vz)

    frags = game.get_game_variable(GameVariable.FRAGCOUNT)
    deaths = game.get_game_variable(GameVariable.DEATHCOUNT)
    new_kills = max(0, frags - prev_frags)
    prev_frags = frags

    dmg_total += new_kills * HP_PER_KILL
    now = time.time()
    dps = dmg_total / max(1e-3, now - prev_time)

    stats = {
        "speed":  speed,
        "kills":  int(frags),
        "deaths": int(deaths),
        "dps":    dps
    }
    sock.sendto(json.dumps(stats).encode(), UDP_ADDR)

    time.sleep(0.01)

