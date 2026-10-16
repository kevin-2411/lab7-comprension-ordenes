# Datos

`ordenes_ejemplo.json` incluye las cinco órdenes de niveles del código original.
Las referencias son propuestas para probar la evaluación; el equipo debe revisarlas.
No son las 150 muestras de desarrollo ni las 30 grabaciones solicitadas.
En particular, "me alcanzas" se anota como "alcanzar" en esta propuesta.
No se incluye "dejé" como acción dirigida al robot.

Para agregar sus datos, usen una lista JSON de registros con `id` único,
`orden` y, para evaluar acierto, `referencia`. `nivel` permite evaluar robustez.
También se admiten listas de cadenas sin anotación, pero no producen F1.
La anotación de referencia nunca se incluye en el prompt del modelo.

No cambien el nombre de un archivo de resultados de Q8 y lo presenten como
datos de referencia. Predicciones, referencias y configuración son elementos distintos.
Este proyecto conserva Transformers FP32 en CPU, no una configuración GGUF Q8.
