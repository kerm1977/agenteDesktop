# REGLAS del agente y de todo código generado

## Agente (este proyecto)
- Máximo 250 líneas por archivo; dividir en módulos.
- UI en español. Todo nativo Qt (PySide6): nada de navegador ni WebView.
- Preferir editar archivos existentes sobre crear nuevos.
- Sin dependencias pesadas innecesarias.

## Normas de todo proyecto que el agente crea
1. **Teléfono**: solo dígitos y `+` (código de área). Nada de letras.
2. **Correo**: validar `@` y `.` para la extensión (usuario@dominio.ext).
3. **Nombres**: Title Case — primera letra de cada palabra en mayúscula.
4. **Contraseña**: `type=password` con asteriscos + botón ojito en JS.
5. **Máx. 250 líneas por archivo** — dividir en módulos si crece.
6. **Módulos por carpeta**: cada módulo en su carpeta con sus archivos.
7. **Cero CDNs**: todo framework/librería/JS se guarda local en el proyecto.
8. **MD por proyecto**: cada proyecto tiene su .md explicándolo.
9. **Nombre comentado**: cada archivo lleva su nombre en la primera línea.
10. **OTA local**: cada proyecto tiene su sistema de actualización con
    puerto propio; la app registra los puertos usados (`puertos_ota`).
11. **Sintaxis limpia**: código claro y legible en cualquier lenguaje
    (Python, Flask, Django, Capacitor, Bootstrap, Vue, JS…).
12. **Formularios**: validación por tipo — números en campos numéricos,
    letras en campos de texto, especiales solo si se permiten.
