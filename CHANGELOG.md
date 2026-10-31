# Changelog — legitimate-interest

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

---

## [v1.4] — 2026-10-31

Bundled tests made portable to the standalone public copy (`scripts/stage-public-copy.sh`
+ `scripts/check-public-portability.sh`). No change to the Art. 6(1)(f) method, gates, or
templates.

- **`tests/conftest.py` extended with `find_schema()`**, which locates a shared
  portfolio schema (`docs/standards/schemas/*.schema.json`) by walking up from the test
  file's own location — works identically whether the schemas sit at the monorepo root
  or at the root of a flat public copy (the staging script now copies them there).
  `test_cli_input_guard.py`, `test_emit_core_artefact.py`, and
  `test_emit_core_artefact_malformed.py` use it, and now derive the skill's own paths
  (`SKILL_ROOT`) from the test file's own location, instead of a hard-coded
  `REPO_ROOT`, which only resolved correctly inside the monorepo.

## [v1.3] — 2026-10-02

Break-it test 2026-10-02 fixes (`scratchpad/breakit/legitimate-interest/p1-p12`,
`LEDGER.md`). Highest-priority legal-content gap closed, four validator logic
holes closed, and the CLI's crash-on-bad-input bug fixed.

- **HIGH — Pre-Assessment Gate G5 (legal content)**: added a new gate to
  "Pre-Assessment Gate: Is Art. 6(1)(f) Even Available?" (SKILL.md) — Art.
  6(1)(f) alone can never legitimise Art. 9(1) special category data or Art. 10
  criminal-offence/conviction data. Art. 9(2) is an exhaustive, closed list of
  conditions (a)-(j) that does not include legitimate interest; Art. 10
  additionally requires official-authority control or Member State/Union law
  authorisation with safeguards. The LIA must identify the applicable
  condition before proceeding, or stop and flag. Matching line added to the
  Summary Format output template, and to `references/step3-balancing.md`'s
  nature-of-data table. Verified against GDPR Art. 9(1)/9(2)(a)-(j)/10 text
  (gdpr-info.eu) — legitimate interest is not one of the (a)-(j) conditions,
  which follows directly from the closed wording of Art. 9(2) itself, cited
  "see also" to C-252/21 *Meta v. Bundeskartellamt*, EU:C:2023:537 with no
  paragraph pin (2026-10-02 correction: an earlier paras. 85-90 pin-cite for
  this specific point was dropped — that range was never verified against the
  primary judgment text and risked actually concerning the separate Art.
  9(2)(e) manifestly-public-data question). The pre-existing, separately
  verified para. 89 citation for "a dataset with even one Art. 9(1) item is
  sensitive in its entirety" (`step3-balancing.md` line 47) is untouched.
- **`references/legitimate-interest-sidecar-schema.json`** (schema v1.0 →
  v1.1, backwards compatible) — added an optional top-level `special_category`
  object (`involved`, `categories[]`, `art9_condition`) recording the Gate G5
  outcome. Absence means nothing was recorded either way, never "not
  involved".
- **New validator rule `ART9-1`** (rejection) — `special_category.involved:
  true` with `overall.li_appropriate` in `yes`/`conditional` and no
  `art9_condition` recorded is a rejection: Art. 6(1)(f) cannot stand in for
  the missing Art. 9(2)/Art. 10 basis.
- **`LOGIC-1` extended** — previously only checked `overall.li_appropriate ==
  'yes'`; now treats `'conditional'` identically (the schema's own description
  already said `li_appropriate` can only be `'yes'`/`'conditional'` when every
  reached step passed — `'conditional'` is a positive claim too).
- **New validator rule `LOGIC-2`** (rejection) — `step1.verdict: pass` can no
  longer coexist with `lawful`/`articulated`/`real_and_present: false`; the
  three criteria are cumulative (EDPB Guidelines 1/2024, para. 17).
- **New validator rule `LOGIC-3`** (rejection) — `step3.verdict: pass` can no
  longer coexist with `balance: against` and an empty/absent
  `mitigating_measures[]`; per `step3-balancing.md`, an against-balance
  requires mitigating measures and a re-run balance before it can be treated
  as resolved in the controller's favour.
- **`COMPLETE-1` escalated** — a missing `step3` verdict after `step1`/`step2`
  both pass was previously always a warning (an exit-0 pass). It now escalates
  to rejection when `overall.li_appropriate` makes a positive claim (`yes` or
  `conditional`) despite the incomplete test; it remains a warning when no
  positive claim is made (`overall.li_appropriate: no`).
- **CLI crash fix (`validator/validate.py`)** — the file-read/JSON-parse step
  had no guard at all: a missing file, an unreadable file, invalid UTF-8, or
  invalid JSON syntax raised an uncaught exception with a raw traceback; a
  non-object top-level JSON document (array/string/null/number) additionally
  crashed `--emit-core-artefact`'s `{**sidecar, ...}` dict-spread with a
  `TypeError`. All five cases now fail closed: a clean one-line message, exit
  1, `status: "failed"` with a single `INPUT-1` rejection finding (mirroring
  `RUNNER-0`'s shape), and — with `--emit-core-artefact` — a schema-valid
  `blocked` artefact instead of no file or a traceback.
- **Anti-result-driven-balancing instruction** — STEP 3 now explicitly states
  that the balancing test follows the facts, not a desired outcome, and
  instructs the skill to decline a request to "make the balance come out in
  our favour."
- **Validator-scope disclaimer added to `README.md`** — mirrors the sentence
  already in `SKILL.md`'s "Machine-readable output" section: a passing
  validation result means the sidecar is internally consistent and complete,
  never that the legal analysis is correct.
- **9 new/updated fixtures** (`validator/fixtures/`) mirroring the break-it
  probes, plus a dedicated CLI input-guard test file
  (`tests/test_cli_input_guard.py`) covering missing/unreadable/non-UTF-8/
  malformed-JSON/non-object-top-level input, both with and without
  `--emit-core-artefact`.
- **`sources.lock.json`** — `references/step3-balancing.md` re-verified
  2026-10-02 (the Art. 9/10 callout addition); manifest `generated_at` bumped
  to match.

---

## [v1.2] — 2026-09-24

Portfolio standard Level 1 (structural-tier) adoption
(`docs/projects/gdpr-skills-marathon/SIX-SKILL-ADOPTION-BRIEF-2026-09-24.md`
§4). No changes to the LIA methodology or legal content — this adds a
machine-readable sidecar alongside the existing human deliverable.

- **`references/legitimate-interest-sidecar-schema.json`** (new) — native sidecar
  shape: `step1`/`step2`/`step3` verdicts, `overall.li_appropriate`, a domain-specific
  `gaps[]` register of unresolved balancing factors, and `validation.findings[]` for
  the deterministic validator's own gate-vocabulary diagnostics.
- **`validator/`** (new) — `lia_validator` package + `validate.py` CLI (PEP 723
  launcher). Five rules: `SCHEMA-1` (schema conformance), `LOGIC-1` (the three-step
  test is conjunctive — `overall.li_appropriate` cannot be `yes` if a reached step's
  verdict is `fail`), `ORDER-1` (the test should short-circuit once a step fails),
  `COMPLETE-1` (step3 is required once step1 and step2 both pass), `SRC-1`
  (`sources.lock.json` coverage + 12-month freshness), plus the `RUNNER-0`
  empty-registry fail-closed guard. `--emit-core-artefact` projects the live result
  into the portfolio `skill-artefact-1.1` core artefact, populating `sources[]` from
  `sources.lock.json`, `handoffs[]` to `data-subject-rights` when the overall verdict
  could support an Art. 21(1) objection re-assessment, and `unknowns[]` from the
  sidecar's own `gaps[]` — never hard-coded empty.
- **`sources.lock.json`** (new) — covers all 9 `references/*.md` files with honest
  per-file `last_verified` dates: `data-subject-rights.md` and `jurisdiction-notes.md`
  at `2026-08-21` (the v1.1 citation-audit fixes CF-14/CF-24 actually touched them),
  the other 7 files at the `2026-06-11` v1.0 baseline (untouched by that audit).
- **`conformance.json`** (new) — declares `tier: structural`, `standard_version: 1.4`.
  `uv run --with jsonschema python scripts/check_conformance.py` reports
  `CONFORMANT legitimate-interest`.
- **32 pytest cases** (`tests/`) — schema self-validity, every rule proven to fire
  alone on its own fixture, the `--emit-core-artefact` CLI contract, and adversarial
  malformed-input regression tests (never crash; always emit a schema-valid artefact).
- **`SKILL.md`** — new "Machine-readable output" section pointing at the sidecar
  schema and the validator CLI.

---

## [v1.1] — 2026-08-21

Corrections from the portfolio audit (`docs/projects/gdpr-skills-marathon/AUDIT-2026-08-19.md`, findings CF-14, CF-15, CF-24). No behavioural changes — citation and pinpoint-locator fixes only.

- **CF-14** — `references/data-subject-rights.md`: the profiling-inclusion clause under the right to object to direct marketing was mis-cited to Art. 21(3) (the "processing must cease" consequence); corrected to Art. 21(2), matching the rest of the skill.
- **CF-15** — `SKILL.md` Gate G4 (post-hoc basis-switching): dropped the borrowed "EDPB Guidelines 1/2024, para. 9" pinpoint, which actually covers a different proposition (LI-not-a-default, correctly cited at Critical Reminder #1), and cited EDPB Guidelines 5/2020 on Consent instead — the same authority Critical Reminder #8 already uses for this doctrine.
- **CF-24** — `SKILL.md` Gate G1 and `references/jurisdiction-notes.md`: the public-authority carve-out was cited as "Art. 6(1), second indent," a locator that doesn't exist in the Regulation; corrected to "Art. 6(1), second subparagraph" in both files.

---

## [v1.0] — 2026-06-11

First **reviewed** release. Promoted from v0.9 on the strength of the iteration-1 skill-vs-no-skill eval benchmark (the v0.9 entry flagged this as the gating step).

- **`evals/evals.json` authored** — 4 realistic practitioner scenarios spanning the skill's high-stakes coverage: AI training on scraped data, B2B direct marketing, employee monitoring, and credit-scoring profiling (7 objectively-checkable assertions each).
- **Iteration-1 benchmark** (Sonnet, with-skill vs no-skill baseline, same model both sides): with-skill **100%** (28/28 assertions) vs baseline **75%** (21/28) — a **+25.0 pp** differential.
- **Where the skill adds value (baseline misses):** the baseline failed to cite EDPB Guidelines 1/2024 in *all four* cases, and on the credit-scoring case missed both the CJEU SCHUFA line and the Art. 21 right to object — precisely the current, specific authorities the skill bundles. With-skill LIAs were also ~4× more thorough and consistently reached a documented, accountability-ready conclusion.
- Eval artifacts: `../legitimate-interest-workspace/iteration-1/` (benchmark.json/.md + per-run grading + review viewer).

No SKILL.md content changes from v0.9 — the promotion rests on the benchmark.

**Status:** reviewed. Iteration-2 candidate (non-blocking): the with-skill LIAs run long (~8k words); a future express/short mode or length cap could improve practitioner ergonomics (cf. the legal-analysis-forge v1.1 explainer-length lesson).

---

## [v0.9] — 2026-06-09

Initial monorepo release. Canonicalised into the monorepo from the live lawve.ai copy
(`legitimate-interest-oliver-schmidt-prietz`, authored 2026-04-06), which until now lived only on
lawve.ai. Content captured verbatim from the live skill; monorepo frontmatter
(`author` / `license` / `version`) added — no substantive content changes.

- **SKILL.md** — GDPR Art. 6(1)(f) Legitimate Interest Assessment via the EDPB three-step test,
  producing a documented LIA suitable for accountability records. Grounded in EDPB Guidelines 1/2024,
  EDPB Opinion 28/2024 (AI models), the EDPB OSS Case Digest on Legitimate Interest (Dr. TJ McIntyre,
  March 2026), CNIL Recommendations on Legitimate Interest for AI Development (June 2025), UK ICO
  guidance (incl. the DUA Act 2025 "Recognised Legitimate Interest" basis), and key CJEU case law.
- **9 `references/`** — three-step modules (`step1-legitimate-interest`, `step2-necessity`,
  `step3-balancing`), `context-modules` (marketing, fraud, IT security, employee monitoring, AI
  training, web scraping, credit checks), `cjeu-case-law`, `oss-enforcement-practice` (62 OSS + 5 EDPB
  binding decisions), `additional-regulatory-sources`, `data-subject-rights` (Art. 21 right to object),
  and `jurisdiction-notes` (EU / UK / FR / DE).

**Status:** pre-review (v0.9). Pending the iteration-1 skill-vs-no-skill eval benchmark to promote to
v1.0 (an `evals/evals.json` is still to be authored — it was not part of the live lawve package).
Already published on lawve.ai (jurisdictions EU/UK/FR/DE).

---
