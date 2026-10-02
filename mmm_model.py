"""
Motor del "gemelo digital": un Marketing Mix Model liviano.

No depende de librerías pesadas (nada de PyMC) — usa numpy/scipy para encontrar,
por optimización, los parámetros de adstock (efecto retardado) y saturación
(rendimientos decrecientes) que mejor explican los mensajes observados a partir
del gasto en Meta y Google.

Esto es la versión "MVP acotado" del roadmap (Fase 1). El día que se valide el
enfoque, este mismo contrato de entrada/salida puede migrar a PyMC-Marketing para
sumar el modelado jerárquico multi-cliente sin tocar el resto del sistema.
"""
import numpy as np
from scipy.optimize import minimize


def _adstock(spend, decay):
    out = np.zeros_like(spend, dtype=float)
    carry = 0.0
    for t, x in enumerate(spend):
        carry = x + decay * carry
        out[t] = carry
    return out


def _saturate(x, k):
    return x / (x + k)


class CampaignTwin:
    """
    Modela 'messages' (mensajes/conversaciones iniciadas) en función del gasto en
    Meta y Google. Mensajes es la etapa del funnel más directamente ligada al gasto;
    leads y conversiones se derivan con sus tasas de paso (ver simulate.py).
    """

    PARAM_NAMES = [
        "intercept", "trend", "seas_amp", "seas_phase",
        "decay_meta", "k_meta", "beta_meta",
        "decay_google", "k_google", "beta_google",
    ]

    def __init__(self):
        self.params = None

    def _predict_raw(self, params, meta_spend, google_spend, t):
        (intercept, trend, seas_amp, seas_phase,
         decay_meta, k_meta, beta_meta,
         decay_google, k_google, beta_google) = params

        baseline = intercept + trend * t + seas_amp * np.sin(2 * np.pi * t / 52 + seas_phase)
        meta_effect = beta_meta * _saturate(_adstock(meta_spend, decay_meta), k_meta)
        google_effect = beta_google * _saturate(_adstock(google_spend, decay_google), k_google)
        return baseline + meta_effect + google_effect

    def fit(self, meta_spend, google_spend, messages):
        t = np.arange(len(messages))
        meta_spend = np.asarray(meta_spend, dtype=float)
        google_spend = np.asarray(google_spend, dtype=float)
        messages = np.asarray(messages, dtype=float)

        def loss(p):
            pred = self._predict_raw(p, meta_spend, google_spend, t)
            return np.mean((pred - messages) ** 2)

        x0 = [messages.mean(), 0.0, 1.0, 0.0, 0.3, 2000, 50, 0.3, 2000, 50]
        bounds = [
            (0, None), (-5, 5), (0, 50), (-np.pi, np.pi),
            (0, 0.9), (1, 1e5), (0, 1000),
            (0, 0.9), (1, 1e5), (0, 1000),
        ]
        res = minimize(loss, x0, bounds=bounds, method="L-BFGS-B")
        self.params = res.x
        # guardamos el historial de gasto de entrenamiento: hace falta para que el
        # adstock de las semanas futuras "recuerde" el gasto reciente, en vez de
        # arrancar de cero en la primera semana simulada.
        self._fit_meta_spend = meta_spend
        self._fit_google_spend = google_spend
        self._fit_len = len(messages)
        return self

    def predict_insample(self):
        """Predicción sobre las mismas semanas usadas para entrenar."""
        t = np.arange(self._fit_len)
        return self._predict_raw(self.params, self._fit_meta_spend, self._fit_google_spend, t)

    def predict_future(self, meta_spend_future, google_spend_future):
        """
        Predicción para semanas nuevas, continuando el efecto retardado (adstock)
        del gasto histórico con el que se entrenó el modelo.
        """
        meta_spend_future = np.asarray(meta_spend_future, dtype=float)
        google_spend_future = np.asarray(google_spend_future, dtype=float)
        meta_full = np.concatenate([self._fit_meta_spend, meta_spend_future])
        google_full = np.concatenate([self._fit_google_spend, google_spend_future])
        t_full = np.arange(len(meta_full))
        pred_full = self._predict_raw(self.params, meta_full, google_full, t_full)
        return pred_full[self._fit_len:]
