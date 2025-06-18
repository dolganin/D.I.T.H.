import os, sys, time, json, math, socket
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from coNNquest.connquest.ConquestWrapper import ConNquestEnv
from vizdoom import GameVariable               # для VELOCITY_*/FRAG/DEATH
import vizdoom as vzd

# ==== Doom init ==============================================================
host_args = (
        "-host 1 deathmatch +timelimit 0 +sv_forcerespawn 1 +sv_nocrouch 1"
)
env = ConNquestEnv(disable_monsters=True, extra_args=host_args)
env.reset()

# ==== UDP init ===============================================================
UDP_ADDR = ("127.0.0.1", 50007)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ==== вспомогательные переменные ============================================
prev_frags  = env.game.get_game_variable(GameVariable.FRAGCOUNT)
prev_time   = time.time()
dmg_total   = 0.0                               # накопленный урон
HP_PER_KILL = 100                               # оценка хп бота

env.spawn_wave()
# ==== цикл ===================================================================
while True:
    env.game.advance_action()

    # скорость игрока (модуль трёх осей)
    vx = env.game.get_game_variable(GameVariable.VELOCITY_X)
    vy = env.game.get_game_variable(GameVariable.VELOCITY_Y)
    vz = env.game.get_game_variable(GameVariable.VELOCITY_Z)
    speed = math.sqrt(vx*vx + vy*vy + vz*vz)

    # убийства / смерти
    frags = env.game.get_game_variable(GameVariable.FRAGCOUNT)
    deaths = env.game.get_game_variable(GameVariable.DEATHCOUNT)
    new_kills = max(0, frags - prev_frags)
    prev_frags = frags

    # «урон» по боту считаем грубо: 100 hp на каждый kill
    dmg_total += new_kills * HP_PER_KILL

    # dps = накопленный урон / время работы
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
