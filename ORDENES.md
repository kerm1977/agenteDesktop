# Catálogo de órdenes del agente

El enrutador (`core/ordenes.py`, 449 sinónimos en 10 intenciones) entiende
todas estas formas y cualquier variante con sinónimos de la lista.
Para regenerar las miles de combinaciones completas:
`.venv\Scripts\python.exe gen_ordenes_md.py`

## Intenciones y sus verbos

### crear
crea, crear, créame, cree, genera, generar, genérame, haz, hace, haceme,
hácelo, fabrica, construye, construir, constrúyeme, arma, armar, ármame,
produce, producir, monta, montar, levanta, levantar, inicia, iniciar,
comienza, empezá, nueva, nuevo, quiero, necesito, agrega, agrégame, añade,
añadir, mete, métele, inventa, inventar, diseña, diseñar, desarrolla,
desarrollar, escribe, escribí, redacta, redactar, programa, programar,
codifica, codificar, lanza, lanzar, instala, instalar, implementa,
implementar, prepara, prepárame, fórmame, dale forma, levántame, pon,
ponme, setea, configura, maqueta, modela, compone, compílame, ensambla.

### borrar (incluye desinstalar y todas las formas de destruir)
borra, borrar, bórrame, elimina, eliminar, elimíname, quita, quitar,
quítame, suprime, suprimir, suprimí, delete, desaparece, desaparecer,
desaparéceme, fulmina, fulminar, destruye, destruir, aniquila, aniquilar,
saca, sacar, sácame, extermina, liquida, liquidar, barre, barrer, limpia,
limpiar, vacía, vaciar, desinstala, desinstalar, remueve, remover, retira,
retirar, erradica, tira, tirar, bota, botar, deshecha, desinstálame,
desmonta, desarma, desconecta, desvincula, expulsa, purga, púrgame,
trunca, nivélalo, fumígalo, échalo, sácalo, vétalo, bórralo, mata,
eliminalo, quítamelo.

### analizar / leer / resumir / verificar contenido
analiza, analizar, analízame, lee, leer, léeme, resume, resumir, resúmime,
examina, examinar, revisa, revisar, revísame, escanea, escanear, estudia,
estudiar, procesa, procesar, evalúa, evaluar, inspecciona, inspeccionar,
comprueba, comprobar, verifica, verificar, checa, chequea, mira, mirar,
mírame, observa, observar, detecta, detectar, audita, auditar, escudriña,
investiga, investigar, diagnostica, diagnosticar, interpreta, interpretar,
descifra, descifrar, explícame, cuéntame, muéstrame el contenido,
enséñame, detalla, detallar, desglosa, desglosar, desmenuza, explora,
explorar, radiografía, supervisa, controla, monitorea, vigila, mide,
medir, cuantifica, cataloga, inventaria, mapea, mapear, traza, trazar,
sondea, palpa, disecciona, escarba, escárbame, descompón, desarma el,
abre el contenido, reporta, repórtame, infórmame, avísame qué dice,
qué dice, qué contiene, cuéntame de qué trata.

### abrir / mostrar
abre, abrir, ábrimelo, ábrimela, muéstrame, muéstramelo, mostráme,
enséñame, enséñamelo, despliega, desplegar, visualiza, visualizar,
presenta, presentar, carga, cargar, lanza la vista, expande, expandir,
déjame ver, saca a la vista, trae, tráeme, sube, subir, monta en el
editor.

### mover / copiar / respaldar
mueve, mover, muévelo, copia, copiar, cópiame, traslada, trasladar,
cambia de lugar, reubica, reubicar, desplaza, desplazar, lleva, llevar,
mándamelo, envíame, envía, enviar, pasa, pasar, pásamelo, duplica,
duplicar, clona, clonar, réplica, replicar, espejo, espéjame, sincroniza,
sincronizar, exporta, exportar, respalda, respaldar, backup, sálvame una
copia, pégalo, pega en.

### renombrar
renombra, renombrar, renómbrame, cambia el nombre, cámbiale el nombre,
rename, rellama, rellamar, llámalo, llámala, ponle el nombre, bautiza,
bautizar, rotula, rotular, etiqueta, etiquetar, re-etiqueta, titula,
titular, denomina, denominar, rebautiza, rebautizar, cámbiame el nombre.

### verificar / probar / testear
verifica, verificar, comprueba, comprobar, checa, chequea, chequear,
testa, testear, prueba, probar, valida, validar, confirma, confirmar,
asegura, asegurar, certifica, certificar, garantiza, corrobora,
corroborar, constata, constatar, demuestra, demostrar, ejecuta el test,
corre la prueba, haz la prueba, hazme la prueba, fíjate, fíjate si,
mira si, revisa si, checa si, comprueba si, mide el rendimiento,
benchmark, analízame el rendimiento.

### traducir
traduce, traducir, tradúcime, tradúcilo, tradúcila, traducción,
translate, interpreta, interprétame, pásame a, pásalo a, conviértelo a,
convierte a, ponlo en, ponlo en idioma, dilo en, decilo en, escríbalo
en, escríbeme en, versiona a, dóblalo a, subtitúlalo a, al idioma,
a otro idioma.

### ejecutar / correr / lanzar
ejecuta, ejecutar, corre, correr, córrelo, lanza, lanzar, arranca,
arrancar, inicia, iniciar, dispara, disparar, activa, activar, enciende,
encender, prende, prender, ponlo a correr, hazlo, hácelo, házmelo, run,
deploya, despliega, levántalo, levántalo, ponlo en marcha, comándame,
ejecútame el comando, pásame el comando.

### listar / inventariar
lista, listar, lístame, muéstrame qué hay, qué hay en, qué contiene,
qué tiene, qué archivos hay, enumérame, enumera, enumerar, cuéntame qué
hay, dime qué hay, decime qué hay, déjame ver qué hay, inventario,
inventariar, catálogame, escandallo, escandállame, pásame la lista,
dame la lista, muéstrame los archivos, dime los archivos, de qué consta,
qué carpetas hay.

## Estructuras de preguntas → respuestas esperadas

| Patrón del usuario | Comportamiento del agente |
|---|---|
| "¿sabes programar?" | "Sí, programo en HTML, CSS, JS, Vue, Python, Capacitor… ¿qué construimos?" |
| "¿cómo te llamas?" | "Soy Mini Agente, tu agente de código local." |
| "¿tienes sentimientos?" | "No tengo sentimientos como los humanos, pero entiendo lo que me pides." |
| "¿puedes hacer X?" | "Sí. ¿Qué X exactamente?" — y si es orden clara, ejecuta. |
| "crea/haz/genera + página/sitio/web/html" | Genera carpeta + index.html con CDN y la abre en el editor. |
| "crea + carpeta/archivo (+ nombre) (+ lugar)" | create_dir / write_file al instante. |
| "borra/elimina/desinstala + nombre o ruta" | delete_path con su contenido. |
| "renombra X a Y" | os.rename / move real. |
| "mueve/copia X a Y" | mover/copiar real. |
| "abre/muéstrame + carpeta/proyecto" | La abre como raíz en el árbol del editor. |
| "lee/analiza/resume + archivo/pdf/docx" | read_doc y resumen. |
| "clona + URL de GitHub" | clone_repo + abrir en editor. |
| "qué hay en + carpeta" | list_dir. |
| "traduce + texto (+ idioma)" | Traducción al idioma pedido. |
| "¿dónde/cuál/qué/cuándo…?" | Pregunta → responde el modelo, nunca ejecuta acción. |
| Orden sin datos ("borra eso") | Pregunta solo el dato faltante. |

## Objetos reconocidos

carpeta, directorio, archivo, documento, fichero, página, sitio, web,
single page, index.html, app, aplicación, programa, juego, proyecto,
script, código, texto, pdf, word, excel, powerpoint, repositorio, repo.

## Ubicaciones reconocidas

escritorio, descargas, documentos, proyectos, una ruta absoluta
(C:\..., /home/...) o "aquí"/"ahí"/"en mi pc".

## Regla de oro

Las preguntas ("dónde", "cuál", "qué es", "por qué", "cómo se llama")
nunca ejecutan acciones — van al modelo. Las órdenes sí.
