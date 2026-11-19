"""Catálogo de modelos GRATUITOS de PROGRAMACIÓN, descargables vía Ollama.

Curado para equipos SIN GPU dedicada (inferencia por CPU), RAM ~16 GB:
- ligero: ≤3B — recomendados, responden bien en CPU.
- medio: 7–8B — caben en RAM pero responden lento en CPU (techo
  práctico medido en i7-4790 sin GPU).
- No hay modelos fuertes ni >8B: medido que 13B/14B+ no responden
  a tiempo en este equipo y se eliminaron.
Todos con soporte chat/instrucciones; nada de pago.
"""

CATALOGO = [
    # ---------- ligeros (recomendados para CPU) ----------
    {"tag": "qwen2.5-coder:0.5b", "nombre": "Qwen2.5 Coder 0.5B",
     "peso": "ligero", "gb": 0.4, "ram_gb": 2, "ctx": 32768},
    {"tag": "deepseek-coder:1.3b", "nombre": "DeepSeek Coder 1.3B",
     "peso": "ligero", "gb": 0.8, "ram_gb": 3, "ctx": 16384},
    {"tag": "yi-coder:1.5b", "nombre": "Yi-Coder 1.5B",
     "peso": "ligero", "gb": 0.9, "ram_gb": 4, "ctx": 131072},
    {"tag": "qwen2.5-coder:1.5b", "nombre": "Qwen2.5 Coder 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 32768},
    {"tag": "codegemma:2b", "nombre": "CodeGemma 2B",
     "peso": "ligero", "gb": 1.6, "ram_gb": 5, "ctx": 8192},
    {"tag": "qwen2.5-coder:3b", "nombre": "Qwen2.5 Coder 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768},
    {"tag": "starcoder2:3b", "nombre": "StarCoder2 3B",
     "peso": "ligero", "gb": 1.7, "ram_gb": 6, "ctx": 16384},
    {"tag": "granite-code:3b", "nombre": "Granite Code 3B",
     "peso": "ligero", "gb": 2.0, "ram_gb": 6, "ctx": 128000},
    {"tag": "stable-code:3b", "nombre": "Stable Code 3B",
     "peso": "ligero", "gb": 1.6, "ram_gb": 5, "ctx": 16384},
    {"tag": "opencoder:1.5b", "nombre": "OpenCoder 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 4096},

    # ---------- generalistas (conversan y orquestan al coder) ----------
    {"tag": "llama3.2:1b", "nombre": "Llama 3.2 1B",
     "peso": "ligero", "gb": 0.8, "ram_gb": 3, "ctx": 128000,
     "rol": "generalista"},
    {"tag": "llama3.2:3b", "nombre": "Llama 3.2 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 128000,
     "rol": "generalista"},
    {"tag": "qwen2.5:1.5b", "nombre": "Qwen2.5 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 32768,
     "rol": "generalista"},
    {"tag": "qwen2.5:3b", "nombre": "Qwen2.5 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768,
     "rol": "generalista"},
    {"tag": "mistral:7b", "nombre": "Mistral 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 32768,
     "rol": "generalista"},

    # ---------- medios (caben, pero lentos sin GPU) ----------
    {"tag": "codellama:7b-instruct", "nombre": "CodeLlama 7B Instruct",
     "peso": "medio", "gb": 3.8, "ram_gb": 10, "ctx": 16384},
    {"tag": "magicoder:7b", "nombre": "Magicoder 7B",
     "peso": "medio", "gb": 3.8, "ram_gb": 10, "ctx": 16384},
    {"tag": "deepseek-coder:6.7b", "nombre": "DeepSeek Coder 6.7B",
     "peso": "medio", "gb": 3.8, "ram_gb": 10, "ctx": 16384},
    {"tag": "starcoder2:7b", "nombre": "StarCoder2 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 16384},
    {"tag": "codeqwen:7b", "nombre": "CodeQwen1.5 7B",
     "peso": "medio", "gb": 4.2, "ram_gb": 12, "ctx": 65536},
    {"tag": "qwen2.5-coder:7b", "nombre": "Qwen2.5 Coder 7B",
     "peso": "medio", "gb": 4.7, "ram_gb": 12, "ctx": 32768},
    {"tag": "codegemma:7b", "nombre": "CodeGemma 7B",
     "peso": "medio", "gb": 5.0, "ram_gb": 12, "ctx": 8192},
    {"tag": "granite-code:8b", "nombre": "Granite Code 8B",
     "peso": "medio", "gb": 4.9, "ram_gb": 12, "ctx": 128000},
    {"tag": "opencoder:8b", "nombre": "OpenCoder 8B",
     "peso": "medio", "gb": 4.9, "ram_gb": 12, "ctx": 4096},
]

PESOS = {
    "ligero": {"num_ctx": 2048, "num_predict": 1024, "temperature": 0.6},
    "medio": {"num_ctx": 4096, "num_predict": 2048, "temperature": 0.7},
    "fuerte": {"num_ctx": 8192, "num_predict": 4096, "temperature": 0.8},
}
