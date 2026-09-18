# Identidad on-chain del Backend Agent

Esta fase probaba **una sola afirmación**:

> El Backend Agent de Mirag tiene una identidad on-chain verificable y una wallet de
> Stellar Testnet que puede recibir fondos.

Está probada. Y la parte que importa no es que se registrara, sino que el vínculo se **lee de
vuelta del contrato** en vez de darse por hecho.

```
  agent id               #26
  identity registry      CDE3K4COIAGWNNJQQLL26SYI3KBJF5FUDHXG5FA6GYDJCG7T5V7FIWZH
  wallet                 GDKCQKGNHLYT2JEC23BJGEMKKJH6CCIWE2AN25BBDX4ORJI2ITUYLBZS
  wallet EN LA CADENA    GDKCQKGNHLYT2JEC23BJGEMKKJH6CCIWE2AN25BBDX4ORJI2ITUYLBZS
  ✓ VERIFICADO ON-CHAIN
    get_agent_wallet(26) devuelve la misma wallet que usa Mirag.
    No es lo que Mirag dice de si mismo: es lo que responde el contrato.
```

**Coste**: $0 en modelo. Solo XLM de Testnet, que no vale nada.

---

## 1 · Lo que se hizo, en la cadena de verdad

| paso | resultado |
|---|---|
| keypair generado | `GDKCQKGN…` · la secreta solo en `.env`, nunca impresa |
| Friendbot | 10 000 XLM · tx `dc089ab0…` |
| `register_with_uri(caller, agent_uri)` | **agent_id 26** · tx `8d314298…` |
| `set_agent_wallet(caller, 26, wallet)` | tx `1f3220ed…` |
| `get_agent_wallet(26)` **leído de vuelta** | devuelve la wallet de Mirag → **verificado** |

La metadata va **on-chain** como data URI en base64 (605 bytes de los 8 KB que permite el
estándar): no hay ningún servidor que mantener para que la identidad siga siendo legible.

---

## 2 · Tres correcciones que solo aparecieron al leer el WASM

El plan exigía leer la ABI del contrato desplegado antes de escribir nada, en vez de programar
contra lo que dice la documentación pública. Encontró tres cosas:

1. **`register(caller)` no lleva `metadata_uri`.** La web dice `register(caller, metadata_uri)`.
   Programar contra eso habría fallado en la primera llamada. Para registrar con metadata hay que
   usar `register_with_uri` o `register_full`.
2. **El registro es un ERC‑721.** Tiene `approve`, `transfer`, `balance`, `owner_of`, `token_uri`:
   la identidad del agente es un NFT y `agent_id == token_id`. Eso importa para lo que viene
   después: una identidad de agente es transferible.
3. **`get_metadata` documenta en su propio código** que la clave `agentWallet` va a un slot de
   almacenamiento dedicado. El vínculo identidad↔wallet no es una entrada de metadata cualquiera.

También, ya en ejecución: **Friendbot devuelve 403 al User-Agent por defecto de `urllib`**
(`Python-urllib/3.x`). El mismo GET con `curl` da 200. Está anotado en el código con el porqué.

La ABI completa, los tres contratos de Testnet y las versiones exactas están en
[docs/blockchain.md](../docs/blockchain.md). Se puede regenerar con
`demos/blockchain_agent_demo.py --abi`, que la lee de la cadena.

---

## 3 · El problema que esto creaba, y que era el trabajo de verdad

`estado.py:67` le decía a la interfaz **«cero dependencias externas»**, y `estado.py:134`
respondía «Solo biblioteca estándar: 0 dependencias externas» a quien preguntara de qué está hecho
Mirag. README y dos documentos repetían lo mismo.

El único test que hacía cumplir esa invariante escaneaba `RAIZ.glob("*.py")`: **no recursivo, solo
la raíz**. Una carpeta `blockchain/` le era invisible. Un `import stellar_sdk` ahí dentro habría
pasado en verde mientras el producto seguía afirmando lo contrario — el mismo defecto que este
proyecto lleva diez fases cerrando: *algo afirmado que nada observa*.

Se cerró en tres movimientos:

1. **La frase dice dónde vale.** `estado.py`, README, `CURRENT_ARCHITECTURE` y `PRODUCT_OVERVIEW`
   ahora dicen «el núcleo no tiene dependencias externas; la capa `blockchain/` declara
   stellar-sdk».
2. **Tres tests nuevos que ven las subcarpetas** (`tests/test_arquitectura_repo.py`):
   `el_nucleo_sigue_sin_dependencias_externas` (AST sobre la raíz, tiene que dar 0),
   `la_capa_blockchain_solo_usa_lo_que_declara` (AST **recursivo**, comparado contra
   `pyproject.toml` en los dos sentidos: ni usa sin declarar ni declara sin usar), y
   `el_claim_de_dependencias_dice_la_verdad`, que ata la frase a la medición.
3. **Prueba del vacío**, porque un guardián sin comprobar es una promesa:

| se rompe a propósito | qué pasa |
|---|---|
| `import yaml` dentro de `blockchain/` | ❌ `usa sin declarar: ['yaml']` |
| el claim de `estado.py` vuelve a la versión que mentía | ❌ `afirma cero dependencias sin decir dónde vale` |
| `import stellar_sdk` en producción | ❌ 2 casos, uno de ellos `el núcleo sigue sin dependencias externas` |

---

## 4 · La frontera, y qué la hace real

```
  Mirag core — 30 .py planos en la raíz · stdlib puro · 0 dependencias
        │
        │  server.py, import PEREZOSO dentro del handler
        ▼
  blockchain/ — paquete aislado, venv propio
        aquí y solo aquí: stellar_sdk, la clave, el socket
```

«Aislada» no es una intención, es esto, y cada línea tiene su test:

| propiedad | cómo se comprueba |
|---|---|
| `import server` funciona sin `stellar-sdk` | subproceso con el intérprete del sistema |
| `import blockchain` **no** carga el SDK | subproceso que imprime `'stellar_sdk' in sys.modules` |
| ningún `.py` de la raíz importa `stellar_sdk` | AST sobre la raíz |
| el socket vive en **un** archivo | AST: nadie más nombra `Server`, `SorobanServer`, `ContractClient`, `urlopen`, `requests` |
| toda la red pasa por `_pedir` | AST: cada función pública de `client.py` lo llama |
| el candado no se puede esquivar | se parchea `_pedir` y se exige que las 3 rutas lo noten |

Las 21 suites del núcleo siguen corriendo con el intérprete del sistema, sin venv y sin red.
Eso no es una comodidad: es la definición operativa del aislamiento.

---

## 5 · El candado

`agent.OFFLINE` **no cubre la red genérica** — es un `if` dentro de `agent.llm()`, y ya había
precedentes de sockets sin candado (`fixture_proyecto`, `sondas`). Así que la capa lleva el suyo,
con la forma de `vectores._impedimento()`:

```python
RED = os.environ.get("MIRAG_BLOCKCHAIN", "off")   # off | testnet
REDES = {"testnet": {...}}                         # mainnet NO está, y es a propósito
```

**Mainnet no es alcanzable.** No está en `REDES`, y un valor desconocido **lanza** en vez de caer
a un defecto silencioso, que es exactamente como se acaba hablando con la red real sin querer.
Hay un test que lo prueba con `mainnet`, `public`, `pubnet`, `MAINNET` y `prod`.

Y con la capa apagada, **no se simula nada**: se dice que está apagada. Un doble que se enciende
solo sería la interfaz mintiendo.

---

## 6 · La clave secreta

Reglas, y lo que hace cumplir cada una:

| regla | mecanismo |
|---|---|
| vive en un solo archivo | `blockchain/wallet/claves.py`; `generar()` es la **única** función del repositorio que devuelve un secreto, y un test lo comprueba por AST |
| `WalletService` no la expone | no existe `secreto()`, ni `pagar()`, ni `enviar()` — comprobado por AST, no importando |
| ningún módulo de producción la lee | AST sobre la raíz. `empaquetado.py` la **nombra** para cazarla, que es lo contrario de usarla, y esa excepción está declarada |
| no sale por HTTP | `Estado.para_la_pagina()` **lanza** si detecta `S[A-Z2-7]{55}` en el JSON de salida |
| no se cuela en un ZIP | `empaquetado.SECRETOS` ahora reconoce semillas de Stellar |
| un error no la ecoa | un mensaje que repite la clave la publica en los logs; hay un test con una clave basura |

Comprobado en ejecución, con la capa encendida: `grep -rE 'S[A-Z2-7]{55}'` sobre todo el
repositorio devuelve **solo `.env`**, y ninguna de las cuatro rutas HTTP la deja salir.

Y esta fase **no gasta**: no hay ninguna función de pago saliente, y un test se pone rojo el día
que aparezca una.

---

## 7 · Verificación

| | resultado |
|---|---|
| suite, intérprete del sistema, sin venv, sin red | **485 casos · 0 rojas · 23 suites** (+1 omitido en voz alta) |
| suite con SDK (`uv run --project blockchain`) | **11 casos · TODO OK** |
| 4 demos canónicas | **4/4 CUMPLE EL CONTRATO**, $0 |
| `demos/demo_proyecto.py` | **VERIFICADO** · 16/16 · ZIP 8 408 B · 13 comprobaciones |
| 16 rutas internas, GET **y** HEAD | **16/16 → 404**, incluidas `blockchain/`, su venv, su lock y su pyproject |
| la clave en HTTP y en disco | **0 apariciones** fuera de `.env` |
| el flujo real en Testnet | registrado, asociado y **leído de vuelta** |
| la página | panel verde, con el motivo de por qué puede decir «verificado» |

`tests/test_blockchain_red.py` **no se disfraza de verde** cuando falta el SDK: imprime `OMITIDO`
y cuenta los casos que no se ejecutaron — y ese número se calcula, no se escribe a mano, porque un
número escrito a mano ahí sería otra afirmación que nada observa. Ya mentía en el primer intento
(decía 12, eran 11).

---

## 8 · Dos cosas que la capa destapó

**`test_simbolos` tenía un supuesto caducado.** El caso `una consulta irrelevante no arrastra auth`
usaba «pagos con tarjeta» con el comentario *«no toca este repo»*. Dejó de ser cierto el día que
apareció `wallet/servicio.py` con `pagos()` y `ultimo_pago()`. **El índice no se rompió: acertó.**
Se separó en dos casos —uno con una consulta ajena de verdad, otro que exige que una consulta de
pagos encuentre `blockchain/` y no `auth.py`— y quedó más fuerte que antes.

**No existía ningún test que dijera qué rutas tiene el servidor.** `head_y_get_pasan_por_la_misma_lista`
impide que las listas se dupliquen, pero no que crezcan: una ruta nueva entraba en silencio. Ahora
`la_lista_blanca_esta_cerrada` afirma por igualdad `RUTAS`, `RUTAS_POST` y los literales que
`_servir` despacha aparte. Ese hueco existía desde antes de esta fase.

---

## 9 · Riesgos anotados

**Reset de Testnet.** La red actual tiene ~272 días. Un reset borra la cuenta *y* el despliegue del
contrato. Cuando pase, la interfaz pasa a estado neutro y dice que no puede verificar, en vez de
enseñar datos viejos como buenos — hay un test que simula exactamente ese caso.

**La fuente del contrato no está verificada** en el explorador. Leemos la ABI del WASM desplegado,
que es lo que de verdad se ejecuta, pero no podemos auditar su lógica. Es Testnet, no hay valor en
juego.

**Horizon va camino de EOL.** La URL base está aislada en `blockchain/config.py` para poder migrar
a Stellar RPC sin tocar el resto.

---

## 10 · Lo que sigue sin existir

Pagos entre agentes · escrow · presupuestos · reparto · orquestación PM→Backend→QA · facturación de
OpenRouter on-chain · gasto autónomo · recibos · treasury · multisig · USDC · x402 · contratos
propios · mainnet.

La capacidad de esta fase es **recibir**. Gastar está deliberadamente sin implementar, y hay un test
que lo defiende.

Cuando llegue el reparto, la decisión que habrá que revisar primero está anotada: hoy **el mismo
keypair es owner y wallet**, porque `set_agent_wallet` exige autorización de los dos y con uno solo
basta una firma. En cuanto aparezca un motor de políticas, owner y wallet se separan.
