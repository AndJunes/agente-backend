# 14 · DevOps

> El objetivo no es "automatizar": es **reducir el tiempo entre escribir una línea y que funcione en
> producción sin miedo**. Las métricas DORA miden exactamente eso: frecuencia de despliegue, lead time,
> tasa de fallo de cambios y tiempo de recuperación.


**Cubre del temario:** `git` · `cicd` · `deployment` · `infrastructure` · `secrets` · `rollback` · `failure_modes`

---

## Git

**Lo que un senior usa a diario:**

```bash
git rebase -i main          # limpiar la historia antes de la PR
git cherry-pick <sha>       # llevar un commit concreto a otra rama
git bisect start            # búsqueda binaria del commit que rompió algo
git revert <sha>            # deshacer EN PÚBLICO (crea un commit nuevo)
git reset --hard <sha>      # reescribir EN LOCAL (destructivo)
git reflog                  # la red de seguridad: recupera commits "perdidos"
git log -S "texto"          # cuándo entró o salió ese string del código
git blame -w -C             # quién escribió esto, ignorando espacios y movimientos
```

- **Merge vs rebase:** merge preserva la historia real (y genera commits de merge); rebase produce una
  historia lineal y legible. **La regla: rebase en tu rama local, merge hacia main.** Nunca reescribas la
  historia de una rama compartida.
- **`revert` vs `reset`:** en cualquier rama que otros usen, `revert`. `reset --hard` sobre algo ya empujado
  obliga a un force-push y le rompe el repo a tus compañeros.
- **Estrategias de rama:** **trunk-based** (ramas de vida corta, todo a main varias veces al día, detrás de
  feature flags) es lo que correlaciona con alto rendimiento en los estudios DORA. GitFlow, con sus ramas
  `develop`/`release`/`hotfix`, está pensado para releases versionadas y para software que se instala, no
  para un SaaS que despliega a diario.
- **Buenos commits:** un cambio lógico por commit, mensaje que explica **por qué** (el "qué" ya está en el
  diff), y conventional commits si quieres generar changelogs automáticamente.

> **Ficha** · **Cuándo:** a diario ·
> **Patrón:** trunk-based con ramas de vida corta y feature flags para lo incompleto ·
> **Anti-patrón:** `reset --hard` y force-push sobre una rama compartida ·
> **Límites:** reescribir historia pública rompe el repo de tus compañeros ·
> **Cómo falla:** ramas de semanas que producen merges imposibles ·
> **Decisión:** rebase en local, merge hacia main, `revert` en público ·
> **Trade-off:** historia lineal y legible vs historia fiel a lo que pasó ·
> **Relacionado:** CI/CD, feature flags `[05]`

---

## CI/CD

**CI (Continuous Integration):** cada push se construye y se prueba. **CD** puede ser *Delivery* (siempre
listo para desplegar, con un botón humano) o *Deployment* (despliega solo si pasa todo).

**Pipeline típico y en qué orden va cada cosa (lo rápido primero, para fallar pronto):**

```
1. Lint + formato + type-check        (segundos)
2. Tests unitarios                     (1-2 min)
3. Build de la imagen                  (cacheado)
4. Tests de integración con servicios reales (docker compose / testcontainers)
5. Escaneos: dependencias (SCA), SAST, secretos, imagen
6. Push de la imagen con tag = SHA del commit
7. Deploy a staging  → smoke tests / E2E críticos
8. Deploy a producción (progresivo) → verificación automática → rollback si falla
```

**Principios que se preguntan:**
- **Build once, deploy many.** Construyes **un** artefacto y **el mismo** recorre staging y producción.
  Si reconstruyes por entorno, ya no estás desplegando lo que probaste.
- **La configuración viene del entorno**, no del artefacto (12-factor).
- **Todo rápido o nadie lo usa.** Un pipeline de 40 minutos hace que la gente agrupe cambios, y los cambios
  grandes son los que rompen producción.
- **Pipeline rojo = se para todo.** Un main roto que se tolera acaba con la confianza en los tests.
- **Determinismo:** dependencias con lockfile, imágenes por digest, sin `latest`. Los **tests flaky** son
  veneno: erosionan la confianza hasta que la gente reintenta sin mirar. Cuarentena y arréglalos.

**GitHub Actions — lo esencial:**
```yaml
on: [push, pull_request]
permissions:
  contents: read          # mínimo privilegio; súbelo solo donde haga falta
  id-token: write         # para OIDC hacia el cloud, sin secretos estáticos
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.13', cache: 'pip'}
      - run: pip install -r requirements.txt
      - run: pytest -q
```
- **Fija las acciones de terceros por SHA**, no por tag: un tag se puede mover y ejecutar código arbitrario
  en tu pipeline con acceso a tus secretos (es un ataque de cadena de suministro real y frecuente).
- **Nunca uses `pull_request_target` con código de un fork** salvo que sepas exactamente lo que haces.
- Matrix builds, cache de dependencias, jobs en paralelo, y `concurrency` para cancelar builds obsoletos.

> **Ficha** · **Cuándo:** desde el primer commit ·
> **Patrón:** **build once, deploy many** — un artefacto recorre staging y producción ·
> **Anti-patrón:** reconstruir la imagen para producción (ya no despliegas lo que probaste) ·
> **Límites:** un pipeline lento hace que la gente agrupe cambios, y los lotes grandes rompen más ·
> **Cómo falla:** los **tests flaky** erosionan la confianza hasta que se reintenta sin mirar ·
> **Decisión:** fija las acciones de terceros por SHA — un tag se mueve y ejecuta código con tus secretos ·
> **Trade-off:** más comprobaciones vs velocidad de feedback ·
> **Relacionado:** testing, secrets, supply chain `[06, 11]`

---

## Estrategias de despliegue

| Estrategia | Cómo | Pros | Contras |
|---|---|---|---|
| **Recreate** | apagar y encender | trivial | **downtime** |
| **Rolling** | sustituir pods poco a poco | sin downtime, default de K8s | conviven dos versiones; rollback lento |
| **Blue/green** | dos entornos completos, se cambia el tráfico de golpe | **rollback instantáneo**, pruebas en el idéntico | doble infraestructura; migraciones de DB complicadas |
| **Canary** | 1% → 10% → 50% → 100% | detecta problemas con poco impacto | requiere métricas y automatización buenas |
| **Feature flags** | el código va en producción apagado | despliegue ≠ release, rollback instantáneo | deuda de flags viejas; hay que limpiarlas |

**Lo que se espera que digas:** *deploy* y *release* son cosas distintas. Con feature flags, el código llega
a producción apagado y se enciende para un 1% de usuarios cuando quieras — eso convierte el rollback en un
cambio de configuración de un segundo, sin redeploy. **Es la forma más segura de desplegar que existe**, y a
cambio te obliga a una disciplina de limpieza de flags.

**Lo que casi nadie menciona y demuestra experiencia:** en rolling y canary **conviven dos versiones del
código a la vez**, así que cada cambio debe ser compatible hacia atrás y hacia delante — en la base de datos
(expand/contract, `04-databases.md`), en la API y en el formato de los mensajes de las colas.

> **Ficha** · **Cuándo:** cada cambio que llegue a usuarios ·
> **Patrón:** canary con verificación automática, o feature flags (deploy ≠ release) ·
> **Anti-patrón:** blue/green asumiendo que la base de datos también se duplica ·
> **Límites:** en rolling y canary **conviven dos versiones del código** ·
> **Cómo falla:** un cambio incompatible hacia atrás rompe a la mitad de los usuarios durante el despliegue ·
> **Decisión:** feature flags convierten el rollback en un cambio de configuración de un segundo ·
> **Trade-off:** control fino vs deuda de flags que hay que limpiar ·
> **Relacionado:** migraciones, compatibilidad `[04]`

---

## Rollbacks

- **La pregunta que define la madurez de un equipo: "¿cuánto tardas en volver atrás?"** Si la respuesta es
  "depende", no hay estrategia de rollback.
- **Rollback de código** es fácil: vuelve al artefacto anterior (por eso los tags inmutables importan).
- **Rollback de datos** es lo difícil: una migración que borró una columna no se deshace. Por eso
  expand/contract — **nunca destruyas en el mismo despliegue que introduces.**
- **Roll forward** (arreglar hacia delante) es a menudo mejor cuando el rollback implicaría revertir
  migraciones. Decide antes del incidente, no durante.
- Automatiza el rollback ante señales claras (error rate, latencia) en el despliegue canario.

> **Ficha** · **Cuándo:** planificado **antes** de desplegar ·
> **Patrón:** artefactos inmutables por digest y rollback automático ante señales claras ·
> **Anti-patrón:** descubrir durante el incidente que la migración no se puede revertir ·
> **Límites:** el código se revierte fácil; **los datos no** ·
> **Cómo falla:** revertir el código con un esquema ya migrado rompe todo peor ·
> **Decisión:** nunca destruyas en el mismo despliegue en que introduces ·
> **Trade-off:** rollback (rápido, a veces imposible) vs roll-forward (más lento, siempre viable) ·
> **Relacionado:** expand/contract, incident response `[04, 10]`

---

## Infrastructure as Code

**Por qué:** infraestructura versionada, revisable en PR, reproducible y auditable. El *ClickOps* (tocar la
consola a mano) produce entornos que nadie sabe recrear y que divergen en silencio.

**Terraform / OpenTofu:**
```hcl
resource "aws_db_instance" "principal" {
  identifier     = "api-prod"
  engine         = "postgres"
  instance_class = var.tamano_db
  storage_encrypted = true
  deletion_protection = true      # el flag que te salva de un terraform destroy
}
```

- **Estado (`state`):** el mapa entre tu código y los recursos reales. **Guárdalo remoto (S3 + bloqueo)**,
  nunca en el repo — contiene datos sensibles y se corrompe si dos personas aplican a la vez.
- **`plan` antes de `apply`**, siempre, y en la PR para que se revise.
- **Módulos** para no repetirte, **workspaces o directorios** por entorno.
- **Declarativo vs imperativo:** Terraform declara el estado final; Ansible ejecuta pasos. Terraform para
  aprovisionar, Ansible/cloud-init para configurar dentro.
- **Drift:** alguien tocó la consola a mano y la realidad ya no coincide. Detéctalo con `plan` periódico en
  CI. Y desactiva los permisos de escritura manuales en producción si puedes.

> **Ficha** · **Cuándo:** toda infraestructura que no sea un experimento ·
> **Patrón:** `plan` revisado en la PR; estado remoto con bloqueo ·
> **Anti-patrón:** ClickOps — tocar la consola y que nadie sepa recrear el entorno ·
> **Límites:** el estado contiene datos sensibles y se corrompe si dos aplican a la vez ·
> **Cómo falla:** **drift** — alguien tocó a mano y la realidad ya no coincide con el código ·
> **Decisión:** `deletion_protection` en todo lo que tenga datos ·
> **Trade-off:** rigor y trazabilidad vs agilidad para un cambio urgente ·
> **Relacionado:** entornos, IAM `[13]`

---

## Environments y configuración

- **dev → staging → producción**, con staging lo más parecido posible a producción (mismo tipo de base de
  datos, misma versión, datos anonimizados de volumen similar). Un staging que no se parece no prueba nada.
- **12-factor:** configuración en variables de entorno, sin archivos por entorno dentro del artefacto.
- **Valida la configuración al arrancar** y falla ruidosamente si falta algo. Un servicio que arranca con una
  variable vacía y falla a las tres horas es mucho peor que uno que no arranca.
- **Paridad dev/prod:** usa Docker Compose o devcontainers para que "en mi máquina funciona" deje de ser una
  frase.
- **Datos de producción en desarrollo: no.** Anonimiza o genera datos sintéticos. Es un riesgo legal (RGPD),
  no solo técnico.

> **Ficha** · **Cuándo:** al montar dev, staging y producción ·
> **Patrón:** 12-factor — configuración por entorno, artefacto idéntico ·
> **Anti-patrón:** datos reales de producción en desarrollo (riesgo legal, no solo técnico) ·
> **Límites:** un staging que no se parece a producción no prueba nada ·
> **Cómo falla:** el servicio arranca con una variable vacía y falla tres horas después ·
> **Decisión:** valida la configuración al arrancar y falla ruidosamente si falta algo ·
> **Trade-off:** fidelidad de staging vs coste de mantenerlo ·
> **Relacionado:** secrets, paridad dev/prod `[06]`

---

## Secrets management

- Fuente de verdad: Vault / AWS Secrets Manager / GCP Secret Manager / secretos del proveedor de CI.
  Inyectados en tiempo de ejecución, nunca horneados en la imagen.
- **OIDC en vez de claves estáticas** entre CI y cloud (`13-cloud-infrastructure.md`).
- **Rotación** con ventana de solapamiento (`06-security.md`).
- **Detección:** secret scanning en el repo, en el historial y en los logs de CI. Si algo se filtró,
  **rotar es obligatorio** — borrar el commit no sirve.
- **Los secretos de Kubernetes están en base64, no cifrados.** Activa el cifrado en reposo de etcd o usa
  un operador (External Secrets, Sealed Secrets).

> **Ficha** · **Cuándo:** toda credencial, desde el primer día ·
> **Patrón:** gestor de secretos + inyección en runtime + **OIDC** en vez de claves estáticas ·
> **Anti-patrón:** secretos en el repo, en la imagen, o en los logs ·
> **Límites:** los Secrets de Kubernetes están en **base64, no cifrados** por defecto ·
> **Cómo falla:** un secreto filtrado sigue en forks y en logs de CI: borrar el commit no sirve ·
> **Decisión:** si se filtró, rotar es obligatorio ·
> **Trade-off:** rotación frecuente (segura, operativamente cara) vs claves longevas ·
> **Relacionado:** IAM, cryptography `[06, 13]`

---

## La checklist de un despliegue

**Antes:**
- [ ] CI en verde (tests, lint, tipos, escaneos de seguridad).
- [ ] Migraciones **compatibles hacia atrás** — expand/contract `[04]`.
- [ ] Feature flags listas para apagar lo nuevo sin redeploy.
- [ ] Plan de rollback **escrito**; y si la migración no es reversible, dicho en voz alta antes.

**Durante:**
- [ ] Despliegue progresivo con verificación automática entre pasos.
- [ ] Comparar las señales de oro **de la versión nueva contra la vieja**, no el agregado `[12]`.
- [ ] Vigilar errores **nuevos**, no solo el total: 50 errores nuevos se esconden dentro de un error rate
      que apenas se mueve.

**Después:**
- [ ] Verificar el camino crítico de negocio de verdad (un checkout real, no un 200 en `/health`).
- [ ] Vigilar lo que tarda en aparecer: memory leaks, conexiones sin cerrar, colas que crecen despacio.
- [ ] Cerrar el ciclo: apagar la flag vieja, contraer la migración, borrar el código muerto.

**El principio que lo resume:** *los despliegues deben ser aburridos*. Si desplegar produce ansiedad, el
problema no es el despliegue — es que falta automatización, observabilidad o reversibilidad.

> **Ficha** · **Cuándo:** cada despliegue a producción ·
> **Patrón:** progresivo + verificación automática + rollback preparado ·
> **Anti-patrón:** desplegar y mirar el dashboard agregado (la versión vieja te oculta la nueva) ·
> **Límites:** la checklist no sustituye a la automatización; lo manual se olvida ·
> **Cómo falla:** el problema aparece horas después, cuando ya nadie relaciona causa y efecto ·
> **Decisión:** ¿el rollback requiere revertir datos? Entonces planifica roll-forward ·
> **Trade-off:** ceremonia vs frecuencia de despliegue ·
> **Relacionado:** migraciones, feature flags, observabilidad `[04, 12]`

---

## La checklist de producción de un servicio nuevo

Lo que debe existir **antes** de recibir tráfico real. Es el resumen operativo de todas las cajas:

**Operación:** health checks `live`/`ready` bien separados `[12]` · graceful shutdown que respeta SIGTERM
`[10]` · límites de recursos `[13]` · timeouts en todas las llamadas salientes `[10]` · rollback probado.

**Observabilidad:** logs estructurados con `trace_id` · métricas de las cuatro señales · tracing
distribuido · alertas basadas en SLO con runbook · dashboard `[12]`.

**Seguridad:** autenticación y **autorización a nivel de objeto** · secretos fuera del código · TLS ·
rate limiting · validación de entradas · dependencias escaneadas · security headers `[06]`.

**Datos:** migraciones reversibles · backups **probados** · retención definida · PII identificada `[04, 15]`.

**Resiliencia:** retries con backoff · circuit breakers · degradación definida por funcionalidad ·
idempotencia donde se reintenta `[08, 10]`.

**Documentación:** README con cómo correrlo, runbook de fallos conocidos, ADRs de las decisiones
importantes `[05]`, y **quién está de guardia**.

> **Ficha** · **Cuándo:** antes del primer tráfico real de cualquier servicio ·
> **Patrón:** la checklist como criterio de aceptación, no como sugerencia ·
> **Anti-patrón:** "eso lo añadimos después de lanzar" ·
> **Límites:** cumplirla no garantiza que no falle, solo que sabrás qué pasó y podrás revertir ·
> **Cómo falla:** los tres que más se olvidan: graceful shutdown, separar liveness de readiness, y el runbook ·
> **Decisión:** si no hay dueño ni on-call, el servicio no está listo para producción ·
> **Trade-off:** tiempo antes de lanzar vs incidentes después ·
> **Relacionado:** todas las cajas operativas `[06, 08, 10, 12, 13]`

---

## Preguntas de entrevista y trade-offs

**Q: ¿Cómo despliegas sin downtime una versión que cambia el esquema de la base de datos?**
Expand/contract en varios despliegues, con el código compatible con ambos esquemas durante la transición.
*Señal:* dices explícitamente que durante un rolling update **conviven dos versiones del código**, así que la
compatibilidad hacia atrás no es opcional.

**Q: ¿Blue/green o canary?**
Blue/green para rollback instantáneo y cambios grandes; canary cuando quieres detectar regresiones con
impacto mínimo y tienes métricas para automatizar la decisión. *Señal:* señalas que blue/green choca con las
migraciones de base de datos (los dos entornos comparten datos) y que canary necesita observabilidad buena
para no ser teatro.

**Q: ¿Qué es trunk-based development y por qué?**
Ramas de vida corta que integran a main a diario, con feature flags para lo incompleto. Reduce el dolor de
los merges y el tamaño de los cambios, que es lo que correlaciona con menos fallos. *Señal:* mencionas DORA
y que lotes pequeños son más seguros porque el radio de impacto de cada cambio es pequeño.

**Q: Producción está rota y no sabes qué commit fue. ¿Qué haces?**
Primero mitigar (rollback o feature flag), luego investigar — `git bisect` o revisar qué se desplegó con la
correlación temporal del incidente. *Señal:* separas mitigar de diagnosticar; mucha gente intenta entender
el bug mientras los usuarios siguen afectados.

**Q: ¿Por qué no construir la imagen otra vez para producción?**
Porque el artefacto que pruebas debe ser exactamente el que despliegas. Reconstruir introduce diferencias
(dependencias transitivas, fecha, caché). *Señal:* lo llamas por su nombre — build once, deploy many — y lo
unes a tags inmutables por digest.

**Trade-off central de esta caja:** *velocidad de entrega vs seguridad del cambio*. La intuición dice que
son opuestos; los datos de DORA dicen lo contrario: los equipos que despliegan más a menudo **fallan menos**,
porque los lotes pequeños son más fáciles de revisar, de probar y de revertir. La automatización es lo que
hace posible que ambas suban a la vez.

---

## Fuentes

- [DORA — State of DevOps / Four Keys](https://dora.dev/) — por qué desplegar más a menudo correlaciona con fallar menos.
- *Accelerate* (Forsgren, Humble, Kim) — la investigación detrás de las métricas DORA.
- [Trunk Based Development](https://trunkbaseddevelopment.com/)
- [GitHub Actions — Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) — fijar acciones por SHA, `pull_request_target`.
- [Terraform — State](https://developer.hashicorp.com/terraform/language/state) · [OpenTofu](https://opentofu.org/)
