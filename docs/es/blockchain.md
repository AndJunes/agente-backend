# La capa blockchain de Mirag

Estado actual, en una pantalla:

```
Red                     Stellar TESTNET, y solo testnet
Agente                  Backend Agent
Identidad               Stellar 8004 (Soroban), Identity Registry
Capacidad actual        RECIBIR
Pagos salientes         NO IMPLEMENTADO
Mainnet                 NO ALCANZABLE (no está en NETWORKS; un valor desconocido lanza)
Candado                 MIRAG_BLOCKCHAIN=off por defecto
Dependencia             stellar-sdk, el extra opcional: pip install -e ".[blockchain]"
```

La capa está **aislada**: ningún módulo del core importa `stellar_sdk`, importar
`mirag.integrations.blockchain` tampoco lo importa, y el servidor arranca y la suite entera del core
corre sin el paquete instalado. El SDK se importa de forma perezosa, dentro de
`blockchain.status()`, y solo cuando el candado está abierto.

La página lee la capa a través de `GET /api/v1/blockchain/agent` (ver [api.md](../en/api.md)).

---

## Puesta en marcha

```bash
pip install -e ".[blockchain]"                               # el extra opcional
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --create
# copiá las dos líneas que imprime a .env, y después:
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --fund
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --register
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py          # leer y verificar
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --abi    # la ABI, desde la cadena
```

Nada de la demo se ejecuta solo: cada paso que escribe en la cadena pide su bandera, con el operador
delante. Sin banderas solo lee. Con el candado puesto dice qué falta y sale sin tocar la red.

| Variable | Por defecto | Significado |
|---|---|---|
| `MIRAG_BLOCKCHAIN` | `off` | El candado. `testnet` lo abre. Cualquier otro valor **lanza** `UnknownNetworkError`. Se relee en cada llamada. |
| `STELLAR_PUBLIC_KEY` | - | La dirección del agente. Basta para un panel de solo lectura. Se ignora si hay secreto (la dirección se deriva de él). |
| `STELLAR_SECRET_KEY` | - | La clave que firma. Solo la lee `wallet/keys.py`. Nunca se imprime, nunca llega a la página, nunca se empaqueta. |
| `STELLAR_AGENT_ID` | - | El id 8004 que Mirag *afirma* tener; `identity()` lo contrasta con la cadena. |
| `STELLAR_REGISTRATION_TX` | - | Hash de la transacción `register_with_uri` (no se puede recalcular después). |
| `STELLAR_WALLET_TX` | - | Hash de la transacción `set_agent_wallet`. |

`.env` no se versiona nunca. Las claves van ahí, no en el historial de la shell.

---

## El código

```
src/mirag/integrations/blockchain/
  __init__.py          la fachada: status(agent, simulate) y available(); nunca lanza
  config.py            el candado (BlockchainLock), NETWORKS (solo testnet), enlaces al explorador
  models.py            Wallet, Payment, Identity, AgentStatus.for_page() (rechaza una semilla)
  metadata.py          el documento de registro EIP-8004 y su data URI (tope de 8 KiB)
  doubles.py           estados fijos copiados de lecturas reales: todo bien / sin identidad / sin verificar
  service.py           StatusService: wallet + identidad -> AgentStatus   (importa el SDK)
  stellar/client.py    StellarClient: el ÚNICO módulo que abre sockets; un solo estrangulamiento
  identity/registry.py IdentityRegistry: register_with_uri, set_agent_wallet, lecturas, identity()
  wallet/keys.py       AgentKeys: el ÚNICO módulo que ve la clave secreta
  wallet/service.py    WalletService: dirección, saldo, pagos entrantes, fondeo en testnet
scripts/blockchain_agent_demo.py
```

Comprobaciones: los tests que cubrían esta capa (su candado, su frontera, sus secretos, sus
modelos, y una suite contra la red real) se eliminaron con el resto de `tests/`.
`scripts/blockchain_agent_demo.py` es la forma manual de ejercitarla.

---

## Lo que está verificado contra la cadena

Todo lo de abajo se leyó de Testnet el **2026-09-16**, no de documentación. El comando que lo
produce es `scripts/blockchain_agent_demo.py --abi`.

### Contratos

| registro | red | contrato |
|---|---|---|
| Identity | **testnet** | `CDE3K4COIAGWNNJQQLL26SYI3KBJF5FUDHXG5FA6GYDJCG7T5V7FIWZH` |
| Reputation | testnet | `CBZEAGIEI3HXMDRLF44KLQJQQOH6LCYWWSGJVSYQYQO2HQ6DDGZ7HT55` |
| Validation | testnet | `CC5USZRO26MOIAVNYTTJDS63C2OBBLREOAOET4CPF2EZWO3YFKLMO3SL` |
| Identity | mainnet *(no se usa)* | `CBGPDCJIHQ32G42BE7F2CIT3YW6XRN5ED6GQJHCRZSNAYH6TGMCL6X35` |

Identity de testnet: WASM `f25af88f3e26f603a6569b2554b3f85ccc8af9a88f3b904fba873637c64eb2ab`,
creado por `GCCWEPP2MFAU…`, **fuente sin verificar** en el explorador. Por eso la ABI de abajo se
leyó del WASM y no de un blog.

Lecturas en vivo el 2026-09-16: `version() = "0.1.0"` · `total_agents() = 26` ·
ids válidos **0…25** (`agent_exists(26) = False`: el contador es total, los ids empiezan en 0).

### La ABI que usamos

```
register(caller: ADDRESS)                                   -> U32
register_with_uri(caller: ADDRESS, agent_uri: STRING)        -> U32
register_full(caller: ADDRESS, agent_uri: STRING,
              metadata: Vec<MetadataEntry>)                  -> U32

set_agent_wallet(caller: ADDRESS, agent_id: U32,
                 new_wallet: ADDRESS)                        -> Result<VOID, IdentityError>
get_agent_wallet(agent_id: U32)                              -> Option<ADDRESS>
unset_agent_wallet(caller: ADDRESS, agent_id: U32)           -> Result<VOID, IdentityError>

agent_uri(agent_id: U32)                                     -> Result<STRING, IdentityError>
set_agent_uri(caller, agent_id, new_uri: STRING)             -> Result<VOID, IdentityError>
get_metadata(agent_id: U32, key: STRING)                     -> Option<BYTES>
set_metadata(caller, agent_id, key: STRING, value: BYTES)    -> Result<VOID, IdentityError>

agent_exists(agent_id: U32)                                  -> BOOL
total_agents()                                               -> U32
owner_of(token_id: U32)                                      -> ADDRESS
find_owner(agent_id: U32)                                    -> Option<ADDRESS>     # no revienta
version()                                                    -> STRING
extend_ttl(agent_id: U32)                                    -> ()
```

`IdentityError`: `NotOwnerOrApproved=1`, `UriNotSet=2`, `AgentNotFound=3`,
`MetadataKeyTooLong=4`, `MetadataValueTooLong=5`, `TooManyMetadataKeys=6`,
`ReservedMetadataKey=7`, `EmptyValue=8`, y 9–11 del mecanismo de upgrade.

**Tres correcciones a lo que dice la documentación pública**, encontradas al leer el WASM:

1. **`register(caller)` no lleva `metadata_uri`.** La web dice `register(caller, metadata_uri)`.
   Para registrar con metadata hay que usar `register_with_uri` o `register_full`.
2. El registro es un **ERC-721**: tiene `approve`, `transfer`, `balance`, `owner_of`, `token_uri`.
   La identidad del agente es un NFT, y `agent_id == token_id`.
3. `get_metadata` documenta en su propio doc-comment que *«routes `agentWallet` key to the dedicated
   wallet storage slot»*: el vínculo identidad↔wallet es un slot propio, no una entrada de metadata
   cualquiera. Se lee con `get_agent_wallet`.

### El formato de metadata que se usa de verdad

`agent_uri` no apunta a un servidor: es un **data URI con el JSON en base64**, embebido en la
cadena. Leído del agente #0 del registro:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "…",
  "description": "…",
  "image": "…",
  "services": [{"name": "x402", "endpoint": "…", "version": "1.0", "description": "…"},
               {"name": "mcp",  "endpoint": "…"}],
  "supportedTrust": ["reputation"],
  "x402": true
}
```

Mirag usa la misma forma, sin `x402` ni `services` de pago —esta fase no cobra nada— y con el
tope de 8 KiB del data URI, comprobado en local (`MetadataTooLargeError`) antes de firmar nada.

---

## Decisiones, con su motivo

**El vínculo se lee de vuelta, nunca se afirma.** `IdentityRegistry.identity()` llama a
`get_agent_wallet(agent_id)` y lo compara con la wallet que usa Mirag. `verified` es esa
comparación. `STELLAR_AGENT_ID` es solo una afirmación; si la cadena dice otra cosa, la página
muestra SIN VERIFICAR y el motivo.

**El mismo keypair es owner y wallet.** `set_agent_wallet(caller, agent_id, new_wallet)` exige
autorización del owner **y** de la wallet. Usando un solo keypair para ambos roles basta una firma.
Es una decisión, no un accidente: cuando aparezca el *policy engine*, owner y wallet se separan.

**El secreto no sale de `wallet/keys.py`.** `AgentKeys.signer()` devuelve un `Keypair`, nunca la
cadena; los errores nunca repiten la clave; `AgentKeys.generate()` es la única función que devuelve
un secreto. `WalletService` no tiene ningún getter del secreto. Hay tests que comprueban que ningún
otro módulo de la capa —ni ningún módulo del core— lee `STELLAR_SECRET_KEY`, que
`AgentStatus.for_page()` lanza si algo con forma de semilla (`S` + 55 base32) está por salir, y que
una semilla `S…` fabricada es cazada por la inspección de paquetes
(`mirag.projects.packaging.SECRETS`).

**Un solo módulo abre sockets.** `stellar/client.py` es el único archivo que nombra `Server`,
`SorobanServer`, `ContractClient` o `urlopen`, y cada método de red pasa por
`StellarClient._request`, que vuelve a comprobar el candado aunque quien llama ya lo haya hecho.

**Recibir sí, gastar no.** No hay ninguna función de pago saliente ni ninguna herramienta de pago
expuesta al modelo. La capacidad de esta fase es RECIBIR.

**Mainnet no es alcanzable.** `NETWORKS` solo contiene `testnet`. Un `MIRAG_BLOCKCHAIN` desconocido
**lanza**; no cae a ningún defecto.

**La fachada nunca lanza.** Capa apagada, SDK ausente, red caída, contrato borrado tras un reset de
testnet: `status()` devuelve `AgentStatus(available=False, reason=...)` y el servidor sigue sirviendo.

---

## Riesgos anotados

**Reset de Testnet.** La red actual tiene ~272 días (ledger ≈ 4 701 000). Un reset borra la cuenta
del agente **y** el despliegue del contrato 8004. Cuando pase: la UI pasa a estado neutro y dice que
no puede verificar, en vez de enseñar datos viejos como buenos. Para recuperar hay que repetir el
flujo entero de `scripts/blockchain_agent_demo.py` y actualizar el `STELLAR_AGENT_ID` guardado.

**Horizon va camino de EOL.** Se usa hoy porque funciona y devuelve JSON plano. Las URLs base viven
en `config.py` para poder migrar a Stellar RPC sin tocar el resto.

**La fuente del contrato no está verificada.** Leemos su ABI del WASM desplegado, que es lo que de
verdad se ejecuta, pero no podemos auditar su lógica. Es Testnet y no hay valor en juego.

---

## Versiones

| qué | versión |
|---|---|
| `stellar-sdk` | 16.1.0 (declarado como `stellar-sdk>=16.1.0` en el extra `blockchain`) |
| Python | ≥ 3.11 (el mínimo del proyecto) |
| contrato Identity (testnet) | `version()` → `0.1.0` |

El extra se instala en el mismo entorno que Mirag. El core nunca lo importa: solo lo hace la ruta
perezosa dentro de `blockchain.status()`, con `MIRAG_BLOCKCHAIN=testnet`.
