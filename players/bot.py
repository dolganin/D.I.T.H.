import os, sys, time, json, socket, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from coNNquest.connquest.ConquestWrapper import ConNquestEnv
from system.adaptive_system import AdaptiveEnsembleAgent

MODELS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

# ==== Doom init ==============================================================
join_args = "-join 127.0.0.1"
env = ConNquestEnv(disable_monsters=True, extra_args=join_args)
env.game.set_window_visible(False)
env.game.set_mode(env.game.Mode.PLAYER)

# ==== UDP приёмник ===========================================================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 50007))
sock.setblocking(False)

# ==== агент ==================================================================
agent = AdaptiveEnsembleAgent(
    stormtrooper_model_path=os.path.join(MODELS, "stormtrooper.onnx"),
    pacifist_model_path   =os.path.join(MODELS, "pacifist.onnx"),
    balanced_model_path   =os.path.join(MODELS, "balanced.onnx"),
    momentum=0.99,
    n_actions=env.game.get_available_buttons_size()
)

state = env.game.get_state()
while True:
    # --- приём статистики от хоста ------------------------------------------
    try:
        pkt, _ = sock.recvfrom(4096)
        s = json.loads(pkt.decode())
        agent.log_step(moved=s["speed"], dmg=s["dps"], alive=not env.game.is_player_dead())
        if s["deaths"] > 0:
            agent.log_death()
    except BlockingIOError:
        pass                              

    # --- обычный цикл игры ---------------------------------------------------
    if env.game.is_episode_finished():
        env.game.new_episode()

    buf = state.screen_buffer if state else np.zeros((1,), dtype=np.float32)
    idx = agent.get_action(buf.flatten())
    action = [0]*env.game.get_available_buttons_size()
    if idx < len(action):
        action[idx] = 1

    reward = env.game.make_action(action)
    agent.log_step(0, max(0, -reward))
    if env.game.is_player_dead():
        agent.log_death()
        env.game.respawn_player()

    state = env.game.get_state()
    time.sleep(0.01)
