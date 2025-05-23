import os, sys, time
# добавить корень проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from coNNquest.connquest.ConquestWrapper import ConNquestEnv

host_args = (
    "-host 2 -deathmatch "
    "+timelimit 0 +sv_forcerespawn 1 +sv_nocrouch 1 "
    "+set cl_run 1 +set crosshair 1 +freelook 1"
)

env = ConNquestEnv(disable_monsters=True, extra_args=host_args)
env.game.set_mode(env.game.Mode.SPECTATOR)
env.reset()

while True:
    env.game.advance_action()
    time.sleep(0.01)
