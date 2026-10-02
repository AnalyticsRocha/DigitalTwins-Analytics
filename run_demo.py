"""
Corre el pipeline completo del prototipo: genera datos sintéticos (hasta tener
acceso al Hub real), entrena el modelo, valida con backtesting, simula un cambio
de presupuesto, y guarda un gráfico de resultado.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from synthetic_data import generate
from backtest import run_backtest
from simulate import simulate_budget_change

ACCENT = "#F97316"
BG = "#111110"
CARD = "#1B1A17"
GRID = "#2A2822"
TEXT = "#F5F3EE"
MUTED = "#A8A49B"

df = generate()
print(f"Datos sintéticos: {len(df)} semanas, cliente '{df.client_id.iloc[0]}'\n")

bt = run_backtest(df, holdout_weeks=12)
print(f"Backtesting — margen de error (MAPE): {bt['mape']:.1f}%")
print("(con datos reales del Hub este número va a ser más alto; sirve de piso de referencia)\n")

model, residuals = bt["model"], bt["residuals"]
last_meta = df.meta_spend.tail(4).mean()
last_google = df.google_spend.tail(4).mean()
budget_pct = 15
weeks_ahead = 4
sim = simulate_budget_change(model, last_meta, last_google, budget_pct,
                              weeks_ahead=weeks_ahead, residuals=residuals)

conv_total = sim["conversions"].sum()
lo = sim["band"]["conversions_lower"].sum()
hi = sim["band"]["conversions_upper"].sum()
print(f"Simulación what-if — presupuesto {budget_pct:+d}%:")
print(f"  conversiones proyectadas ({weeks_ahead} semanas): {conv_total:.0f}  (rango 90%: {lo:.0f}–{hi:.0f})\n")

# ---------- gráfico ----------
history = df.messages.values
history_weeks = np.arange(len(history))
future_weeks = np.arange(len(history), len(history) + weeks_ahead)

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(CARD)

ax.plot(history_weeks, history, color=ACCENT, linewidth=2, label="Real (histórico)")
ax.plot(
    np.concatenate([[history_weeks[-1]], future_weeks]),
    np.concatenate([[history[-1]], sim["messages"]]),
    color=ACCENT, linewidth=2, linestyle="--", label=f"Simulado ({budget_pct:+d}% presupuesto)",
)
ax.fill_between(
    future_weeks, sim["band"]["messages_lower"], sim["band"]["messages_upper"],
    color=ACCENT, alpha=0.18, label="Rango de confianza (90%)",
)
ax.axvline(history_weeks[-1], color=MUTED, linestyle=":", linewidth=1)
ax.text(history_weeks[-1], ax.get_ylim()[1], "Hoy", color=MUTED, fontsize=9, ha="center", va="bottom")

ax.set_title("Mensajes semanales — real vs. simulado", color=TEXT, fontsize=13, pad=14)
ax.set_xlabel("Semana", color=MUTED)
ax.set_ylabel("Mensajes", color=MUTED)
ax.tick_params(colors=MUTED)
for spine in ax.spines.values():
    spine.set_color(GRID)
ax.grid(color=GRID, linewidth=0.5)
legend = ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=9)

fig.tight_layout()
fig.savefig("/home/claude/digital-twin-prototype/backtest_simulation.png", dpi=150, facecolor=BG)
print("Gráfico guardado: backtest_simulation.png")
