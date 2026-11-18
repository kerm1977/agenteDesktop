"""Catálogo de modelos GRATUITOS con chat, descargables vía Ollama.

Solo modelos con soporte de chat/instrucciones (nada de base o embeddings).
ram_gb = RAM total mínima recomendada; ctx = contexto típico soportado.
peso: ligero | medio | fuerte.
"""

CATALOGO = [
    # ---------- ligeros (≤ ~6 GB RAM) ----------
    {"tag": "smollm2:360m", "nombre": "SmolLM2 360M",
     "peso": "ligero", "gb": 0.3, "ram_gb": 2, "ctx": 8192},
    {"tag": "tinyllama:1.1b", "nombre": "TinyLlama 1.1B",
     "peso": "ligero", "gb": 0.6, "ram_gb": 3, "ctx": 2048},
    {"tag": "smollm2:1.7b", "nombre": "SmolLM2 1.7B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 8192},
    {"tag": "qwen2.5:0.5b", "nombre": "Qwen2.5 0.5B",
     "peso": "ligero", "gb": 0.4, "ram_gb": 3, "ctx": 32768},
    {"tag": "qwen2.5:1.5b", "nombre": "Qwen2.5 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 32768},
    {"tag": "qwen2.5-coder:1.5b", "nombre": "Qwen2.5 Coder 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 32768},
    {"tag": "llama3.2:1b", "nombre": "Llama 3.2 1B",
     "peso": "ligero", "gb": 1.3, "ram_gb": 4, "ctx": 131072},
    {"tag": "gemma2:2b", "nombre": "Gemma 2 2B",
     "peso": "ligero", "gb": 1.6, "ram_gb": 5, "ctx": 8192},
    {"tag": "gemma3:1b", "nombre": "Gemma 3 1B",
     "peso": "ligero", "gb": 0.8, "ram_gb": 4, "ctx": 32768},
    {"tag": "qwen2.5:3b", "nombre": "Qwen2.5 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768},
    {"tag": "qwen2.5-coder:3b", "nombre": "Qwen2.5 Coder 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768},
    {"tag": "llama3.2:3b", "nombre": "Llama 3.2 3B",
     "peso": "ligero", "gb": 2.0, "ram_gb": 6, "ctx": 131072},
    {"tag": "phi3:mini", "nombre": "Phi-3 Mini 3.8B",
     "peso": "ligero", "gb": 2.3, "ram_gb": 6, "ctx": 131072},
    {"tag": "phi4-mini", "nombre": "Phi-4 Mini 3.8B",
     "peso": "ligero", "gb": 2.5, "ram_gb": 6, "ctx": 131072},
    {"tag": "gemma3:4b", "nombre": "Gemma 3 4B",
     "peso": "ligero", "gb": 3.3, "ram_gb": 8, "ctx": 131072},

    # ---------- medios (8–16 GB RAM) ----------
    {"tag": "qwen2.5:7b", "nombre": "Qwen2.5 7B",
     "peso": "medio", "gb": 4.7, "ram_gb": 12, "ctx": 32768},
    {"tag": "qwen2.5-coder:7b", "nombre": "Qwen2.5 Coder 7B",
     "peso": "medio", "gb": 4.7, "ram_gb": 12, "ctx": 32768},
    {"tag": "llama3.1:8b", "nombre": "Llama 3.1 8B",
     "peso": "medio", "gb": 4.9, "ram_gb": 12, "ctx": 131072},
    {"tag": "mistral:7b", "nombre": "Mistral 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 32768},
    {"tag": "codellama:7b", "nombre": "CodeLlama 7B",
     "peso": "medio", "gb": 3.8, "ram_gb": 12, "ctx": 16384},
    {"tag": "gemma2:9b", "nombre": "Gemma 2 9B",
     "peso": "medio", "gb": 5.8, "ram_gb": 14, "ctx": 8192},
    {"tag": "deepseek-r1:7b", "nombre": "DeepSeek R1 7B",
     "peso": "medio", "gb": 4.7, "ram_gb": 12, "ctx": 131072},
    {"tag": "deepseek-r1:8b", "nombre": "DeepSeek R1 8B (Llama)",
     "peso": "medio", "gb": 5.2, "ram_gb": 14, "ctx": 131072},
    {"tag": "deepseek-coder-v2:lite", "nombre": "DeepSeek Coder V2 Lite",
     "peso": "medio", "gb": 8.9, "ram_gb": 16, "ctx": 16384},

    # ---------- fuertes (>16 GB RAM) ----------
    {"tag": "gemma3:12b", "nombre": "Gemma 3 12B",
     "peso": "fuerte", "gb": 8.1, "ram_gb": 20, "ctx": 131072},
    {"tag": "codellama:13b", "nombre": "CodeLlama 13B",
     "peso": "fuerte", "gb": 7.4, "ram_gb": 20, "ctx": 16384},
    {"tag": "qwen2.5:14b", "nombre": "Qwen2.5 14B",
     "peso": "fuerte", "gb": 9.0, "ram_gb": 20, "ctx": 32768},
    {"tag": "qwen2.5-coder:14b", "nombre": "Qwen2.5 Coder 14B",
     "peso": "fuerte", "gb": 9.0, "ram_gb": 20, "ctx": 32768},
    {"tag": "phi4:14b", "nombre": "Phi-4 14B",
     "peso": "fuerte", "gb": 9.1, "ram_gb": 20, "ctx": 16384},
    {"tag": "gemma3:27b", "nombre": "Gemma 3 27B",
     "peso": "fuerte", "gb": 17.0, "ram_gb": 40, "ctx": 131072},
    {"tag": "qwen2.5:32b", "nombre": "Qwen2.5 32B",
     "peso": "fuerte", "gb": 20.0, "ram_gb": 42, "ctx": 32768},
    {"tag": "qwen2.5-coder:32b", "nombre": "Qwen2.5 Coder 32B",
     "peso": "fuerte", "gb": 19.0, "ram_gb": 40, "ctx": 32768},
    {"tag": "codellama:34b", "nombre": "CodeLlama 34B",
     "peso": "fuerte", "gb": 19.0, "ram_gb": 42, "ctx": 16384},
]

PESOS = {
    "ligero": {"num_ctx": 2048, "num_predict": 1024, "temperature": 0.6},
    "medio": {"num_ctx": 4096, "num_predict": 2048, "temperature": 0.7},
    "fuerte": {"num_ctx": 8192, "num_predict": 4096, "temperature": 0.8},
}
