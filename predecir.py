"""Entrada única del sistema: texto, archivo JSON o audios."""
import argparse
import sys
from pathlib import Path
from sistema import Sistema, MODELOS, EXTENSIONES, guardar_json, leer_ordenes

def crear_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--texto", help="Una orden escrita entre comillas.")
    grupo.add_argument("--entrada", type=Path, help="Archivo JSON, audio o carpeta de audios.")
    parser.add_argument("--salida", required=True, type=Path)
    parser.add_argument("--modelo", choices=MODELOS, default="qwen15")
    parser.add_argument("--dispositivo", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--whisper", choices=["tiny", "small"], default="tiny")
    parser.add_argument("--prompt", choices=["zero", "fewshot"], default="fewshot")
    parser.add_argument("--offline", action="store_true", help="Usar exclusivamente modelos descargados.")
    parser.add_argument("--sin-voz", action="store_true", help="No generar WAV para entradas de audio.")
    return parser

def main(argv=None, fabrica=Sistema):
    parser = crear_parser()
    args = parser.parse_args(argv)
    audios = False
    try:
        if args.texto is not None:
            if not args.texto.strip():
                raise ValueError("La orden no puede estar vacía.")
            entradas = [{"id": "orden_001", "orden": args.texto}]
        elif not args.entrada.exists():
            raise ValueError(f"No existe la entrada: {args.entrada}")
        elif args.entrada.is_file() and args.entrada.suffix.lower() == ".json":
            entradas = leer_ordenes(args.entrada)
        else:
            rutas = sorted(args.entrada.iterdir()) if args.entrada.is_dir() else [args.entrada]
            rutas = [r for r in rutas if r.is_file() and r.suffix.lower() in EXTENSIONES]
            if not rutas:
                raise ValueError("No se encontraron audios compatibles en la entrada.")
            audios = True
            entradas = [{"id": f"orden_{i:03d}", "archivo": str(r)} for i, r in enumerate(rutas, 1)]
        fuentes = [args.entrada] if args.entrada is not None and args.entrada.is_file() else []
        if audios:
            fuentes.extend(Path(e["archivo"]) for e in entradas)
        if any(args.salida.resolve() == p.resolve() for p in fuentes):
            raise ValueError("La salida debe ser distinta de los archivos de entrada.")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

    sistema = fabrica(modelo=args.modelo, dispositivo=args.dispositivo, whisper=args.whisper,
                      prompt=args.prompt, offline=args.offline)
    resultados = []
    errores = 0
    try:
        if audios:
            sistema.preparar_audio(sin_voz=args.sin_voz)
        for entrada in entradas:
            print(f"Procesando {entrada['id']}...", file=sys.stderr)
            try:
                if audios:
                    destino = None if args.sin_voz else args.salida.parent / "respuestas_audio" / (entrada["id"] + ".wav")
                    pred = sistema.procesar_audio(entrada["archivo"], destino)
                else:
                    pred = sistema.comprender(entrada["orden"])
                pred.update(sistema.memoria())
                pred.update(id=entrada["id"], modelo=args.modelo, dispositivo=args.dispositivo, prompt=args.prompt)
                if audios:
                    pred["archivo_entrada"] = entrada["archivo"]
            except Exception as exc:
                errores += 1
                pred = {"id": entrada["id"], "error_ejecucion": str(exc), "json_valido": False}
            resultados.append(pred)
            guardar_json(args.salida, resultados)
    finally:
        sistema.cerrar()
    print(f"Guardadas {len(resultados)} predicciones en {args.salida}")
    return 1 if errores else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
