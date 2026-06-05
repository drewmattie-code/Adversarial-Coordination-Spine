#!/usr/bin/env python3
"""
ACS runnable example: Planner / Generator / Evaluator with typed handoffs.
=========================================================================

Demonstrates the core Adversarial Coordination Spine mechanic end to end, with
no dependencies (stdlib only). It:

  1. Has a Planner write a contract (the criteria) as a typed handoff on disk.
  2. Has a Generator produce an artifact and hand it off, also on disk.
  3. Has an Evaluator, a SEPARATE actor with its own session and "model",
     grade the artifact against the contract and REJECT the first pass.
  4. Has the Generator revise, and the Evaluator accept the second pass.
  5. Validates every handoff against schema/handoff.v1.json.

The point: the Evaluator is structurally separate from the Generator (different
session, different model, grades against the contract only), so it cannot
rubber-stamp. State crosses roles on disk, not in a shared context window. Run:

    python3 examples/pipeline.py

License: MIT
"""

import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = HERE.parent / "schema"

_TYPES = {
    "object": dict, "array": list, "string": str,
    "boolean": bool, "number": (int, float), "integer": int,
}


def validate(instance, schema, path="$"):
    errs = []
    t = schema.get("type")
    if t:
        if t in ("number", "integer") and isinstance(instance, bool):
            return [f"{path}: expected {t}, got boolean"]
        if not isinstance(instance, _TYPES[t]):
            return [f"{path}: expected {t}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in {schema['enum']}")
    if t == "object" and isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errs.append(f"{path}: missing required '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errs.append(f"{path}: unexpected property '{key}'")
        for key, sub in props.items():
            if key in instance:
                errs += validate(instance[key], sub, f"{path}.{key}")
    if t == "array" and isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            errs += validate(item, schema["items"], f"{path}[{i}]")
    return errs


# A deterministic clock so the example is reproducible (no wall-clock calls).
_TICK = [0]


def stamp():
    _TICK[0] += 1
    return f"2026-06-05T12:{_TICK[0]:02d}:00Z"


def write_handoff(workspace, schema, **fields):
    fields.setdefault("timestamp", stamp())
    errs = validate(fields, schema)
    if errs:
        raise AssertionError(f"handoff failed schema validation: {errs}")
    path = workspace / f"{fields['handoff_id']}.json"
    path.write_text(json.dumps(fields, indent=2))
    return fields


# ---------------------------------------------------------------------------
# The contract for this sprint: a user-signup form spec.
# ---------------------------------------------------------------------------

CONTRACT = [
    {"id": "c1", "text": "Spec includes an email field"},
    {"id": "c2", "text": "Spec includes a password field"},
    {"id": "c3", "text": "Password minimum length is at least 8"},
    {"id": "c4", "text": "Spec includes a password confirmation field"},
    {"id": "c5", "text": "Passwords are hashed, never stored in plaintext"},
]


def generator(version):
    """Produces the artifact. v1 is deliberately deficient; v2 fixes it."""
    if version == 1:
        return {
            "fields": ["email", "password"],
            "password_min_length": 4,
            "storage": "plaintext",
        }
    return {
        "fields": ["email", "password", "password_confirmation"],
        "password_min_length": 12,
        "storage": "argon2id-hashed",
    }


def evaluator(artifact, contract):
    """
    SEPARATE actor. Grades the artifact against the contract only. It has no
    idea how the Generator built the artifact; it just checks the result.
    """
    checks = {
        "c1": "email" in artifact.get("fields", []),
        "c2": "password" in artifact.get("fields", []),
        "c3": artifact.get("password_min_length", 0) >= 8,
        "c4": "password_confirmation" in artifact.get("fields", []),
        "c5": "plaintext" not in artifact.get("storage", "").lower(),
    }
    results = [{"id": c["id"], "passed": checks[c["id"]],
                "note": "" if checks[c["id"]] else f"fails: {c['text']}"}
               for c in contract]
    passed = all(r["passed"] for r in results)
    fails = [r["id"] for r in results if not r["passed"]]
    summary = "all criteria pass" if passed else f"rejected: {', '.join(fails)} failed"
    return {"passed": passed, "results": results, "summary": summary}


def main():
    schema = json.loads((SCHEMA / "handoff.v1.json").read_text())
    workspace = pathlib.Path(tempfile.mkdtemp(prefix="acs-"))
    sprint = "signup-form"
    print(f"Workspace (state on disk): {workspace}\n")

    # 1) Planner -> Generator: the contract
    write_handoff(workspace, schema,
                  handoff_id="h1-plan", sprint_id=sprint,
                  from_role="planner", to_role="generator", kind="plan",
                  contract={"criteria": CONTRACT},
                  provenance={"session_id": "plan-001", "model": "planner-model"})
    print("Planner sealed a contract with 5 criteria.\n")

    history = []
    accepted = False
    for attempt in (1, 2):
        # 2) Generator -> Evaluator: an artifact submission
        artifact = generator(attempt)
        art_path = workspace / f"artifact-v{attempt}.json"
        art_path.write_text(json.dumps(artifact, indent=2))
        write_handoff(workspace, schema,
                      handoff_id=f"h{attempt}-submit", sprint_id=sprint,
                      from_role="generator", to_role="evaluator", kind="submission",
                      artifact_ref=str(art_path),
                      provenance={"session_id": f"gen-00{attempt}", "model": "generator-model"})

        # 3) Evaluator -> Generator: a verdict (separate session + model)
        verdict = evaluator(artifact, CONTRACT)
        write_handoff(workspace, schema,
                      handoff_id=f"h{attempt}-verdict", sprint_id=sprint,
                      from_role="evaluator", to_role="generator", kind="verdict",
                      artifact_ref=str(art_path), verdict=verdict,
                      provenance={"session_id": f"eval-00{attempt}", "model": "evaluator-model"})

        mark = "ACCEPT" if verdict["passed"] else "REJECT"
        print(f"Attempt {attempt}: Generator submitted -> Evaluator {mark}")
        print(f"    {verdict['summary']}")
        history.append(verdict["passed"])
        if verdict["passed"]:
            accepted = True
            break

    # validate every handoff file on disk against the schema
    files = sorted(workspace.glob("h*.json"))
    all_ok = True
    for f in files:
        errs = validate(json.loads(f.read_text()), schema)
        if errs:
            all_ok = False
            print(f"  INVALID handoff {f.name}: {errs[:2]}")

    print(f"\nHandoffs written: {len(files)}, all valid against handoff.v1.json: {all_ok}")
    print(f"First-pass rejection happened: {history[0] is False}  "
          f"(ACS target: a real evaluator rejects >30% of first passes)")
    print(f"Final state: {'SEALED, artifact accepted' if accepted else 'NOT accepted'}")

    # The adversarial point, stated plainly
    print("\nWhy this is not a rubber stamp: the Evaluator ran as its own session")
    print("and model, graded only against the contract, and had no access to how")
    print("the Generator built the artifact. Separation is structural, not polite.")

    return 0 if all_ok and accepted and history[0] is False else 1


if __name__ == "__main__":
    sys.exit(main())
