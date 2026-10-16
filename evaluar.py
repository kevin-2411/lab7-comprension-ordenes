"""Comparar tres LLM sobre las mismas órdenes escritas."""
import argparse
import csv
import statistics
from pathlib import Path
from sistema import Sistema, MODELOS, leer_ordenes, guardar_json
from metricas import evaluar

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--salida", type=Path, default=Path("resultados/comparacion_llm"))
    parser.add_argument("--modelos", choices=MODELOS, nargs="+", default=list(MODELOS))
    parser.add_argument("--dispositivo", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--prompt", choices=["zero", "fewshot"], default="zero")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    ordenes = leer_ordenes(args.entrada)
    args.salida.mkdir(parents=True, exist_ok=True)
    resumen = []
    for nombre in args.modelos:
        sistema = Sistema(nombre, args.dispositivo, prompt=args.prompt, offline=args.offline)
        registros = []
        try:
            # Calentamiento excluido; descarga y carga también quedan fuera.
            sistema.comprender("Trae la pelota")
            for orden in ordenes:
                print(f"{nombre}: {orden['id']}", flush=True)
                pred = sistema.comprender(orden["orden"])
                registros.append({**orden, "prediccion": pred, **sistema.memoria()})
                guardar_json(args.salida / f"{nombre}_detalle.json", registros)
        finally:
            sistema.cerrar()
        anotados = [r for r in registros if "referencia" in r]
        def pares(subconjunto):
            return [(r["referencia"], {"acciones": r["prediccion"]["acciones"]}) for r in subconjunto]
        fila = {"modelo": nombre, "dispositivo": args.dispositivo, "prompt": args.prompt,
                "n_ordenes": len(registros), "n_con_referencia": len(anotados),
                "latencia_llm_mediana_s": statistics.median(r["prediccion"]["latencia_llm_s"] for r in registros),
                "ram_actual_max_muestras_gib": max(r["ram_actual_proceso_gib"] for r in registros),
                "json_valido_pct": 100 * sum(r["prediccion"]["json_valido"] for r in registros) / len(registros),
                **evaluar(pares(anotados))}
        robustos = [r for r in anotados if r.get("nivel") in (4, 5)]
        fila["F1_niveles_4_5"] = evaluar(pares(robustos))["F1_promedio"]
        resumen.append(fila)
        guardar_json(args.salida / "resumen.json", resumen)
        with (args.salida / "resumen.csv").open("w", encoding="utf-8", newline="") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=list(fila))
            writer.writeheader()
            writer.writerows(resumen)
    for fila in resumen:
        print(fila)

if __name__ == "__main__":
    main()
