"""ART9-1 — Art. 6(1)(f) alone cannot legitimise Art. 9/10 data (Pre-Assessment Gate G5).

GDPR Art. 9(2) lists an EXHAUSTIVE, closed set of lawful conditions (a)-(j) for
processing special categories of personal data (Art. 9(1)); legitimate interest
under Art. 6(1)(f) is not among them — this follows directly from the closed
wording of Art. 9(2) itself (see also C-252/21 Meta v. Bundeskartellamt,
EU:C:2023:537). Separately, a dataset containing even one Art. 9(1) item is
sensitive in its entirety and requires its own, independent Art. 9(2)
derogation (C-252/21, para. 89). Art. 10 criminal-offence/conviction data additionally requires
processing "only under the control of official authority" or authorisation by
Union/Member State law providing appropriate safeguards. SKILL.md's
Pre-Assessment Gate G5 instructs the assessment to identify the applicable
Art. 9(2) condition (or Art. 10 authorisation) before treating li_appropriate
as 'yes'/'conditional'.

The sidecar's `special_category` object is OPTIONAL (schema v1.1, backward
compatible): its absence means nothing to this rule — it only fires when the
assessment itself has recorded special_category.involved: true. This rule
NEVER infers special-category involvement from step2.data_categories text (no
keyword heuristics, per FIX-BRIEF 2026-10-02): that inference is the
assessment's job (Gate G5), not the deterministic validator's — a free-text
heuristic would risk false positives on innocuous wording (e.g. "wellness
newsletter") that the brief's no-false-positives rule forbids guessing at.
Findings-based — never raises.
"""
from ..findings import Finding
from ..registry import rule

SPEC = "SKILL.md#pre-assessment-gate-is-art-61f-even-available"
_POSITIVE_CLAIMS = ("yes", "conditional")


def _special_category(sidecar):
    sc = sidecar.get("special_category")
    return sc if isinstance(sc, dict) else None


def _overall_li_appropriate(sidecar):
    overall = sidecar.get("overall")
    if not isinstance(overall, dict):
        return None
    return overall.get("li_appropriate")


@rule(id="ART9-1", severity="rejection", category="logic",
      description="special_category.involved: true requires an identified Art. 9(2) condition "
                  "(or Art. 10 authorisation) in art9_condition before overall.li_appropriate "
                  "can be 'yes'/'conditional' — Art. 6(1)(f) alone never legitimises Art. 9/10 "
                  "data.",
      spec_anchor=SPEC)
def special_category_requires_art9_condition(sidecar, ctx):
    sc = _special_category(sidecar)
    if sc is None or sc.get("involved") is not True:
        return []
    li = _overall_li_appropriate(sidecar)
    if li not in _POSITIVE_CLAIMS:
        return []
    condition = sc.get("art9_condition")
    if isinstance(condition, str) and condition.strip():
        return []
    return [Finding(
        rule_id="ART9-1", category="logic", severity="rejection",
        message=("special_category.involved is true (Art. 9 special category or Art. 10 "
                  "criminal-offence data) but no art9_condition (an Art. 9(2)(a)-(j) condition, "
                  "or an Art. 10 official-authority/authorisation basis) is recorded, while "
                  f"overall.li_appropriate is '{li}'. Art. 6(1)(f) alone can never make special "
                  "category or criminal-offence processing lawful — Art. 9(2) is an exhaustive, "
                  "closed list of conditions that does not include legitimate interest (see "
                  "also C-252/21 Meta v. Bundeskartellamt, EU:C:2023:537) — an independent "
                  "Art. 9(2) condition (or Art. 10 authorisation) must be identified."),
        spec_anchor=SPEC, field="special_category.art9_condition", entry_type="gate",
        fix_hint="Identify which Art. 9(2)(a)-(j) condition (or Art. 10 authorisation basis) "
                 "applies and record it in special_category.art9_condition, or correct "
                 "overall.li_appropriate until one has been identified.",
    )]
