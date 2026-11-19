"""Vocabulario de órdenes: sinónimos por intención, en español.

El enrutador llama `intenciones(texto)` y obtiene el conjunto de
acciones detectadas — da igual cómo lo diga el usuario.
"""
import re, unicodedata


def _norm(t):
    t = " " + t.lower() + " "
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn")
    return t


VERBOS = {
    "crear": [
        "crea", "crear", "creame", "cree", "genera", "generar", "generame",
        "haz", "hace", "haceme", "hacelo", "fabrica", "fabricar",
        "construye", "construir", "construyeme", "arma", "armar", "armame",
        "produce", "producir", "monta", "montar", "levanta", "levantar",
        "inicia", "iniciar", "comienza", "empeza", "nueva", "nuevo",
        "quiero", "necesito", "agrega", "agregame", "anade", "anadir",
        "mete", "metele", "inventa", "inventar", "disena", "disenar",
        "desarrolla", "desarrollar", "escribe", "escribi", "redacta",
        "redactar", "programa", "programar", "codifica", "codificar",
        "lanza", "lanzar", "instala", "instalar", "implementa",
        "implementar", "prepara", "preparame", "formame", "dale forma",
        "levantame", "pon", "ponme", "setea", "configura", "maqueta",
        "modela", "compone", "compilame", "ensambla", "levan"],
    "borrar": [
        "borra", "borrar", "borrame", "elimina", "eliminar", "eliminame",
        "quita", "quitar", "quitame", "suprime", "suprimir", "suprimi",
        "delete", "desaparece", "desaparecer", "desapareceme", "fulmina",
        "fulminar", "destruye", "destruir", "aniquila", "aniquilar",
        "saca", "sacar", "sacame", "extermina", "liquida", "liquidar",
        "barre", "barrer", "limpia", "limpiar", "vacia", "vaciar",
        "desinstala", "desinstalar", "remueve", "remover", "retira",
        "retirar", "erradica", "tira", "tirar", "bota", "botar",
        "deshecha", "desinstalame", "desmonta", "desarma", "desconecta",
        "desvincula", "expulsa", "purga", "purgame", "trunca", "rafia",
        "rase", "nivelalo", "fumigate", "echalo", "sacalo", "vetalo",
        "borralo", "sacalo", "matame", "mata", "elimina lo", "quitamelo"],
    "analizar": [
        "analiza", "analizar", "analizame", "lee", "leer", "leeme",
        "resume", "resumir", "resumime", "examina", "examinar",
        "revisa", "revisar", "revisame", "escanea", "escanear",
        "estudia", "estudiar", "procesa", "procesar", "evalua",
        "evaluar", "inspecciona", "inspeccionar", "comprueba",
        "comprobar", "verifica", "verificar", "checa", "chequea",
        "mira", "mirar", "mirame", "observa", "observar", "detecta",
        "detectar", "audita", "auditar", "escudrina", "investiga",
        "investigar", "diagnostica", "diagnosticar", "interpreta",
        "interpretar", "descifra", "descifrar", "explicame", "cuentame",
        "muestrame el contenido", "ensename", "detalla", "detallar",
        "desglosa", "desglosar", "desmenuza", "explora", "explorar",
        "radiografia", "supervisa", "controla", "monitorea", "vigila",
        "mide", "medir", "cuantifica", "cataloga", "inventaria",
        "mapea", "mapear", "traza", "trazar", "sondea", "palpa",
        "disecciona", "escarba", "escarbame", "decompon", "desarma el",
        "abre el contenido", "sumario", "sumario de", "reporta",
        "reportame", "informame", "avisame que dice", "que dice",
        "que contiene", "cuentame de que trata"],
    "abrir": [
        "abre", "abrir", "abrimelo", "abrimela", "muestrame", "mostrame",
        "ensename", "enseniame", "despliega", "desplegar", "visualiza",
        "visualizar", "presenta", "presentar", "carga", "cargar",
        "lanza la vista", "expande", "expander", "muestramelo",
        "dejame ver", "dejamelo ver", "saca a la vista", "trae",
        "traeme", "sube", "subir", "monta en el editor"],
    "mover": [
        "mueve", "mover", "muevelo", "copia", "copiar", "copiame",
        "traslada", "trasladar", "cambia de lugar", "reubica",
        "reubicar", "desplaza", "desplazar", "lleva", "llevar",
        "mandamelo", "enviame", "envia", "enviar", "pasa", "pasar",
        "pasamelo", "duplica", "duplicar", "clona", "clonar",
        "replica", "replicar", "espejo", "espejame", "sincroniza",
        "sincronizar", "exporta", "exportar", "respalda", "respaldar",
        "backup", "salvame una copia", "pegalo", "pega en"],
    "renombrar": [
        "renombra", "renombrar", "renombrame", "cambia el nombre",
        "cambiale el nombre", "rename", "rellama", "rellamar",
        "llamalo", "llamala", "ponle el nombre", "bautiza", "bautizar",
        "rotula", "rotular", "etiqueta", "etiquetar", "re-etiqueta",
        "re-etiquetar", "titula", "titular", "denomina", "denominar",
        "rebautiza", "rebautizar", "cambiame el nombre"],
    "verificar": [
        "verifica", "verificar", "comprueba", "comprobar", "checa",
        "chequea", "chequear", "testa", "testear", "prueba", "probar",
        "valida", "validar", "confirma", "confirmar", "asegura",
        "asegurar", "certifica", "certificar", "garantiza",
        "corrobora", "corroborar", "constata", "constatar",
        "demuestra", "demostrar", "ejecuta el test", "corre la prueba",
        "haz la prueba", "hace la prueba", "hazme la prueba",
        "fijate", "fijate si", "mira si", "revisa si", "checa si",
        "comprueba si", "mide el rendimiento", "benchmark",
        "analizame el rendimiento"],
    "traducir": [
        "traduce", "traducir", "traducime", "traducilo", "traducila",
        "traduccion", "translate", "interpreta", "interpretame",
        "pasame a", "pasalo a", "convertilo a", "convierte a",
        "ponlo en", "ponlo en idioma", "dilo en", "decilo en",
        "escribilo en", "escribime en", "versiona a", "versioname a",
        "doblalo a", "subtitulalo a", "al idioma", "a otro idioma"],
    "ejecutar": [
        "ejecuta", "ejecutar", "corre", "correr", "correlo", "lanza",
        "lanzar", "arranca", "arrancar", "inicia", "iniciar",
        "dispara", "disparar", "activa", "activar", "enciende",
        "encender", "prende", "prender", "ponlo a correr", "hazlo",
        "hacelo", "hazmelo", "run", "deploya", "despliega",
        "levantalo", "levantar", "ponlo en marcha", "comandame",
        "ejecutame el comando", "pasame el comando"],
    "listar": [
        "lista", "listar", "listame", "muestrame que hay",
        "que hay en", "que contiene", "que tiene", "que archivos hay",
        "enumerame", "enumera", "enumerar", "cuentame que hay",
        "dime que hay", "decime que hay", "dejame ver que hay",
        "inventario", "inventariar", "catalogame", "escandallo",
        "escandallame", "pasame la lista", "dame la lista",
        "muestrame los archivos", "dime los archivos",
        "de que consta", "que carpetas hay"],
}

_RX = {k: re.compile(r"\b(" + "|".join(sorted(set(v), key=len,
                     reverse=True)) + r")", re.I)
       for k, v in VERBOS.items()}


def intenciones(texto):
    """Conjunto de intenciones detectadas en el mensaje."""
    t = _norm(texto or "")
    return {k for k, rx in _RX.items() if rx.search(t)}


def verbos_grupo(nombre):
    return list(VERBOS.get(nombre, []))
