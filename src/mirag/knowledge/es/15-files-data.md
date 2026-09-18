# 15 · Files & Data

> Mover bytes parece trivial hasta que alguien sube un vídeo de 4 GB, un CSV con 10 millones de filas o un
> archivo llamado `../../etc/passwd`. **La regla que lo gobierna todo: tu backend no debería tocar los bytes
> si puede evitarlo.**


**Cubre del temario:** `uploads` · `storage` · `processing` · `streaming` · `security` · `failure_modes`

---

## El patrón correcto: presigned URLs

**Mal:** cliente → tu servidor → S3. Tu app se come el ancho de banda, la memoria y el tiempo de request.
Un archivo de 2 GB te bloquea un worker durante minutos.

**Bien:**
```
1. Cliente pide permiso        → POST /uploads  {nombre, tipo, tamaño}
2. Tu backend valida y firma   → devuelve una URL prefirmada (PUT) + un upload_id
3. Cliente sube DIRECTO a S3   → PUT https://bucket.s3.../abc?X-Amz-Signature=...
4. Cliente avisa               → POST /uploads/{id}/completar
   (o mejor: S3 emite un evento y tu backend reacciona)
```

**Qué validas al firmar (paso 2), que es donde está la seguridad real:**
- Que el usuario tiene permiso y cuota disponible.
- **Tamaño máximo**, con `content-length-range` en la política de la firma (si no, suben 50 GB).
- **Content-type permitido**, incluido en la firma.
- **La clave del objeto la generas tú** (`tenant/{id}/uploads/{uuid}.jpg`) — **nunca uses el nombre que manda
  el cliente**: es path traversal y sobrescritura de archivos ajenos.
- **Expiración corta** de la URL (minutos).

**Para descargas** igual: presigned URL de lectura con expiración, en vez de proxyficar gigabytes. Si
necesitas control de acceso por request, firma la URL **después** de comprobar permisos.

> **Ficha** · **Cuándo:** cualquier subida o descarga de archivos ·
> **Patrón:** el backend solo valida y firma; los bytes van directos al object storage ·
> **Anti-patrón:** proxyficar gigabytes por tu aplicación ·
> **Límites:** la firma debe incluir `content-length-range` y tipo, o suben 50 GB ·
> **Cómo falla:** usar el nombre del cliente como clave permite path traversal y sobrescribir lo ajeno ·
> **Decisión:** la clave del objeto **la genera el servidor** (`tenant/{id}/uploads/{uuid}`) ·
> **Trade-off:** control (proxy) vs escalabilidad (directo) ·
> **Relacionado:** object storage, validación `[13]`

---

## Multipart y uploads resumibles

Para archivos grandes (>100 MB) o redes inestables:

1. `CreateMultipartUpload` → devuelve un `uploadId`.
2. Subir partes (mínimo 5 MB cada una salvo la última), **en paralelo**, cada una con su ETag.
3. `CompleteMultipartUpload` con la lista de partes.

**Ventajas:** reintentas **solo la parte fallida**, subes en paralelo (mucho más rápido), y puedes pausar y
reanudar.

**Detalle operativo que se olvida:** las subidas multipart **incompletas siguen ocupando y facturando**
espacio invisible. Configura una *lifecycle rule* que las aborte a los N días. Es un coste oculto clásico.

> **Ficha** · **Cuándo:** archivos grandes o redes inestables ·
> **Patrón:** trocear, subir en paralelo, reintentar solo la parte fallida ·
> **Anti-patrón:** reintentar la subida entera tras un corte al 90% ·
> **Límites:** mínimo 5 MB por parte salvo la última ·
> **Cómo falla:** los multipart **incompletos siguen facturando** espacio invisible ·
> **Decisión:** lifecycle rule que aborta subidas incompletas a los N días ·
> **Trade-off:** complejidad del cliente vs robustez y velocidad ·
> **Relacionado:** coste, object storage `[13]`

---

## Validación y seguridad de archivos

**Nunca confíes en:**
- **La extensión.** `foto.jpg` puede ser un ejecutable.
- **El `Content-Type` que manda el cliente.** Es un header, se falsifica.
- **El nombre del archivo.** Path traversal (`../../`), caracteres nulos, nombres reservados de Windows
  (`CON`, `PRN`), unicode engañoso, longitudes absurdas.

**Haz:**
- **Comprueba los magic bytes** (los primeros bytes del archivo) con una librería de detección de tipo, y
  verifica que coincidan con lo que dices aceptar.
- **Renombra siempre** a un identificador que generes tú; guarda el nombre original solo como metadato para
  mostrarlo.
- **Límites de tamaño** en la firma, en el proxy y en la aplicación.
- **Sirve desde otro dominio** (o un subdominio dedicado sin cookies) con `Content-Disposition: attachment`
  y `X-Content-Type-Options: nosniff`. Servir contenido subido desde tu dominio principal es **XSS almacenado
  con esteroides**: un SVG o un HTML subido ejecuta JavaScript con tus cookies.
- **Cuidado con los SVG:** son XML y pueden contener scripts. Sanitízalos o conviértelos a raster.
- **Zip bombs:** un zip de 1 MB puede descomprimirse en 1 TB. Limita el ratio y el tamaño descomprimido.
- **XXE:** al parsear XML del usuario, desactiva las entidades externas o expones archivos locales y SSRF.

**Virus scanning:** ClamAV (open source) o los servicios del cloud. El patrón habitual es **cuarentena**:
subir a un bucket aislado → escanear asíncronamente → mover al bucket definitivo solo si está limpio. El
archivo no es accesible mientras tanto. Obligatorio si los usuarios comparten archivos entre sí.

> **Ficha** · **Cuándo:** todo archivo que suba un usuario ·
> **Patrón:** magic bytes + límites de tamaño y dimensiones + renombrar siempre ·
> **Anti-patrón:** fiarse de la extensión o del `Content-Type` ·
> **Límites:** detectar el tipo real no garantiza que el contenido sea inofensivo ·
> **Cómo falla:** un SVG o HTML servido desde tu dominio es **XSS almacenado** con tus cookies `[06]` ·
> **Decisión:** sirve desde otro dominio, con `attachment` y `nosniff` ·
> **Trade-off:** restricción de formatos vs flexibilidad para el usuario ·
> **Relacionado:** XSS, headers, antivirus `[02, 06]`

---

## Procesamiento de imágenes y vídeo

**Imágenes:**
- **Nunca en el request.** Redimensionar es CPU y memoria: va a una cola (`08-distributed-systems.md`).
- **Genera derivados** (thumbnail, medio, grande) y sirve por CDN. Formatos modernos: WebP y AVIF con
  fallback.
- **Límites de "bomba de descompresión"**: una imagen de 50.000×50.000 píxeles ocupa gigabytes al
  descomprimirse aunque el archivo pese poco. Valida dimensiones **antes** de procesar.
- **Quita los metadatos EXIF** antes de servir: contienen **coordenadas GPS**, modelo de cámara y fecha.
  Es una fuga de privacidad real y frecuente.
- Alternativa: un servicio de transformación bajo demanda (imgproxy, Cloudinary) con URLs firmadas —
  menos almacenamiento y más flexibilidad.

**Vídeo:**
- **Transcodificación** a varias resoluciones y bitrates (mucho más caro que imágenes). Cola dedicada, o un
  servicio gestionado (MediaConvert, Mux).
- **Streaming adaptativo** (HLS/DASH): el vídeo se trocea y el reproductor elige la calidad según el ancho
  de banda. No se sirve un MP4 gigante.
- **Diseña para trabajos largos:** progreso consultable, reanudable, con timeout generoso y notificación al
  terminar (webhook o SSE al cliente).

> **Ficha** · **Cuándo:** cualquier media subido por usuarios ·
> **Patrón:** en cola, nunca en el request; derivados servidos por CDN ·
> **Anti-patrón:** redimensionar dentro del handler HTTP ·
> **Límites:** una imagen de 50.000×50.000 ocupa gigabytes al descomprimirse aunque pese poco ·
> **Cómo falla:** los metadatos **EXIF llevan coordenadas GPS**: fuga de privacidad al servirlos ·
> **Decisión:** valida dimensiones **antes** de procesar; quita EXIF siempre ·
> **Trade-off:** pregenerar derivados (almacenamiento) vs transformar bajo demanda (CPU y latencia) ·
> **Relacionado:** background jobs, CDN `[09]`

---

## CSV, Excel y exportaciones

**Importar:**
- **Streaming siempre.** Leer un CSV de 2 GB con `read()` es un OOM garantizado. Procesa fila a fila o en
  lotes.
- **Valida y reporta por filas**: no abortes todo por un error en la fila 8.432. Devuelve un informe de
  errores con número de línea y motivo, y decide la política (todo o nada / parcial con informe).
- **Procesa en background** con progreso. Un import de 500.000 filas no cabe en un request HTTP.
- **Idempotencia:** si el usuario sube el mismo archivo dos veces, no dupliques. Hash del archivo + clave
  natural por fila.
- **Trampas de encoding:** UTF-8 con y sin BOM, Latin-1, separadores `;` en Excel europeo, saltos de línea
  dentro de campos entrecomillados. Usa una librería de CSV de verdad, **nunca `split(",")`**.

**Exportar:**
- **Streaming** de la respuesta con un cursor del lado del servidor, no cargando todo en memoria.
- Si es grande: genera asíncronamente en S3 y manda un enlace por email o notificación.

**CSV injection (una vulnerabilidad que casi nadie conoce):** si un campo empieza por `=`, `+`, `-` o `@`,
Excel lo interpreta como fórmula y puede ejecutar comandos al abrirlo. **Escapa prefijando un apóstrofo**
en las exportaciones. Ha causado incidentes reales de ejecución de código en máquinas de usuarios.

> **Ficha** · **Cuándo:** importaciones y exportaciones de datos ·
> **Patrón:** streaming en ambos sentidos, por lotes, con informe de errores por fila ·
> **Anti-patrón:** `split(",")` en vez de una librería CSV, y cargar el archivo entero en memoria ·
> **Límites:** encodings (BOM, Latin-1), separadores `;` de Excel europeo, saltos de línea entrecomillados ·
> **Cómo falla:** **CSV injection** — un campo que empieza por `=` se ejecuta como fórmula al abrirlo ·
> **Decisión:** aborta todo o importa parcial con informe: decídelo y documéntalo ·
> **Trade-off:** validación estricta vs tolerancia a datos sucios reales ·
> **Relacionado:** background jobs, idempotencia `[08]`

---

## PDFs

- **Generación:** desde HTML (Puppeteer/Playwright/WeasyPrint — más fácil de maquetar) o con librerías
  (ReportLab). Es **CPU-intensivo y lento**: va a una cola, no al request.
- **Puppeteer en producción:** abre un navegador entero por documento. Limita la concurrencia, reutiliza el
  navegador, y ponle timeout — es una fuente clásica de fugas de memoria y de contenedores muertos.
- **Si el HTML incluye datos del usuario**, un `<img src="http://169.254.169.254/...">` dentro del documento
  te da **SSRF** desde el renderizador. Desactiva el acceso a red o restringe por allowlist.
- **Leer PDFs** (extracción de texto/tablas) es notoriamente irregular: PDFs escaneados necesitan OCR
  (Tesseract o servicios del cloud). No prometas exactitud sin probar con documentos reales.

> **Ficha** · **Cuándo:** facturas, informes, contratos ·
> **Patrón:** generar en cola, con timeout y concurrencia limitada ·
> **Anti-patrón:** abrir un navegador headless por documento dentro del request ·
> **Límites:** la extracción de texto es irregular; los escaneados necesitan OCR ·
> **Cómo falla:** un `<img src="http://169.254.169.254/...">` en el HTML da **SSRF** desde el renderizador `[06]` ·
> **Decisión:** desactiva el acceso a red del renderizador o restríngelo por allowlist ·
> **Trade-off:** HTML (fácil de maquetar, pesado) vs librerías (rápidas, rígidas) ·
> **Relacionado:** SSRF, background jobs `[06]`

---

## Background processing

Todo lo de esta caja acaba aquí. **Regla: si tarda más de ~1 segundo o puede fallar, no va en el request.**

```
POST /informes  →  202 Accepted + {job_id, status_url}
                   encola el trabajo
GET /jobs/{id}  →  {estado: "procesando", progreso: 45}
                → {estado: "listo", url_descarga: "..."}
```

- **Estado del job en la base de datos**: pendiente → procesando → completado / fallido, con progreso,
  resultado, error y timestamps.
- **Idempotencia y reintentos** (`08-distributed-systems.md`): un worker puede morir a mitad y el mensaje
  se reentrega. El job debe poder reanudarse o repetirse sin duplicar efectos.
- **Colas separadas por tipo y prioridad** (bulkheads): que un import de 2 horas no bloquee el envío de
  emails de verificación.
- **Visibilidad:** progreso para el usuario, y métricas de profundidad de cola y edad del mensaje más antiguo
  para ti.
- **Limpieza:** archivos temporales, jobs viejos y resultados caducados. El disco lleno es una causa de
  incidente sorprendentemente frecuente.

> **Ficha** · **Cuándo:** todo lo que tarde más de ~1 segundo o pueda fallar ·
> **Patrón:** 202 + `job_id` + estado consultable; colas separadas por prioridad ·
> **Anti-patrón:** generar un informe dentro del request HTTP ·
> **Límites:** el worker puede morir a mitad: el job debe ser reanudable o repetible ·
> **Cómo falla:** un import de 2 horas bloquea la cola de los emails de verificación ·
> **Decisión:** bulkheads — una cola por tipo de trabajo `[10]` ·
> **Trade-off:** complejidad (estado, progreso, limpieza) vs respuesta inmediata al usuario ·
> **Relacionado:** colas, idempotencia, bulkheads `[08, 10]`

---

## Retención, privacidad y ciclo de vida

- **Lifecycle rules** para bajar de clase de almacenamiento y borrar lo caducado: de las optimizaciones de
  coste más rentables que existen.
- **RGPD y borrado:** el derecho al olvido choca con los backups y con las obligaciones contables
  (`07-payments.md`). La solución habitual es **anonimizar** los datos personales conservando el
  registro económico, y documentar los plazos.
- **Cifrado en reposo** por defecto, y a nivel de campo lo realmente sensible.
- **Versionado y object lock** como defensa contra borrados accidentales y ransomware.
- **Nunca uses datos reales de producción en desarrollo.** Anonimiza o genera sintéticos.

> **Ficha** · **Cuándo:** al definir qué se guarda y cuánto ·
> **Patrón:** lifecycle rules + cifrado en reposo + versionado con object lock ·
> **Anti-patrón:** guardarlo todo para siempre por si acaso ·
> **Límites:** el derecho al borrado del RGPD choca con la retención contable obligatoria ·
> **Cómo falla:** los backups conservan datos que creías borrados ·
> **Decisión:** anonimiza los datos personales conservando el registro económico `[07]` ·
> **Trade-off:** coste y riesgo legal de guardar vs valor de los datos históricos ·
> **Relacionado:** cumplimiento, coste, backups `[06, 13]`

---

## Cómo falla el manejo de archivos

| Fallo | Causa | Mitigación |
|---|---|---|
| **Subida interrumpida** | red inestable, archivo grande | multipart resumible |
| **Multipart huérfano** | el cliente abandonó | lifecycle rule que aborta a los N días |
| **Archivo corrupto** | corte a mitad, o bytes alterados | **checksum del cliente** (`Content-MD5`/SHA-256) verificado al completar |
| **Tipo falseado** | se confió en la extensión | magic bytes |
| **XSS almacenado** | HTML/SVG servido desde tu dominio | dominio separado + `attachment` + `nosniff` |
| **Zip bomb** | 1 MB que descomprime 1 TB | límite de ratio y de tamaño descomprimido |
| **Bomba de imagen** | dimensiones enormes con poco peso | validar dimensiones antes de procesar |
| **Path traversal** | nombre del cliente usado como clave | clave generada por el servidor |
| **Disco lleno** | temporales sin limpiar | limpieza y cuotas; procesar en streaming |
| **OOM al procesar** | archivo cargado entero en memoria | streaming por lotes |
| **Huérfanos** | el registro en la DB falló tras subir | job de conciliación que borra lo que no referencia nadie |
| **Referencia rota** | se borró el objeto pero no la fila | borrado en dos fases con marca de pendiente |

**El caso que más se olvida: la consistencia entre el archivo y su registro.** Subir a S3 y guardar en la
base de datos son **dos escrituras a dos sistemas** — el mismo problema de doble escritura que resuelve el
outbox (`[08]`). El patrón práctico: crear la fila como `pendiente` → subir → marcar `listo`; y un job
periódico que limpia las `pendientes` viejas y los objetos sin fila.

```python
async def completar_subida(upload_id: str, actor: Usuario):
    registro = await repo.uploads.get(upload_id, tenant_id=actor.tenant_id)
    meta = await s3.head_object(Bucket=BUCKET, Key=registro.clave)     # ¿existe de verdad?

    if meta["ContentLength"] != registro.tamano_declarado:
        raise ArchivoInconsistente()
    if meta["ChecksumSHA256"] != registro.checksum_declarado:          # integridad real
        await s3.delete_object(Bucket=BUCKET, Key=registro.clave)
        raise ArchivoCorrupto()

    await repo.uploads.marcar_listo(upload_id)      # solo ahora es visible para el usuario
    await cola.encolar("procesar_archivo", upload_id)
```

> **Ficha** · **Cuándo:** toda subida que tenga registro en base de datos ·
> **Patrón:** pendiente → subir → verificar (tamaño y checksum) → listo, más job de limpieza ·
> **Anti-patrón:** marcar el archivo como disponible antes de comprobar que llegó entero ·
> **Límites:** no puedes garantizar atomicidad entre el object storage y la base de datos ·
> **Cómo falla:** huérfanos en ambos sentidos — objetos sin fila y filas sin objeto ·
> **Decisión:** el estado `pendiente` es lo que hace reconciliable la inconsistencia ·
> **Trade-off:** un paso extra y un job de limpieza a cambio de no acumular basura ni enlaces rotos ·
> **Relacionado:** outbox, conciliación, coste `[07, 08, 13]`

---

## Preguntas de entrevista y trade-offs

**Q: Diseña la subida de archivos de hasta 5 GB.**
Presigned multipart upload directo a S3; el backend solo valida permisos, cuota, tipo y tamaño al firmar, y
reacciona al evento de finalización. *Señal:* mencionas que el backend no debe proxyficar los bytes, el
abort de multiparts incompletos, y que la clave del objeto la genera el servidor.

**Q: ¿Cómo validas que un archivo es realmente una imagen?**
Magic bytes con una librería de detección, dimensiones máximas, y reconversión/normalización. *Señal:*
dices que ni la extensión ni el `Content-Type` sirven, y mencionas las bombas de descompresión y el problema
de los SVG con scripts.

**Q: ¿Por qué no servir los archivos subidos desde tu dominio principal?**
Porque un HTML o SVG subido ejecutaría JavaScript con acceso a las cookies de tu dominio. *Señal:* citas
`Content-Disposition: attachment`, `nosniff` y el dominio separado, y lo llamas por su nombre: XSS almacenado.

**Q: Un usuario sube un CSV de 2 GB con 10 millones de filas. ¿Cómo lo procesas?**
Subida directa a object storage, job en background, lectura en streaming por lotes, validación por filas con
informe de errores, progreso consultable e idempotencia por hash. *Señal:* mencionas el encoding y los
separadores como el problema real que más tiempo consume en la práctica.

**Q: ¿Qué es CSV injection?**
Que un campo que empieza por `=` se ejecute como fórmula al abrir el archivo en Excel. Se mitiga escapando
el prefijo. *Señal:* saberlo ya es la señal — es una vulnerabilidad que se pasa por alto casi siempre y
demuestra que piensas en el ciclo completo del dato, no solo en tu API.

**Trade-off central de esta caja:** *control vs coste y escalabilidad*. Cuanto más pasan los bytes por tu
aplicación, más control tienes (validación inmediata, transformación, autorización fina) y peor escalas.
La postura senior es **delegar el transporte al object storage y al CDN**, y quedarte con lo que sí es tuyo:
permisos, validación, metadatos y orquestación del procesamiento.

---

## Fuentes

- [AWS S3 — Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) y [Multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)
- [OWASP — File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP — CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection)
- [RFC 7233 — HTTP Range Requests](https://www.rfc-editor.org/rfc/rfc7233)
