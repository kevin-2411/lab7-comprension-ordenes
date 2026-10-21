"""Graba una orden por micrófono y reutiliza el sistema de Lab 7."""
import argparse
import json
import math
import sys
import uuid
import wave
from pathlib import Path


def grabar(ruta, segundos=None, dispositivo=None):
    # Importación diferida: las pruebas y --help no requieren hardware.
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Instala el micrófono con: python -m pip install -r requirements-microfono.txt") from exc
    info = sd.query_devices(dispositivo, kind="input")
    frecuencia = int(info["default_samplerate"])
    sd.check_input_settings(device=dispositivo, channels=1, dtype="int16", samplerate=frecuencia)
    input(f"Micrófono: {info['name']}. Pulsa ENTER para comenzar...")
    if segundos is None:
        bloques, errores = [], []

        def recibir(datos, frames, tiempo, estado):
            if estado:
                errores.append(str(estado))
            # El búfer del callback se reutiliza: conservar una copia en bytes.
            bloques.append(datos.astype("<i2", copy=False).tobytes())

        with sd.InputStream(samplerate=frecuencia, channels=1, dtype="int16",
                            device=dispositivo, callback=recibir):
            print("HABLA AHORA. Pulsa ENTER otra vez para terminar.", flush=True)
            input()
        if errores:
            raise RuntimeError(f"La captura tuvo interrupciones ({'; '.join(errores)}). Intenta de nuevo.")
        audio_pcm = b"".join(bloques)
        if not audio_pcm:
            raise RuntimeError("La grabación está vacía. Vuelve a intentarlo y habla antes del segundo ENTER.")
    else:
        print(f"HABLA AHORA... ({segundos:g} segundos)", flush=True)
        try:
            muestras = sd.rec(round(segundos * frecuencia), samplerate=frecuencia,
                              channels=1, dtype="int16", device=dispositivo)
            estado = sd.wait()
        except BaseException:
            sd.stop()
            raise
        if estado:
            raise RuntimeError(f"La captura tuvo interrupciones ({estado}). Intenta grabar de nuevo.")
        audio_pcm = muestras.astype("<i2", copy=False).tobytes()
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(ruta), "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(frecuencia)
        archivo.writeframes(audio_pcm)
    print("Grabación terminada. Procesando con Whisper y el LLM; espera...", flush=True)


def reproducir(ruta):
    if sys.platform == "win32":
        import winsound
        winsound.PlaySound(str(Path(ruta).resolve()), winsound.SND_FILENAME)
    else:
        import numpy as np
        import sounddevice as sd
        with wave.open(str(ruta), "rb") as archivo:
            if archivo.getsampwidth() != 2:
                raise ValueError("La reproducción requiere un WAV PCM de 16 bits.")
            muestras = np.frombuffer(archivo.readframes(archivo.getnframes()), dtype="<i2")
            sd.play(muestras.reshape(-1, archivo.getnchannels()), archivo.getframerate())
            sd.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duracion", type=float, help="Opcional: grabar de 1 a 60 segundos. Sin esta opción, ENTER inicia y ENTER termina.")
    parser.add_argument("--microfono", type=int, help="Índice del micrófono; por defecto, el de Windows.")
    parser.add_argument("--listar-microfonos", action="store_true")
    parser.add_argument("--salida", type=Path, default=Path("resultados/prueba_microfono.json"))
    parser.add_argument("--modelo", choices=["qwen05", "qwen15", "smollm17"], default="qwen15")
    parser.add_argument("--prompt", choices=["zero", "fewshot"], default="fewshot")
    parser.add_argument("--dispositivo", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--whisper", choices=["tiny", "small"], default="tiny")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--sin-voz", action="store_true", help="Mostrar respuesta sin generar ni reproducir voz.")
    args = parser.parse_args(argv)
    if args.listar_microfonos:
        import sounddevice as sd
        print(sd.query_devices())
        return 0
    if args.duracion is not None and (not math.isfinite(args.duracion) or not 1 <= args.duracion <= 60):
        parser.error("--duracion debe estar entre 1 y 60 segundos.")
    if args.salida.suffix.lower() != ".json":
        parser.error("--salida debe terminar en .json.")
    # Cada captura tiene su propio nombre; se conserva como evidencia de entrada.
    captura = args.salida.parent / "capturas_microfono" / f"microfono_{uuid.uuid4().hex}.wav"
    grabar(captura, args.duracion, args.microfono)
    from predecir import main as predecir
    argumentos = ["--entrada", str(captura), "--salida", str(args.salida),
                  "--modelo", args.modelo, "--prompt", args.prompt,
                  "--dispositivo", args.dispositivo, "--whisper", args.whisper]
    if args.offline:
        argumentos.append("--offline")
    if args.sin_voz:
        argumentos.append("--sin-voz")
    codigo = predecir(argumentos)
    if codigo:
        print(f"No se completó la interpretación. Consulta {args.salida}.", file=sys.stderr)
        return codigo
    resultado = json.loads(args.salida.read_text(encoding="utf-8"))[0]
    print("\nTranscripción:", resultado.get("transcripcion", ""))
    print("Respuesta:", resultado.get("respuesta", ""))
    if not args.sin_voz and resultado.get("audio_respuesta"):
        try:
            reproducir(resultado["audio_respuesta"])
        except Exception as exc:
            print(f"Respuesta guardada, pero no se pudo reproducir: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nGrabación o procesamiento cancelado.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print("Comprueba el micrófono y sus permisos. Para ver dispositivos: python escuchar.py --listar-microfonos", file=sys.stderr)
        raise SystemExit(1)
