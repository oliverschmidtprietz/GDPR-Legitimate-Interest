# Legitimate Interest (GDPR Art. 6(1)(f) LIA) — Deployment Guide

GDPR **Legitimate Interest Assessment** skill for Claude — guides a structured Art. 6(1)(f) assessment
using the EDPB three-step test and produces a documented LIA suitable for accountability records.

## Overview

Combines the current legitimate-interest sources into a guided three-step workflow:

- **EDPB Guidelines 1/2024** on Art. 6(1)(f) (adopted 8 October 2024) — the core interpretive document
- **EDPB Opinion 28/2024** on AI models (17 December 2024) — AI-specific LIA guidance
- **EDPB OSS Case Digest on Legitimate Interest** (Dr. TJ McIntyre, March 2026) — 62 OSS decisions + 5 EDPB binding decisions
- **CNIL Recommendations on Legitimate Interest for AI Development** (19 June 2025) + web-scraping focus sheet
- **UK ICO Legitimate Interests Guidance** (updated 23 March 2026) — incl. the DUA Act 2025 "Recognised Legitimate Interest" basis and the divergent necessity standard
- **CJEU case law** and key context modules (direct marketing, fraud prevention, IT security, employee monitoring, AI training, web scraping, credit checks)
- **Jurisdiction coverage** — EU, UK, FR, DE

## File Structure

```
skills/legitimate-interest/
├── SKILL.md                              # Main skill instructions (deploy this)
├── CHANGELOG.md                          # Version history
├── README.md                             # This file
└── references/
    ├── step1-legitimate-interest.md      # Step 1 — identifying the legitimate interest
    ├── step2-necessity.md                # Step 2 — necessity / data minimisation
    ├── step3-balancing.md                # Step 3 — balancing test
    ├── context-modules.md                # Context-specific modules (marketing, fraud, AI training, …)
    ├── cjeu-case-law.md                  # Key CJEU holdings
    ├── oss-enforcement-practice.md       # EDPB OSS Case Digest — enforcement patterns
    ├── additional-regulatory-sources.md  # EDPB Opinion 28/2024, CNIL AI, ICO/DUA Act
    ├── data-subject-rights.md            # Right to object (Art. 21) and related rights
    └── jurisdiction-notes.md             # EU / UK / FR / DE notes
```

## Deploy

Copy `SKILL.md` and `references/` to your Claude skills directory (or install via your platform's skill
mechanism). The skill activates on legitimate-interest / Art. 6(1)(f) / "Interessenabwägung" /
"berechtigtes Interesse" / LIA / three-step-test prompts.

## Version History

See [CHANGELOG.md](CHANGELOG.md). Current status: **pre-review (v0.9)** — pending the iteration-1
eval benchmark to promote to v1.0. Already published on [lawve.ai](https://lawve.ai/en/skills/legitimate-interest-oliver-schmidt-prietz).

## License

AGPL-3.0 — see the repository `LICENSE`.
