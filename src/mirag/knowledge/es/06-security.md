# 06 · Security

> **Autenticación = quién eres. Autorización = qué puedes hacer.** Confundirlas en una entrevista es
> descalificatorio. La mayoría de las brechas reales no son criptografía rota: son autorización mal hecha.


**Cubre del temario:** `concepts` · `authentication` · `authorization` · `attacks` · `cryptography` · `implementations` · `constraints` · `failure_modes` · `tradeoffs`

---

## Sessions vs tokens

### Sesiones con cookie (stateful)

El servidor guarda la sesión (Redis/DB) y el cliente solo lleva un ID opaco en una cookie.

```
Set-Cookie: sid=aleatorio_de_256_bits; HttpOnly; Secure; SameSite=Lax; Path=/
```

- ✅ **Revocación instantánea** (borras la sesión del store y se acabó).
- ✅ El token no contiene datos: si se filtra, no revela nada.
- ✅ Puedes cambiar permisos y aplican al instante.
- ❌ Estado compartido (necesitas Redis) y requiere cuidado con CSRF.

### JWT (stateless)

Un token firmado que **contiene** los claims. `header.payload.signature`, base64url.

```json
{"sub":"user_42","exp":1789..., "iat":1789..., "iss":"api.tuapp.com", "aud":"api", "scope":"pedidos:read"}
```

- ✅ No necesitas consultar un store en cada request; cómodo entre servicios.
- ❌ **No se puede revocar** antes de que expire (sin añadir una denylist, que te devuelve al estado).
- ❌ El payload es **legible por cualquiera** (firmado ≠ cifrado). Nunca metas datos sensibles.
- ❌ Si cambias el rol de un usuario, su token viejo sigue diciendo "admin" hasta que caduque.

**Errores de JWT que preguntan en entrevistas:**
1. **`alg: none`** — el atacante quita la firma. Tu librería debe tener una **allowlist de algoritmos**.
2. **Confusión RS256/HS256** — el atacante firma con la clave *pública* como si fuera secreto HMAC.
3. **No validar `exp`, `iss`, `aud`** — un token de otro entorno o de otro servicio te vale.
4. **Guardarlo en `localStorage`** — cualquier XSS lo roba. Cookie `HttpOnly` es más segura.
5. **Expiración larga** — un JWT de 30 días es una llave maestra.

**El patrón correcto:** **access token corto (5-15 min) + refresh token largo, opaco y revocable**,
guardado en cookie `HttpOnly`, con **rotación**: cada uso del refresh emite uno nuevo e invalida el anterior.
Si se reutiliza uno ya usado, es señal de robo → **invalidas toda la familia de tokens de ese usuario**.
(Esto se llama *refresh token rotation with reuse detection* y es lo que se espera que sepas en 2026.)

**Cuándo cada uno:** app web con un solo backend → **sesiones**, casi siempre. Microservicios, APIs públicas,
móvil o federación → JWT con la disciplina de arriba.

> **Ficha** · **Cuándo:** al diseñar el login de cualquier sistema ·
> **Patrón:** access token corto + refresh largo, opaco, **rotativo con detección de reuso** ·
> **Anti-patrón:** JWT de 30 días en `localStorage` ·
> **Límites:** **un JWT no se puede revocar** antes de que expire sin volver al estado ·
> **Cómo falla:** cambias el rol de un usuario y su token sigue diciendo "admin" hasta caducar ·
> **Decisión:** ¿un solo backend y web? Sesiones. ¿APIs distribuidas o móvil? Tokens con rotación ·
> **Trade-off:** revocación inmediata (sesiones, exige estado) vs independencia (JWT, exige caducidad corta) ·
> **Relacionado:** cookies, OAuth2, CSRF `[02]`

---

## OAuth2 y OpenID Connect

**OAuth2 es autorización delegada**, no autenticación. **OIDC es la capa de autenticación encima de OAuth2**
(añade el `id_token`, que sí dice quién es el usuario). Usar el `access_token` de OAuth2 para "iniciar sesión"
es el error conceptual clásico.

**Roles:** Resource Owner (el usuario) · Client (tu app) · Authorization Server (Google, Auth0) ·
Resource Server (la API).

**Flujos:**
- **Authorization Code + PKCE** — **el único que debes usar** para web, SPA y móvil. PKCE (`code_verifier` /
  `code_challenge`) evita que alguien que intercepte el `code` lo canjee.
- **Client Credentials** — máquina a máquina, sin usuario.
- **Device Code** — TVs y dispositivos sin teclado.
- ~~Implicit~~ y ~~Password (ROPC)~~ — **deprecados**. Decir que usarías implicit en una entrevista es una
  bandera roja.

**Detalles que importan:** el parámetro `state` (anti-CSRF del propio flujo), `nonce` en OIDC (liga el
`id_token` a tu petición), validar la firma del `id_token` contra el JWKS del proveedor, y **redirect URIs
en allowlist exacta** (un `redirect_uri` con comodín es cómo se roban cuentas).

> **Ficha** · **Cuándo:** login social, federación y acceso delegado ·
> **Patrón:** **Authorization Code + PKCE**, siempre; `state` y `nonce` obligatorios ·
> **Anti-patrón:** flujo Implicit o Password (ROPC) — deprecados; nombrarlos es bandera roja ·
> **Límites:** OAuth2 es **autorización**; para autenticar necesitas OIDC y el `id_token` ·
> **Cómo falla:** un `redirect_uri` con comodín permite robar el código de autorización ·
> **Decisión:** valida siempre firma, `iss`, `aud` y `exp` contra el JWKS del proveedor ·
> **Trade-off:** delegar identidad (menos contraseñas que guardar) vs depender de un tercero ·
> **Relacionado:** JWT, integraciones OAuth `[16]`

---

## Autorización: RBAC y ABAC

- **RBAC** — permisos por rol (`admin`, `editor`, `viewer`). Simple, auditable, y se queda corto en cuanto
  aparece multi-tenancy ("es admin **de su organización**").
- **ABAC** — decisión en función de atributos (usuario, recurso, acción, contexto): *"puede editar si
  `recurso.owner_id == usuario.id` y es horario laboral"*. Flexible, más difícil de auditar.
- **ReBAC** — basado en relaciones (el modelo de Google Zanzibar, y de OpenFGA / SpiceDB): *"puede ver el
  documento si es miembro de la carpeta que lo contiene"*. Es hacia donde va la industria para permisos
  jerárquicos complejos.

**Los principios que se evalúan:**
- **Deny by default.** Todo prohibido salvo lo explícitamente permitido.
- **Autoriza en el servidor, sobre cada objeto.** Ocultar un botón en el frontend no es autorización.
- **IDOR / BOLA** (*Insecure Direct Object Reference* / *Broken Object Level Authorization*) es
  **la vulnerabilidad nº1 de APIs en el OWASP API Top 10**: `GET /facturas/1234` devuelve la factura de otro
  porque solo comprobaste que estás autenticado. **Cada acceso debe verificar la propiedad del recurso**, y
  la forma robusta es que la query lo incluya: `WHERE id = $1 AND tenant_id = $2`.
- **Centraliza la decisión** (una capa de policy) pero **aplícala en el punto de acceso a datos**, que es el
  único sitio por el que pasa todo.

> **Ficha** · **Cuándo:** desde el primer endpoint que devuelva datos de alguien ·
> **Patrón:** deny by default + comprobación **a nivel de objeto**, en la propia query ·
> **Anti-patrón:** comprobar solo autenticación y confiar en el ID de la URL (**IDOR/BOLA**) ·
> **Límites:** RBAC se queda corto en cuanto hay multi-tenancy ("admin **de su** organización") ·
> **Cómo falla:** es el **nº1 del OWASP API Top 10** y no genera ningún error: solo fuga silenciosa ·
> **Decisión:** hazlo imposible por construcción (RLS o repositorio con scope), no con un `if` por endpoint ·
> **Trade-off:** granularidad (ABAC/ReBAC) vs auditabilidad y rendimiento ·
> **Relacionado:** multi-tenancy, permisos `[17]`

---

## MFA

- **TOTP** (apps de autenticación, RFC 6238): secreto compartido + tiempo. Barato y bueno.
- **WebAuthn / Passkeys** — criptografía asimétrica ligada al dominio: **resistente a phishing**, que es lo
  que TOTP y SMS no son. Es el estándar al que todo el mundo está migrando.
- **SMS** — el más débil (SIM swapping), pero mejor que nada.
- **Códigos de recuperación** de un solo uso, hasheados en la DB.
- **Detalle que se olvida:** al activar MFA hay que **invalidar las sesiones existentes**, y las operaciones
  sensibles (cambiar email, retirar dinero) deben pedir **re-autenticación**, no fiarse de la sesión.

> **Ficha** · **Cuándo:** cuentas con acceso a dinero, datos personales o administración ·
> **Patrón:** WebAuthn/passkeys como primera opción; TOTP como alternativa ·
> **Anti-patrón:** SMS como único segundo factor (SIM swapping) ·
> **Límites:** TOTP y SMS **no** resisten phishing; WebAuthn sí, porque está ligado al dominio ·
> **Cómo falla:** activar MFA sin invalidar las sesiones existentes deja la puerta abierta ·
> **Decisión:** operaciones sensibles piden **re-autenticación**, no basta la sesión ·
> **Trade-off:** seguridad vs fricción y tickets de soporte por pérdida de dispositivo ·
> **Relacionado:** sessions, recuperación de cuenta `[16]`

---

## Password hashing

```
NUNCA: md5, sha1, sha256 (son rápidas — esa es exactamente la propiedad que no quieres)
SÍ:    Argon2id  (primera opción en 2026)
       scrypt
       bcrypt    (aceptable; ojo con el límite de 72 bytes)
       PBKDF2    (si necesitas cumplir FIPS)
```

- Son **lentas a propósito** y con **salt por usuario** (que va dentro del hash, no es secreto).
- **Argon2id** además resiste ataques con GPU/ASIC porque consume memoria. Parámetros orientativos:
  ~19-64 MB de memoria, 2-3 iteraciones, paralelismo 1-4; ajústalos a que tarde ~100-250 ms en tu hardware.
- **Pepper** (secreto global, fuera de la DB) añade defensa si te roban solo la base de datos.
- **Al verificar, compara en tiempo constante** y devuelve **el mismo error** para "usuario no existe" y
  "contraseña incorrecta" (si no, tienes un oráculo de enumeración de usuarios). Cuidado también con el
  *timing*: si el usuario no existe y no hasheas nada, respondes más rápido y te delatas.
- **Política moderna (NIST):** longitud mínima 8-12, **sin** caducidad forzada, **sin** reglas absurdas de
  caracteres, y **comprobar contra listas de contraseñas filtradas** (k-anonymity con HaveIBeenPwned).

> **Ficha** · **Cuándo:** si guardas contraseñas (y plantéate no hacerlo) ·
> **Patrón:** **Argon2id** con parámetros calibrados a ~100-250 ms en tu hardware ·
> **Anti-patrón:** SHA-256 o MD5 — son rápidas, que es justo la propiedad que no quieres ·
> **Límites:** bcrypt trunca a 72 bytes; subir los parámetros de Argon2 consume RAM por login ·
> **Cómo falla:** mensajes distintos para "usuario no existe" y "contraseña incorrecta" permiten enumerar cuentas ·
> **Decisión:** política NIST — longitud mínima, **sin** caducidad forzada, contrastar con listas filtradas ·
> **Trade-off:** coste de verificación (defensa) vs latencia del login y CPU del servidor ·
> **Relacionado:** cryptography, timing attacks `[01]`

---

## Encryption y secrets

- **En tránsito:** TLS 1.3 en todas partes, también dentro de tu VPC (mTLS entre servicios).
- **En reposo:** cifrado de disco/volumen (lo da el cloud) + cifrado a nivel de campo para lo realmente
  sensible. **Envelope encryption**: una clave de datos (DEK) por registro, cifrada con una clave maestra
  (KEK) que vive en un KMS/HSM. Rotar la KEK no obliga a recifrar todos los datos.
- **Simétrico** (AES-GCM, ChaCha20-Poly1305) — rápido, una clave. **Usa siempre AEAD** (cifra *y* autentica);
  AES-CBC sin MAC es vulnerable a padding oracle.
- **Asimétrico** (RSA, Ed25519) — firma y establecimiento de claves.
- **Nunca inventes criptografía.** Usa libsodium o la del lenguaje. Y nunca reutilices un nonce/IV.
- **Hashing ≠ cifrado ≠ codificación.** Base64 no es seguridad.

**Secrets management:**
- Nunca en el repo. Nunca en la imagen de Docker. Nunca en logs (cuidado con loguear el objeto request entero).
- Vault, AWS Secrets Manager, GCP Secret Manager, o variables de entorno inyectadas por la plataforma.
- **Rotación** sin downtime: acepta la clave vieja y la nueva durante la ventana de transición.
- **Secret scanning** en CI y en el pre-commit. Y si un secreto se filtró: **rotarlo es obligatorio**;
  borrar el commit no sirve de nada porque ya está en los forks y en los logs de CI.

> **Ficha** · **Cuándo:** datos sensibles en reposo y toda credencial ·
> **Patrón:** AEAD (AES-GCM/ChaCha20-Poly1305) + envelope encryption con KMS ·
> **Anti-patrón:** inventar criptografía, reutilizar un nonce, o meter secretos en la imagen Docker ·
> **Límites:** cifrar en reposo no protege de una app comprometida, que tiene la clave ·
> **Cómo falla:** un secreto filtrado sigue en los forks y en los logs de CI: **borrar el commit no sirve** ·
> **Decisión:** si se filtró, **rotar es obligatorio**, no opcional ·
> **Trade-off:** cifrado a nivel de campo (protege más) vs imposibilidad de indexar y buscar ·
> **Relacionado:** secrets management, IAM `[13, 14]`

---

## OWASP: las vulnerabilidades que debes saber explicar

### Injection (SQL, NoSQL, comandos)
```python
# vulnerable
cur.execute(f"SELECT * FROM usuarios WHERE email = '{email}'")
# correcto: consultas parametrizadas, SIEMPRE
cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
```
Los ORMs protegen **salvo** cuando concatenas SQL crudo o pasas nombres de columna dinámicos (esos no se
pueden parametrizar: valida contra una allowlist). En NoSQL, el equivalente es pasar un objeto donde
esperabas un string: `{"$gt": ""}` como contraseña.

### XSS
Ejecutar JS del atacante en el navegador de la víctima. **Stored** (guardado en tu DB), **reflected**
(en la respuesta), **DOM-based** (en el cliente).
Defensa: **escapado contextual por defecto** (los templates modernos lo hacen), `Content-Security-Policy`,
cookies `HttpOnly`, y sanitizar HTML con una librería probada (DOMPurify) si de verdad necesitas permitirlo.
**Como backend te importa** porque tu API es la que devuelve el dato que alguien pintará.

### CSRF
El navegador de la víctima envía una request autenticada sin que ella quiera (porque las cookies viajan
solas). **Solo aplica a autenticación por cookie**, no a `Authorization: Bearer`.
Defensa: `SameSite=Lax/Strict`, **token anti-CSRF** (double-submit o sincronizado con la sesión), y
comprobar `Origin`/`Referer`. Y que los GET no muten estado nunca.

### SSRF
Haces que tu servidor pida una URL que controla el atacante → alcanza servicios internos, o el
**endpoint de metadatos del cloud** (`169.254.169.254`) y roba credenciales IAM. **Ha causado brechas
enormes (Capital One).**
Defensa: allowlist de dominios, resolver el DNS y **bloquear rangos privados** (10/8, 172.16/12, 192.168/16,
127/8, 169.254/16), no seguir redirecciones ciegamente, IMDSv2 en AWS, y salida a internet a través de un
proxy controlado. **Muy relevante si tu backend descarga URLs que da el usuario o llama a herramientas de un
agente de IA** (ver `18-ai-backend.md`).

### Otros del top
- **Broken access control** (IDOR/BOLA) — el nº1. Ya cubierto arriba.
- **Security misconfiguration** — debug activado, permisos por defecto, buckets S3 públicos, CORS `*`.
- **Vulnerable components** — dependencias sin parchear; `npm audit`/Dependabot y SBOM.
- **Insecure deserialization** — `pickle` de Python o la deserialización nativa de Java sobre datos de
  usuario es ejecución remota de código. Usa JSON.
- **SSTI** — template injection: renderizar una plantilla con input del usuario.
- **Mass assignment** — ya visto en `03-apis.md`.
- **Path traversal** — `../../etc/passwd`. Normaliza la ruta y verifica que sigue dentro del directorio base.

> **Ficha** · **Cuándo:** en cada revisión de código y antes de exponer nada ·
> **Patrón:** consultas parametrizadas, escapado contextual, allowlists, mínimo privilegio ·
> **Anti-patrón:** sanear con expresiones regulares propias en vez de usar la primitiva correcta ·
> **Límites:** los ORMs protegen salvo en SQL crudo y nombres de columna dinámicos ·
> **Cómo falla:** **SSRF** alcanza el endpoint de metadatos del cloud y roba credenciales IAM ·
> **Decisión:** toda entrada de usuario que se convierta en URL, consulta, HTML o ruta necesita su defensa específica ·
> **Trade-off:** validación estricta rompe casos legítimos raros y evita clases enteras de ataques ·
> **Relacionado:** IDOR, deserialización, IAM `[13, 18]`

---

## Security headers

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; object-src 'none'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

- **HSTS** obliga a HTTPS en visitas futuras (elimina el downgrade). `preload` es difícil de revertir:
  pruébalo primero con `max-age` bajo.
- **CSP** es la defensa en profundidad contra XSS. La versión seria usa **nonces o hashes**, no
  `unsafe-inline`. Despliégala primero en `Content-Security-Policy-Report-Only`.
- **`frame-ancestors 'none'`** sustituye al viejo `X-Frame-Options` (clickjacking).
- **`nosniff`** evita que el navegador adivine el tipo y ejecute como JS algo que subió un usuario.

> **Ficha** · **Cuándo:** en toda respuesta HTML, y varios también en APIs ·
> **Patrón:** HSTS + CSP con nonces + `nosniff` + `frame-ancestors 'none'` ·
> **Anti-patrón:** CSP con `unsafe-inline` — no protege de casi nada ·
> **Límites:** `preload` de HSTS es difícil de revertir; pruébalo con `max-age` bajo ·
> **Cómo falla:** sin `nosniff`, un archivo subido por un usuario se ejecuta como JavaScript ·
> **Decisión:** despliega CSP primero en `Report-Only` y mide antes de forzar ·
> **Trade-off:** defensa en profundidad vs romper scripts de terceros legítimos ·
> **Relacionado:** XSS, uploads, CORS `[02, 15]`

---

## Webhook signatures y token rotation

**Verificar un webhook entrante (el patrón de Stripe/GitHub):**
```python
import hmac, hashlib, time

def verificar(payload_crudo: bytes, cabecera_firma: str, secreto: str, tolerancia=300):
    ts, firma = parsear(cabecera_firma)
    if abs(time.time() - int(ts)) > tolerancia:        # 1) anti-replay
        raise ValueError("timestamp fuera de tolerancia")
    esperada = hmac.new(secreto.encode(), f"{ts}.".encode() + payload_crudo, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperada, firma):        # 2) comparación en tiempo constante
        raise ValueError("firma inválida")
```
**Tres cosas que se hacen mal:** firmar el body **ya parseado** en vez del crudo (cualquier reserialización
cambia bytes y rompe la firma), comparar con `==` (timing attack), y no comprobar el timestamp (replay).

**Rotación de claves y tokens:** siempre con **ventana de solapamiento** — el sistema acepta la clave vieja
y la nueva durante un tiempo, se migra a los clientes, y luego se retira la vieja. Aplica igual a claves de
firma de JWT (publica varias en el JWKS con distintos `kid`), a secretos de webhook y a API keys.

> **Ficha** · **Cuándo:** al emitir o recibir webhooks, y al rotar cualquier clave ·
> **Patrón:** HMAC sobre el **body crudo** + timestamp en la firma + `compare_digest` ·
> **Anti-patrón:** firmar el body ya parseado, o comparar con `==` (timing attack) ·
> **Límites:** la firma prueba origen e integridad, **no** evita duplicados: deduplica aparte ·
> **Cómo falla:** sin comprobar el timestamp, un atacante reproduce una petición válida antigua ·
> **Decisión:** toda rotación con ventana de solapamiento: acepta clave vieja y nueva a la vez ·
> **Trade-off:** ventana de solapamiento (sin downtime) vs periodo con dos claves válidas ·
> **Relacionado:** webhooks, integraciones `[03, 16]`

---

## Implementación: la pila de seguridad de un servicio

El orden importa tanto como las piezas.

```python
# 1) Autenticacion: resuelve QUIEN eres. No decide nada mas.
async def autenticar(request) -> Usuario:
    token = request.cookies.get("sid") or extraer_bearer(request)
    if not token:
        raise NoAutenticado()                       # -> 401
    sesion = await store.obtener(token)             # opaco -> lookup; JWT -> verificar firma
    if not sesion or sesion.expirada:
        raise NoAutenticado()
    return sesion.usuario

# 2) Autorizacion a nivel de objeto: se decide SOBRE EL RECURSO, no sobre la ruta.
def autorizar(actor: Usuario, accion: str, recurso=None):
    if accion not in PERMISOS.get(actor.rol, ()):
        raise SinPermiso()                          # -> 403
    if recurso is not None and recurso.tenant_id != actor.tenant_id:
        raise NoEncontrado()                        # -> 404, NO 403: no reveles que existe

# 3) La defensa que de verdad funciona: que la query no pueda devolver lo ajeno.
class RepositorioConScope:
    def __init__(self, sesion, tenant_id):
        self.sesion, self.tenant_id = sesion, tenant_id

    def pedidos(self):
        return self.sesion.query(Pedido).filter(Pedido.tenant_id == self.tenant_id)
        #                                       ^ imposible olvidarlo en el endpoint nuevo
```

**El detalle del 404 vs 403:** devolver 403 sobre un recurso ajeno confirma que **existe**. Para recursos
privados, 404 es la respuesta correcta.

**Row-Level Security de Postgres** lleva la defensa al motor, donde ningún desarrollador puede saltársela:

```sql
ALTER TABLE pedidos ENABLE ROW LEVEL SECURITY;
CREATE POLICY aislamiento ON pedidos
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- y en cada conexion del pool: SET app.tenant_id = '...';
```

> **Ficha** · **Cuándo:** todo servicio multi-usuario ·
> **Patrón:** autenticar en middleware, autorizar por objeto, y **hacer cumplir el scope en la capa de datos** ·
> **Anti-patrón:** un `if usuario.rol == "admin"` repetido por endpoints ·
> **Límites:** RLS exige propagar el tenant por conexión; con PgBouncer en modo transaction hay que fijarlo por transacción ·
> **Cómo falla:** el endpoint nuevo que alguien añade el mes que viene olvida el filtro ·
> **Decisión:** si la defensa depende de recordar algo, acabará fallando ·
> **Trade-off:** enforcement en la DB (robusto, rígido) vs en la app (flexible, olvidable) ·
> **Relacionado:** multi-tenancy, IDOR, connection pooling `[04, 17]`

---

## Constraints: cumplimiento y límites del sistema

| Restricción | Qué te obliga a hacer |
|---|---|
| **RGPD** | base legal, minimización, derecho de acceso y borrado, **notificar brechas en 72 h** |
| **PCI DSS** | no tocar datos de tarjeta si puedes evitarlo; el widget del PSP reduce el alcance a SAQ A `[07]` |
| **SOC 2 / ISO 27001** | control de accesos, audit logs, gestión de cambios, revisión periódica de permisos |
| **Residencia de datos** | infraestructura por región; condiciona la arquitectura entera `[05]` |
| **Retención** | obligación contable de conservar años **vs** derecho al borrado: anonimizar, no borrar |
| **Sectorial** (HIPAA, PSD2…) | cifrado específico, MFA obligatoria, registro de accesos de lectura |

**Threat modeling** — el ejercicio de media hora que evita la mitad de los incidentes. Dibuja el flujo de
datos, marca los **límites de confianza** (dónde un dato pasa de no fiable a fiable) y en cada uno pregunta
**STRIDE**: *Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of
privilege*.

```
[navegador] --(no confiable)--> [CDN/WAF] --> [API] --(confiable)--> [DB]
                                              |
                                              +--(NO confiable)--> [webhook de terceros]
                                              +--(NO confiable)--> [contenido recuperado por un agente] [18]
```

**Los límites de confianza que la gente olvida:** los webhooks entrantes, los archivos subidos, el
contenido que tu backend descarga de una URL, y **el texto que le llega a un LLM** — que puede contener
instrucciones (`[18]`).

> **Ficha** · **Cuándo:** al diseñar una feature que toca datos personales o dinero ·
> **Patrón:** STRIDE sobre un diagrama de flujo de datos, con los límites de confianza marcados ·
> **Anti-patrón:** tratar el cumplimiento como papeleo posterior en vez de requisito de diseño ·
> **Límites:** el cumplimiento normativo **no** es seguridad; es el suelo, no el techo ·
> **Cómo falla:** el dato personal aparece en un log o en una herramienta de analítica, no en la base de datos ·
> **Decisión:** si no sabes dónde están tus datos personales, no puedes cumplir nada ·
> **Trade-off:** aislamiento por cliente o región (caro) vs cumplimiento y ventas enterprise ·
> **Relacionado:** PCI, audit logs, retención `[07, 15, 17]`

---

## Cómo falla la seguridad en la práctica

Los incidentes reales rara vez son criptografía rota. Por frecuencia:

| Fallo | Cómo entra | Qué lo habría evitado |
|---|---|---|
| **Autorización rota (IDOR)** | cambiar un ID en la URL | scope en la capa de datos |
| **Credencial filtrada** | en el repo, en un log, en una imagen | secret scanning + rotación + OIDC en vez de claves |
| **Dependencia vulnerable** | una transitiva sin parchear | Dependabot, SBOM, actualizar |
| **Bucket público** | configuración por defecto | bloqueo de acceso público a nivel de cuenta |
| **SSRF → credenciales IAM** | una URL que da el usuario | allowlist, bloquear rangos privados, IMDSv2 |
| **Ingeniería social** | phishing al equipo | passkeys (resisten phishing), 4 ojos para lo crítico |
| **Insider o cuenta comprometida** | permisos excesivos acumulados | mínimo privilegio + revisión periódica |
| **Inyección** | SQL crudo concatenado | consultas parametrizadas |
| **XSS almacenado** | archivo subido servido desde tu dominio | dominio separado + `nosniff` + `attachment` `[15]` |

**Defensa en profundidad:** ninguna capa es suficiente. WAF, autenticación, autorización, mínimo
privilegio, cifrado, monitorización y capacidad de respuesta. Diseña asumiendo que **una de ellas fallará**,
y que el objetivo es limitar el radio de impacto (`[10]`).

> **Ficha** · **Cuándo:** al priorizar trabajo de seguridad ·
> **Patrón:** invertir por probabilidad × impacto — autorización y secretos primero ·
> **Anti-patrón:** discutir el algoritmo de cifrado mientras tienes un IDOR sin cubrir ·
> **Límites:** no existe "seguro"; existe "cuánto cuesta atacarnos" ·
> **Cómo falla:** los fallos graves son **silenciosos**: nadie recibe una alerta por una fuga de datos ·
> **Decisión:** si no puedes detectarlo, no puedes responder: monitorización antes que más controles ·
> **Trade-off:** seguridad vs usabilidad y velocidad de entrega ·
> **Relacionado:** incident response, observabilidad `[10, 12]`

---

## Responder a un incidente de seguridad

El proceso es **distinto** al de un incidente normal (`[10]`): aquí la evidencia importa tanto como
restaurar el servicio.

1. **Contener sin destruir evidencia.** Aislar la máquina — **no apagarla**, la memoria se pierde.
   Revocar credenciales y tokens, cerrar el vector de entrada.
2. **Evaluar el alcance:** qué se accedió, qué datos, desde cuándo. Aquí es donde los audit logs `[17]` y
   la retención de logs te salvan o te hunden.
3. **Rotar todo** lo que pudo comprometerse: claves, secretos, tokens de sesión, credenciales de servicio.
4. **Notificar.** El RGPD exige notificar a la autoridad en **72 horas** desde que se conoce una brecha con
   riesgo para los derechos de las personas. **Involucra a legal desde el minuto uno**: no es una decisión
   de ingeniería.
5. **Postmortem** y cierre del vector, incluidos **los controles que deberían haberlo detectado**.

**Preparación previa que marca la diferencia:** saber quién decide, tener contactos de legal y
comunicación, tener logs con retención suficiente, y poder **rotar secretos rápido sin romper producción**
(de ahí la ventana de solapamiento). Un simulacro de brecha revela en una hora todo lo que falta.

> **Ficha** · **Cuándo:** ante sospecha de compromiso, acceso indebido o filtración ·
> **Patrón:** contener → evaluar alcance → rotar → notificar → postmortem ·
> **Anti-patrón:** apagar la máquina (pierdes la memoria) o reinstalar antes de investigar ·
> **Límites:** sin logs con retención suficiente no puedes determinar el alcance — y si no puedes
> determinarlo, legalmente asumes el peor caso ·
> **Cómo falla:** se descubre meses después, cuando los logs ya han rotado ·
> **Decisión:** el reloj de las 72 horas empieza al **conocer** la brecha, no al confirmarla ·
> **Trade-off:** contener rápido (restauras antes) vs preservar evidencia (entiendes qué pasó) ·
> **Relacionado:** audit logs, retención, incident response `[10, 15, 17]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Sesiones o JWT?**
Depende de si necesitas revocación inmediata y de si es un solo backend. Web clásica → sesiones. APIs
distribuidas → access token corto + refresh rotativo revocable. *Señal:* dices explícitamente que **un JWT
no se puede revocar** y que la "solución" de la denylist devuelve el estado que supuestamente evitabas.

**Q: ¿Dónde guardas el JWT en el navegador?**
Cookie `HttpOnly; Secure; SameSite`. En `localStorage` cualquier XSS lo roba. *Señal:* aceptas el
trade-off — con cookie vuelves a necesitar protección CSRF — y explicas cómo lo cubres (SameSite + token
anti-CSRF).

**Q: ¿Qué es IDOR y cómo lo previenes sistemáticamente?**
Acceder a un recurso ajeno cambiando el ID porque solo se comprobó la autenticación. Se previene filtrando
**siempre** por propietario/tenant en la propia query, no con un `if` suelto en el controlador. *Señal:*
dices que lo robusto es hacerlo imposible por construcción (scoping en el repositorio, RLS en Postgres),
porque un `if` se olvida en el endpoint nuevo.

**Q: Te roban la base de datos. ¿Qué pasa con las contraseñas?**
Si están con Argon2id + salt, el atacante tiene que atacar cada hash por separado y le sale carísimo. *Señal:*
explicas **por qué** SHA-256 no vale (es rápida: miles de millones de intentos por segundo con GPU) y qué
aporta el pepper si vive fuera de la DB.

**Q: ¿Qué es SSRF y por qué es tan peligrosa en el cloud?**
Porque el servidor tiene acceso a la red interna y al endpoint de metadatos, del que se sacan credenciales
IAM. *Señal:* mencionas IMDSv2, la allowlist con resolución DNS previa (para evitar DNS rebinding) y que
afecta directamente a features modernas como "dame la URL y te la resumo" o las herramientas de un agente.

**Q: ¿Cómo diseñas permisos en una app multi-tenant?**
`tenant_id` en todas las tablas y en todas las queries, roles dentro del tenant, y verificación a nivel de
objeto. *Señal:* propones Row-Level Security de Postgres o un repositorio que inyecta el `tenant_id`
automáticamente, porque depender de que cada dev lo recuerde acaba en fuga entre clientes.

**Trade-off central de esta caja:** *seguridad vs fricción y complejidad operativa*. Todo control tiene coste
(latencia, UX, soporte). Lo que se espera de un senior es priorizar por riesgo real: la autorización a nivel
de objeto y la gestión de secretos previenen más incidentes que cualquier discusión sobre el algoritmo
de cifrado.

---

## Fuentes

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) y [OWASP API Security Top 10](https://owasp.org/API-Security/) — el segundo es el relevante para backend.
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — la referencia práctica por tema.
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) — política moderna de contraseñas.
- [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)
- [WebAuthn / passkeys](https://webauthn.guide/) · [Argon2 RFC 9106](https://www.rfc-editor.org/rfc/rfc9106.html)
- [Microsoft STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
