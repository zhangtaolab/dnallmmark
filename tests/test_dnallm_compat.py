"""
dnallm compatibility map integrity (261014-l6h, L6H-02).

The committed ``pipeline/dnallm_compat.json`` records, for EXACTLY the
59 official registry keys, whether dnallm (the READ-ONLY sibling clone
../DNALLM @ dev, authority ``MODEL_INFO`` in ``dnallm/models/
modeling_auto.py``) carries a per-architecture loader for that model,
plus the dnallm-authoritative ModelScope download ID and channel for
every adapted entry. The next quick task's slot-2 model-download screen
reads this map for its default-list filter (registry default list =
dnllm-adapted models only, the 2026-10-14 maintainer ruling).

CI-SAFETY (the task contract): this suite reads ONLY the two committed
JSON artifacts — it imports NOTHING from dnallm and never touches
../DNALLM (CI stays GPU/dnallm-free). The map is (re)generated offline
on the maintainer's machine by ``script/audit_dnallm_compat.py``, which
is the only component that reads the sibling clone.

What is pinned here:

- the compat map's schema_version is 1 and its models-object keys are
  EXACTLY the ``pipeline/models_info.json`` keys (set equality; 59
  entries, the count itself pinned — a registry edit without a compat
  regen fails loudly);
- every adapted entry carries non-null family/architecture and a
  well-formed ``org/name`` modelscope ID; every unadapted entry carries
  null family/architecture/modelscope/channel (no half-verdicts);
- the minimal alignment regression locks over the fields the audit
  fixed (the slot-authority DNABERT-2 modelscope ID, the org-authority
  GenomeOcean/MutBERT huggingface IDs) plus the plan-critical
  plant-dnamamba-6mer verdict (the Task-3 download target);
- no key anywhere contains "chaoba" case-insensitively (the 261014-ir9
  confidential-series pin, restated over both files).

See also:
    - ``script/audit_dnallm_compat.py`` — the offline generator (the
      only ../DNALLM reader; encodes the five authority rules).
    - ``tests/test_model_registry.py`` — the 59-entry registry shape
      contract this map's key set is pinned against.
    - ``tests/test_directories_config.py`` — the startup-config loader
      the download-queue reroute consumes (L6H-03).
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_INFO = REPO_ROOT / "pipeline" / "models_info.json"
DNALLM_COMPAT = REPO_ROOT / "pipeline" / "dnallm_compat.json"

#: The official registry count (62 -> 59 at 261014-ir9; the audit map
#: must carry exactly this many keys — a registry change without a map
#: regen is a drift failure, never a silent pass).
REGISTRY_COUNT = 59

#: The ModelScope repo-id shape the adapted entries must carry (the
#: same allowlist grammar the download channel composes argv against).
REPO_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

#: The two channel values an adapted entry may carry: the MODEL_INFO
#: modelscope slot (authoritative mirror) or the kept lgq12697 default
#: mirror (the ID dnallm's own load_preset_model downloads for
#: slot-None members — source="modelscope", the 2026-10-14 authority).
ADAPTED_CHANNELS = frozenset({"modelscope-slot", "modelscope-mirror"})


def load_models_info():
    with open(MODELS_INFO, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_compat():
    with open(DNALLM_COMPAT, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_compat_schema_version_is_1():
    doc = load_compat()
    assert doc["schema_version"] == 1


def test_compat_models_keys_exactly_match_registry_59():
    """THE key-set gate: compat models keys == registry keys, and the
    count is pinned at 59 — adding/removing a registry model without
    regenerating the compat map fails here."""
    registry = load_models_info()
    compat = load_compat()["models"]
    assert len(registry) == REGISTRY_COUNT
    assert len(compat) == REGISTRY_COUNT
    assert set(compat) == set(registry)


def test_compat_records_dnallm_commit():
    """The map's authority provenance: the dnallm commit MODEL_INFO was
    read at (a full 40-hex sha, never a branch name)."""
    commit = load_compat()["dnallm_commit"]
    assert isinstance(commit, str)
    assert re.fullmatch(r"[0-9a-f]{40}", commit), commit


def test_every_adapted_entry_carries_family_architecture_modelscope():
    """Adapted verdicts are complete: non-null family + architecture +
    a well-formed org/name modelscope ID + a known channel."""
    compat = load_compat()["models"]
    adapted = {key: entry for key, entry in compat.items()
               if entry["dnllm_adapted"] is True}
    assert adapted, "the map must carry at least one adapted model"
    for key, entry in adapted.items():
        assert isinstance(entry["family"], str) and entry["family"], key
        assert isinstance(entry["architecture"], str) \
            and entry["architecture"], key
        assert isinstance(entry["modelscope"], str), key
        assert REPO_ID_RE.fullmatch(entry["modelscope"]), \
            (key, entry["modelscope"])
        assert entry["channel"] in ADAPTED_CHANNELS, (key, entry)


def test_every_unadapted_entry_carries_null_fields():
    """Unadapted verdicts carry NO partial data: family/architecture/
    modelscope/channel are all null (informational fields stay in the
    registry itself; the map never half-records a download target)."""
    compat = load_compat()["models"]
    unadapted = {key: entry for key, entry in compat.items()
                 if entry["dnllm_adapted"] is False}
    assert unadapted, "the map must carry at least one unadapted model"
    for key, entry in unadapted.items():
        assert entry["family"] is None, key
        assert entry["architecture"] is None, key
        assert entry["modelscope"] is None, key
        assert entry["channel"] is None, key


def test_dnabert2_modelscope_slot_lock():
    """Slot authority: DNABERT-2-117M's modelscope field is the
    MODEL_INFO slot value (was lgq12697/DNABERT-2-117M), in BOTH the
    registry and the compat map."""
    expected = "ZhejiangLab-LifeScience/DNABERT-2-117M"
    assert load_models_info()["DNABERT-2-117M"]["modelscope"] == expected
    compat = load_compat()["models"]["DNABERT-2-117M"]
    assert compat["dnllm_adapted"] is True
    assert compat["modelscope"] == expected
    assert compat["channel"] == "modelscope-slot"


def test_genomeocean_huggingface_org_lock():
    """Org authority: GenomeOcean-500M's huggingface field is the
    family slot's org (was DOEJGI/GenomeOcean-500M)."""
    entry = load_models_info()["GenomeOcean-500M"]
    assert entry["huggingface"] == "pGenomeOcean/GenomeOcean-500M"


def test_mutbert_huggingface_org_lock():
    """Org authority: MutBERT-Multi's huggingface field is the family
    slot's org (was CompBioDSA/MutBERT-Multi)."""
    entry = load_models_info()["MutBERT-Multi"]
    assert entry["huggingface"] == "JadenLong/MutBERT-Multi"


def test_plant_dnamamba_6mer_adapted_modelscope_slot():
    """The Task-3 download target: plant-dnamamba-6mer is adapted with
    the zhangtaolab slot ID over the modelscope-slot channel."""
    compat = load_compat()["models"]["plant-dnamamba-6mer"]
    assert compat["dnllm_adapted"] is True
    assert compat["modelscope"] == "zhangtaolab/plant-dnamamba-6mer"
    assert compat["channel"] == "modelscope-slot"


def test_no_chaoba_keys_in_registry_or_compat():
    """The 261014-ir9 pin over both files: no key contains "chaoba"
    case-insensitively (the confidential series lives only in history
    and the private local overlay)."""
    for doc in (load_models_info(), load_compat()["models"]):
        offenders = [key for key in doc if "chaoba" in key.lower()]
        assert offenders == []
