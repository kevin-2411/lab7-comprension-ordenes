"""Motor del laboratorio. No descarga ni carga modelos al importar el módulo."""
import gc
import json
import os
import re
import time
import wave
from pathlib import Path
from prompts import PROMPT_SISTEMA, PROMPT_FEWSHOT

MODELOS = {
    "qwen05": "Qwen/Qwen2.5-0.5B-Instruct",
    "qwen15": "Qwen/Qwen2.5-1.5B-Instruct",
    "smollm17": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
}
VOZ_REPO = "rhasspy/piper-voices"
VOZ_BASE = "es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"
EXTENSIONES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".aac"}

def cumple_esquema(data):
    if not isinstance(data, dict) or set(data) != {"acciones"}:
        return False
    if not isinstance(data["acciones"], list):
        return False
    for accion in data["acciones"]:
        if not isinstance(accion, dict) or set(accion) != {
            "accion", "objetos", "personas", "lugares"
        }:
            return False
        if not isinstance(accion["accion"], str) or not accion["accion"].strip():
            return False
        for categoria in ("objetos", "personas", "lugares"):
            if not isinstance(accion[categoria], list):
                return False
            for entidad in accion[categoria]:
                if not isinstance(entidad, dict) or set(entidad) != {"nombre", "adjetivos"}:
                    return False
                if not isinstance(entidad["nombre"], str) or not entidad["nombre"].strip():
                    return False
                if not isinstance(entidad["adjetivos"], list) or not all(
                    isinstance(adj, str) for adj in entidad["adjetivos"]
                ):
                    return False
    return True

def interpretar_salida(texto):
    # No se recorta ni repara para mejorar artificialmente JSON válido.
    try:
        data = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return None, "La salida original no es un único JSON válido."
    if not cumple_esquema(data):
        return None, "El JSON no cumple el esquema de acciones y entidades."
    return data, None

def interpretar_para_ejecucion(texto):
    """Acepta un único bloque Markdown; conserva la validez original separada.

    No corrige entidades, JSON incompleto ni texto adicional. json_valido
    continúa midiendo la salida original; json_utilizable mide el contenido
    validado que puede utilizar el pipeline tras retirar solo el envoltorio.
    """
    data, error = interpretar_salida(texto)
    if data is not None:
        return data, True, False, None
    if not isinstance(texto, str):
        return None, False, False, error
    bloque = re.fullmatch(
        r"\s*```(?:json)?\s*\n([\s\S]*?)\n\s*```\s*",
        texto, flags=re.IGNORECASE,
    )
    if bloque:
        candidato, _ = interpretar_salida(bloque.group(1).strip())
        if candidato is not None:
            return candidato, False, True, error
    return None, False, False, error

def describir(entidades):
    return " y ".join(
        " ".join([e["nombre"]] + e["adjetivos"]) for e in entidades
    )

def detectar_referentes_sin_resolver(data):
    """Detecta etiquetas pronominales; no adivina ni sustituye referentes.

    Si había antecedente pero el modelo dejó un pronombre en vez de resolverlo,
    se pide aclaración igualmente. Las acciones originales quedan intactas.
    """
    problemas = []
    if data is None:
        return problemas
    demostrativos = {"eso", "esto", "aquello", "ese", "esa", "esos", "esas",
                     "este", "esta", "estos", "estas", "aquel", "aquella",
                     "aquellos", "aquellas"}
    for indice, accion in enumerate(data["acciones"]):
        for entidad in accion["objetos"]:
            nombre = " ".join(entidad["nombre"].casefold().split())
            if nombre in demostrativos:
                problemas.append({"indice_accion": indice, "categoria": "objetos",
                                  "nombre": entidad["nombre"],
                                  "motivo": "El modelo devolvió un pronombre sin identificar el objeto."})
    return problemas

def generar_respuesta_robot(data):
    if data is None:
        return "No pude interpretar la orden. ¿Puedes repetirla?"
    if detectar_referentes_sin_resolver(data):
        return "¿A qué objeto te refieres? Dime su nombre, por favor."
    if not data["acciones"]:
        return "No identifiqué una instrucción para el robot."
    partes = []
    for acc in data["acciones"]:
        verbo = acc["accion"]
        if verbo in {"traer", "llevar", "buscar", "tomar", "entregar", "poner", "alcanzar"} and not acc["objetos"]:
            return f"¿Qué objeto quieres que utilice para {verbo}?"
        if verbo == "ir" and not acc["lugares"]:
            return "¿A qué lugar quieres que vaya?"
        if verbo in {"saludar", "acompañar", "recibir", "avisar"} and not acc["personas"]:
            return f"¿A qué persona quieres que me dirija para {verbo}?"
        frase = f"Voy a {verbo}"
        if acc["objetos"]:
            frase += " " + describir(acc["objetos"])
        if acc["lugares"]:
            preposicion = " en " if verbo in {"poner", "buscar", "tomar"} else " a "
            frase += preposicion + describir(acc["lugares"])
        if acc["personas"]:
            frase += " a " + describir(acc["personas"])
        partes.append(frase)
    return ". Luego, ".join(partes) + "."

def guardar_json(ruta, data):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Escritura atómica para conservar el último avance completo.
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(ruta)

def leer_ordenes(ruta):
    data = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("ordenes")
    if not isinstance(data, list) or not data:
        raise ValueError("La entrada debe ser una lista no vacía o un objeto con una lista 'ordenes'.")
    resultado = []
    ids = set()
    for numero, item in enumerate(data, 1):
        if isinstance(item, str):
            item = {"orden": item}
        if not isinstance(item, dict) or not isinstance(item.get("orden"), str) or not item["orden"].strip():
            raise ValueError(f"Orden {numero}: falta el campo de texto 'orden'.")
        item = dict(item)
        item.setdefault("id", f"orden_{numero:03d}")
        if not isinstance(item["id"], str) or item["id"] in ids:
            raise ValueError(f"Orden {numero}: id inválido o duplicado.")
        ids.add(item["id"])
        if "referencia" in item and not cumple_esquema(item["referencia"]):
            raise ValueError(f"Orden {numero}: referencia con esquema inválido.")
        resultado.append(item)
    return resultado

class Sistema:
    def __init__(self, modelo="qwen05", dispositivo="cpu", whisper="tiny", prompt="zero", offline=False):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        self.torch = torch
        if dispositivo == "cuda" and not torch.cuda.is_available():
            raise ValueError("No hay GPU CUDA disponible. Usa --dispositivo cpu.")
        self.dispositivo = dispositivo
        self.identificador = MODELOS[modelo]
        self.offline = offline
        self.tamano_whisper = whisper
        self.prompt = PROMPT_FEWSHOT if prompt == "fewshot" else PROMPT_SISTEMA
        self.whisper = None
        self.voz = None
        self.tokenizer = AutoTokenizer.from_pretrained(self.identificador, local_files_only=offline)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.identificador,
            torch_dtype=torch.float16 if dispositivo == "cuda" else torch.float32,
            low_cpu_mem_usage=True,
            local_files_only=offline,
        ).to(dispositivo)
        self.model.eval()

    def sincronizar(self):
        if self.dispositivo == "cuda":
            self.torch.cuda.synchronize()

    def comprender(self, orden):
        mensajes = [{"role": "system", "content": self.prompt},
                    {"role": "user", "content": f"Orden: {orden}"}]
        prompt = self.tokenizer.apply_chat_template(mensajes, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.dispositivo)
        self.sincronizar()
        inicio = time.perf_counter()
        with self.torch.inference_mode():
            salida = self.model.generate(
                **inputs, max_new_tokens=350, do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        self.sincronizar()
        latencia = time.perf_counter() - inicio
        raw = self.tokenizer.decode(salida[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        data, valido_original, markdown_retirado, error = interpretar_para_ejecucion(raw)
        problemas_referentes = detectar_referentes_sin_resolver(data)
        requiere_aclaracion = bool(problemas_referentes)
        if data is not None:
            requiere_aclaracion = requiere_aclaracion or any(
                (a["accion"] in {"traer", "llevar", "buscar", "tomar", "entregar", "poner", "alcanzar"} and not a["objetos"])
                or (a["accion"] == "ir" and not a["lugares"])
                or (a["accion"] in {"saludar", "acompañar", "recibir", "avisar"} and not a["personas"])
                for a in data["acciones"]
            )
        return {"transcripcion": orden,
                "acciones": data["acciones"] if data is not None else [],
                "acciones_ejecutables": data["acciones"] if data is not None and not requiere_aclaracion else [],
                "requiere_aclaracion": requiere_aclaracion,
                "referentes_sin_resolver": problemas_referentes,
                "respuesta": generar_respuesta_robot(data),
                "json_valido": valido_original,
                "json_utilizable": data is not None,
                "markdown_retirado": markdown_retirado,
                "salida_original": raw, "error_formato": error,
                "latencia_llm_s": latencia}

    def preparar_audio(self, sin_voz=False):
        # Las cargas se hacen antes de medir el pipeline.
        if self.whisper is None:
            from faster_whisper import WhisperModel
            self.whisper = WhisperModel(
                self.tamano_whisper, device=self.dispositivo,
                compute_type="float16" if self.dispositivo == "cuda" else "int8",
                local_files_only=self.offline,
            )
        if self.voz is None and not sin_voz:
            from huggingface_hub import hf_hub_download
            from piper import PiperVoice
            modelo = hf_hub_download(VOZ_REPO, VOZ_BASE, local_files_only=self.offline)
            config = hf_hub_download(VOZ_REPO, VOZ_BASE + ".json", local_files_only=self.offline)
            self.voz = PiperVoice.load(modelo, config_path=config)

    def procesar_audio(self, ruta, salida_voz=None):
        if self.whisper is None or (salida_voz is not None and self.voz is None):
            self.preparar_audio(sin_voz=salida_voz is None)
        inicio_total = time.perf_counter()
        inicio = time.perf_counter()
        segmentos, _ = self.whisper.transcribe(str(ruta), language="es", beam_size=5)
        texto = " ".join(s.text.strip() for s in segmentos).strip()
        tiempo_s2t = time.perf_counter() - inicio
        resultado = self.comprender(texto)
        tiempo_t2s = 0.0
        if salida_voz is not None:
            salida_voz = Path(salida_voz)
            salida_voz.parent.mkdir(parents=True, exist_ok=True)
            inicio = time.perf_counter()
            with wave.open(str(salida_voz), "wb") as archivo:
                self.voz.synthesize_wav(resultado["respuesta"], archivo)
            tiempo_t2s = time.perf_counter() - inicio
        resultado.update(latencia_s2t_s=tiempo_s2t, latencia_t2s_s=tiempo_t2s,
                         latencia_total_s=time.perf_counter() - inicio_total,
                         audio_respuesta=str(salida_voz) if salida_voz is not None else None)
        return resultado

    def memoria(self):
        import psutil
        return {"ram_actual_proceso_gib": psutil.Process(os.getpid()).memory_info().rss / 1024**3,
                "vram_actual_torch_gib": self.torch.cuda.memory_allocated() / 1024**3
                if self.dispositivo == "cuda" else 0.0}

    def cerrar(self):
        self.model = self.tokenizer = self.whisper = self.voz = None
        gc.collect()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
