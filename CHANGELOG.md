# Changelog — legitimate-interest

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

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
