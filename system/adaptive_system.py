"""
Адаптивный ансамбль:
- три ONNX-модели (pacifist / balanced / stormtrooper)
- экспоненциальное «забывание» статистики (momentum)
- fall-back на случай отсутствия моделей (рандом)
"""
import os
import numpy as np
from abc import ABC
import onnxruntime as ort

class AdaptiveEnsembleAgent(ABC):
    def __init__(
        self,
        stormtrooper_model_path: str,
        pacifist_model_path: str,
        balanced_model_path: str,
        momentum: float = 0.99,
        d_min=0.0, d_max=10.0,
        v_min=0.0, v_max=5.0,
        p_min=0.0, p_max=50.0,
        n_actions: int = 8,
    ):
        # загружаем модели, если есть
        self.has_models = all(os.path.isfile(p) for p in
                              (stormtrooper_model_path,
                               pacifist_model_path,
                               balanced_model_path))
        if self.has_models:
            self.st_sess = ort.InferenceSession(stormtrooper_model_path)
            self.pc_sess = ort.InferenceSession(pacifist_model_path)
            self.ba_sess = ort.InferenceSession(balanced_model_path)
            self.st_in = self.st_sess.get_inputs()[0].name
            self.pc_in = self.pc_sess.get_inputs()[0].name
            self.ba_in = self.ba_sess.get_inputs()[0].name
        else:
            print("⚠️  ONNX-модели не найдены — действия будут случайными")

        # скользящая статистика
        self.m = momentum
        self.deaths = 0.0
        self.distance = 0.0
        self.damage = 0.0
        self.ticks = 0.0

        self.d_min, self.d_max = d_min, d_max
        self.v_min, self.v_max = v_min, v_max
        self.p_min, self.p_max = p_min, p_max
        self.n_actions = n_actions

    # ---- логирование ----
    def log_step(self, moved, dmg, alive=True):
        self.distance = self.distance * self.m + moved
        self.damage   = self.damage   * self.m + dmg
        if alive:
            self.ticks = self.ticks * self.m + 1

    def log_death(self):
        self.deaths = self.deaths * self.m + 1

    # ---- util ----
    def _norm(self, x, x_min, x_max):
        return (x - x_min) / (x_max - x_min + 1e-8)

    def _weights(self):
        d = self.deaths
        v = self.distance / max(1.0, self.ticks)
        p = self.damage   / max(1.0, self.ticks)

        d_t = self._norm(d, self.d_min, self.d_max)
        v_t = self._norm(v, self.v_min, self.v_max)
        p_t = self._norm(p, self.p_min, self.p_max)

        S_p  = d_t + (1 - v_t) + (1 - p_t)        
        S_sr = (1 - d_t) + v_t + p_t               
        S_s  = 1 - abs(S_sr - S_p) / 3            

        s = np.array([S_p, S_s, S_sr])
        w = np.exp(s) / np.sum(np.exp(s))
        return w  # pacifist, balanced, stormtrooper

    def _run(self, sess, inp_name, state):
        return sess.run(None, {inp_name: state.astype(np.float32)})[0]

    # ---- публичный метод ----
    def get_action(self, state: np.ndarray):
        if not self.has_models:
            # случайное действие
            return np.random.randint(self.n_actions)

        w_p, w_b, w_s = self._weights()
        p  = self._run(self.pc_sess, self.pc_in, state)
        b  = self._run(self.ba_sess, self.ba_in, state)
        st = self._run(self.st_sess, self.st_in, state)
        probs = w_p * p + w_b * b + w_s * st
        return int(np.argmax(probs))
