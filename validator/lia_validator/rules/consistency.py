"""LOGIC-1 / ORDER-1 / COMPLETE-1 — three-step-test internal consistency.

The EDPB three-step test (SKILL.md "Three-Step Test: Guided Assessment") is
CONJUNCTIVE and meant to SHORT-CIRCUIT: step2 is only reached if step1 passes,
step3 only if step2 passes, and the overall li_appropriate verdict can only be
'yes'/'conditional' if no reached step failed. These rules catch the sidecar
recording a self-contradictory combination of verdicts. All findings-based —
never raise (a defensively-read missing/malformed step or overall block simply
means the rule has nothing to say, not a crash).
"""
from ..findings import Finding
from ..registry import rule

SPEC_STEP1 = "SKILL.md#step-1-pursuit-of-a-legitimate-interest"
SPEC_STEP3 = "SKILL.md#step-3-balancing-test"


def _step(sidecar, name):
    step = sidecar.get(name)
    return step if isinstance(step, dict) else None


@rule(id="LOGIC-1", severity="rejection", category="logic",
      description="overall.li_appropriate must not be 'yes' when any reached step's verdict is 'fail' "
                  "— the three-step test is conjunctive.",
      spec_anchor=SPEC_STEP1)
def conjunctive_contradiction(sidecar, ctx):
    out = []
    overall = sidecar.get("overall")
    if not isinstance(overall, dict) or overall.get("li_appropriate") != "yes":
        return out
    for name in ("step1", "step2", "step3"):
        step = _step(sidecar, name)
        if step is not None and step.get("verdict") == "fail":
            out.append(Finding(
                rule_id="LOGIC-1", category="logic", severity="rejection",
                message=(f"{name}.verdict is 'fail' but overall.li_appropriate is 'yes' — the "
                          "three-step test is conjunctive: a failed step means Art. 6(1)(f) "
                          "cannot be relied on, so the overall verdict cannot be 'yes'."),
                spec_anchor=SPEC_STEP1, field=f"{name}.verdict", entry_type="step",
                fix_hint=f"Either correct {name}.verdict or correct overall.li_appropriate "
                         "— they currently contradict each other.",
            ))
    return out


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
                  "balancing test is not optional once reached.",
      spec_anchor=SPEC_STEP3)
def completeness_step3_required(sidecar, ctx):
    step1 = _step(sidecar, "step1")
    step2 = _step(sidecar, "step2")
    if not (step1 is not None and step1.get("verdict") == "pass"):
        return []
    if not (step2 is not None and step2.get("verdict") == "pass"):
        return []
    step3 = _step(sidecar, "step3")
    if step3 is None or not step3.get("verdict"):
        return [Finding(
            rule_id="COMPLETE-1", category="consistency", severity="warning",
            message=("step1 and step2 both passed, but step3 (the balancing test) is missing "
                      "or has no verdict — the three-step test is not complete without a "
                      "balancing outcome."),
            spec_anchor=SPEC_STEP3, field="step3.verdict", entry_type="step",
            fix_hint="Record step3.verdict once the balancing test has been performed.",
        )]
    return []
