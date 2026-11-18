"""Catálogo de modelos gratuitos descargables vía Ollama.

ram_gb = RAM total mínima recomendada; ctx = contexto típico soportado.
peso: ligero | medio | fuerte.
"""

CATALOGO = [
    {"tag": "qwen2.5-coder:1.5b", "nombre": "Qwen2.5 Coder 1.5B",
     "peso": "ligero", "gb": 1.0, "ram_gb": 4, "ctx": 32768},
    {"tag": "qwen2.5-coder:3b", "nombre": "Qwen2.5 Coder 3B",
     "peso": "ligero", "gb": 1.9, "ram_gb": 6, "ctx": 32768},
    {"tag": "llama3.2:1b", "nombre": "Llama 3.2 1B",
     "peso": "ligero", "gb": 1.3, "ram_gb": 4, "ctx": 131072},
    {"tag": "llama3.2:3b", "nombre": "Llama 3.2 3B",
     "peso": "ligero", "gb": 2.0, "ram_gb": 6, "ctx": 131072},
    {"tag": "phi4-mini", "nombre": "Phi-4 Mini 3.8B",
     "peso": "ligero", "gb": 2.5, "ram_gb": 6, "ctx": 131072},
    {"tag": "qwen2.5-coder:7b", "nombre": "Qwen2.5 Coder 7B",
     "peso": "medio", "gb": 4.7, "ram_gb": 12, "ctx": 32768},
    {"tag": "deepseek-coder-v2:lite", "nombre": "DeepSeek Coder V2 Lite",
     "peso": "medio", "gb": 8.9, "ram_gb": 16, "ctx": 16384},
    {"tag": "codellama:7b", "nombre": "CodeLlama 7B",
     "peso": "medio", "gb": 3.8, "ram_gb": 12, "ctx": 16384},
    {"tag": "mistral:7b", "nombre": "Mistral 7B",
     "peso": "medio", "gb": 4.1, "ram_gb": 12, "ctx": 32768},
    {"tag": "gemma3:4b", "nombre": "Gemma 3 4B",
     "peso": "medio", "gb": 3.3, "ram_gb": 10, "ctx": 131072},
    {"tag": "qwen2.5-coder:14b", "nombre": "Qwen2.5 Coder 14B",
     "peso": "fuerte", "gb": 9.0, "ram_gb": 20, "ctx": 32768},
    {"tag": "qwen2.5-coder:32b", "nombre": "Qwen2.5 Coder 32B",
     "peso": "fuerte", "gb": 19.0, "ram_gb": 40, "ctx": 32768},
    {"tag": "deepseek-r1:8b", "nombre": "DeepSeek R1 8B",
     "peso": "fuerte", "gb": 5.2, "ram_gb": 14, "ctx": 131072},
    {"tag": "codellama:13b", "nombre": "CodeLlama 13B",
     "peso": "fuerte", "gb": 7.4, "ram_gb": 20, "ctx": 16384},
]

PESOS = {
    "ligero": {"num_ctx": 2048, "num_predict": 1024, "temperature": 0.6},
    "medio": {"num_ctx": 4096, "num_predict": 2048, "temperature": 0.7},
    "fuerte": {"num_ctx": 8192, "num_predict": 4096, "temperature": 0.8},
}
