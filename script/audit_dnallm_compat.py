"""Audit the official model registry against dnallm's MODEL_INFO authority (261014-l6h, L6H-02).

Purpose
-------
The 2026-10-14 maintainer ruling makes dnallm (the READ-ONLY sibling
clone ``../DNALLM``, branch ``dev``) the single download authority: every
model download flows through ``dnallm.models.model.download_model`` on
ModelScope, and the registry's default list may carry ONLY
dnallm-adapted models (authority = the per-architecture loader set in
``dnallm/models/modeling_auto.py``'s ``MODEL_INFO``). This script aligns
the committed ``pipeline/models_info.json`` ID fields with that
authority and emits the committed verdict map
``pipeline/dnallm_compat.json`` that the next quick task's slot-2
model-download screen consumes.

Authority rules (encoded EXACTLY; the five rules of the plan):

1. **Member matching** — each registry entry is matched by the BASENAME
   (last path segment) of its non-empty ``huggingface`` or ``modelscope``
   field against the union of every ``MODEL_INFO`` family's
   ``huggingface`` + ``modelscope`` + ``default`` entries' basenames.
   Every match decision is printed (family + which list + position).
2. **huggingface-field fix** — a matched member whose family
   huggingface slot (same member position) differs ONLY in org (same
   basename) is rewritten to the slot value.
3. **modelscope-field fix** — a matched member whose family modelscope
   slot (same member position) is non-None and differs from our field
   is rewritten to the slot value.
4. **modelscope-field KEEP** — slot is None but our value matches
   ``lgq12697/<basename>``: kept verbatim, channel
   ``modelscope-mirror`` (dnallm's own default channel —
   ``load_preset_model`` resolves every family to its lgq12697 default
   and downloads with ``source="modelscope"``).
5. **No family membership after the fixes** — ``dnllm_adapted`` false;
   registry fields untouched (informational only).

Input
-----
- ``pipeline/models_info.json`` — the committed official registry (59
  entries; the compat map's key set is pinned to this file's keys).
- ``<dnallm-root>/dnallm/models/modeling_auto.py`` — ``MODEL_INFO``,
  loaded via ``importlib.util`` file-path import (the module imports
  only ``collections``; NO dnallm install and NO yaml are needed — CI
  never runs this script).

Output
------
- ``pipeline/models_info.json`` — rewritten in place with ONLY the
  rule-2/rule-3 field fixes applied (serialization recipe:
  ``json.dumps(doc, indent=4, ensure_ascii=False, sort_keys=True)`` +
  one trailing newline; the script REFUSES to write if the recipe does
  not roundtrip the CURRENT file byte-identically — a reflowed diff
  means the recipe is wrong, never the data).
- ``pipeline/dnallm_compat.json`` — ``{"schema_version": 1,
  "dnallm_commit": <sha>, "models": {<registry key>: {"dnllm_adapted":
  bool, "family": str|null, "architecture": <MODEL_INFO
  model_architecture>|null, "modelscope": <download ID: slot value or
  kept lgq12697 mirror; null when unadapted>, "channel":
  "modelscope-slot"|"modelscope-mirror"|null}}}`` — exactly the
  registry's keys, same serialization recipe.
- stdout — the full audit report: every one of the 59 verdicts with
  each fix as ``before -> after``.

Usage
-----
Run from anywhere (paths resolve from ``__file__``, never CWD)::

    python script/audit_dnallm_compat.py [--dnallm-root ../DNALLM]

See also:
    - ``DNALLM/dnallm/models/modeling_auto.py`` — MODEL_INFO (the
      read-only authority).
    - ``DNALLM/dnallm/models/model.py`` — ``download_model`` (the retry
      wrapper every download must flow through) and
      ``load_preset_model`` (the lgq12697 default-mirror channel).
    - ``tests/test_dnallm_compat.py`` — the CI-safe pins over the two
      committed artifacts (never imports dnallm).
"""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# ===== Configuration =====

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_INFO_PATH = REPO_ROOT / "pipeline" / "models_info.json"
COMPAT_PATH = REPO_ROOT / "pipeline" / "dnallm_compat.json"
DEFAULT_DNALLM_ROOT = (REPO_ROOT.parent / "DNALLM").resolve()
MODELING_AUTO_RELATIVE = Path("dnallm") / "models" / "modeling_auto.py"

#: The dnallm default-mirror org (rule 4): every MODEL_INFO family's
#: ``default`` lives under this org and ``load_preset_model`` downloads
#: it with ``source="modelscope"`` — a kept mirror ID IS a dnallm
#: ModelScope channel for a slot-None member.
MIRROR_ORG = "lgq12697"

#: The three family lists a registry basename is matched against, in
#: provenance order (the position used for slot lookups comes from the
#: huggingface list first — the lists are position-aligned in MODEL_INFO).
FAMILY_LISTS = ("huggingface", "modelscope", "default")


def recipe(doc):
    """The one serialization recipe both output files use.

    Args:
        doc (dict): the parsed JSON document.

    Returns:
        str: the exact file text (sorted keys, indent 4, one trailing
        newline).
    """
    return json.dumps(doc, indent=4, ensure_ascii=False,
                      sort_keys=True) + "\n"


def repo_basename(repo_id):
    """The last path segment of a repo id (None for empty/None).

    Args:
        repo_id (str | None): a ``org/name`` repo id (or the empty
            string the registry uses for absent IDs).

    Returns:
        str | None: the basename, or None when there is nothing to
        match on.
    """
    if not isinstance(repo_id, str) or not repo_id.strip():
        return None
    return repo_id.rstrip("/").rsplit("/", 1)[-1]


def load_model_info(dnallm_root):
    """Load MODEL_INFO from the read-only sibling clone by file path.

    A file-path ``importlib.util`` load — NO dnallm install and NO
    package import (``modeling_auto.py`` imports only ``collections``,
    verified against dev @ cd4be43).

    Args:
        dnallm_root (Path): the sibling clone root (branch ``dev``).

    Returns:
        dict: ``MODEL_INFO`` — family name -> {huggingface: list,
        modelscope: list, default: str, model_architecture: str, ...}.

    Raises:
        SystemExit: the module file is absent or carries no MODEL_INFO.
    """
    module_path = Path(dnallm_root) / MODELING_AUTO_RELATIVE
    if not module_path.is_file():
        raise SystemExit(
            f"[Error] {module_path} not found — pass --dnallm-root "
            f"pointing at the read-only sibling clone (branch dev)."
        )
    spec = importlib.util.spec_from_file_location(
        "dnallm_modeling_auto_audit", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(
            f"[Error] could not build an import spec for {module_path}."
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model_info = getattr(module, "MODEL_INFO", None)
    if not isinstance(model_info, dict):
        raise SystemExit(
            f"[Error] {module_path} carries no MODEL_INFO dict."
        )
    return model_info


def dnallm_commit(dnallm_root):
    """The sibling clone's HEAD sha (the compat map's provenance).

    Args:
        dnallm_root (Path): the sibling clone root.

    Returns:
        str: the full commit sha.

    Raises:
        SystemExit: git is unavailable or the clone has no HEAD.
    """
    proc = subprocess.run(
        ["git", "-C", str(dnallm_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(
            f"[Error] could not read HEAD of {dnallm_root}: "
            f"{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def family_matches(basename, model_info):
    """Every (family, list, position) a registry basename matches.

    Args:
        basename (str | None): the registry entry's repo-id basename.
        model_info (dict): MODEL_INFO.

    Returns:
        list[tuple]: ``(family, list_name, position)` — position is the
        index in the matched list (None for the scalar ``default``);
        provenance order per family, MODEL_INFO order across families.
    """
    if basename is None:
        return []
    matches = []
    for family, info in model_info.items():
        for list_name in FAMILY_LISTS:
            entries = info.get(list_name)
            values = entries if isinstance(entries, list) else [entries]
            for position, value in enumerate(values):
                if repo_basename(value) == basename:
                    matches.append((family, list_name, position))
                    break  # first hit per list is the member position
    return matches


def slot_values(family_info, position):
    """The huggingface/modelscope slots at one member position.

    Args:
        family_info (dict): one MODEL_INFO family.
        position (int | None): the member position (None -> no slots).

    Returns:
        tuple: ``(hf_slot, ms_slot)`` — each the slot value or None
        (position out of range or the slot itself None).
    """
    if position is None:
        return None, None

    def at(list_name):
        entries = family_info.get(list_name)
        if not isinstance(entries, list) or position >= len(entries):
            return None
        value = entries[position]
        return value if isinstance(value, str) and value else None

    return at("huggingface"), at("modelscope")


def mirror_form(repo_id):
    """Whether a repo id is the ``lgq12697/<basename>`` default mirror.

    Args:
        repo_id (str): the registry entry's modelscope field value.

    Returns:
        bool: True iff the org is the mirror org and the name equals
        the id's own basename (rule 4's keep form).
    """
    parts = repo_id.split("/")
    return (len(parts) == 2 and parts[0] == MIRROR_ORG
            and parts[1] == repo_basename(repo_id))


def audit_entry(entry, model_info):
    """Apply the five authority rules to one registry entry.

    Args:
        entry (dict): the registry entry (NOT mutated — the fixed copy
            is returned).
        model_info (dict): MODEL_INFO.

    Returns:
        tuple: ``(fixed_entry, verdict)` where ``verdict`` is the
        report line's data dict with keys ``adapted``, ``family``,
        ``architecture``, ``modelscope``, ``channel``, ``match``,
        ``fixes`` (list of ``(field, before, after)``).
    """
    fixed = dict(entry)
    hf_basename = repo_basename(entry.get("huggingface"))
    ms_basename = repo_basename(entry.get("modelscope"))
    # match on the huggingface basename first (the primary ID), then
    # the modelscope basename — same member either way
    matches = (family_matches(hf_basename, model_info)
               or family_matches(ms_basename, model_info))
    verdict = {
        "adapted": False, "family": None, "architecture": None,
        "modelscope": None, "channel": None, "match": None, "fixes": [],
    }
    if not matches:
        return fixed, verdict
    family, list_name, position = matches[0]
    family_info = model_info[family]
    hf_slot, ms_slot = slot_values(family_info, position)
    verdict.update({
        "adapted": True,
        "family": family,
        "architecture": family_info.get("model_architecture"),
        "match": f"{family} via {list_name}[{position}]"
        + (f" (+{len(matches) - 1} more)" if len(matches) > 1 else ""),
    })
    # rule 2 — huggingface org fix (same basename, different org)
    our_hf = entry.get("huggingface")
    if (isinstance(our_hf, str) and our_hf and hf_slot is not None
            and hf_slot != our_hf
            and repo_basename(hf_slot) == repo_basename(our_hf)):
        fixed["huggingface"] = hf_slot
        verdict["fixes"].append(("huggingface", our_hf, hf_slot))
    # rules 3/4 — the modelscope download channel
    our_ms = entry.get("modelscope")
    if isinstance(our_ms, str) and our_ms:
        if ms_slot is not None:
            verdict["channel"] = "modelscope-slot"
            verdict["modelscope"] = ms_slot
            if ms_slot != our_ms:
                fixed["modelscope"] = ms_slot
                verdict["fixes"].append(("modelscope", our_ms, ms_slot))
        elif mirror_form(our_ms):
            verdict["channel"] = "modelscope-mirror"
            verdict["modelscope"] = our_ms
        else:
            # defensive: adapted with a slot-None non-mirror field —
            # never occurs over the committed 59; reported loudly.
            verdict["channel"] = "modelscope-mirror"
            verdict["modelscope"] = our_ms
            verdict["fixes"].append(
                ("modelscope", our_ms, our_ms + " (NON-MIRROR KEEP)"))
    return fixed, verdict


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit pipeline/models_info.json against dnallm "
                    "MODEL_INFO and write pipeline/dnallm_compat.json.")
    parser.add_argument(
        "--dnallm-root", default=None,
        help="the read-only sibling clone root (default: "
             f"{DEFAULT_DNALLM_ROOT}, resolved from this script — "
             "never CWD)")
    args = parser.parse_args(argv)
    dnallm_root = (Path(args.dnallm_root).resolve()
                   if args.dnallm_root else DEFAULT_DNALLM_ROOT)

    with open(MODELS_INFO_PATH, "r", encoding="utf-8") as fh:
        current_text = fh.read()
    registry = json.loads(current_text)
    # the recipe guard: refuse to write if the recipe would reflow the
    # CURRENT file (the diff must ever show only ID value lines)
    if recipe(registry) != current_text:
        raise SystemExit(
            "[Error] the serialization recipe does not roundtrip "
            f"{MODELS_INFO_PATH} byte-identically — fix the recipe "
            "before writing anything (a reflowed diff hides real "
            "changes)."
        )

    model_info = load_model_info(dnallm_root)
    commit = dnallm_commit(dnallm_root)

    fixed_registry = {}
    compat_models = {}
    adapted_count = 0
    fix_count = 0
    print(f"dnallm authority: {dnallm_root} @ {commit}")
    print(f"registry: {len(registry)} entries; rules 1-5 applied:\n")
    for key in sorted(registry):
        fixed, verdict = audit_entry(registry[key], model_info)
        fixed_registry[key] = fixed
        if verdict["adapted"]:
            adapted_count += 1
            compat_models[key] = {
                "dnllm_adapted": True,
                "family": verdict["family"],
                "architecture": verdict["architecture"],
                "modelscope": verdict["modelscope"],
                "channel": verdict["channel"],
            }
            fix_parts = [
                f"{field}: {before} -> {after}"
                for field, before, after in verdict["fixes"]]
            fix_count += len(verdict["fixes"])
            print(f"  ADAPTED   {key}")
            print(f"            match={verdict['match']} "
                  f"arch={verdict['architecture']} "
                  f"channel={verdict['channel']}")
            print(f"            modelscope={verdict['modelscope']}")
            for part in fix_parts:
                print(f"            FIX {part}")
        else:
            compat_models[key] = {
                "dnllm_adapted": False,
                "family": None,
                "architecture": None,
                "modelscope": None,
                "channel": None,
            }
            names = " or ".join(
                name for name in (
                    repo_basename(registry[key].get("huggingface")),
                    repo_basename(registry[key].get("modelscope")),
                ) if name) or "(no IDs)"
            print(f"  UNADAPTED {key} ({names})")
    compat = {
        "schema_version": 1,
        "dnallm_commit": commit,
        "models": compat_models,
    }
    MODELS_INFO_PATH.write_text(recipe(fixed_registry), encoding="utf-8")
    COMPAT_PATH.write_text(recipe(compat), encoding="utf-8")
    unadapted_count = len(registry) - adapted_count
    print(f"\nverdicts: {adapted_count} adapted, {unadapted_count} "
          f"unadapted ({len(registry)} total); {fix_count} field fix(es)")
    print(f"written: {MODELS_INFO_PATH}")
    print(f"written: {COMPAT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
