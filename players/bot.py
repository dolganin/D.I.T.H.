import os, sys, time, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from coNNquest.connquest.ConquestWrapper import ConNquestEnv
from system.adaptive_system import AdaptiveEnsembleAgent

MODELS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

join_args = "-join 127.0.0.1"
env = ConNquestEnv(disable_monsters=True, extra_args=join_args)
env.game.set_window_visible(False)
env.game.set_mode(env.game.Mode.PLAYER)

agent = AdaptiveEnsembleAgent(
    stormtrooper_model_path=os.path.join(MODELS, "stormtrooper.onnx"),
    pacifist_model_path   =os.path.join(MODELS, "pacifist.onnx"),
    balanced_model_path   =os.path.join(MODELS, "balanced.onnx"),
    momentum=0.99,
    n_actions=env.game.get_available_buttons_size()
)

state = env.game.get_state()
while True:
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
