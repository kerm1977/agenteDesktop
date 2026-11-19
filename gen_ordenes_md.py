"""Genera ORDENES.md: verbos x objetos x ubicaciones (miles de frases).

    .venv\\Scripts\\python.exe gen_ordenes_md.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ordenes

OBJ = ["una carpeta", "un archivo", "un documento", "un proyecto",
       "la carpeta", "el archivo", "el documento", "la carpeta X",
       "el archivo notas.txt", "mi proyecto", "una pagina web",
       "un single page", "un index.html", "un sitio web", "un script",
       "un programa", "una app", "un juego", "una calculadora",
       "un reporte", "el pdf", "este texto", "la carpeta tribu",
       "el proyecto billetera", "una base de datos"]
LUG = ["", " en el escritorio", " en descargas", " en documentos",
       " dentro de proyectos", " aqui", " en mi pc"]

lines = ["# Catalogo de ordenes del agente", "",
         "Generado: verbos x objetos x ubicaciones.",
         "El enrutador entiende todas estas formas y variantes.", ""]
total = 0
for g, verbs in ordenes.VERBOS.items():
    lines += ["## " + g + " (" + str(len(verbs)) + " sinonimos)", ""]
    for verb in verbs:
        for o in OBJ:
            for l in LUG[:5]:
                lines.append("- " + verb + " " + o + l)
                total += 1
    lines.append("")
lines.append("**Total: " + str(total) + " combinaciones.**")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "ORDENES.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ORDENES.md:", total, "combinaciones")
