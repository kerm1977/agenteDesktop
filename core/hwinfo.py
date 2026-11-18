"""Escaneo de hardware del equipo (RAM, CPU, GPU, disco) vía PowerShell."""
import json
import re
import subprocess


def _ps(script, timeout=15):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, timeout=timeout, errors="replace")
    return out.stdout.strip()


def scan():
    """Devuelve dict con ram_gb, cpu, gpu:[{nombre,vram_gb}], disco_libre_gb."""
    datos = {"ram_gb": 0.0, "cpu": "?", "gpu": [], "disco_libre_gb": 0.0}

    raw = _ps("(Get-CimInstance Win32_ComputerSystem)"
              ".TotalPhysicalMemory")
    try:
        datos["ram_gb"] = round(int(raw) / (1024 ** 3), 1)
    except ValueError:
        pass

    datos["cpu"] = _ps("(Get-CimInstance Win32_Processor | "
                       "Select-Object -First 1).Name") or "?"

    raw = _ps("Get-CimInstance Win32_VideoController | "
              "Select-Object Name,AdapterRAM | ConvertTo-Json -Compress")
    try:
        gpus = json.loads(raw)
        if isinstance(gpus, dict):
            gpus = [gpus]
        for g in gpus:
            vram = g.get("AdapterRAM") or 0
            datos["gpu"].append({
                "nombre": g.get("Name", "?"),
                "vram_gb": round(int(vram) / (1024 ** 3), 1)})
    except (json.JSONDecodeError, TypeError):
        for name in re.findall(r"[A-Z].+", raw):
            datos["gpu"].append({"nombre": name.strip(), "vram_gb": 0.0})

    raw = _ps("(Get-PSDrive -Name C).Free")
    try:
        datos["disco_libre_gb"] = round(int(raw) / (1024 ** 3), 1)
    except ValueError:
        pass

    datos["vram_max_gb"] = max([g["vram_gb"] for g in datos["gpu"]]
                              or [0.0])
    return datos


def compatible(model, hw):
    """True si el modelo cabe en el equipo (RAM usable ≈ 80% del total)."""
    if not hw:
        return None
    usable = hw.get("ram_gb", 0) * 0.8
    return model.get("ram_gb", 999) <= usable
