"""Comparar Whisper Tiny y Small sobre una grabación real."""
import argparse
import gc
import re
import time
from pathlib import Path
from sistema import guardar_json

def normalizar(texto):
    return " ".join(re.sub(r"[^\w\s]", "", texto.casefold()).split())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--referencia", required=True, help="Transcripción literal del audio.")
    parser.add_argument("--salida", type=Path, default=Path("resultados/comparacion_whisper.json"))
    parser.add_argument("--dispositivo", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if not args.audio.is_file() or not normalizar(args.referencia):
        parser.error("Se necesita un audio existente y una referencia no vacía.")
    from faster_whisper import WhisperModel
    from jiwer import wer
    resultados = []
    for tamano in ("tiny", "small"):
        modelo = WhisperModel(tamano, device=args.dispositivo,
                              compute_type="int8" if args.dispositivo == "cpu" else "float16",
                              local_files_only=args.offline)
        # Misma grabación para calentamiento, fuera de la medición.
        segmentos, _ = modelo.transcribe(str(args.audio), language="es", beam_size=5)
        list(segmentos)
        inicio = time.perf_counter()
        segmentos, _ = modelo.transcribe(str(args.audio), language="es", beam_size=5)
        texto = " ".join(s.text.strip() for s in segmentos).strip()
        tiempo = time.perf_counter() - inicio
        resultados.append({"whisper": tamano, "dispositivo": args.dispositivo,
                           "transcripcion": texto, "latencia_s2t_s": tiempo,
                           "WER_pct": 100 * wer(normalizar(args.referencia), normalizar(texto))})
        guardar_json(args.salida, {"referencia": args.referencia, "resultados": resultados})
        del modelo
        gc.collect()
    print(resultados)

if __name__ == "__main__":
    main()
