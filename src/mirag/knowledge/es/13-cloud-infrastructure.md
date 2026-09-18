# 13 · Cloud & Infrastructure

> No hace falta ser SRE, pero sí saber **dónde corre tu código, cómo llega el tráfico hasta él y por qué
> se cae**. En una entrevista senior te van a pedir que dibujes esto en una pizarra.


**Cubre del temario:** `linux` · `containers` · `orchestration` · `cloud` · `networking` · `storage` · `iam` · `tradeoffs`

---

## Linux: lo que un backend usa de verdad

**Diagnóstico en producción — el kit mínimo:**

```bash
top / htop           # CPU y memoria por proceso
ps aux --sort=-%mem  # quién come memoria
df -h                # disco lleno (causa de incidentes más tonta y más común)
du -sh *             # qué lo llena
free -h              # RAM y swap
netstat -tlnp / ss -tlnp   # qué escucha en qué puerto
lsof -i :8000        # quién tiene ese puerto
lsof -p PID | wc -l  # file descriptors abiertos (los "too many open files")
dmesg | tail         # ¿el kernel mató algo? (OOM killer)
strace -p PID        # en qué syscall está atascado
journalctl -u svc -f # logs del servicio
```

**Conceptos que se preguntan:**
- **Procesos y señales:** `SIGTERM` (por favor, termina — **es la que debes manejar** para hacer shutdown
  elegante) vs `SIGKILL` (mueres ya, no se puede capturar). Kubernetes manda SIGTERM, espera
  `terminationGracePeriodSeconds` y luego SIGKILL.
- **OOM killer:** cuando falta memoria, el kernel elige una víctima y la mata. En un contenedor se ve como
  `OOMKilled` y un reinicio inexplicable.
- **File descriptors:** cada socket y archivo abierto es uno. `ulimit -n` bajo es la causa real de muchos
  fallos bajo carga.
- **Permisos** (`chmod`/`chown`), usuarios no-root, y **nunca corras el contenedor como root**.
- **cgroups y namespaces:** los dos mecanismos del kernel sobre los que se construyen los contenedores —
  cgroups limita recursos, namespaces aísla la visión (procesos, red, filesystem).

> **Ficha** · **Cuándo:** en cualquier incidente que toque la máquina ·
> **Patrón:** manejar SIGTERM para apagar con orden; vigilar FDs y disco ·
> **Anti-patrón:** ignorar SIGTERM y dejar que SIGKILL corte las peticiones en vuelo ·
> **Límites:** `ulimit -n` acota las conexiones abiertas simultáneas ·
> **Cómo falla:** **disco lleno** — la causa de incidente más tonta y más frecuente ·
> **Decisión:** si el proceso no es PID 1 con forma exec, no recibe las señales ·
> **Trade-off:** contenedores mínimos (sin herramientas de diagnóstico) vs depurabilidad ·
> **Relacionado:** graceful shutdown, file descriptors `[01, 10]`

---

## Docker

**El modelo mental:** una imagen es un sistema de archivos en capas + metadatos. Un contenedor es un proceso
del host, aislado con namespaces y limitado con cgroups. **No es una máquina virtual**: comparte el kernel.

**Dockerfile de calidad:**
```dockerfile
# 1) Multi-stage: compilas en una imagen gorda, copias a una flaca
FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .                  # 2) primero las deps: capa cacheada
RUN pip install --no-cache-dir -r requirements.txt --target /deps

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1                   # 3) logs sin buffer -> los ves en tiempo real
COPY --from=build /deps /usr/local/lib/python3.13/site-packages
COPY . /app
WORKDIR /app
USER 1000:1000                           # 4) no-root
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

**Las reglas:**
- **Orden de capas = velocidad de build.** Lo que cambia poco (dependencias) va arriba; el código, abajo.
- **Multi-stage** reduce tamaño y superficie de ataque (el compilador no viaja a producción).
- **`.dockerignore`** — sin él metes `.git`, `node_modules` y secretos en la imagen.
- **Imágenes base pequeñas** (slim, distroless). Alpine usa musl en vez de glibc, lo que a veces da fallos
  sutiles de DNS y rendimiento en Python: úsala sabiendo eso.
- **Nunca secretos en el Dockerfile.** Quedan en la capa para siempre, aunque los borres después.
- **Fija versiones** (`python:3.13-slim`, no `latest`) o tus builds no son reproducibles.
- **Un proceso por contenedor**, y que escriba **logs a stdout/stderr**. Los logs a archivo dentro de un
  contenedor son logs perdidos.
- **Señales:** usa la forma exec de `CMD` (`["cmd","arg"]`) para que tu proceso sea PID 1 y reciba SIGTERM.
  Con la forma shell, lo recibe `/bin/sh` y tu app muere sin cerrar nada.

> **Ficha** · **Cuándo:** empaquetar cualquier servicio ·
> **Patrón:** multi-stage, capas ordenadas por frecuencia de cambio, usuario no-root, versiones fijadas ·
> **Anti-patrón:** secretos en el Dockerfile (quedan en la capa para siempre) y tag `latest` ·
> **Límites:** comparte kernel con el host: no es aislamiento de seguridad fuerte ·
> **Cómo falla:** la forma shell de `CMD` hace que tu proceso no reciba SIGTERM ·
> **Decisión:** logs a stdout, un proceso por contenedor, `.dockerignore` siempre ·
> **Trade-off:** imagen mínima (segura, difícil de depurar) vs completa ·
> **Relacionado:** señales, CI/CD `[14]`

---

## Kubernetes

**Objetos que debes conocer:**

| Objeto | Qué es |
|---|---|
| **Pod** | la unidad mínima: uno o más contenedores que comparten red y volúmenes |
| **Deployment** | gestiona ReplicaSets: réplicas, rolling updates y rollback |
| **Service** | IP y DNS estables que balancean a los pods (ClusterIP, NodePort, LoadBalancer) |
| **Ingress / Gateway API** | entrada HTTP desde fuera, routing por host/path, TLS |
| **ConfigMap / Secret** | configuración y secretos (Secret es base64, **no cifrado** por defecto) |
| **StatefulSet** | pods con identidad y disco estables (bases de datos) |
| **Job / CronJob** | trabajo puntual o programado |
| **HPA** | autoescalado por métricas |
| **PDB** | PodDisruptionBudget: cuántos pueden caerse a la vez durante mantenimiento |

**Lo que de verdad hay que entender:**

- **Es un bucle de reconciliación.** Tú declaras el estado deseado; el controlador trabaja sin parar para
  que la realidad coincida. No das órdenes, declaras intenciones.
- **Requests vs limits:**
  - `requests` = lo que el scheduler reserva. Determina **dónde** cabe tu pod.
  - `limits` = el techo. Superar el de memoria = **OOMKilled**; superar el de CPU = **throttling**
    (tu app no muere, se vuelve inexplicablemente lenta — causa clásica de picos de p99).
  - Sin `requests`, el scheduler apila pods y los nodos se saturan.
- **Probes** — y confundirlas causa incidentes:
  - `liveness`: si falla, **reinicia el pod**. Si la pones demasiado agresiva, entras en un bucle de
    reinicios bajo carga.
  - `readiness`: si falla, **lo saca del balanceo** sin matarlo. Es la que debe comprobar dependencias.
  - `startup`: da margen a apps que arrancan lento antes de que actúen las otras dos.
- **Graceful shutdown:** al terminar un pod, Kubernetes lo quita del Service *y* manda SIGTERM **a la vez**
  (no en orden garantizado). Por eso se añade un `preStop` con unos segundos de espera: si no, recibes
  tráfico después de empezar a cerrar y devuelves 502 en cada despliegue.
- **Rolling update** con `maxSurge`/`maxUnavailable` es el default; blue/green y canary se montan encima
  (`14-devops.md`).

**Cuándo NO usar Kubernetes:** un equipo pequeño con tres servicios. El coste operativo (upgrades, red,
RBAC, observabilidad, el propio cluster) es real. **Cloud Run, ECS Fargate, App Runner o una PaaS resuelven
el 90% de los casos con el 10% del esfuerzo.** Decir esto en una entrevista demuestra criterio, no ignorancia.

> **Ficha** · **Cuándo:** varios servicios y equipo con capacidad de operarlo ·
> **Patrón:** requests y limits explícitos, probes bien separadas, PDB y `preStop` ·
> **Anti-patrón:** dependencias externas en la liveness probe ·
> **Límites:** superar el límite de memoria = **OOMKilled**; superar el de CPU = **throttling silencioso** ·
> **Cómo falla:** picos de p99 inexplicables por CPU throttling del contenedor ·
> **Decisión:** con 3 servicios y equipo pequeño, Cloud Run o ECS resuelven el 90% con el 10% del esfuerzo ·
> **Trade-off:** control total vs coste operativo permanente ·
> **Relacionado:** health checks, graceful shutdown, despliegues `[10, 12, 14]`

---

## Redes en la nube

```
Internet
   │
[ DNS ]  →  [ CDN ]  →  [ WAF ]  →  [ Load Balancer (TLS) ]
                                         │
                            ┌────────────┴────────────┐
                       [ subred pública: LB, NAT GW ]
                            │
                       [ subred privada: tus servicios ]
                            │
                       [ subred aislada: base de datos ]
```

- **VPC:** tu red privada. **Subredes públicas** (con ruta a un internet gateway) vs **privadas** (salen a
  internet solo por un NAT gateway; **nadie entra desde fuera**).
- **La regla de oro: tu base de datos nunca está en una subred pública.** Solo acepta conexiones desde el
  security group de tu aplicación.
- **Security groups** (stateful, a nivel de instancia; la respuesta vuelve automáticamente) vs **NACLs**
  (stateless, a nivel de subred, con reglas de entrada y salida separadas).
- **Reverse proxy** (nginx, Envoy, Traefik): TLS, routing, buffering de clientes lentos, compresión,
  rate limiting básico. Protege a tu app de clientes maliciosamente lentos (slowloris).
- **Zonas de disponibilidad (AZ):** despliega en al menos dos. Una región es un conjunto de AZs; la
  **multi-región** es mucho más cara y compleja (replicación de datos, latencia, split-brain) y casi nunca
  se justifica antes de tener un negocio grande.

> **Ficha** · **Cuándo:** al montar la infraestructura de un entorno ·
> **Patrón:** LB en subred pública; servicios en privada; base de datos en subred aislada ·
> **Anti-patrón:** base de datos accesible desde internet ·
> **Límites:** el NAT gateway cobra por GB: el tráfico saliente puede ser una sorpresa cara ·
> **Cómo falla:** tras terminar TLS en el LB, sin `X-Forwarded-*` tu app no sabe ni la IP ni el esquema ·
> **Decisión:** multi-AZ siempre; multi-región solo con motivo de negocio ·
> **Trade-off:** aislamiento de red vs complejidad de configuración ·
> **Relacionado:** TLS, load balancing, coste `[02, 09]`

---

## Object storage (S3 y equivalentes)

- **Es un almacén de objetos, no un filesystem.** No hay directorios de verdad (los `/` son parte del
  nombre), no hay append, y renombrar es copiar y borrar.
- **Consistencia:** desde 2020 S3 es *strongly consistent* para lecturas tras escritura — la vieja pregunta
  de entrevista sobre consistencia eventual ya está obsoleta, y saberlo es un punto.
- **Clases de almacenamiento:** Standard → Infrequent Access → Glacier. Con **lifecycle rules** automáticas,
  es de las optimizaciones de coste más rentables que existen.
- **Presigned URLs** para subir y descargar sin pasar por tu backend (`15-files-data.md`).
- **Seguridad:** bloquear acceso público a nivel de cuenta, cifrado en reposo, versionado (protege de
  borrados accidentales y de ransomware), y políticas de bucket mínimas.

> **Ficha** · **Cuándo:** todo archivo de usuario, backup o exportación ·
> **Patrón:** presigned URLs, bloqueo de acceso público, versionado y lifecycle rules ·
> **Anti-patrón:** proxyficar los bytes por tu aplicación ·
> **Límites:** no es un filesystem: no hay append y renombrar es copiar y borrar ·
> **Cómo falla:** buckets públicos por configuración por defecto ·
> **Decisión:** S3 es *strongly consistent* desde 2020 — la vieja pregunta sobre consistencia eventual está obsoleta ·
> **Trade-off:** latencia mayor que un disco local vs durabilidad y escala ·
> **Relacionado:** uploads, backups, coste `[15]`

---

## Serverless

**Funciones (Lambda, Cloud Functions) y contenedores serverless (Cloud Run, Fargate).**

- ✅ Cero gestión de servidores, escalado automático a cero, pago por uso, ideal para tráfico irregular,
  webhooks, crons y procesamiento de eventos.
- ❌ **Cold starts**, límites de tiempo de ejecución, dificultad con conexiones persistentes a bases de datos
  (necesitas un pooler o driver HTTP: ver `04-databases.md`), y coste alto con tráfico constante y elevado.
- **El coste se invierte:** con tráfico bajo o esporádico, serverless es dramáticamente más barato; con
  tráfico constante 24/7, un contenedor siempre encendido gana por mucho.
- **Modelos modernos** (como Fluid Compute) reutilizan instancias entre requests concurrentes, lo que reduce
  cold starts y cambia bastante este cálculo respecto a la Lambda clásica de 2018.

> **Ficha** · **Cuándo:** tráfico irregular, webhooks, crons, procesamiento de eventos ·
> **Patrón:** funciones sin estado y con arranque rápido ·
> **Anti-patrón:** abrir una conexión nueva a Postgres por invocación ·
> **Límites:** cold starts, tiempo máximo de ejecución, y conexiones persistentes difíciles ·
> **Cómo falla:** un pico de concurrencia abre miles de conexiones y tumba la base de datos ·
> **Decisión:** necesitas pooler externo o driver HTTP sí o sí `[04]` ·
> **Trade-off:** barato con tráfico esporádico, caro con tráfico constante ·
> **Relacionado:** connection pooling, cold starts `[04]`

---

## IAM

**El modelo que hay que interiorizar:** *quién* (principal) puede hacer *qué* (acción) sobre *qué recurso*,
*bajo qué condiciones*.

- **Mínimo privilegio.** Empieza denegando y añade lo necesario. `Action: "*"` es un hallazgo de auditoría.
- **Roles, no claves.** Una instancia/pod asume un rol y obtiene credenciales temporales rotadas solas.
  **Las claves de acceso estáticas en variables de entorno son lo que se filtra en GitHub.**
- **OIDC federation:** tu pipeline de CI (GitHub Actions) asume un rol en el cloud **sin guardar secretos**.
  Es el estándar actual y sustituye a las claves de larga duración.
- **Separación de entornos:** cuentas/proyectos distintos para dev, staging y producción. Es la barrera más
  efectiva contra "lo he borrado en prod sin querer".
- **Conecta con SSRF** (`06-security.md`): si alguien alcanza el endpoint de metadatos, obtiene las
  credenciales del rol. Por eso el mínimo privilegio no es burocracia — limita el daño de una brecha.

> **Ficha** · **Cuándo:** cada recurso de cloud que crees ·
> **Patrón:** roles con credenciales temporales; OIDC entre CI y cloud ·
> **Anti-patrón:** claves de acceso estáticas en variables de entorno ·
> **Límites:** los permisos se acumulan con el tiempo y nadie los revisa ·
> **Cómo falla:** **SSRF** llega al endpoint de metadatos y obtiene las credenciales del rol `[06]` ·
> **Decisión:** cuentas separadas por entorno: la barrera más efectiva contra "lo borré en prod" ·
> **Trade-off:** mínimo privilegio (seguro, fricción) vs permisos amplios ·
> **Relacionado:** SSRF, secrets, CI/CD `[06, 14]`

---

## Almacenamiento: volúmenes y estado en contenedores

El disco de un contenedor es **efímero**: desaparece al reiniciar. Todo lo que deba sobrevivir necesita
un mecanismo explícito.

| Tipo | Vida | Uso |
|---|---|---|
| Filesystem del contenedor | muere con el pod | temporales de un solo uso |
| `emptyDir` | vive lo que el pod | cache entre contenedores del mismo pod |
| **PersistentVolume (PVC)** | independiente del pod | bases de datos, colas con disco |
| **Object storage (S3)** | permanente | archivos de usuario, backups, exportaciones `[15]` |

```yaml
# StatefulSet: identidad y disco estables por replica (postgres-0, postgres-1...)
volumeClaimTemplates:
  - metadata: {name: datos}
    spec:
      accessModes: ["ReadWriteOnce"]     # un solo nodo puede montarlo a la vez
      resources: {requests: {storage: 100Gi}}
```

**`ReadWriteOnce` es la restricción que sorprende:** la mayoría de volúmenes de bloque solo se montan en
**un nodo**. Si quieres que varios pods escriban el mismo disco necesitas `ReadWriteMany` (NFS, EFS), que
es más lento y más caro. **En la práctica, la respuesta correcta casi siempre es no compartir disco:**
usa object storage o la base de datos.

> **Ficha** · **Cuándo:** cualquier servicio que escriba algo que deba sobrevivir ·
> **Patrón:** stateless por defecto; estado en la DB o en object storage ·
> **Anti-patrón:** guardar uploads en el disco local del contenedor — desaparecen y no se comparten ·
> **Límites:** `ReadWriteOnce` impide que varios nodos monten el mismo volumen ·
> **Cómo falla:** funciona con una réplica y se rompe en cuanto escalas a dos ·
> **Decisión:** si el archivo lo sube un usuario, va a object storage, nunca a disco local ·
> **Trade-off:** disco local (rápido, atado a un nodo) vs object storage (escalable, con latencia) ·
> **Relacionado:** uploads, StatefulSets `[15]`

---

## Coste: dónde se va el dinero

El coste es responsabilidad de ingeniería. Ordenado por retorno de la optimización:

| Sumidero | Por qué pasa | Qué hacer |
|---|---|---|
| **Observabilidad descontrolada** | logs en DEBUG, métricas de alta cardinalidad | samplear, filtrar en el Collector, ajustar retención `[12]` |
| **Almacenamiento sin lifecycle** | nada se borra ni baja de clase | reglas de ciclo de vida: la optimización más rentable |
| **Instancias sobredimensionadas** | "por seguridad" | medir uso real; savings plans para la base, spot para lo tolerante |
| **Entornos de no producción 24/7** | nadie los apaga | apagar dev y staging fuera de horario |
| **Transferencia de datos** | entre zonas y hacia internet | el coste que más sorprende; colocar servicios en la misma AZ |
| **Tráfico de bots** | a veces la mitad de las peticiones | WAF y rate limiting `[03]` |
| **Multipart incompletos** | subidas abortadas que siguen facturando | lifecycle rule que las aborta `[15]` |
| **NAT gateway** | todo el tráfico saliente pasa por ahí | VPC endpoints para S3 y servicios del cloud |
| **Tokens de LLM** | modelo grande para tareas triviales | modelo por tarea, caching, límites `[18]` |

**Higiene mínima:** etiquetar los recursos por servicio y entorno (sin eso no puedes atribuir el gasto),
alertas de presupuesto, y revisar la factura mensualmente. **Una alerta de gasto anómalo es tan importante
como una de latencia:** un bucle infinito o un retry storm se ven antes en la factura que en las métricas.

> **Ficha** · **Cuándo:** revisión mensual, y al diseñar cualquier cosa que escale ·
> **Patrón:** etiquetado obligatorio + alertas de presupuesto + lifecycle rules ·
> **Anti-patrón:** descubrir el problema al recibir la factura ·
> **Límites:** optimizar coste puede empeorar latencia o disponibilidad ·
> **Cómo falla:** la observabilidad acaba costando más que la infraestructura que observa ·
> **Decisión:** ataca primero lo que no afecta al usuario (retención, entornos parados, clases de almacenamiento) ·
> **Trade-off:** coste vs rendimiento y visibilidad ·
> **Relacionado:** observabilidad, lifecycle, IA `[12, 15, 18]`

---

## Preguntas de entrevista y trade-offs

**Q: Dibuja cómo llega una request desde el navegador a tu contenedor.**
DNS → CDN → WAF → load balancer (termina TLS) → ingress/service → pod. *Señal:* mencionas dónde termina el
TLS, que a partir de ahí necesitas `X-Forwarded-For`, y que la base de datos vive en una subred privada sin
ruta desde internet.

**Q: Un pod se reinicia constantemente. ¿Cómo lo depuras?**
`kubectl describe pod` (eventos, razón del último estado: OOMKilled, CrashLoopBackOff), logs del contenedor
anterior (`--previous`), revisar límites de memoria y la liveness probe. *Señal:* sabes que una liveness
demasiado estricta puede provocar el bucle de reinicios *ella misma* cuando la app está lenta pero viva.

**Q: ¿Qué diferencia hay entre liveness y readiness?**
Liveness reinicia, readiness saca del balanceo. *Señal:* dices que las dependencias externas se comprueban
en readiness y **no** en liveness — si metes la DB en la liveness, una caída de la DB reinicia todos tus
pods y empeora el incidente.

**Q: ¿Serverless o contenedores?**
Según el patrón de tráfico y los requisitos de latencia. *Señal:* hablas de cold starts, del problema de
las conexiones a la base de datos y de la inversión del coste con tráfico constante, en vez de decir que uno
es mejor.

**Q: ¿Por qué no usar `latest` como tag?**
Porque el build deja de ser reproducible y un rollback no te devuelve al mismo artefacto. *Señal:* lo unes
a la inmutabilidad: la misma imagen con el mismo digest se promociona de staging a producción sin
reconstruirse (`14-devops.md`).

**Trade-off central de esta caja:** *control vs coste operativo*. Kubernetes te da control total y te cobra
en complejidad permanente; una PaaS te quita control y te devuelve tiempo de ingeniería. La respuesta senior
depende del tamaño del equipo, no de la moda: **elige la cosa más simple que soporte tus requisitos reales
de escala, aislamiento y cumplimiento.**

---

## Fuentes

- [Kubernetes docs — Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Docker — Best practices for writing Dockerfiles](https://docs.docker.com/build/building/best-practices/)
- [The Twelve-Factor App](https://12factor.net/) — configuración, procesos sin estado, paridad entre entornos.
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) — los pilares de coste, fiabilidad y seguridad.
- [Vercel — Fluid Compute](https://vercel.com/docs/fundamentals/fluid-compute) — reutilización de instancias para reducir cold starts.
