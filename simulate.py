"""
La función que el dashboard (el mockup que ya armamos) necesita del lado del motor:
dado un cambio de presupuesto, proyectar mensajes / leads / conversiones futuras,
con una banda de confianza basada en el error histórico medido en el backtest.
"""
import numpy as np


def simulate_budget_change(model, last_meta_spend, last_google_spend, budget_pct,
                            weeks_ahead=4, residuals=None, lead_rate=0.42, conv_rate=0.60,
                            n_bootstrap=500, seed=11):
    """
    model: CampaignTwin ya entrenado.
    last_meta_spend / last_google_spend: gasto semanal promedio reciente (punto de partida).
    budget_pct: cambio de presupuesto a simular, ej. 15 para +15%.
    residuals: residuos del backtest (para construir la banda de confianza por bootstrap).
    """
    factor = 1 + budget_pct / 100
    meta_future = np.full(weeks_ahead, last_meta_spend * factor)
    google_future = np.full(weeks_ahead, last_google_spend * factor)

    messages_point = model.predict_future(meta_future, google_future)
    leads_point = messages_point * lead_rate
    conversions_point = leads_point * conv_rate

    band = None
    if residuals is not None and len(residuals) > 1:
        rng = np.random.default_rng(seed)
        boot = np.empty((n_bootstrap, weeks_ahead))
        for b in range(n_bootstrap):
            noise = rng.choice(residuals, size=weeks_ahead, replace=True)
            boot[b] = messages_point + noise
        lower = np.percentile(boot, 5, axis=0)
        upper = np.percentile(boot, 95, axis=0)
        band = {
            "messages_lower": lower,
            "messages_upper": upper,
            "leads_lower": lower * lead_rate,
            "leads_upper": upper * lead_rate,
            "conversions_lower": lower * lead_rate * conv_rate,
            "conversions_upper": upper * lead_rate * conv_rate,
        }

    return {
        "budget_pct": budget_pct,
        "messages": messages_point,
        "leads": leads_point,
        "conversions": conversions_point,
        "band": band,
    }


if __name__ == "__main__":
    from synthetic_data import generate
    from backtest import run_backtest

    df = generate()
    bt = run_backtest(df)
    model, residuals = bt["model"], bt["residuals"]

    last_meta = df.meta_spend.tail(4).mean()
    last_google = df.google_spend.tail(4).mean()

    for pct in (-15, 0, 15, 30):
        res = simulate_budget_change(model, last_meta, last_google, pct, residuals=residuals)
        conv_total = res["conversions"].sum()
        if res["band"]:
            lo = res["band"]["conversions_lower"].sum()
            hi = res["band"]["conversions_upper"].sum()
            print(f"Presupuesto {pct:+d}%:  conversiones proyectadas (4 semanas) = {conv_total:.0f}  "
                  f"(rango 90%: {lo:.0f}–{hi:.0f})")
        else:
            print(f"Presupuesto {pct:+d}%:  conversiones proyectadas (4 semanas) = {conv_total:.0f}")
