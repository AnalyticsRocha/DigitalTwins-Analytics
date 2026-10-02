"""
Genera datos sintéticos semanales que respetan el contrato de datos (data_contract.md).
Sirve de reemplazo temporal del Hub mientras no hay acceso a los datos reales.

La "verdad" que usamos para generar los datos (decays, saturaciones, coeficientes)
es desconocida para el modelo — el modelo tiene que *descubrirla* a partir de los
datos, igual que pasaría con datos reales del Hub.
"""
import numpy as np
import pandas as pd


def _adstock(spend, decay):
    """Efecto retardado: el impacto de una semana de gasto se extiende a las siguientes."""
    out = np.zeros_like(spend, dtype=float)
    carry = 0.0
    for t, x in enumerate(spend):
        carry = x + decay * carry
        out[t] = carry
    return out


def _saturate(x, k):
    """Rendimientos decrecientes: más gasto rinde cada vez menos."""
    return x / (x + k)


def generate(n_weeks=104, client_id="distribuidora-norte", seed=7):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2024-01-01", periods=n_weeks, freq="W-MON")

    # --- gasto semanal por canal (con algo de variación realista) ---
    meta_spend = 1800 + 400 * np.sin(np.arange(n_weeks) / 6) + rng.normal(0, 150, n_weeks)
    google_spend = 1400 + 300 * np.sin(np.arange(n_weeks) / 8 + 1) + rng.normal(0, 120, n_weeks)
    meta_spend = np.clip(meta_spend, 300, None)
    google_spend = np.clip(google_spend, 300, None)

    # --- "verdad" oculta que el modelo va a tener que redescubrir ---
    true_decay_meta, true_k_meta, true_beta_meta = 0.35, 2200, 95
    true_decay_google, true_k_google, true_beta_google = 0.55, 1600, 70

    meta_effect = true_beta_meta * _saturate(_adstock(meta_spend, true_decay_meta), true_k_meta)
    google_effect = true_beta_google * _saturate(_adstock(google_spend, true_decay_google), true_k_google)

    trend = 0.15 * np.arange(n_weeks)
    seasonality = 8 * np.sin(2 * np.pi * np.arange(n_weeks) / 52)
    baseline = 40 + trend + seasonality

    noise = rng.normal(0, 6, n_weeks)
    messages = np.clip(baseline + meta_effect + google_effect + noise, 5, None)

    # Leads y conversiones como fracciones (con algo de ruido propio) de la etapa anterior
    lead_rate = 0.42 + rng.normal(0, 0.02, n_weeks)
    conv_rate = 0.60 + rng.normal(0, 0.02, n_weeks)
    leads = np.clip(messages * np.clip(lead_rate, 0.2, 0.7), 1, None)
    conversions = np.clip(leads * np.clip(conv_rate, 0.3, 0.9), 0, None)

    df = pd.DataFrame({
        "client_id": client_id,
        "week_start": weeks,
        "meta_spend": meta_spend.round(2),
        "google_spend": google_spend.round(2),
        "messages": messages.round(0).astype(int),
        "leads": leads.round(0).astype(int),
        "conversions": conversions.round(0).astype(int),
    })
    return df


if __name__ == "__main__":
    df = generate()
    print(df.head())
    print(f"\n{len(df)} semanas generadas para '{df.client_id.iloc[0]}'")
