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
    {"tag": "gemma2:2b", "nombre": "Gemma 2 2B",
     "peso": "ligero", "gb": 1.6, "ram_gb": 5, "ctx": 8192,
     "rol": "generalista"},
    {"tag": "phi3:mini", "nombre": "Phi-3 Mini",
     "peso": "ligero", "gb": 2.2, "ram_gb": 6, "ctx": 131072,
     "rol": "generalista"},
    {"tag": "mistral:7b", "nombre": "Mistral 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 32768,
     "rol": "generalista"},

    # ---------- minimodelos generalistas (rapidísimos en CPU) ----------
    {"tag": "smollm2:135m", "nombre": "SmolLM2 135M",
     "peso": "ligero", "gb": 0.1, "ram_gb": 1, "ctx": 8192,
     "rol": "minimodelo"},
    {"tag": "smollm2:360m", "nombre": "SmolLM2 360M",
     "peso": "ligero", "gb": 0.3, "ram_gb": 2, "ctx": 8192,
     "rol": "minimodelo"},
    {"tag": "smollm2:1.7b", "nombre": "SmolLM2 1.7B",
     "peso": "ligero", "gb": 1.1, "ram_gb": 4, "ctx": 8192,
     "rol": "minimodelo"},
    {"tag": "tinyllama:1.1b", "nombre": "TinyLlama 1.1B",
     "peso": "ligero", "gb": 0.7, "ram_gb": 3, "ctx": 2048,
     "rol": "minimodelo"},
    {"tag": "qwen2.5:0.5b", "nombre": "Qwen2.5 0.5B",
     "peso": "ligero", "gb": 0.4, "ram_gb": 2, "ctx": 32768,
     "rol": "minimodelo"},
    {"tag": "falcon3:1b", "nombre": "Falcon 3 1B",
     "peso": "ligero", "gb": 0.7, "ram_gb": 3, "ctx": 32768,
     "rol": "minimodelo"},
    {"tag": "falcon3:3b", "nombre": "Falcon 3 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768,
     "rol": "minimodelo"},
    {"tag": "orca-mini:3b", "nombre": "Orca Mini 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 2048,
     "rol": "minimodelo"},

    # ---------- salud / medicina (con peso: lentos en CPU) ----------
    {"tag": "medllama2", "nombre": "MedLlama2 7B",
     "peso": "medio", "gb": 3.8, "ram_gb": 10, "ctx": 4096,
     "rol": "salud"},
    {"tag": "meditron:7b", "nombre": "Meditron 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 4096,
     "rol": "salud"},
    {"tag": "openbiollm:8b", "nombre": "OpenBioLLM 8B",
     "peso": "medio", "gb": 4.9, "ram_gb": 12, "ctx": 8192,
     "rol": "salud"},

    # ---------- visión (describen imágenes) ----------
    {"tag": "moondream", "nombre": "Moondream 1.8B",
     "peso": "ligero", "gb": 1.7, "ram_gb": 5, "ctx": 2048,
     "rol": "vision"},

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

# orden de los grupos en el selector de modelos
GRUPOS = ["Programación", "General", "Minimodelos", "Salud", "Visión"]


def rol_de(tag):
    """Propósito del modelo para agruparlo en el selector."""
    import re
    t = (tag or "").lower()
    if re.search(r"coder|code|starcoder|codellama|codeqwen|granite|"
                 r"opencoder|magicoder", t):
        return "Programación"
    if re.search(r"med|salud|bio|clinical|meditron", t):
        return "Salud"
    if re.search(r"moondream|llava|bakllava|vision", t):
        return "Visión"
    if re.search(r"0\.5b|135m|360m|1\.1b|[:\-]1b|1\.5b|1\.6b|1\.7b|"
                 r"[:\-]2b|tiny|smollm|mini", t):
        return "Minimodelos"
    return "General"
