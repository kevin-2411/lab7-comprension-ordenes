# Laboratorio 7 · Comprensión de órdenes en español para robots

Sistema en Python que interpreta órdenes escritas o grabadas y devuelve JSON
con acciones, objetos, personas, adjetivos y lugares. Con audio integra:
**Whisper → LLM → respuesta por plantillas → Piper**.

## Configuración y evidencia incluidas

Se probó en **Windows, CMD, Python 3.11.9, CPU**, con
**Qwen2.5-1.5B-Instruct, prompt few-shot, Whisper Tiny y Piper en español**.
Se conservaron los archivos reales del equipo en `audios/` y `resultados/`.
La respuesta hablada fue escuchada y confirmada por el usuario.

Los comandos de predicción y preparación usan ahora **`qwen15` y `fewshot`**
como opciones predeterminadas, de acuerdo con esas pruebas. `evaluar.py`
conserva `zero` como prompt predeterminado para la comparación; especifíquelo.
Las funciones y los modelos son los mismos probados: no se introdujo otra
configuración de inferencia al preparar esta revisión.

**Alcance de la verificación:** pruebas funcionales de órdenes simples,
compuestas, ambiguas y una grabación; no es una evaluación exhaustiva.
Las latencias siguen siendo altas. La carpeta no incluye las 150 órdenes
propias, las 30 grabaciones ni el informe final; esos elementos y los
resultados de otras configuraciones se deben incorporar cuando estén listos.
No se ejecutan acciones en un robot físico.

## 1. Instalar en Windows

1. Instalar Python 3.11 de 64 bits. Si ya se dispone del administrador de
   instalación de Python, se puede usar `py install 3.11`.
2. Descomprimir el proyecto. Abrir la carpeta que contiene `predecir.py`.
3. En el Explorador, presionar **Ctrl + L**, escribir `cmd` y pulsar Enter.
4. Ejecutar los siguientes comandos uno por uno:

```bat
py -3.11 --version
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -c requirements-windows.txt
```

`requirements-windows.txt` contiene las versiones exactas que el equipo
registró después de instalar y probar el sistema. Se usa como archivo de
restricciones para reproducirlas con Python 3.11. Las versiones se
conservaron tal como fueron proporcionadas; esta revisión no repitió su
instalación en otro computador.

`requirements.txt` conserva los rangos de dependencias del proyecto. Para
otros sistemas operativos, partir de esos rangos y validar el nuevo entorno.
No se ha verificado aquí una instalación en Linux ni en macOS.

### Si ya lo estabas usando

No reinstalar Python ni las librerías por esta actualización. Copiar los
archivos revisados a la carpeta de trabajo y conservar `.venv`, los audios,
los resultados y la caché de modelos. Volver a ejecutar las pruebas de lógica.
Para retomar una sesión en CMD solo se necesita abrir la carpeta y activar:

```bat
.venv\Scripts\activate
```

## 2. Comprobar el código y descargar los modelos

Pruebas de lógica, JSON e interfaz; no descargan ni ejecutan un LLM:

```bat
python -m unittest discover -s tests -v
```

La versión que probó el equipo pasó siete pruebas en Windows. Esta revisión
agrega tres comprobaciones de Markdown y referentes sin resolver; se
comprobaron diez pruebas en el entorno de revisión, sin pesos de modelos.
El mensaje «La salida debe ser distinta de los archivos de entrada» es
esperado en la prueba que verifica que no se sobrescriba un archivo de entrada.
El resultado global debe terminar en `OK`.

Con internet, descargar el LLM principal y los componentes de audio:

```bat
python preparar_modelos.py --modelo qwen15 --audio
```

Esperar a «Descargas terminadas». Esta preparación descarga también Whisper
Small para la comparación de S2T. Los pesos quedan en la caché local del
usuario de Hugging Face, no dentro del repositorio. Las descargas previas se
reutilizan. La advertencia de enlaces simbólicos en Windows no impide usar
la caché, aunque esta puede ocupar más espacio.

## 3. Ejecutar el sistema

### Una orden escrita

```bat
python predecir.py --texto "Trae el libro verde" --modelo qwen15 --prompt fewshot --salida resultados/nueva_prueba_texto.json --offline
```

Ver el archivo:

```bat
chcp 65001
type resultados\nueva_prueba_texto.json
```

La página de códigos UTF-8 permite ver tildes correctamente en CMD.

### Una grabación: prueba completa

Se incluye la grabación real `audios/audio1.ogg`. El siguiente comando es el
mismo que funcionó en el equipo del usuario, cambiando solo la ruta de salida
para conservar la evidencia anterior:

```bat
python predecir.py --entrada audios/audio1.ogg --modelo qwen15 --prompt fewshot --salida resultados/nueva_prueba_audio.json --offline
```

Ver el JSON y escuchar la respuesta:

```bat
type resultados\nueva_prueba_audio.json
start "" "resultados\respuestas_audio\orden_001.wav"
```

Los WAV se guardan en `respuestas_audio/` al lado del JSON. Al repetir una
prueba en la misma carpeta, los WAV con el mismo nombre se reemplazan.
Usar una carpeta de salida distinta para conservar todos los WAV anteriores.

### Carpeta completa: comando único de ejecución

Después de la instalación y descarga, este comando usa la configuración
probada (Qwen 1.5B, few-shot, Whisper Tiny, CPU y respuesta de Piper):

```bat
python predecir.py --entrada audios/ --salida resultados/lote/predicciones.json --offline
```

También puede usarse la forma de entrega de la guía:

```bat
python predecir.py --entrada audios/ --salida predicciones.json --offline
```

Los archivos que no son audio se omiten. Se admite WAV, MP3, M4A, FLAC,
OGG, WEBM y AAC. Una carpeta vacía produce un error. La lectura de carpetas
no recorre subcarpetas. Los resultados se guardan después de cada entrada.
`--sin-voz` omite únicamente la síntesis de respuesta hablada.

### Varias órdenes escritas

```bat
python predecir.py --entrada datos/ordenes_ejemplo.json --salida resultados/lote_texto.json --offline
```

El formato de entrada se explica en `datos/LEEME.md`. Se admiten listas de
cadenas o registros con `id`, `orden`, `nivel` y `referencia` opcional.
Las anotaciones no se envían al LLM. El formato de archivos de predicciones
no debe confundirse con el de las anotaciones de referencia.

## 4. Entender el JSON

El archivo de salida contiene una **lista** con una predicción por entrada.

| Campo | Significado |
| --- | --- |
| `transcripcion` | Texto escrito o reconocido por Whisper |
| `acciones` | Extracción del LLM después de validar el esquema; conserva errores semánticos del modelo |
| `acciones_ejecutables` | Acciones no bloqueadas por las comprobaciones de información incompleta; no se envían a un robot |
| `requiere_aclaracion` | Se detectó falta de información o un pronombre de objeto sin resolver |
| `referentes_sin_resolver` | Diagnóstico del pronombre devuelto por el modelo |
| `respuesta` | Confirmación o pregunta generada por plantillas |
| `json_valido` | La salida original completa cumple JSON y el esquema |
| `json_utilizable` | Se pudo obtener contenido con esquema válido, incluso retirando un bloque Markdown |
| `markdown_retirado` | Se retiró exclusivamente un bloque Markdown que envolvía la respuesta |
| `salida_original` | Respuesta original del modelo, para análisis |
| `error_formato` | Motivo del rechazo del formato original, aunque se haya recuperado el contenido |
| `latencia_llm_s` | Tiempo de generación del LLM |
| `latencia_s2t_s`, `latencia_t2s_s` | Transcripción y síntesis; solo para audio |
| `latencia_total_s` | Pipeline con audio, sin descargar/cargar modelos ni reproducir el WAV |
| `ram_actual_proceso_gib` | RAM RSS del proceso al tomar la muestra; no es el pico continuo |

Retirar Markdown no convierte `json_valido` en verdadero. Tampoco corrige las
entidades. Si el LLM devuelve `eso` como objeto, se conserva esa predicción,
se marca la aclaración y se bloquean las acciones ejecutables. Si no incluye
un objeto para una acción que lo requiere, la plantilla también pregunta.
Si un referente existía pero el LLM no lo resolvió, el sistema pide aclaración
en vez de adivinarlo. Este control es una validación adicional, no un acierto
atribuible al LLM ni una solución general de todas las ambigüedades.

## 5. Evidencia real y limitaciones

Los JSON originales se conservaron sin modificar. Las pruebas ocurrieron
con distintas versiones de prompts y validación durante el desarrollo; no
son repeticiones de un benchmark uniforme y no deben promediarse como tal.

| Prueba guardada | Observación | Tiempo medido |
| --- | --- | --- |
| `prueba_texto.json` | Qwen 0.5B zero-shot: predijo «trabajar» para «Trae el vaso» | LLM 7,61 s |
| `prueba_nueva.json` | Qwen 0.5B few-shot: omitió «verde» | LLM 10,19 s |
| `prueba_qwen15.json` | Qwen 1.5B: «traer», «libro» y «verde» correctos | LLM 24,16 s |
| `prueba_compuesta.json` | Dos acciones y referente «cuaderno amarillo» correctos | LLM 52,72 s |
| `prueba_ambigua_v3.json` | El LLM dejó «eso»; la validación pidió aclaración | LLM 26,19 s |
| `prueba_audio.json` | Pipeline completo: «traer», «libro» y «verde»; WAV confirmado | Total 34,36 s |

En la prueba de audio, Whisper Tiny produjo «Trá el libro Verde.» y el LLM
extrajo la intención indicada. La RAM actual del proceso fue 6,35 GiB. No es
una medición del pico del sistema. El total de 34,36 s incluyó 0,66 s de S2T,
31,59 s del LLM y 2,09 s de T2S, además del resto del procesamiento.
La latencia observada supera las metas de la guía: queda pendiente optimizar
la ejecución y evaluar de nuevo. Una prueba correcta no garantiza acierto en
órdenes nuevas. No se adjunta aquí una comparación completa de los tres LLM
ni un resultado general de F1 o WER.

`resultados/resumen_pruebas.csv` resume los archivos adjuntos sin crear nuevas
mediciones. Los archivos `prueba_ambigua*` muestran la evolución de las
correcciones, conservando el fallo del modelo para su análisis.

### Q8 y otras implementaciones

Esta entrega ejecuta Transformers: **FP32 para el LLM en CPU** y Whisper INT8.
No es el mismo motor ni la misma cuantización que un modelo GGUF Q8 en Ollama.
No se incorporaron los resultados Q8 de otras pruebas: hacerlo requiere su
código, prompts y datos correspondientes. No presentar estas mediciones como
si fueran resultados de esa configuración.

## 6. Comparaciones adicionales

Modelos disponibles:

| Opción | Modelo |
| --- | --- |
| `qwen15` | `Qwen/Qwen2.5-1.5B-Instruct` |
| `qwen05` | `Qwen/Qwen2.5-0.5B-Instruct` |
| `smollm17` | `HuggingFaceTB/SmolLM2-1.7B-Instruct` |

Descargar los tres antes de comparar:

```bat
python preparar_modelos.py --comparacion --audio
```

Evaluar un conjunto anotado (las cinco órdenes incluidas solo sirven para
demostración; sustituir por el conjunto del equipo):

```bat
python evaluar.py --entrada datos/ordenes_ejemplo.json --salida resultados/comparacion_zero --prompt zero --offline
python evaluar.py --entrada datos/ordenes_ejemplo.json --salida resultados/comparacion_fewshot --prompt fewshot --offline
```

Se generan detalles por modelo, `resumen.csv` y `resumen.json`. No se han
repetido estas comparaciones como parte de la revisión del ZIP.

- F1 acumula TP, FP y FN por orden para cinco categorías, conservando
  repeticiones. Las categorías sin soporte ni predicciones quedan sin definir.
- El F1 promedio es la media de las categorías definidas. Sin `referencia`
  no se puede calcular. Robustez usa solamente niveles 4 y 5 anotados.
- Estructura reporta precisión y recall de relaciones entre acción, entidad y
  adjetivo. Son métricas propuestas, a contrastar con el evaluador del curso.
- Se evalúan `acciones`, no `acciones_ejecutables`, para no ocultar un fallo
  del modelo mediante el bloqueo de ejecución.
- JSON válido mide la salida original. No hay decodificación restringida por
  gramática; el formato se solicita mediante prompt y se valida después.
- La latencia comparativa es del LLM, no del pipeline completo. Se excluyen
  descarga, carga, tokenización y calentamiento.
- La RAM comparativa es el máximo de muestras puntuales del proceso, no el
  pico continuo del sistema. No se da por cumplido el límite de 8 GB.

Algunas de las cinco órdenes coinciden con los ejemplos del prompt. **No usar
esas coincidencias para concluir generalización.** Separar desarrollo y prueba,
ajustar el prompt solo con desarrollo y comparar todos los modelos sobre las
mismas órdenes y el mismo hardware.

Comparar Whisper Tiny y Small sobre la grabación incluida:

```bat
python comparar_whisper.py --audio audios/audio1.ogg --referencia "Trae el libro verde" --salida resultados/comparacion_whisper.json --offline
```

Confirmar que esa es la transcripción literal antes de evaluar WER. Se
normalizan mayúsculas, puntuación y espacios. WER de un solo audio no representa
el rendimiento general. También debe estudiarse la propagación de errores
comparando acciones desde el texto correcto y desde la transcripción.

La demostración opcional de lematización con spaCy se conserva, pero no fue
confirmada durante las pruebas compartidas:

```bat
python -m spacy download es_core_news_sm
python comprobar_spacy.py
```

No está integrada como una corrección automática de las predicciones.

## 7. Solución de problemas

- **Faltan archivos en caché con `--offline`:** conectar internet y repetir
  `python preparar_modelos.py --modelo qwen15 --audio`; esperar a que termine.
- **El JSON no existe:** revisar si el programa falló antes de procesar la
  orden. Un error de carga puede ocurrir antes de crear el archivo.
- **Tildes extrañas en CMD:** ejecutar `chcp 65001` antes de mostrar el JSON.
- **Avisos `torch_dtype` o flags de generación:** aparecieron también en las
  ejecuciones correctas. Conservar el error completo si la ejecución se detiene.
- **Falta `.venv` al descargar el repositorio:** es intencional; cada persona
  crea su propio entorno con las instrucciones de instalación.
- **Desconexión:** la instalación y descarga necesitan internet. `--offline`
  permite inferencia con los modelos ya disponibles en ese usuario y equipo.
- **GPU:** `--dispositivo cuda` es opcional para desarrollo y exige GPU/PyTorch
  compatibles. La configuración probada y las mediciones adjuntas usan CPU.

## 8. Archivos y subida a GitHub

| Archivo o carpeta | Contenido |
| --- | --- |
| `predecir.py` | Comando de entrada para texto y audio |
| `sistema.py` | Comprensión, formato, aclaraciones, Whisper y Piper |
| `prompts.py` | Prompts originales y refuerzo de reglas de ambigüedad |
| `preparar_modelos.py` | Descarga previa de pesos y voz |
| `evaluar.py`, `metricas.py` | Comparación de LLM y métricas |
| `comparar_whisper.py` | Comparación S2T y WER |
| `comprobar_spacy.py` | Demostración de lematización |
| `requirements.txt` | Rangos de dependencias |
| `requirements-windows.txt` | Versiones capturadas del entorno probado |
| `audios/` | Grabación real de prueba |
| `resultados/` | Evidencia, WAV y versiones del entorno |
| `datos/` | Cinco ejemplos y formato de datos |
| `tests/` | Pruebas automáticas sin pesos de modelos |
| `original/` | Código de Colab recibido, para trazabilidad |

Descomprimir el ZIP. En GitHub crear un repositorio y usar la opción de subir
archivos. Arrastrar **el contenido de esta carpeta**, con sus subcarpetas;
`README.md` y `predecir.py` deben quedar en la raíz del repositorio. Guardar
los cambios y comprobar que el profesor tenga acceso. No subir el ZIP como
único archivo ni subir `.venv`, cachés, pesos o tokens de acceso.

Antes de entregar el enlace, ejecutar los comandos documentados desde una
copia limpia. La subida del código por sí sola no prueba su instalación en
otro computador ni completa la evaluación general que falta adjuntar.

## Fuentes de los componentes

- [Qwen 1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
- [Qwen 0.5B](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [SmolLM2 1.7B](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct)
- [Transformers](https://huggingface.co/docs/transformers/)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Piper](https://github.com/OHF-Voice/piper1-gpl)
- [Voces de Piper](https://huggingface.co/rhasspy/piper-voices)
- [spaCy](https://spacy.io/)

Los componentes y pesos conservan sus respectivas licencias; los pesos se
descargan de sus fuentes y no se incluyen en el repositorio. No se asigna una
licencia nueva al código original del equipo.
