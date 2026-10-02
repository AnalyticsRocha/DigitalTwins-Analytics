# Prototipo — Digital Twin de Campañas (Fase 1 + Fase 2 del roadmap)

Primer paso técnico de la propuesta, construido **sin depender del código del Hub**:
usa datos sintéticos que respetan el contrato de datos (`data_contract.md`), para que
el día que haya acceso real solo haga falta reemplazar `synthetic_data.py` por una
consulta real — el modelo, el backtesting y la simulación no cambian.

## Archivos

- **`data_contract.md`** — el formato de datos que el Hub va a tener que entregar.
- **`synthetic_data.py`** — genera datos de muestra con ese formato (hace de "Hub" temporal).
- **`mmm_model.py`** — el motor: adstock (efecto retardado) + saturación (rendimientos
  decrecientes), ajustado por optimización a partir de los datos.
- **`backtest.py`** — entrena con las primeras semanas, proyecta las últimas, mide el
  margen de error (MAPE) — la validación que se definió en la propuesta.
- **`simulate.py`** — la función what-if: dado un % de cambio de presupuesto, proyecta
  mensajes → leads → conversiones, con una banda de confianza (bootstrap sobre el
  error del backtest).
- **`run_demo.py`** — corre todo de punta a punta y genera el gráfico de resultado.

## Correrlo

```
pip install numpy pandas scipy scikit-learn matplotlib
python3 run_demo.py
```

## Resultado de esta corrida

- Backtesting: **2,7% de margen de error** sobre datos sintéticos (con datos reales va
  a ser más alto — esto es un piso de referencia, no la cifra final).
- Simulación a +15% de presupuesto: conversiones proyectadas a 4 semanas con su rango
  de confianza al 90%.

## Qué NO es todavía este prototipo

- No es el modelo jerárquico multi-cliente que planteamos con PyMC-Marketing — esta es
  la versión liviana para validar que el enfoque (adstock + saturación + backtesting)
  funciona de punta a punta antes de invertir en la versión completa.
- No está conectado al Hub — corre sobre datos sintéticos hasta que haya acceso.
- El gráfico y las funciones (`simulate_budget_change`) están pensados para alimentar
  directamente al dashboard que ya armamos (mismo concepto: real vs. simulado, banda
  de confianza, % de presupuesto como input).

## Próximo paso natural

Una vez haya acceso al Hub: reemplazar `synthetic_data.py` por la consulta real
(mismas columnas del contrato) y volver a correr `backtest.py` — ahí vamos a saber el
margen de error real, que es el número que decide si esto ya está listo para que el
equipo de marketing lo use en decisiones.
