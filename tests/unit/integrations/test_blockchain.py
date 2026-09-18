"""The Stellar layer: the lock, the border, the secrets and the honesty of the claim.

Everything here runs **without stellar-sdk installed and without network**. That is not a
limitation of the tests: it is exactly the property being checked. If this suite ever needed
the SDK, the layer would have stopped being isolated. (When the SDK happens to be installed,
the tests that need it absent hide it on purpose.)
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import replace
from functools import cache
from pathlib import Path
from types import ModuleType

import pytest

import mirag
from mirag.container import Container
from mirag.core.errors import UnknownNetworkError
from mirag.integrations import blockchain
from mirag.integrations.blockchain import config, doubles, metadata, models
from mirag.integrations.blockchain.config import BlockchainDisabledError, BlockchainLock
from mirag.integrations.blockchain.metadata import MetadataTooLargeError
from mirag.integrations.blockchain.models import AgentStatus, SecretLeakError
from mirag.integrations.blockchain.wallet.keys import AgentKeys, MissingKeyError
from mirag.projects.packaging import SECRETS

PACKAGE_ROOT = Path(mirag.__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = SRC_ROOT.parent
LAYER = PACKAGE_ROOT / "integrations" / "blockchain"
DEMO = REPO_ROOT / "scripts" / "blockchain_agent_demo.py"
DOCS = {"en": REPO_ROOT / "docs" / "en" / "blockchain.md",
        "es": REPO_ROOT / "docs" / "es" / "blockchain.md"}

SECRET_VARIABLE = "STELLAR_SECRET_KEY"
LAYER_VARIABLES = ("MIRAG_BLOCKCHAIN", "STELLAR_PUBLIC_KEY", SECRET_VARIABLE, "STELLAR_AGENT_ID",
                   "STELLAR_REGISTRATION_TX", "STELLAR_WALLET_TX")
# The modules that import the SDK at the top. Hiding the SDK means forgetting them too.
SDK_SIDE_MODULES = ("service", "stellar.client", "identity.registry", "wallet.service")
PUBLIC = "G" + "A" * 55
SEED = "S" + "A" * 55
OFF_JSON = {"available": False, "reason": "MIRAG_BLOCKCHAIN is off: Stellar is not contacted",
            "identity": None, "wallet": None, "last_payment": None, "links": {}}


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """No case inherits a key or a network from the developer's shell (or another test)."""
    for name in LAYER_VARIABLES:
        monkeypatch.delenv(name, raising=False)


@cache
def layer_modules() -> tuple[tuple[str, str, ast.Module], ...]:
    """``(relative path, source, tree)`` for every module of the layer."""
    files = sorted(LAYER.rglob("*.py"))
    assert len(files) >= 13, f"the scan does not see the layer: {len(files)} files in {LAYER}"
    modules = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        modules.append((path.relative_to(LAYER).as_posix(), source, ast.parse(source)))
    return tuple(modules)


def imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module and not node.level:
        return [node.module]
    return []


def hide_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import stellar_sdk`` fail, whether or not it is installed."""
    monkeypatch.setitem(sys.modules, "stellar_sdk", None)  # type: ignore[arg-type]
    for name in SDK_SIDE_MODULES:
        monkeypatch.delitem(sys.modules, f"{blockchain.__name__}.{name}", raising=False)


def load_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("blockchain_agent_demo", DEMO)
    assert spec and spec.loader, f"cannot load {DEMO}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ══ 1 · the lock ══════════════════════════════════════════════════════════════

def test_the_layer_is_off_by_default() -> None:
    """Like MIRAG_OFFLINE: we do not trust ourselves to remember, we prevent it."""
    assert config.network() == config.OFF
    assert not config.available()
    assert "off" in config.obstacle()
    assert blockchain.available() is False


def test_the_lock_is_reread_on_every_call(monkeypatch: pytest.MonkeyPatch) -> None:
    lock = BlockchainLock()
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    assert lock.available() and lock.settings().name == "testnet"
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "off")
    assert not lock.available()


def test_an_injected_environment_drives_the_lock() -> None:
    assert BlockchainLock({"MIRAG_BLOCKCHAIN": " TestNet "}).settings().name == config.TESTNET
    assert not BlockchainLock({}).available()
    assert not BlockchainLock({"MIRAG_BLOCKCHAIN": ""}).available()


def test_only_testnet_exists() -> None:
    """The most important fact of the layer: there is no way to reach mainnet by accident."""
    assert set(config.NETWORKS) == {config.TESTNET}, set(config.NETWORKS)
    for network in config.NETWORKS.values():
        assert "testnet" in network.horizon and "testnet" in network.rpc
        assert "Test SDF Network" in network.passphrase


@pytest.mark.parametrize("attempt", ["mainnet", "public", "pubnet", "MAINNET", "prod"])
def test_mainnet_is_unreachable(monkeypatch: pytest.MonkeyPatch, attempt: str) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", attempt)
    with pytest.raises(UnknownNetworkError):
        config.obstacle()
    with pytest.raises(UnknownNetworkError):
        config.settings()
    assert blockchain.available() is False
    status = blockchain.status()
    assert not status.available and attempt.lower() in status.reason


def test_an_unknown_network_raises_instead_of_falling_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "whatever")
    with pytest.raises(UnknownNetworkError, match="Mainnet is absent on purpose"):
        config.settings()


def test_while_off_there_are_no_settings_to_hand_out() -> None:
    with pytest.raises(BlockchainDisabledError, match="off"):
        config.settings()
    with pytest.raises(BlockchainDisabledError):
        config.account_link(PUBLIC)


def test_explorer_links_point_at_the_active_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    explorer = config.NETWORKS[config.TESTNET].explorer
    assert config.account_link(PUBLIC) == f"{explorer}/account/{PUBLIC}"
    assert config.tx_link("ab" * 32) == f"{explorer}/tx/{'ab' * 32}"
    registry = config.NETWORKS[config.TESTNET].identity_registry
    assert config.contract_link(registry) == f"{explorer}/contract/{registry}"


@pytest.mark.parametrize("value", [None, "off", "testnet", "mainnet", "garbage", "", " OFF "])
def test_the_facade_never_raises(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    """The server cannot fall over because the layer is having a bad day."""
    if value is not None:
        monkeypatch.setenv("MIRAG_BLOCKCHAIN", value)
    status = blockchain.status()
    assert isinstance(status, AgentStatus), f"{value!r} returned {type(status)}"
    if not status.available:
        assert status.reason, f"{value!r}: off without saying why"
    json.dumps(status.for_page())


def test_nothing_real_is_simulated_on_its_own() -> None:
    """A double that switched itself on would be the UI lying."""
    status = blockchain.status()
    assert not status.available
    assert status.identity is None and status.wallet is None and status.last_payment is None


def test_the_off_status_is_exactly_the_documented_json() -> None:
    assert blockchain.status().for_page() == OFF_JSON


def test_simulate_forces_the_doubles_even_when_off() -> None:
    status = blockchain.status(simulate=True)
    assert status.available and status.identity is not None and status.identity.verified


def test_a_missing_sdk_is_reported_with_the_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    hide_sdk(monkeypatch)
    monkeypatch.setenv("MIRAG_BLOCKCHAIN", "testnet")
    status = blockchain.status()
    assert not status.available
    assert 'pip install -e ".[blockchain]"' in status.reason


# ══ 2 · the border ════════════════════════════════════════════════════════════

@pytest.mark.slow
def test_importing_the_layer_does_not_import_the_sdk() -> None:
    """The property that lets the core run without the optional dependency.

    A fresh interpreter with an import guard: any ATTEMPT to import ``stellar_sdk`` is
    recorded (and fails), so the check means something even when the SDK is installed.
    """
    code = textwrap.dedent("""
        import json, os, sys

        attempts = []

        class Guard:
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] == "stellar_sdk":
                    attempts.append(name)
                    raise ModuleNotFoundError(f"blocked by the test: {name}")
                return None

        sys.meta_path.insert(0, Guard())
        import mirag.integrations.blockchain as blockchain
        import mirag.integrations.blockchain.wallet.keys
        after_import = list(attempts)
        off = blockchain.status().for_page()
        simulated = blockchain.status(simulate=True).for_page()
        after_off = list(attempts)
        os.environ["MIRAG_BLOCKCHAIN"] = "testnet"
        on = blockchain.status()
        print(json.dumps({"after_import": after_import, "after_off": after_off,
                          "loaded": "stellar_sdk" in sys.modules, "off": off["available"],
                          "simulated": simulated["available"], "on_reason": on.reason,
                          "on_attempts": len(attempts)}))
    """)
    env = {k: v for k, v in os.environ.items() if k not in LAYER_VARIABLES}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC_ROOT), env.get("PYTHONPATH")]))
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT, env=env,
                            capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == 0, result.stderr[-800:]
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report["after_import"] == [], f"importing the layer tried the SDK: {report}"
    assert report["after_off"] == [], f"an off status tried the SDK: {report}"
    assert report["loaded"] is False
    assert report["off"] is False and report["simulated"] is True
    # With the lock open, the SDK is wanted - and its absence is said, not raised.
    assert report["on_attempts"] >= 1
    assert 'pip install -e ".[blockchain]"' in report["on_reason"]


@pytest.mark.parametrize("network", [None, "testnet"])
def test_the_container_status_works_without_the_sdk(monkeypatch: pytest.MonkeyPatch,
                                                     shared_container: Container,
                                                     network: str | None) -> None:
    hide_sdk(monkeypatch)
    if network:
        monkeypatch.setenv("MIRAG_BLOCKCHAIN", network)
    page = shared_container.blockchain_status()
    json.dumps(page)
    assert set(page) == set(OFF_JSON)
    assert page["available"] is False and page["reason"]
    if network is None:
        assert page == OFF_JSON


def test_only_the_client_names_socket_apis() -> None:
    """What client.py's docstring claims, checked. The rule is about the SOCKET, not the SDK."""
    socket_names = {"Server", "SorobanServer", "ContractClient", "urlopen", "create_connection"}
    socket_modules = {"socket", "requests", "httpx", "aiohttp", "urllib3", "urllib.request",
                      "http.client"}
    offenders = []
    for relative, _, tree in layer_modules():
        if relative == "stellar/client.py":
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Attribute):
                names.append(node.attr)
            elif isinstance(node, ast.ImportFrom | ast.Import):
                names.extend(alias.name for alias in node.names)
                offenders.extend(f"{relative} imports {module}" for module in imported_modules(node)
                                 if module in socket_modules or module.split(".")[0] in socket_modules)
            offenders.extend(f"{relative} names {name}" for name in names if name in socket_names)
    assert not offenders, "network outside client.py:\n  " + "\n  ".join(offenders)


def test_the_sdk_enters_only_where_declared() -> None:
    offenders = []
    for relative, _, tree in layer_modules():
        for node in ast.walk(tree):
            if not any(module.split(".")[0] == "stellar_sdk" for module in imported_modules(node)):
                continue
            if relative == "stellar/client.py":
                continue
            names = {alias.name for alias in node.names}  # type: ignore[attr-defined]
            if relative == "wallet/keys.py" and isinstance(node, ast.ImportFrom) \
                    and node.module == "stellar_sdk" and names == {"Keypair"}:
                continue  # pure cryptography, imported lazily: the declared exception
            offenders.append(f"{relative}: {ast.unparse(node)}")
    assert not offenders, f"stellar_sdk imported where it is not declared: {offenders}"


def test_every_network_method_goes_through_the_choke_point() -> None:
    source = (LAYER / "stellar" / "client.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    [client] = [node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "StellarClient"]
    methods = {node.name: node for node in client.body if isinstance(node, ast.FunctionDef)}

    def attribute_calls(function: ast.FunctionDef) -> set[str]:
        return {node.func.attr for node in ast.walk(function)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}

    # The choke point itself re-checks the lock, even if the caller already did.
    assert "obstacle" in attribute_calls(methods["_request"])
    pure = {"xlm_balance"}  # parsing only, declared here
    public = [fn for name, fn in methods.items() if not name.startswith("_") and name not in pure]
    assert len(public) >= 6, f"only {len(public)} network methods to check"
    for function in public:
        assert "_request" in attribute_calls(function), \
            f"StellarClient.{function.name}() goes to the network without _request"


# ══ 3 · the secrets ═══════════════════════════════════════════════════════════

def test_only_the_keys_module_names_the_secret_variable() -> None:
    offenders = [relative for relative, source, _ in layer_modules()
                 if SECRET_VARIABLE in source and relative != "wallet/keys.py"]
    assert not offenders, f"the secret variable is handled outside wallet/keys.py: {offenders}"


def test_only_the_keys_module_returns_or_generates_a_secret() -> None:
    """``AgentKeys.generate()`` is the only function in the repo that returns a private key."""
    offenders = []
    for relative, _, tree in layer_modules():
        if relative == "wallet/keys.py":
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and (
                    node.attr == "secret"
                    or (node.attr == "random" and isinstance(node.value, ast.Name)
                        and node.value.id == "Keypair")):
                offenders.append(f"{relative}: {ast.unparse(node)}")
    assert not offenders, f"secrets returned or generated outside wallet/keys.py: {offenders}"


def test_no_core_module_reads_the_secret_key() -> None:
    """The invariant is not "does not name it" but "does not READ it".

    ``projects/packaging.py`` must name it: it hunts for it before a ZIP reaches the user.
    Naming it to detect it is the opposite of using it. What no core module may do is take
    it from the environment, which is how it would end up in a trace, a log or the model's
    context.
    """
    hunters = {"projects/packaging.py"}  # declared: names it to detect it
    sources = [path for path in sorted(PACKAGE_ROOT.rglob("*.py"))
               if LAYER not in path.parents]
    assert len(sources) >= 25, f"the scan does not see the core: {len(sources)} files"
    offenders = []
    for path in sources:
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        if SECRET_VARIABLE not in source:
            continue
        if relative not in hunters:
            offenders.append(f"{relative} names it without being declared")
            continue
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and node.value == SECRET_VARIABLE:
                offenders.append(f"{relative} uses it as a loose string, not inside the regex")
    assert not offenders, f"the secret key is handled by the core: {offenders}"
    for hunter in hunters:
        assert SECRET_VARIABLE in (PACKAGE_ROOT / hunter).read_text(encoding="utf-8"), \
            "the hunter forgot the key: a ZIP with a seed would pass"


def test_the_wallet_exposes_no_secret_and_no_spending() -> None:
    """By AST and not by importing: the wallet service drags the SDK in, and this file runs
    on purpose without it. A test that could only check this with the SDK installed would
    check nothing in the normal suite."""
    tree = ast.parse((LAYER / "wallet" / "service.py").read_text(encoding="utf-8"))
    defined = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert defined, "wallet/service.py defines no function"
    forbidden = {"secret", "secret_key", "private_key", "seed", "signer", "keypair",
                 "pay", "send", "transfer"}
    assert not defined & forbidden, f"the wallet service exposes {defined & forbidden}"
    assert {"wallet", "payments", "last_payment", "fund_testnet"} <= defined, defined


def test_no_outgoing_payment_function_exists() -> None:
    """The declared capability is to RECEIVE. If that changes, it has to show."""
    spending = re.compile(r"(^|_)(pay|send|transfer|withdraw|spend)(_|$)")
    trees = [(relative, tree) for relative, _, tree in layer_modules()]
    trees.append(("scripts/blockchain_agent_demo.py", ast.parse(DEMO.read_text(encoding="utf-8"))))
    offenders = [f"{relative}: def {node.name}()"
                 for relative, tree in trees for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                 and spending.search(node.name)]
    assert not offenders, f"outgoing spending appeared: {offenders}"


@pytest.mark.parametrize("where", ["identity.uri", "reason", "links", "wallet.address"])
def test_what_goes_out_over_http_cannot_carry_a_seed(where: str) -> None:
    """The last firewall: ``for_page()`` RAISES when it sees something shaped like a seed."""
    status = doubles.status()
    assert status.identity is not None and status.wallet is not None
    poisoned = {
        "identity.uri": lambda: replace(status, identity=replace(status.identity, uri=SEED)),
        "reason": lambda: replace(status, reason=f"oops {SEED}"),
        "links": lambda: replace(status, links={"account": f"https://x/{SEED}"}),
        "wallet.address": lambda: replace(status, wallet=replace(status.wallet, address=SEED)),
    }[where]()
    with pytest.raises(SecretLeakError, match="secret"):
        poisoned.for_page()


def test_the_normal_status_goes_out() -> None:
    page = doubles.status().for_page()
    assert page["available"] and page["identity"]["verified"]
    assert not models.contains_seed(json.dumps(page))


def test_the_page_json_has_exactly_the_documented_keys() -> None:
    page = doubles.status().for_page()
    assert set(page) == {"available", "reason", "identity", "wallet", "last_payment", "links"}
    assert set(page["identity"]) == {"agent", "agent_id", "registry", "network", "onchain_wallet",
                                     "uri", "registration_tx", "wallet_tx", "verified", "reason"}
    assert set(page["wallet"]) == {"agent", "address", "network", "balance", "exists"}
    assert set(page["last_payment"]) == {"hash", "from", "amount", "asset", "at"}
    assert set(page["links"]) <= {"account", "registry", "tx"}


def test_packaging_catches_a_stellar_seed() -> None:
    """A Stellar key inside a delivered project has to block the download."""
    fabricated = b"SECRET = '" + SEED.encode() + b"'"
    assert SECRETS.search(fabricated), "the secrets regex does not recognise a Stellar seed"


def test_the_keys_never_show_the_secret() -> None:
    keys = AgentKeys({SECRET_VARIABLE: SEED})
    assert keys.has_secret()
    assert SEED not in repr(keys) and SEED not in str(keys)


def test_without_a_secret_the_address_is_the_public_key() -> None:
    keys = AgentKeys({"STELLAR_PUBLIC_KEY": f"  {PUBLIC} "})
    assert not keys.has_secret() and keys.address() == PUBLIC


def test_without_any_key_signing_is_refused_by_name() -> None:
    keys = AgentKeys({})
    assert keys.address() == "" and not keys.can_sign()
    with pytest.raises(MissingKeyError, match=SECRET_VARIABLE):
        keys.signer()


# ══ 4 · the models and the metadata ═══════════════════════════════════════════

def test_addresses_are_told_apart_by_their_shape() -> None:
    assert models.is_public_key(PUBLIC)
    assert models.is_public_key(doubles.WALLET) and models.is_public_key(doubles.PAYER)
    assert not models.is_public_key(SEED)
    assert not models.is_public_key("G" + "A" * 54)
    assert not models.is_public_key(None)
    assert models.is_contract(config.NETWORKS[config.TESTNET].identity_registry)
    assert models.contains_seed("something S" + "B" * 55 + " in the middle")
    assert not models.contains_seed(PUBLIC)


def test_a_status_is_really_frozen() -> None:
    status = doubles.status()
    with pytest.raises(TypeError):
        status.links["tx"] = "changed"  # type: ignore[index]
    assert models.disabled("why") == AgentStatus(available=False, reason="why")


def test_the_identity_summary_only_previews_the_uri() -> None:
    identity = doubles.status().identity
    assert identity is not None and len(identity.uri) > models.URI_PREVIEW_CHARS
    assert len(identity.summary()["uri"]) == models.URI_PREVIEW_CHARS


def test_the_metadata_has_the_shape_of_the_standard() -> None:
    document = metadata.registration_document(wallet=PUBLIC)
    assert document["type"] == metadata.REGISTRATION_TYPE
    assert document["type"].endswith("#registration-v1")
    assert document["agentWallet"] == PUBLIC
    assert document["role"] == "backend" and document["capabilities"]
    assert "agentWallet" not in metadata.registration_document()


def test_the_metadata_round_trips() -> None:
    uri = metadata.backend_uri(PUBLIC)
    assert uri.startswith(metadata.DATA_URI_PREFIX)
    assert len(uri) < metadata.MAX_URI_BYTES
    assert metadata.from_uri(uri) == metadata.registration_document(wallet=PUBLIC)


@pytest.mark.parametrize("uri", [
    "https://example.com/a.json",
    "data:application/json;base64,!!!",
    "data:application/json;base64,WzEsMl0=",  # a JSON list, not a document
    "",
    None,
])
def test_an_unreadable_uri_is_information_not_an_exception(uri: str | None) -> None:
    assert metadata.from_uri(uri) is None


def test_metadata_that_does_not_fit_is_rejected_here_and_not_on_chain() -> None:
    huge = replace(metadata.BACKEND_PROFILE, description="x" * metadata.MAX_URI_BYTES)
    with pytest.raises(MetadataTooLargeError):
        metadata.to_uri(huge.document())
    assert issubclass(MetadataTooLargeError, ValueError)


def test_the_doubles_cover_the_three_states() -> None:
    good, bare, unverified = doubles.status(), doubles.without_identity(), doubles.not_verified()
    assert good.identity is not None and good.identity.verified and good.last_payment is not None
    assert "tx" in good.links
    assert bare.available and bare.identity is None and bare.wallet is not None
    assert unverified.identity is not None and not unverified.identity.verified
    assert unverified.identity.reason and unverified.last_payment is None
    assert "tx" not in unverified.links


# ══ 5 · the demo and the documentation ════════════════════════════════════════

@pytest.mark.parametrize("flag", [[], ["--fund"], ["--register"], ["--abi"]])
def test_the_demo_does_not_touch_the_network_while_off(capsys: pytest.CaptureFixture[str],
                                                        flag: list[str]) -> None:
    assert load_demo().main(flag, dotenv=False) == 1
    assert "off" in capsys.readouterr().out


def test_the_demo_never_overwrites_nor_prints_an_existing_secret(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv(SECRET_VARIABLE, SEED)
    assert load_demo().main(["--create"], dotenv=False) == 1
    out = capsys.readouterr().out
    assert SEED not in out and SECRET_VARIABLE in out


@pytest.mark.parametrize(("locale", "phrases"), [
    ("en", ("RECEIVE", "NOT IMPLEMENTED", "NOT REACHABLE", "MIRAG_BLOCKCHAIN=off")),
    ("es", ("RECIBIR", "NO IMPLEMENTADO", "NO ALCANZABLE", "MIRAG_BLOCKCHAIN=off")),
])
def test_the_documentation_says_what_the_code_does(locale: str, phrases: tuple[str, ...]) -> None:
    document = DOCS[locale].read_text(encoding="utf-8")
    for phrase in phrases:
        assert phrase in document, f"docs/{locale}/blockchain.md does not say {phrase!r}"
    assert config.NETWORKS[config.TESTNET].identity_registry in document, \
        "the contract the code uses is not the one the documentation names"
    assert 'pip install -e ".[blockchain]"' in document
    assert "scripts/blockchain_agent_demo.py" in document


def test_the_documentation_names_every_variable_the_code_reads() -> None:
    variables: set[str] = set()
    for _, _, tree in layer_modules():
        for node in tree.body:
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                    and any(isinstance(t, ast.Name) and t.id.endswith("_VARIABLE")
                            for t in node.targets)):
                variables.add(str(node.value.value))
    assert variables == set(LAYER_VARIABLES), variables
    for locale, path in DOCS.items():
        document = path.read_text(encoding="utf-8")
        missing = sorted(v for v in variables if v not in document)
        assert not missing, f"docs/{locale}/blockchain.md does not name {missing}"
