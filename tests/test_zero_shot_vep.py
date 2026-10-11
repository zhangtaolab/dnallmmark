# =====================================================================
# test_zero_shot_vep.py — stub-scorer CPU suite for the VEP driver
# (SC-6/REV-08, 06-03)
#
# Every test runs through the driver's REAL enumeration / sanity /
# emission logic with the suite kernels swapped out at the injectable
# scorer seam (tests -> script/zero_shot_vep.py via the stub): no
# torch, no dnallm, no GPU anywhere in this module — importing
# ``zero_shot_vep`` at the top IS the executed CPU-importability
# proof, and the source-contract test pins the module top-level
# statically (the CI/torch boundary, Pitfall 2).
#
# The stub double parses THIS REPO's committed, hand-authored fixture
# VCF (trusted test data — the driver's untrusted-data discipline
# governs the product path, where the suite's scikit-allel reader does
# all cohort parsing) and fabricates suite-shaped ``VepResult.to_dict``
# payloads with deterministic deltas: deleterious-labeled variants at
# ``-2.0``, benign-labeled at ``-0.2``, and the RC control pass
# NEGATING then shifting the deltas (an additive shift alone cannot
# flip the ordering — negation makes the RC AUROC disagree with the
# forward one, so the reported asymmetry is real arithmetic, not a
# constant), and one length-changing ALT skipped. The fixture cohort
# is authored so the CLNSIG labels cohere with the codon-translation
# consequence classes (nonsense = Pathogenic/Likely_pathogenic,
# synonymous = Benign), which is what makes the stub's label-keyed
# deltas exercise the driver's class-keyed sanity medians in both
# polarities.
# =====================================================================

import ast
import json
from pathlib import Path

import pytest
import zero_shot_vep as zsv  # conftest puts script/ on sys.path
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO_ROOT / "script" / "zero_shot_vep.py"
SCHEMA_PATH = REPO_ROOT / "schemas" / "vep_zero_shot.json"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "vep_zero_shot"
COHORT_VCF = FIXTURE_DIR / "cohort.vcf"
REFERENCE_JSON = FIXTURE_DIR / "reference.json"
EXPECTED_ROWS = FIXTURE_DIR / "expected_stub_rows.json"
COMMITTED_ARTIFACT = REPO_ROOT / "dnallm-mark" / "data" / "vep_zero_shot.json"
REAL_REGISTRY = REPO_ROOT / "pipeline" / "models_info.json"

# The synthetic chromosome: 14 codons, frame 0 from offset 0 —
# ATG GAA CAG TGG GGC CCT GTG TCA AAA TTT ATG GGG CCC TTT
# (hand-designed so every scored variant's consequence class is
# derivable by codon translation; see the classification table below).
REFERENCE_SEQUENCE = "ATGGAACAGTGGGGCCCTGTGTCAAAATTTATGGGGCCCTTT"

# The synthetic registry slice: MLM/CLM/DL/EMPTY coverage plus the
# 6-mer spelling that must normalize to "6mer" at read time.
REGISTRY_SLICE = {
    "stub-bert-6mer": {
        "type": "MLM", "Tokenizer": "6mer",
        "Model_path": "models/stub-bert-6mer",
        "huggingface": "", "modelscope": "",
    },
    "stub-dl-cnn": {
        "type": "DL", "Tokenizer": "one-hot",
        "Model_path": "models/stub-dl-cnn",
        "huggingface": "", "modelscope": "",
    },
    "stub-empty-row": {
        "type": "", "Tokenizer": "singlebase",
        "Model_path": "models/stub-empty-row",
        "huggingface": "", "modelscope": "",
    },
    "stub-gpt-bpe": {
        "type": "CLM", "Tokenizer": "BPE",
        "Model_path": "models/stub-gpt-bpe",
        "huggingface": "", "modelscope": "",
    },
    "stub-gpt-spelled": {
        "type": "CLM", "Tokenizer": "6-mer",
        "Model_path": "models/stub-gpt-spelled",
        "huggingface": "", "modelscope": "",
    },
}

# The hand-derived consequence classification of every fixture SNV
# (pos, ref, alt) -> expected class under frame-0 codon translation.
EXPECTED_CLASSES = {
    (4, "G", "T"): "nonsense",    # GAA -> TAA (Glu -> stop)
    (7, "C", "T"): "nonsense",    # CAG -> TAG (Gln -> stop)
    (11, "G", "A"): "nonsense",   # TGG -> TAG (Trp -> stop)
    (23, "C", "A"): "nonsense",   # TCA -> TAA (Ser -> stop)
    (15, "C", "T"): "synonymous",  # GGC -> GGT (Gly)
    (18, "T", "C"): "synonymous",  # CCT -> CCC (Pro)
    (21, "G", "A"): "synonymous",  # GTG -> GTA (Val)
    (36, "G", "T"): "synonymous",  # GGG -> GGT (Gly)
    (25, "A", "T"): "nonsense",   # AAA -> TAA (Lys -> stop)
    (25, "A", "G"): None,         # AAA -> GAA (Lys -> Glu: missense)
    (25, "A", "C"): None,         # AAA -> CAA (Lys -> Gln: missense)
    (25, "A", "AT"): None,        # non-SNV alt: unclassifiable
    (28, "T", "C"): None,         # TTT -> CTT (Phe -> Leu: missense)
}


# ===== The stub scorer seam double =====


def _parse_cohort_rows(vcf_path):
    """Parse THIS REPO's trusted fixture VCF into row dicts (test-only).

    The product path never parses a VCF itself — that is the suite's
    scikit-allel reader. This helper exists only so the stub double
    can fabricate suite-shaped payloads over the committed fixture.
    """
    rows = []
    for line in Path(vcf_path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith(("##", "#CHROM")):
            continue
        fields = line.split("\t")
        info = {}
        for part in fields[7].split(";"):
            key, _, value = part.partition("=")
            info[key] = value
        rows.append(
            {
                "chrom": fields[0],
                "pos": int(fields[1]),
                "ref": fields[3],
                "alts": fields[4].split(","),
                "info": info,
            }
        )
    return rows


class StubScorer:
    """Deterministic double for the lazy suite scorer.

    Mirrors the suite's convention-filter ORDER (CLNVC -> CLNSIG ->
    CLNREVSTAT star floor) and accounting vocabulary so the driver's
    surfaced fields are exercised on suite-shaped data; deltas key on
    the CLNSIG class (deleterious ``-2.0`` / mild ``-0.2``), the RC
    control pass negates and shifts them, and ALTs whose length
    differs from REF are skipped as length-changing. Metrics use a
    pairwise (Mann-Whitney) AUROC with AUPRC as a documented
    placeholder — the product path's AUROC/AUPRC come from the suite
    metric registry, never from this double.
    """

    POSITIVE = frozenset({"Pathogenic", "Likely_pathogenic"})
    NEGATIVE = frozenset({"Benign", "Likely_benign"})
    STAR_TOKENS = frozenset(
        {"criteria_provided", "reviewed_by_expert_panel", "practice_guideline"}
    )
    SKIP_REASONS = (
        "length-changing allele",
        "multi-slot token difference",
        "no change",
    )

    def __init__(self, deleterious=-2.0, mild=-0.2, rc_shift=0.05):
        self.deleterious = deleterious
        self.mild = mild
        self.rc_shift = rc_shift
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        skip_counts = {reason: 0 for reason in self.SKIP_REASONS}
        exclusion_counts = {
            "non_snv_clnvc": 0,
            "unlabeled_clnsig": 0,
            "below_star_floor": 0,
        }
        clnrevstat_counts = {}
        records = []
        rows_read = 0
        for row in _parse_cohort_rows(request.vcf_path):
            rows_read += 1
            if row["info"].get("CLNVC", "") != "single_nucleotide_variant":
                exclusion_counts["non_snv_clnvc"] += 1
                continue
            clnsig = row["info"].get("CLNSIG", "")
            if clnsig in self.POSITIVE:
                label, delta = 1, self.deleterious
            elif clnsig in self.NEGATIVE:
                label, delta = 0, self.mild
            else:
                exclusion_counts["unlabeled_clnsig"] += 1
                continue
            revstat = row["info"].get("CLNREVSTAT", "").split(",")[0]
            clnrevstat_counts[revstat] = clnrevstat_counts.get(revstat, 0) + 1
            if revstat not in self.STAR_TOKENS:
                exclusion_counts["below_star_floor"] += 1
                continue
            if request.is_rc_control:
                delta = -delta + self.rc_shift
            for alt in row["alts"]:
                if len(alt) != len(row["ref"]):
                    skip_counts["length-changing allele"] += 1
                    records.append(
                        {
                            "chrom": row["chrom"],
                            "pos": row["pos"],
                            "ref": row["ref"],
                            "alt": alt,
                            "label": label,
                            "delta": None,
                            "skip_reason": "length-changing allele",
                        }
                    )
                    continue
                records.append(
                    {
                        "chrom": row["chrom"],
                        "pos": row["pos"],
                        "ref": row["ref"],
                        "alt": alt,
                        "label": label,
                        "delta": delta,
                        "skip_reason": None,
                    }
                )
        evaluated = sum(1 for r in records if r["delta"] is not None)
        considered = len(records)
        return {
            "records": records,
            "skip_counts": skip_counts,
            "evaluated": evaluated,
            "skipped": considered - evaluated,
            "skip_fraction": 1.0 if considered == 0 else (considered - evaluated) / considered,
            "metrics": self._metrics(records),
            "convention": {
                "cohort": (
                    "ClinVar-style labels (CLNSIG/CLNREVSTAT/CLNVC) "
                    "[stub double]"
                ),
                "variant_type": "single_nucleotide_variant",
                "labels": (
                    f"{sorted(self.POSITIVE)}=1 vs "
                    f"{sorted(self.NEGATIVE)}=0"
                ),
                "star_floor": 1,
                "score_direction": (
                    "delta = logP(alt) - logP(ref); AUROC/AUPRC computed "
                    "over the deleteriousness score -delta (higher = more "
                    "pathogenic) [stub double]"
                ),
                "excluded": (
                    "non-SNV CLNVC, CLNSIG outside the label whitelist "
                    "(VUS/conflicting/novel), CLNREVSTAT below the star "
                    "floor"
                ),
                "exclusion_counts": exclusion_counts,
                "clnrevstat_counts": dict(sorted(clnrevstat_counts.items())),
                "rows_read": rows_read,
            },
        }

    @staticmethod
    def _metrics(records):
        """Pairwise AUROC (AUPRC placeholder) over -delta; None when
        fewer than two label classes are scored."""
        scored = [
            (r["label"], -r["delta"]) for r in records if r["delta"] is not None
        ]
        if not scored or {label for label, _ in scored} != {0, 1}:
            return None
        pos = [score for label, score in scored if label == 1]
        neg = [score for label, score in scored if label == 0]
        wins = sum(
            (p > n) + 0.5 * (p == n) for p in pos for n in neg
        )
        auroc = wins / (len(pos) * len(neg))
        return {"AUROC": auroc, "AUPRC": auroc}


# ===== Helpers =====


def _write_slice(tmp_path, overlay=None):
    """Materialize the synthetic registry slice under tmp_path."""
    registry = {
        name: dict(row) for name, row in REGISTRY_SLICE.items()
    }
    for name, patch in (overlay or {}).items():
        registry.setdefault(name, {}).update(patch)
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "models_info.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return path


def _run_slice(tmp_path, scorer=None, overlay=None, models=None):
    """Run the driver over the slice + committed fixtures with a stub."""
    out = tmp_path / "out"
    rows = zsv.run_zero_shot_vep(
        _write_slice(tmp_path, overlay=overlay),
        COHORT_VCF,
        REFERENCE_JSON,
        out,
        models_filter=models,
        scorer=scorer or StubScorer(),
    )
    return rows, out


def _row(rows, model):
    return next(row for row in rows if row["model"] == model)


# ===== Import boundary (source contract + executed proof) =====


def test_source_contract_no_module_level_gpu_imports():
    """The driver's MODULE top-level carries no dnallm/torch/peft/allel
    import (the CI/torch boundary) — and the lazy suite import exists
    INSIDE a function (the seam this whole module drives)."""
    forbidden = {"dnallm", "torch", "peft", "allel"}
    tree = ast.parse(DRIVER_PATH.read_text(encoding="utf-8"))
    module_level = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    for node in module_level:
        names = (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
        )
        for name in names:
            assert name.split(".")[0] not in forbidden, (
                f"module-level import of {name!r} breaks the CPU/CI "
                "environment (Pitfall 2)"
            )
    all_froms = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert any(module.startswith("dnallm.inference.vep") for module in all_froms), (
        "the lazy suite-kernel import (from dnallm.inference.vep import "
        "...) must exist inside the GPU run path"
    )


# ===== Codon-translation sanity primitives =====


def test_genetic_code_spot_checks():
    """The standard-code table: start, stops, and 4-fold families."""
    assert zsv._translate_codon("ATG") == "M"
    for stop in ("TAA", "TAG", "TGA"):
        assert zsv._translate_codon(stop) == "*"
    for third in "ACGT":
        assert zsv._translate_codon("GG" + third) == "G"  # Gly 4-fold
        assert zsv._translate_codon("CC" + third) == "P"  # Pro 4-fold
    assert zsv._translate_codon("TTT") == "F"
    assert zsv._translate_codon("GAN") is None  # N block: unclassified


def test_revcomp():
    assert zsv._revcomp("ATGCNN") == "NNGCAT"
    assert zsv._revcomp(zsv._revcomp("ATTGCCA")) == "ATTGCCA"


def test_fixture_variant_classifications():
    """Every fixture variant classifies exactly as hand-derived."""
    for (pos, ref, alt), expected in EXPECTED_CLASSES.items():
        got = zsv._classify_consequence(
            REFERENCE_SEQUENCE, pos - 1, ref, alt
        )
        assert got == expected, (
            f"({pos}, {ref}, {alt}): classified {got!r}, "
            f"expected {expected!r}"
        )


def test_fixture_label_class_coherence():
    """The stub's label-keyed deltas are sound sanity evidence because
    the fixture coheres: every nonsense variant is labeled P/LP and
    every synonymous variant Benign (missense rows may carry either)."""
    nonsense = {
        key for key, cls in EXPECTED_CLASSES.items() if cls == "nonsense"
    }
    synonymous = {
        key for key, cls in EXPECTED_CLASSES.items() if cls == "synonymous"
    }
    pos_labeled_positive = set()
    pos_labeled_negative = set()
    for row in _parse_cohort_rows(COHORT_VCF):
        clnsig = row["info"].get("CLNSIG", "")
        bucket = (
            pos_labeled_positive
            if clnsig in StubScorer.POSITIVE
            else pos_labeled_negative
            if clnsig in StubScorer.NEGATIVE
            else None
        )
        if bucket is None:
            continue
        for alt in row["alts"]:
            bucket.add((row["pos"], row["ref"], alt))
    assert nonsense <= pos_labeled_positive
    assert synonymous <= pos_labeled_negative


# ===== Enumeration + exclusion discipline =====


def test_full_registry_enumeration_counts():
    """The REAL registry: exactly 62 rows, one per entry — 50 evaluated
    (32 mlm / 18 clm), 12 excluded-with-reason (5 DL + 7 EMPTY)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        rows = zsv.run_zero_shot_vep(
            REAL_REGISTRY,
            COHORT_VCF,
            REFERENCE_JSON,
            Path(tmp),
            scorer=StubScorer(),
        )
    assert len(rows) == 62
    assert len({row["model"] for row in rows}) == 62
    evaluated = [row for row in rows if row["excluded_reason"] is None]
    assert len(evaluated) == 50
    assert sum(1 for row in evaluated if row["paradigm"] == "mlm") == 32
    assert sum(1 for row in evaluated if row["paradigm"] == "clm") == 18
    excluded = [row for row in rows if row["excluded_reason"] is not None]
    assert sum(
        1 for row in excluded if row["excluded_reason"] == zsv.DL_EXCLUDED_REASON
    ) == 5
    assert sum(
        1
        for row in excluded
        if row["excluded_reason"] == zsv.EMPTY_EXCLUDED_REASON
    ) == 7


def test_synthetic_slice_rows_and_exclusion_reasons(tmp_path):
    """The slice: 5 rows — 3 evaluated, 1 DL exclusion, 1 EMPTY
    exclusion — and the 6-mer spelling normalizes to 6mer."""
    rows, _ = _run_slice(tmp_path)
    assert [row["model"] for row in rows] == sorted(REGISTRY_SLICE)
    dl = _row(rows, "stub-dl-cnn")
    assert dl["excluded_reason"] == zsv.DL_EXCLUDED_REASON
    assert dl["paradigm"] is None and dl["evaluated"] is None
    empty = _row(rows, "stub-empty-row")
    assert empty["excluded_reason"] == zsv.EMPTY_EXCLUDED_REASON
    spelled = _row(rows, "stub-gpt-spelled")
    assert spelled["tokenizer_type"] == "6mer"
    assert spelled["paradigm"] == "clm"
    assert _row(rows, "stub-bert-6mer")["tokenizer_type"] == "6mer"


def test_missing_type_column_yields_empty_exclusion(tmp_path):
    """A registry row with NO type key at all takes the EMPTY-exclusion
    path (the same missing-type disclosure, not a crash)."""
    rows, _ = _run_slice(
        tmp_path,
        overlay={"stub-notype": {"Tokenizer": "BPE", "Model_path": "x"}},
    )
    row = _row(rows, "stub-notype")
    assert row["excluded_reason"] == zsv.EMPTY_EXCLUDED_REASON


def test_models_filter_discloses_not_selected(tmp_path):
    """--models keeps all 62 registry rows: selected models evaluate;
    non-selected MLM/CLM rows carry the not-selected reason; DL/EMPTY
    rows keep their own (stronger) reasons."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        rows = zsv.run_zero_shot_vep(
            REAL_REGISTRY,
            COHORT_VCF,
            REFERENCE_JSON,
            Path(tmp),
            models_filter={"plant-dnabert-6mer", "plant-dnagpt-BPE"},
            scorer=StubScorer(),
        )
    assert len(rows) == 62
    by = {row["model"]: row for row in rows}
    assert by["plant-dnabert-6mer"]["excluded_reason"] is None
    assert by["plant-dnagpt-BPE"]["excluded_reason"] is None
    mlm_other = next(
        row
        for row in rows
        if row["paradigm"] == "mlm"
        and row["model"] not in {"plant-dnabert-6mer", "plant-dnagpt-BPE"}
    )
    assert mlm_other["excluded_reason"] == zsv.NOT_SELECTED_REASON
    dl = next(
        row for row in rows
        if row["excluded_reason"] == zsv.DL_EXCLUDED_REASON
    )
    assert dl["excluded_reason"] == zsv.DL_EXCLUDED_REASON


# ===== Evaluated-row fields, sanity, RC, skip accounting =====


def test_evaluated_row_carries_suite_accounting(tmp_path):
    """Stub-shaped suite accounting surfaces verbatim: 12 evaluated,
    1 skipped (the length-changing ALT), skip_fraction 1/13, both
    metrics, and the 9-key convention block."""
    rows, _ = _run_slice(tmp_path)
    row = _row(rows, "stub-bert-6mer")
    assert row["evaluated"] == 12
    assert row["skipped"] == 1
    assert row["skip_fraction"] == pytest.approx(1 / 13)
    assert row["auroc"] == pytest.approx(1.0)
    assert row["auprc"] == pytest.approx(1.0)
    assert set(row["convention"]) == {
        "cohort", "variant_type", "labels", "star_floor",
        "score_direction", "excluded", "exclusion_counts",
        "clnrevstat_counts", "rows_read",
    }
    assert row["convention"]["rows_read"] == 13
    assert row["convention"]["exclusion_counts"] == {
        "non_snv_clnvc": 1, "unlabeled_clnsig": 1, "below_star_floor": 1,
    }


def test_sanity_flag_true_and_flips_with_stub_ordering(tmp_path):
    """The synonym-vs-nonsense check is REAL logic: with nonsense more
    deleterious the pass flag is true with exact medians; flipping the
    stub's delta ordering flips the flag to false."""
    rows, _ = _run_slice(tmp_path)
    sanity = _row(rows, "stub-bert-6mer")["sanity"]
    assert sanity["synonymous_median"] == pytest.approx(-0.2)
    assert sanity["nonsense_median"] == pytest.approx(-2.0)
    assert sanity["pass"] is True

    flip_dir = tmp_path / "flip"
    flip_dir.mkdir()
    flipped_rows, _ = _run_slice(
        flip_dir, scorer=StubScorer(deleterious=-0.2, mild=-2.0)
    )
    flipped = _row(flipped_rows, "stub-bert-6mer")["sanity"]
    assert flipped["synonymous_median"] == pytest.approx(-2.0)
    assert flipped["nonsense_median"] == pytest.approx(-0.2)
    assert flipped["pass"] is False


def test_rc_control_clm_only_with_asymmetry(tmp_path):
    """rc_control is a populated dict on CLM rows (forward 1.0, RC 0.0
    under the +2.1 stub shift — a REAL asymmetry computation) and null
    on MLM rows; the RC sidecar VCF lands in the output dir under the
    PER-MODEL name {model}.rc.vcf (LOW-03: a fixed name made every CLM
    model's RC pass in a batch overwrite the same file — the surviving
    sidecar is now auditable against its row)."""
    rows, out = _run_slice(tmp_path)
    clm = _row(rows, "stub-gpt-bpe")["rc_control"]
    assert clm == {
        "auroc_forward": pytest.approx(1.0),
        "auroc_rc": pytest.approx(0.0),
        "asymmetry": pytest.approx(1.0),
    }
    assert (out / "stub-gpt-bpe.rc.vcf").is_file(), (
        "the RC sidecar must be named {model}.rc.vcf — one per model, "
        "never a shared fixed name a batch overwrites (LOW-03)"
    )
    assert not (out / "cohort.rc.vcf").exists(), (
        "the pre-LOW-03 fixed sidecar name must be gone"
    )
    assert _row(rows, "stub-bert-6mer")["rc_control"] is None


def test_scorer_failure_is_a_loud_row_level_exclusion(tmp_path):
    """A scorer exception (model load failure, the paradigm guard)
    becomes that model's disclosed evaluation-failed row — the sibling
    models still evaluate (row-level isolation, never a silent drop)."""

    class ExplodingScorer(StubScorer):
        def __call__(self, request):
            if request.model_row.get("Tokenizer") == "BPE":
                raise ValueError("paradigm guard: boom")
            return super().__call__(request)

    rows, _ = _run_slice(tmp_path, scorer=ExplodingScorer())
    failed = _row(rows, "stub-gpt-bpe")
    assert failed["excluded_reason"].startswith("evaluation failed:")
    assert failed["evaluated"] is None and failed["auroc"] is None
    assert _row(rows, "stub-bert-6mer")["excluded_reason"] is None


# ===== Determinism + schema + chain-produced fixture =====


def test_two_runs_emit_byte_identical_artifacts(tmp_path):
    """Determinism: two full driver runs over the same inputs produce
    byte-identical JSON and CSV."""
    _, out1 = _run_slice(tmp_path / "a")
    _, out2 = _run_slice(tmp_path / "b")
    assert (out1 / "vep_zero_shot.json").read_bytes() == (
        out2 / "vep_zero_shot.json"
    ).read_bytes()
    assert (out1 / "vep_zero_shot.csv").read_bytes() == (
        out2 / "vep_zero_shot.csv"
    ).read_bytes()


def test_emission_validates_schema(tmp_path):
    """The slice emission AND the full 62-row registry emission both
    validate against the strict schema."""
    validator = Draft202012Validator(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    )
    _, out = _run_slice(tmp_path)
    doc = json.loads((out / "vep_zero_shot.json").read_text(encoding="utf-8"))
    assert not list(validator.iter_errors(doc))
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        zsv.run_zero_shot_vep(
            REAL_REGISTRY,
            COHORT_VCF,
            REFERENCE_JSON,
            Path(tmp),
            scorer=StubScorer(),
        )
        full = json.loads(
            (Path(tmp) / "vep_zero_shot.json").read_text(encoding="utf-8")
        )
    assert not list(validator.iter_errors(full))


def test_committed_fixture_validates_schema():
    """The committed expected_stub_rows.json validates against the
    schema (the CI-side shape pin until real data lands)."""
    validator = Draft202012Validator(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    )
    doc = json.loads(EXPECTED_ROWS.read_text(encoding="utf-8"))
    assert not list(validator.iter_errors(doc))


def test_committed_fixture_is_chain_product(tmp_path):
    """The committed expectation fixture equals the driver's own
    emission over the slice + fixtures, byte for byte (chain-produced,
    never hand-edited)."""
    _, out = _run_slice(tmp_path)
    assert (out / "vep_zero_shot.json").read_bytes() == (
        EXPECTED_ROWS.read_bytes()
    )


def test_reference_fixture_is_a_plain_chromosome_mapping():
    """reference.json is the plain mapping form the suite's
    evaluate_vcf consumes directly (the no-FASTA fixture door)."""
    data = json.loads(REFERENCE_JSON.read_text(encoding="utf-8"))
    assert data == {"chrV": REFERENCE_SEQUENCE}


# ===== Publication gate =====


def test_no_committed_data_artifact():
    """Resolved OQ 1: no vep_zero_shot.json exists under
    dnallm-mark/data/ (the artifact + DATA.md links wait for real
    post-E2' runs; nothing registered a SCHEMA_FILES bucket either)."""
    assert not COMMITTED_ARTIFACT.exists()
    schemas_doc = (REPO_ROOT / "tests" / "test_schemas.py").read_text(
        encoding="utf-8"
    )
    assert "vep_zero_shot" not in schemas_doc
