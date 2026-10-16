"""Comprobaciones sin internet ni pesos de modelos."""
import json
import tempfile
import unittest
from pathlib import Path
from sistema import (interpretar_salida, generar_respuesta_robot, leer_ordenes,
                     interpretar_para_ejecucion, detectar_referentes_sin_resolver)
from metricas import evaluar
from predecir import main

def referencia(objeto="taza", adj="roja"):
    return {"acciones": [{"accion": "traer", "objetos": [{"nombre": objeto, "adjetivos": [adj]}], "personas": [], "lugares": []}]}

class MotorSimulado:
    def __init__(self, **kwargs): pass
    def comprender(self, texto):
        return {"transcripcion": texto, "acciones": [], "json_valido": True}
    def memoria(self): return {}
    def cerrar(self): pass

class Pruebas(unittest.TestCase):
    def test_rechaza_texto_extra_y_esquema_incompleto(self):
        for raw in ('Explicación {"acciones":[]}', '{"acciones":[{"accion":"traer"}]}', '[]', '{"acciones":"traer"}'):
            self.assertIsNone(interpretar_salida(raw)[0])
        self.assertEqual(interpretar_salida('{"acciones":[]}')[0], {"acciones": []})

    def test_ambiguedad_pide_aclarar(self):
        data = {"acciones": [{"accion": "traer", "objetos": [], "personas": [], "lugares": []}]}
        self.assertIn("¿Qué objeto", generar_respuesta_robot(data))

    def test_no_cruza_aciertos_entre_ordenes(self):
        a, b = referencia("taza"), referencia("libro")
        self.assertEqual(evaluar([(a, b), (b, a)])["F1_objetos"], 0)
        self.assertEqual(evaluar([(a, a)])["F1_promedio"], 1)

    def test_mala_asociacion_adjetivo_penaliza_estructura(self):
        real = referencia()
        real["acciones"][0]["objetos"].append({"nombre": "libro", "adjetivos": ["azul"]})
        pred = json.loads(json.dumps(real))
        pred["acciones"][0]["objetos"][0]["adjetivos"] = ["azul"]
        pred["acciones"][0]["objetos"][1]["adjetivos"] = ["roja"]
        resultado = evaluar([(real, pred)])
        self.assertEqual(resultado["F1_adjetivos"], 1)
        self.assertLess(resultado["estructura_recall_pct"], 100)

    def test_cli_escribe_lote_sin_modelo_real(self):
        with tempfile.TemporaryDirectory() as carpeta:
            entrada, salida = Path(carpeta)/"entrada.json", Path(carpeta)/"salida.json"
            entrada.write_text('[{"id":"a","orden":"Trae el vaso"},"Qué demora la de hoy"]', encoding="utf-8")
            self.assertEqual(main(["--entrada", str(entrada), "--salida", str(salida)], fabrica=MotorSimulado), 0)
            self.assertEqual(len(json.loads(salida.read_text(encoding="utf-8"))), 2)

    def test_no_sobrescribe_entrada(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta)/"entrada.json"
            ruta.write_text('["Trae el vaso"]', encoding="utf-8")
            with self.assertRaises(SystemExit):
                main(["--entrada", str(ruta), "--salida", str(ruta)], fabrica=MotorSimulado)
            self.assertEqual(json.loads(ruta.read_text(encoding="utf-8")), ["Trae el vaso"])

    def test_markdown_utilizable_sin_contar_formato_original_valido(self):
        raw = "```json\n" + json.dumps(referencia()) + "\n```"
        data, valido_original, retirado, error = interpretar_para_ejecucion(raw)
        self.assertEqual(data, referencia())
        self.assertFalse(valido_original)
        self.assertTrue(retirado)
        self.assertIsNotNone(error)

    def test_no_recupera_markdown_con_explicaciones_extra(self):
        raw = "```json\n" + json.dumps(referencia()) + "\n```"
        self.assertIsNone(interpretar_para_ejecucion("Explicación\n" + raw)[0])
        self.assertIsNone(interpretar_para_ejecucion(raw + "\nExplicación")[0])

    def test_pronombre_pide_aclaracion_sin_alterar_prediccion(self):
        data = referencia("eso", "")
        data["acciones"][0]["objetos"][0]["adjetivos"] = []
        copia = json.loads(json.dumps(data))
        self.assertTrue(detectar_referentes_sin_resolver(data))
        self.assertIn("¿A qué objeto", generar_respuesta_robot(data))
        self.assertEqual(data, copia)

    def test_referencias_ejemplo_validas(self):
        ruta = Path(__file__).resolve().parents[1] / "datos" / "ordenes_ejemplo.json"
        self.assertEqual(len(leer_ordenes(ruta)), 5)

if __name__ == "__main__":
    unittest.main()
