# Mini Agente Desktop

Agente de código local, nativo (PySide6 + Qt), conectado a Ollama u otros
motores compatibles (LM Studio, llama.cpp, API OpenAI). Sin navegador.

## Ejecutar

```
run.bat
```

o manualmente:

```
.venv\Scripts\python.exe app.py
```

## Funciones

- Barra de herramientas: abrir carpeta, guardar, selector de motor/modelo,
  consola, mejorar agente, actualizar.
- Árbol de archivos, editor con números de línea y resaltado, chat con
  tarjetas de tarea contraíbles.
- Memoria del proyecto (`.agente/memoria.json`) que se inyecta al prompt.
- Herramientas del agente: leer/escribir/editar archivos, buscar, mapa del
  proyecto, comandos.
- Consola de errores (dock inferior) con copiar/limpiar.
- Auto-actualización OTA desde GitHub (`manifest.json` en main).
- Modo "Mejorar agente": el chat actúa solo sobre el código de esta app.

## Actualización

La app compara su `version.json` con `manifest.json` del repo en GitHub.
Al detectar cambios descarga los archivos a `.update/` y `core/updater.py`
los aplica al reiniciar. Regenera el manifest con:

```
.venv\Scripts\python.exe gen_manifest.py <nueva_version>
```
