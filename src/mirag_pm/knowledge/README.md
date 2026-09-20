# The corpus of the PM agent

`en/` holds the knowledge base as it was authored: 91 domain documents across 13 domains plus
`99-reference`, and 9 meta files — `INDEX.md` (633 concept terms), `SOURCES.md` (the `[Snnn]`
and `[Ennn]` registers), `GLOSSARY.md`, `CONCEPT_GRAPH.md`, `TAXONOMY.md`, `CORPUS_AUDIT.md`,
`RESEARCH_BACKLOG.md`, `CHANGELOG.md` and `README.md`.

**There is no `es/`, and that is deliberate.** The documents are English; the answer language
is a separate matter, decided by the message catalogue's language directive. A duplicated
Spanish tree would be 91 files that must be edited twice and will eventually disagree, and a
symlink would hide the fact behind a filesystem trick. `PmCorpus.load` falls back to `en/`
and says so in its load report, so the single-language nature of this corpus is visible
rather than simulated.

**Read `en/README.md` before writing any code that consumes this.** It states the contract
every document follows, what each marker means (`⚠`, `[DISPUTED]`, `[SYNTHESIS]`,
`[INFERENCE]`, "do not cite", `UNVERIFIED`), and the ten rules an agent using this knowledge
base has to obey. Those rules are not advice: they are the difference between an agent that
is traceable and one that merely sounds informed.

Nothing here was summarised, trimmed or reformatted on the way in. The tree is byte-identical
to the vault it came from.
