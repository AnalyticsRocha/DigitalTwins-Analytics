"""
Backtesting: la metodología que quedó definida en la propuesta.

Se entrena el modelo con las primeras N semanas y se le pide proyectar las
siguientes; se compara contra lo que "realmente" pasó (en el prototipo, los
datos sintéticos hacen de realidad). El resultado es un margen de error que
sirve de criterio de madurez antes de confiar en el modelo para decisiones.
"""
import numpy as np
from mmm_model import CampaignTwin


def run_backtest(df, holdout_weeks=12):
    train = df.iloc[:-holdout_weeks]
    holdout = df.iloc[-holdout_weeks:]

    model = CampaignTwin().fit(
        train.meta_spend.values, train.google_spend.values, train.messages.values
    )

    pred_holdout = model.predict_future(holdout.meta_spend.values, holdout.google_spend.values)
    actual_holdout = holdout.messages.values

    mape = np.mean(np.abs((actual_holdout - pred_holdout) / actual_holdout)) * 100
    residuals = actual_holdout - pred_holdout  # para el intervalo de confianza en simulate.py

    return {
        "model": model,
        "mape": mape,
        "actual_holdout": actual_holdout,
        "pred_holdout": pred_holdout,
        "residuals": residuals,
        "holdout_weeks": holdout.week_start.values,
    }


if __name__ == "__main__":
    from synthetic_data import generate
    df = generate()
    result = run_backtest(df)
    print(f"Margen de error (MAPE) en backtesting: {result['mape']:.1f}%")
    print("\nReal vs. predicho (últimas semanas del holdout):")
    for wk, a, p in list(zip(result["holdout_weeks"], result["actual_holdout"], result["pred_holdout"]))[-5:]:
        print(f"  {str(wk)[:10]}  real={a:.0f}  predicho={p:.1f}")
