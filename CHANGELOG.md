# Changelog — legitimate-interest

All notable changes to this skill are documented here.

Format: `## [vX.Y] — YYYY-MM-DD`

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
