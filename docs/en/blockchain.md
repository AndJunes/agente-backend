# Mirag's blockchain layer

Where it stands, on one screen:

```
Network                 Stellar TESTNET, and only testnet
Agent                   Backend Agent
Identity                Stellar 8004 (Soroban), Identity Registry
Current capability      RECEIVE
Outgoing payments       NOT IMPLEMENTED
Mainnet                 NOT REACHABLE (absent from NETWORKS; an unknown value raises)
Lock                    MIRAG_BLOCKCHAIN=off by default
Dependency              stellar-sdk, the optional extra: pip install -e ".[blockchain]"
```

The layer is **isolated**: no core module imports `stellar_sdk`, importing
`mirag.integrations.blockchain` does not import it either, and the server starts and the
whole core suite runs without the package installed. The SDK is imported lazily, inside
`blockchain.status()`, and only when the lock is open.

The page reads the layer through `GET /api/v1/blockchain/agent` (see [api.md](api.md)).

---

## Setting it up

```bash
pip install -e ".[blockchain]"                               # the optional extra
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --create
# copy the two printed lines into .env, then:
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --fund
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --register
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py          # read and verify
MIRAG_BLOCKCHAIN=testnet python scripts/blockchain_agent_demo.py --abi    # the ABI, from the chain
```

Nothing in the demo runs on its own: each step that writes to the chain needs its flag, with the
operator in front. Without flags it only reads. With the lock on it says what is missing and exits
without touching the network.

| Variable | Default | Meaning |
|---|---|---|
| `MIRAG_BLOCKCHAIN` | `off` | The lock. `testnet` opens it. Any other value **raises** `UnknownNetworkError`. Re-read on every call. |
| `STELLAR_PUBLIC_KEY` | - | The agent's address. Enough for a read-only panel. Ignored when the secret is set (the address is derived from it). |
| `STELLAR_SECRET_KEY` | - | The signing key. Read only by `wallet/keys.py`. Never printed, never sent to the page, never packaged. |
| `STELLAR_AGENT_ID` | - | The 8004 id Mirag *claims*; `identity()` checks it against the chain. |
| `STELLAR_REGISTRATION_TX` | - | Hash of the `register_with_uri` transaction (it cannot be recomputed later). |
| `STELLAR_WALLET_TX` | - | Hash of the `set_agent_wallet` transaction. |

`.env` is never versioned. Put the keys there, not in the shell history.

---

## The code

```
src/mirag/integrations/blockchain/
  __init__.py          the facade: status(agent, simulate) and available(); never raises
  config.py            the lock (BlockchainLock), NETWORKS (testnet only), explorer links
  models.py            Wallet, Payment, Identity, AgentStatus.for_page() (refuses a seed)
  metadata.py          the EIP-8004 registration document and its data URI (8 KiB cap)
  doubles.py           canned statuses copied from real reads: all good / no identity / not verified
  service.py           StatusService: wallet + identity -> AgentStatus   (imports the SDK)
  stellar/client.py    StellarClient: THE only module that opens sockets; one choke point
  identity/registry.py IdentityRegistry: register_with_uri, set_agent_wallet, reads, identity()
  wallet/keys.py       AgentKeys: the ONLY module that sees the secret key
  wallet/service.py    WalletService: address, balance, incoming payments, testnet funding
scripts/blockchain_agent_demo.py
```

Tests: `tests/unit/integrations/test_blockchain.py` (no SDK, no network: the lock, the border,
the secrets, the models) and `tests/integration/test_blockchain_network.py` (skipped without the
SDK; the tests marked `network` also need `MIRAG_BLOCKCHAIN_NETWORK_TESTS=1`).

---

## What is verified against the chain

Everything below was read from Testnet on **2026-09-16**, not from documentation. The command that
produces it is `scripts/blockchain_agent_demo.py --abi`.

### Contracts

| registry | network | contract |
|---|---|---|
| Identity | **testnet** | `CDE3K4COIAGWNNJQQLL26SYI3KBJF5FUDHXG5FA6GYDJCG7T5V7FIWZH` |
| Reputation | testnet | `CBZEAGIEI3HXMDRLF44KLQJQQOH6LCYWWSGJVSYQYQO2HQ6DDGZ7HT55` |
| Validation | testnet | `CC5USZRO26MOIAVNYTTJDS63C2OBBLREOAOET4CPF2EZWO3YFKLMO3SL` |
| Identity | mainnet *(not used)* | `CBGPDCJIHQ32G42BE7F2CIT3YW6XRN5ED6GQJHCRZSNAYH6TGMCL6X35` |

Testnet Identity: WASM `f25af88f3e26f603a6569b2554b3f85ccc8af9a88f3b904fba873637c64eb2ab`,
created by `GCCWEPP2MFAU…`, **source not verified** on the explorer. That is why the ABI below was
read from the WASM and not from a blog post.

Live reads on 2026-09-16: `version() = "0.1.0"` · `total_agents() = 26` · valid ids **0…25**
(`agent_exists(26) = False`: the counter is a total, ids start at 0).

### The ABI we use

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
find_owner(agent_id: U32)                                    -> Option<ADDRESS>     # does not fail
version()                                                    -> STRING
extend_ttl(agent_id: U32)                                    -> ()
```

`IdentityError`: `NotOwnerOrApproved=1`, `UriNotSet=2`, `AgentNotFound=3`,
`MetadataKeyTooLong=4`, `MetadataValueTooLong=5`, `TooManyMetadataKeys=6`,
`ReservedMetadataKey=7`, `EmptyValue=8`, and 9–11 from the upgrade mechanism.

**Three corrections to the public documentation**, found by reading the WASM:

1. **`register(caller)` does not take a `metadata_uri`.** The web page says
   `register(caller, metadata_uri)`. To register with metadata use `register_with_uri` or
   `register_full`.
2. The registry is an **ERC-721**: it has `approve`, `transfer`, `balance`, `owner_of`,
   `token_uri`. The agent's identity is an NFT, and `agent_id == token_id`.
3. `get_metadata` states in its own doc comment that it *"routes `agentWallet` key to the dedicated
   wallet storage slot"*: the identity <-> wallet link is a slot of its own, not just any metadata
   entry. It is read with `get_agent_wallet`.

### The metadata format actually in use

`agent_uri` does not point at a server: it is a **data URI with the JSON in base64**, embedded in
the chain. Read from agent #0 of the registry:

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

Mirag uses the same shape, without `x402` or paid `services` - this phase charges nothing - and
with the 8 KiB cap on the data URI, checked locally (`MetadataTooLargeError`) before anything is
signed.

---

## Decisions, and why

**The link is read back, never asserted.** `IdentityRegistry.identity()` calls
`get_agent_wallet(agent_id)` and compares it with the wallet Mirag uses. `verified` is that
comparison. `STELLAR_AGENT_ID` is only a claim; if the chain disagrees, the page says NOT VERIFIED
and why.

**The same keypair is owner and wallet.** `set_agent_wallet(caller, agent_id, new_wallet)` requires
authorisation from the owner **and** the wallet. With one keypair for both roles one signature is
enough. It is a decision, not an accident: when a policy engine arrives, owner and wallet split.

**The secret does not leave `wallet/keys.py`.** `AgentKeys.signer()` returns a `Keypair`, never the
string; errors never echo the key; `AgentKeys.generate()` is the only function that returns a
secret. `WalletService` has no secret getter. Tests check that no other module of the layer - and
no core module - reads `STELLAR_SECRET_KEY`, that `AgentStatus.for_page()` raises if anything shaped
like a seed (`S` + 55 base32) is about to go out, and that a fabricated `S…` seed is caught by the
package inspection (`mirag.projects.packaging.SECRETS`).

**Only one module opens sockets.** `stellar/client.py` is the only file that names `Server`,
`SorobanServer`, `ContractClient` or `urlopen`, and every network method goes through
`StellarClient._request`, which re-checks the lock even if the caller already did.

**Receive yes, spend no.** There is no outgoing payment function and no payment tool exposed to the
model. The capability of this phase is to RECEIVE.

**Mainnet is not reachable.** `NETWORKS` only contains `testnet`. An unknown `MIRAG_BLOCKCHAIN`
**raises**; it never falls back to a default.

**The facade never raises.** Layer off, SDK missing, network down, contract gone after a testnet
reset: `status()` returns `AgentStatus(available=False, reason=...)`, and the server keeps serving.

---

## Known risks

**Testnet reset.** The current network is ~272 days old (ledger ≈ 4 701 000). A reset wipes the
agent's account **and** the 8004 contract deployment. When it happens, the UI goes to a neutral state
and says it cannot verify, instead of showing stale data as good. To recover, repeat the whole flow
of `scripts/blockchain_agent_demo.py` and update the stored `STELLAR_AGENT_ID`.

**Horizon is heading to end of life.** It is used today because it works and returns plain JSON.
The base URLs live in `config.py` so the layer can move to Stellar RPC without touching the rest.

**The contract source is not verified.** We read its ABI from the deployed WASM, which is what
actually runs, but we cannot audit its logic. It is Testnet and there is no value at stake.

---

## Versions

| what | version |
|---|---|
| `stellar-sdk` | 16.1.0 (declared as `stellar-sdk>=16.1.0` in the `blockchain` extra) |
| Python | ≥ 3.11 (the project's floor) |
| Identity contract (testnet) | `version()` → `0.1.0` |

The extra installs into the same environment as Mirag. The core never imports it: only the lazy
path inside `blockchain.status()` does, when `MIRAG_BLOCKCHAIN=testnet`.
