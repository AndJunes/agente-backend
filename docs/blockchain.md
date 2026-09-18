# La capa blockchain de Mirag

Estado actual, en una pantalla:

```
Red                     Stellar TESTNET, y solo testnet
Agente                  Backend Agent
Identidad               Stellar 8004 (Soroban), Identity Registry
Capacidad actual        RECIBIR
Pagos salientes         NO IMPLEMENTADO
Mainnet                 NO ALCANZABLE (no está en REDES; un valor desconocido lanza)
Candado                 MIRAG_BLOCKCHAIN=off por defecto
Dependencia             stellar-sdk, declarada en blockchain/pyproject.toml
```

La capa está **aislada**: ningún módulo de producción importa `stellar_sdk`, y
`python3 -c "import server"` sigue funcionando sin el paquete instalado. Ver
[REPOSITORY_STRUCTURE.md](../REPOSITORY_STRUCTURE.md).

---

## Lo que está verificado contra la cadena

Todo lo de abajo se leyó de Testnet el **2026-09-16**, no de documentación. El script que lo
produce vive en `demos/blockchain_agent_demo.py --abi`.

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
límite de 8 KB del data URI.

---

## Decisiones, con su motivo

**El mismo keypair es owner y wallet.** `set_agent_wallet(caller, agent_id, new_wallet)` exige
autorización del owner **y** de la wallet. Usando un solo keypair para ambos roles basta una firma.
Es una decisión, no un accidente: cuando aparezca el *policy engine*, owner y wallet se separan.

**El secreto no sale de `blockchain/wallet/claves.py`.** `WalletService` no expone `secreto()`.
Hay tests que lo comprueban, que comprueban que ningún módulo de la raíz menciona
`STELLAR_SECRET_KEY`, y que una semilla `S…` fabricada es cazada por la inspección de paquetes.

**Recibir sí, gastar no.** No hay ninguna herramienta de pago saliente expuesta al modelo. La
capacidad de esta fase es recibir.

**Mainnet no es alcanzable.** `REDES` solo contiene `testnet`. Un `MIRAG_BLOCKCHAIN` desconocido
**lanza**; no cae a ningún defecto.

---

## Riesgos anotados

**Reset de Testnet.** La red actual tiene ~272 días (ledger ≈ 4 701 000). Un reset borra la cuenta
del agente **y** el despliegue del contrato 8004. Cuando pase: la UI pasa a estado neutro y dice que
no puede verificar, en vez de enseñar datos viejos como buenos. Para recuperar hay que repetir el
flujo entero de `demos/blockchain_agent_demo.py` y actualizar el `agent_id` guardado.

**Horizon va camino de EOL.** Se usa hoy porque funciona y devuelve JSON plano. La URL base está
aislada en `blockchain/config.py` para poder migrar a Stellar RPC sin tocar el resto.

**La fuente del contrato no está verificada.** Leemos su ABI del WASM desplegado, que es lo que de
verdad se ejecuta, pero no podemos auditar su lógica. Es Testnet y no hay valor en juego.

---

## Versiones

| qué | versión |
|---|---|
| `stellar-sdk` | 16.1.0 |
| gestor | `uv` 0.11.28, proyecto en `blockchain/pyproject.toml` |
| Python | ≥ 3.13 (el repo corre 3.14.6) |
| contrato Identity (testnet) | `version()` → `0.1.0` |

El venv vive en `blockchain/.venv/` y **nunca se activa globalmente**: `skills.INTERPRETES` y
`dependencias.instaladas()` observan `shutil.which("python3")`, y activarlo les haría medir otro
intérprete. Siempre `uv run --project blockchain`.
