"""Métricas propuestas; no sustituyen un evaluador oficial del curso."""
from collections import Counter

CATEGORIAS = ("acciones", "objetos", "personas", "adjetivos", "lugares")

def normalizar(texto):
    import unicodedata
    return " ".join(unicodedata.normalize("NFC", texto).casefold().split())

def extraer(data):
    cat = {c: Counter() for c in CATEGORIAS}
    estructura = Counter()
    for indice, acc in enumerate(data["acciones"]):
        verbo = normalizar(acc["accion"])
        cat["acciones"][verbo] += 1
        for categoria in ("objetos", "personas", "lugares"):
            for entidad in acc[categoria]:
                nombre = normalizar(entidad["nombre"])
                estructura[(indice, verbo, categoria, nombre)] += 1
                cat[categoria][nombre] += 1
                for adj in entidad["adjetivos"]:
                    adj = normalizar(adj)
                    cat["adjetivos"][adj] += 1
                    estructura[(indice, verbo, categoria, nombre, adj)] += 1
    return cat, estructura

def conteos(real, pred):
    return (sum((real & pred).values()), sum((pred - real).values()), sum((real - pred).values()))

def f1(valores):
    tp, fp, fn = valores
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None

def evaluar(pares):
    # Acumular por muestra evita que una entidad predicha en otra orden cuente como acierto.
    totales = {c: [0, 0, 0] for c in CATEGORIAS}
    relaciones = [0, 0, 0]
    exactos = 0
    for real, pred in pares:
        cat_real, est_real = extraer(real)
        cat_pred, est_pred = extraer(pred)
        for categoria in CATEGORIAS:
            totales[categoria] = [a + b for a, b in zip(totales[categoria], conteos(cat_real[categoria], cat_pred[categoria]))]
        relaciones = [a + b for a, b in zip(relaciones, conteos(est_real, est_pred))]
        exactos += real == pred
    categorias = {f"F1_{c}": f1(totales[c]) for c in CATEGORIAS}
    presentes = [v for v in categorias.values() if v is not None]
    tp, fp, fn = relaciones
    return {**categorias,
            "F1_promedio": sum(presentes) / len(presentes) if presentes else None,
            "estructura_recall_pct": 100 * tp / (tp + fn) if tp + fn else None,
            "estructura_precision_pct": 100 * tp / (tp + fp) if tp + fp else None,
            "coincidencia_exacta_pct": 100 * exactos / len(pares) if pares else None}
