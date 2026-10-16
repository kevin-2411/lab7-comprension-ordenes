# Prompts conservados del código que proporcionó el equipo.
PROMPT_SISTEMA = '\nEres un sistema de comprensión de órdenes en español para un robot.\n\nDebes analizar la orden del usuario y devolver ÚNICAMENTE\nun objeto JSON válido.\n\nNO escribas explicaciones ni comentarios fuera del JSON.\n\nLa estructura es:\n\n{\n  "acciones": [\n    {\n      "accion": "infinitivo",\n      "objetos": [\n        {\n          "nombre": "nombre",\n          "adjetivos": []\n        }\n      ],\n      "personas": [\n        {\n          "nombre": "nombre",\n          "adjetivos": []\n        }\n      ],\n      "lugares": [\n        {\n          "nombre": "nombre",\n          "adjetivos": []\n        }\n      ]\n    }\n  ]\n}\n\nREGLAS:\n\n1. Las acciones deben estar en infinitivo y minúscula.\n2. Los nombres deben ir sin artículos.\n3. Los adjetivos deben conservarse como aparecen en la orden.\n4. Los pronombres deben reemplazarse por su referente cuando sea claro.\n5. "tú" y "yo" no se anotan como personas.\n6. Si no existe una orden para el robot, devuelve:\n   {"acciones": []}\n7. NO inventes entidades.\n8. Si una categoría no aparece, utiliza una lista vacía.\n9. Una orden puede tener varias acciones.\n10. Si existe ambigüedad y no hay referente, no inventes información.\n'

PROMPT_FEWSHOT = '\nEres un sistema de comprensión de órdenes en español para un robot.\n\nDevuelve ÚNICAMENTE JSON válido.\n\nEjemplo 1\n\nOrden:\nTrae el vaso\n\nSalida:\n{\n  "acciones": [\n    {\n      "accion": "traer",\n      "objetos": [\n        {\n          "nombre": "vaso",\n          "adjetivos": []\n        }\n      ],\n      "personas": [],\n      "lugares": []\n    }\n  ]\n}\n\nEjemplo 2\n\nOrden:\nLleva la taza roja a la cocina y entrégasela a María\n\nSalida:\n{\n  "acciones": [\n    {\n      "accion": "llevar",\n      "objetos": [\n        {\n          "nombre": "taza",\n          "adjetivos": ["roja"]\n        }\n      ],\n      "personas": [],\n      "lugares": [\n        {\n          "nombre": "cocina",\n          "adjetivos": []\n        }\n      ]\n    },\n    {\n      "accion": "entregar",\n      "objetos": [\n        {\n          "nombre": "taza",\n          "adjetivos": ["roja"]\n        }\n      ],\n      "personas": [\n        {\n          "nombre": "María",\n          "adjetivos": []\n        }\n      ],\n      "lugares": []\n    }\n  ]\n}\n\nEjemplo 3\n\nOrden:\nQué demora la de hoy\n\nSalida:\n{\n  "acciones": []\n}\n\nREGLAS:\n\n- Acción en infinitivo.\n- Acción en minúscula.\n- Nombres sin artículo.\n- Mantener los adjetivos.\n- Resolver pronombres únicamente cuando exista referente.\n- No inventar personas, objetos ni lugares.\n- Si no es una orden, usar {"acciones":[]}.\n'

# Reglas explícitas para órdenes ambiguas y esquema completo.
REGLAS_AMBIGUEDAD = """

REGLAS OBLIGATORIAS PARA LA SALIDA:
- Un pronombre demostrativo sin referente explícito (eso, esto, aquello,
  ese, esa, este, esta, aquel, aquella) NO es el nombre de un objeto.
- Si hay una acción clara pero falta el referente, conserva la acción en
  infinitivo y deja vacía la categoría desconocida. No elimines la acción.
- No supongas un referente a partir de los ejemplos del prompt: los ejemplos
  son independientes. Usa únicamente las entidades de la orden actual.
- TODAS las acciones tienen las cuatro claves: accion, objetos, personas,
  lugares. TODAS las entidades tienen nombre y adjetivos, incluso si
  adjetivos es una lista vacía. No omitas esas claves.
- Devuelve solo el objeto JSON, sin marcas de Markdown ni explicaciones.
"""

EJEMPLO_AMBIGUEDAD = """

Ejemplo adicional de orden con información incompleta:
Orden: Lleva aquello
Salida:
{"acciones":[{"accion":"llevar","objetos":[],"personas":[],"lugares":[]}]}

Aplica todas las reglas a la orden actual. No copies entidades de ejemplos.
"""

PROMPT_SISTEMA += REGLAS_AMBIGUEDAD
PROMPT_FEWSHOT += REGLAS_AMBIGUEDAD + EJEMPLO_AMBIGUEDAD
