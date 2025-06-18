# players/bot.py — бот для deathmatch на test.wad без ConNquestEnv

import os, time, json, socket, numpy as np
from vizdoom import DoomGame, Mode
from system.adaptive_system import AdaptiveEnsembleAgent

MODELS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

agent = AdaptiveEnsembleAgent(
    stormtrooper_model_path=os.path.join(MODELS, "stormtrooper.onnx"),
    pacifist_model_path   =os.path.join(MODELS, "pacifist.onnx"),
    balanced_model_path   =os.path.join(MODELS, "normal.onnx"),
    momentum=0.99
)

# --- Doom init ---
game = DoomGame()
game.load_config("my_scenario.cfg")
game.set_doom_scenario_path("maps/statistics.wad")
game.add_game_args("-join 127.0.0.1 -no_rendering")
game.set_window_visible(False)
game.set_mode(Mode.PLAYER)
game.init()

# --- агент ---

# --- UDP-приём ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 50007))
sock.setblocking(False)

# --- основной цикл ---
state = game.get_state()
while True:
    # статистика от хоста
    try:
        pkt, _ = sock.recvfrom(4096)
        s = json.loads(pkt.decode())
        agent.log_step(moved=s["speed"], dmg=s["dps"], alive=not game.is_player_dead())
        if s["deaths"] > 0:
            agent.log_death()
    except BlockingIOError:
        pass

    if game.is_episode_finished():
        game.new_episode()

    if state is not None:
        buf = state.screen_buffer.astype(np.float32) / 255.0  # (3, 480, 640)
    else:
        buf = np.zeros((3, 480, 640), dtype=np.float32)

    obs = np.expand_dims(buf, axis=0)  # (1, 3, 480, 640)
    idx = agent.get_action(obs)

    action = [0] * game.get_available_buttons_size()
    if idx < len(action):
        action[idx] = 1

    reward = game.make_action(action)
    agent.log_step(0, max(0, -reward))

    if game.is_player_dead():
        agent.log_death()
        game.respawn_player()

    state = game.get_state()
    time.sleep(0.01)

