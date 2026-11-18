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
    """Devuelve dict completo del equipo: ram, cpu, gpu, disco, SO."""
    datos = {"ram_gb": 0.0, "cpu": "?", "gpu": [], "disco_libre_gb": 0.0,
             "equipo": "?", "cpu_nucleos": 0, "cpu_hilos": 0,
             "cpu_ghz": 0.0, "ram_modulos": "", "os": "?", "gpu_driver": ""}

    datos["equipo"] = _ps(
        "(Get-CimInstance Win32_ComputerSystem | Select-Object -First 1) | "
        "ForEach-Object { $_.Manufacturer + ' ' + $_.Model }") or "?"

    raw = _ps("(Get-CimInstance Win32_ComputerSystem)"
              ".TotalPhysicalMemory")
    try:
        datos["ram_gb"] = round(int(raw) / (1024 ** 3), 1)
    except ValueError:
        pass

    raw = _ps("Get-CimInstance Win32_Processor | Select-Object -First 1 "
              "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed "
              "| ConvertTo-Json -Compress")
    try:
        c = json.loads(raw)
        datos["cpu"] = c.get("Name", "?")
        datos["cpu_nucleos"] = c.get("NumberOfCores", 0)
        datos["cpu_hilos"] = c.get("NumberOfLogicalProcessors", 0)
        datos["cpu_ghz"] = round(int(c.get("MaxClockSpeed") or 0) / 1000, 2)
    except (json.JSONDecodeError, TypeError):
        datos["cpu"] = _ps("(Get-CimInstance Win32_Processor | "
                           "Select-Object -First 1).Name") or "?"

    datos["ram_modulos"] = _ps(
        "(Get-CimInstance Win32_PhysicalMemory | ForEach-Object "
        "{ [math]::Round($_.Capacity/1GB,1).ToString() + ' GB @ ' + "
        "$_.Speed.ToString() + ' MHz' }) -join ' + '")

    raw = _ps("Get-CimInstance Win32_VideoController | "
              "Select-Object Name,AdapterRAM,DriverVersion "
              "| ConvertTo-Json -Compress")
    try:
        gpus = json.loads(raw)
        if isinstance(gpus, dict):
            gpus = [gpus]
        for g in gpus:
            vram = g.get("AdapterRAM") or 0
            datos["gpu"].append({
                "nombre": g.get("Name", "?"),
                "vram_gb": round(int(vram) / (1024 ** 3), 1),
                "driver": g.get("DriverVersion", "")})
    except (json.JSONDecodeError, TypeError):
        for name in re.findall(r"[A-Z].+", raw):
            datos["gpu"].append({"nombre": name.strip(), "vram_gb": 0.0,
                                 "driver": ""})

    raw = _ps("(Get-PSDrive -Name C).Free")
    try:
        datos["disco_libre_gb"] = round(int(raw) / (1024 ** 3), 1)
    except ValueError:
        pass

    datos["os"] = _ps("(Get-CimInstance Win32_OperatingSystem | "
                      "Select-Object -First 1) | ForEach-Object "
                      "{ $_.Caption + ' ' + $_.OSArchitecture }") or "?"
    datos["vram_max_gb"] = max([g["vram_gb"] for g in datos["gpu"]]
                              or [0.0])
    return datos


def reporte(datos):
    """Texto completo y copiable de las especificaciones del equipo."""
    gpus = "\n".join(
        f"  - {g['nombre']} · VRAM {g['vram_gb']} GB"
        + (f" · driver {g['driver']}" if g.get("driver") else "")
        for g in datos["gpu"]) or "  - (sin GPU detectada)"
    return (
        f"EQUIPO: {datos['equipo']}\n"
        f"Sistema operativo: {datos['os']}\n"
        f"CPU: {datos['cpu']}\n"
        f"  Núcleos: {datos['cpu_nucleos']} · Hilos: {datos['cpu_hilos']}"
        f" · {datos['cpu_ghz']} GHz\n"
        f"RAM total: {datos['ram_gb']} GB\n"
        f"  Módulos: {datos['ram_modulos'] or '—'}\n"
        f"GPU:\n{gpus}\n"
        f"VRAM máxima: {datos['vram_max_gb']} GB "
        "(integrada = usa RAM del sistema)\n"
        f"Disco libre en C: {datos['disco_libre_gb']} GB\n"
        f"Nota: sin GPU dedicada, los modelos de IA corren por CPU — "
        "ideal ≤3B (ligero), usable 7–9B (medio, lento).")


def compatible(model, hw):
    """True si el modelo cabe en el equipo (RAM usable ≈ 80% del total)."""
    if not hw:
        return None
    usable = hw.get("ram_gb", 0) * 0.8
    return model.get("ram_gb", 999) <= usable
