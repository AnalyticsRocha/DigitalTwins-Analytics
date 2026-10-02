# Contrato de datos — Digital Twin de Campañas

Esto es lo único que el motor de simulación necesita recibir del Hub. Mientras no haya
acceso al código del Hub, el prototipo usa datos sintéticos que respetan exactamente
este formato — el día que se conecte el dato real, no hace falta tocar el modelo,
solo alimentar un CSV/dataframe con estas columnas.

## Formato esperado: una fila por semana y por cliente

| columna          | tipo   | descripción                                                   |
|-------------------|--------|----------------------------------------------------------------|
| `client_id`        | string | identificador del cliente (para el futuro modelo jerárquico)   |
| `week_start`        | date   | lunes de la semana (ISO `YYYY-MM-DD`)                           |
| `meta_spend`        | float  | gasto semanal en Meta Ads ($)                                   |
| `google_spend`      | float  | gasto semanal en Google Ads ($)                                 |
| `messages`          | int    | mensajes/conversaciones iniciadas (click-to-message, leads form)|
| `leads`             | int    | leads calificados generados esa semana                         |
| `conversions`       | int    | conversiones (ventas) atribuidas esa semana                    |

## Supuestos de este prototipo

- Mínimo recomendado: **~2 años de historial semanal** por cliente (104 filas), en línea
  con el piso de datos que se definió para el modelo estadístico completo.
- El modelo no necesita nada más del Hub por ahora — sin audiencia ni creatividades
  todavía. Eso queda para una fase posterior (Fase 5 — Expansión, según el roadmap).
- Cuando haya más de un cliente, el mismo contrato sirve fila a fila; ahí es donde entra
  el modelo jerárquico (clientes con poco historial piden prestado patrón de los que
  tienen más).
