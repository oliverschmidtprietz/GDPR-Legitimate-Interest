"""LOGIC-1 / LOGIC-2 / LOGIC-3 / ORDER-1 / COMPLETE-1 — three-step-test internal
consistency.

The EDPB three-step test (SKILL.md "Three-Step Test: Guided Assessment") is
CONJUNCTIVE and meant to SHORT-CIRCUIT: step2 is only reached if step1 passes,
step3 only if step2 passes, and the overall li_appropriate verdict can only be
'yes'/'conditional' if no reached step failed. These rules catch the sidecar
recording a self-contradictory combination of verdicts. All findings-based —
never raise (a defensively-read missing/malformed step or overall block simply
means the rule has nothing to say, not a crash).

'conditional' is treated identically to 'yes' throughout this module: the
sidecar schema's own description (legitimate-interest-sidecar-schema.json,
overall.li_appropriate) says li_appropriate can only be 'yes'/'conditional'
when every reached step's verdict is not 'fail' — 'conditional' is still a
POSITIVE claim that Art. 6(1)(f) is (at least conditionally) available, not a
neutral or negative one.
"""
from ..findings import Finding
from ..registry import rule

SPEC_STEP1 = "SKILL.md#step-1-pursuit-of-a-legitimate-interest"
SPEC_STEP3 = "SKILL.md#step-3-balancing-test"

_POSITIVE_CLAIMS = ("yes", "conditional")


def _step(sidecar, name):
    step = sidecar.get(name)
    return step if isinstance(step, dict) else None


def _overall_li_appropriate(sidecar):
    overall = sidecar.get("overall")
    if not isinstance(overall, dict):
        return None
    return overall.get("li_appropriate")


@rule(id="LOGIC-1", severity="rejection", category="logic",
      description="overall.li_appropriate must not be 'yes'/'conditional' when any reached "
                  "step's verdict is 'fail' — the three-step test is conjunctive.",
      spec_anchor=SPEC_STEP1)
def conjunctive_contradiction(sidecar, ctx):
    out = []
    li = _overall_li_appropriate(sidecar)
    if li not in _POSITIVE_CLAIMS:
        return out
    for name in ("step1", "step2", "step3"):
        step = _step(sidecar, name)
        if step is not None and step.get("verdict") == "fail":
            out.append(Finding(
                rule_id="LOGIC-1", category="logic", severity="rejection",
                message=(f"{name}.verdict is 'fail' but overall.li_appropriate is '{li}' — the "
                          "three-step test is conjunctive: a failed step means Art. 6(1)(f) "
                          f"cannot be relied on, so the overall verdict cannot be '{li}'."),
                spec_anchor=SPEC_STEP1, field=f"{name}.verdict", entry_type="step",
                fix_hint=f"Either correct {name}.verdict or correct overall.li_appropriate "
                         "— they currently contradict each other.",
            ))
    return out


@rule(id="LOGIC-2", severity="rejection", category="logic",
      description="step1.verdict cannot be 'pass' when any of its three cumulative criteria "
                  "(lawful / articulated / real_and_present) is recorded as false.",
      spec_anchor=SPEC_STEP1)
def step1_cumulative_criteria_contradiction(sidecar, ctx):
    step1 = _step(sidecar, "step1")
    if step1 is None or step1.get("verdict") != "pass":
        return []
    out = []
    for criterion in ("lawful", "articulated", "real_and_present"):
        if step1.get(criterion) is False:
            out.append(Finding(
                rule_id="LOGIC-2", category="logic", severity="rejection",
                message=(f"step1.{criterion} is false but step1.verdict is 'pass' — EDPB "
                          "Guidelines 1/2024, para. 17 requires all three criteria (lawful, "
                          "articulated, real_and_present) cumulatively for step1 to pass."),
                spec_anchor=SPEC_STEP1, field=f"step1.{criterion}", entry_type="step",
                fix_hint=f"Either correct step1.{criterion} or correct step1.verdict "
                         "— they currently contradict each other.",
            ))
    return out


@rule(id="LOGIC-3", severity="rejection", category="logic",
      description="step3.verdict cannot be 'pass' when balance is 'against' and no "
                  "mitigating_measures are recorded — step3-balancing.md requires measures "
                  "(and a re-run balance) before the balance can be treated as resolved in "
                  "the controller's favour.",
      spec_anchor=SPEC_STEP3)
def step3_balance_against_contradiction(sidecar, ctx):
    step3 = _step(sidecar, "step3")
    if step3 is None or step3.get("verdict") != "pass" or step3.get("balance") != "against":
        return []
    measures = step3.get("mitigating_measures")
    if isinstance(measures, list) and len(measures) > 0:
        return []
    return [Finding(
        rule_id="LOGIC-3", category="logic", severity="rejection",
        message=("step3.balance is 'against' (the data subjects' interests outweigh the "
                  "controller's) with no mitigating_measures recorded, but step3.verdict is "
                  "'pass'. Per step3-balancing.md: if the balance tips against the controller, "
                  "mitigating measures beyond normal GDPR compliance must be applied and the "
                  "balancing test performed again — if still overridden, Art. 6(1)(f) CANNOT "
                  "be used, period."),
        spec_anchor=SPEC_STEP3, field="step3.verdict", entry_type="step",
        fix_hint="Either record the mitigating_measures that were applied and re-balanced "
                 "(verdict 'pass_with_measures'), or correct step3.verdict to 'fail'.",
    )]


@rule(id="ORDER-1", severity="warning", category="consistency",
      description="step2/step3 should not carry a verdict when step1 (or step2) failed — the "
                  "test should short-circuit.",
      spec_anchor=SPEC_STEP1)
def step_short_circuit(sidecar, ctx):
    out = []
    step1 = _step(sidecar, "step1")
    if step1 is not None and step1.get("verdict") == "fail":
        for name in ("step2", "step3"):
            step = _step(sidecar, name)
            if step is not None and step.get("verdict") is not None:
                out.append(Finding(
                    rule_id="ORDER-1", category="consistency", severity="warning",
                    message=(f"step1.verdict is 'fail' (Art. 6(1)(f) not available), but "
                              f"{name}.verdict is still recorded ('{step.get('verdict')}'). The "
                              "three-step test should short-circuit at step1."),
                    spec_anchor=SPEC_STEP1, field=f"{name}.verdict", entry_type="step",
                    fix_hint=f"Drop {name}.verdict, or record it as not reached, once step1 fails.",
                ))
    step2 = _step(sidecar, "step2")
    if step2 is not None and step2.get("verdict") == "fail":
        step3 = _step(sidecar, "step3")
        if step3 is not None and step3.get("verdict") is not None:
            out.append(Finding(
                rule_id="ORDER-1", category="consistency", severity="warning",
                message=(f"step2.verdict is 'fail', but step3.verdict is still recorded "
                          f"('{step3.get('verdict')}'). The three-step test should short-circuit "
                          "at step2."),
                spec_anchor=SPEC_STEP1, field="step3.verdict", entry_type="step",
                fix_hint="Drop step3.verdict, or record it as not reached, once step2 fails.",
            ))
    return out


@rule(id="COMPLETE-1", severity="warning", category="consistency",
      description="step3 must carry a verdict once step1 and step2 have both passed — the "
                  "balancing test is not optional once reached. Escalates from warning to "
                  "rejection when overall.li_appropriate makes a positive claim ('yes' or "
                  "'conditional') despite the missing balancing outcome — a positive claim "
                  "is only ever a warning-level issue when nothing is actually being asserted.",
      spec_anchor=SPEC_STEP3)
def completeness_step3_required(sidecar, ctx):
    step1 = _step(sidecar, "step1")
    step2 = _step(sidecar, "step2")
    if not (step1 is not None and step1.get("verdict") == "pass"):
        return []
    if not (step2 is not None and step2.get("verdict") == "pass"):
        return []
    step3 = _step(sidecar, "step3")
    if step3 is not None and step3.get("verdict"):
        return []
    li = _overall_li_appropriate(sidecar)
    if li in _POSITIVE_CLAIMS:
        return [Finding(
            rule_id="COMPLETE-1", category="consistency", severity="rejection",
            message=("step1 and step2 both passed, but step3 (the balancing test) is missing "
                      f"or has no verdict, while overall.li_appropriate makes the positive claim "
                      f"'{li}'. A positive overall verdict cannot rest on an incomplete "
                      "three-step test — step3 is not optional once reached."),
            spec_anchor=SPEC_STEP3, field="step3.verdict", entry_type="step",
            fix_hint="Record step3.verdict once the balancing test has been performed, or "
                     "correct overall.li_appropriate to 'no' until it has been.",
        )]
    return [Finding(
        rule_id="COMPLETE-1", category="consistency", severity="warning",
        message=("step1 and step2 both passed, but step3 (the balancing test) is missing "
                  "or has no verdict — the three-step test is not complete without a "
                  "balancing outcome."),
        spec_anchor=SPEC_STEP3, field="step3.verdict", entry_type="step",
        fix_hint="Record step3.verdict once the balancing test has been performed.",
    )]
    return []
