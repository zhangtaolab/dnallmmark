"""Zero-shot variant-effect-prediction registry batch driver (SC-6/REV-08).

Purpose
-------
Enumerate every entry of ``pipeline/models_info.json`` exactly once and
score the ClinVar-shaped cohort through the DNALLM suite's tested VEP
kernels, emitting the dual ``vep_zero_shot.json`` + ``vep_zero_shot.csv``
artifacts (the n_audit convention). One row per registry model — 62 rows
ALWAYS: the 32 MLM and 18 CLM models are scored under their registry
paradigm, the 5 DL-architecture models and 7 empty-type rows are emitted
as excluded-with-reason rows, never dropped (skip-as-data discipline).

Each evaluated row carries the suite's own accounting verbatim
(``evaluated`` / ``skipped`` / ``skip_fraction`` / ``AUROC`` / ``AUPRC``
/ the convention block), plus two driver-owned sanity channels:

- ``sanity`` — the synonym-vs-nonsense expectation: median paradigm
  delta over the cohort's synonymous vs nonsense variants, ``pass``
  true iff the nonsense median is SMALLER (more deleterious under the
  alt-minus-ref convention). Classes are derived by frame-0 codon
  translation of the +strand ORF at contig offset 0 — a SYNTHETIC-
  COHORT convention (disclosed in ``schemas/vep_zero_shot.json``);
  real-cohort consequence classes require transcript annotation and
  stay post-E2' work.
- ``rc_control`` — the reverse-complement control, reported for CLM
  (causal) models ONLY: the cohort re-scored over the reverse-
  complemented reference (forward AUROC, RC AUROC, and their absolute
  asymmetry), the strand-asmetry disclosure the PlantCAD2/evo
  literature documents. Null on MLM rows (masked models have no
  causal strand direction).

Direction of truth
------------------
``pipeline/models_info.json`` is the model authority (the ``type``
column drives the paradigm; DL/EMPTY rows become exclusion rows), and
``dnallm.inference.vep`` at suite tag v1.2.1 is the SCORING authority —
this module NEVER reimplements the scoring math, the same-slot
alignment rule, the paradigm-architecture guard, VCF parsing, or the
AUROC/AUPRC conventions (the kernels carry a 1,515-line suite test
file). The suite is imported LAZILY, inside the default scorer only:
``dnallm`` transitively pulls torch, so a module-level import would
break the CPU/CI environment (tests/test_zero_shot_vep.py pins this
boundary with a source-contract AST check and by importing this module
itself). CPU tests drive the same enumeration/emission logic through
an injectable stub scorer.

Conventions are suite-owned and only DISCLOSED here: deltas are
alt-minus-ref (deleterious NEGATIVE), AUROC/AUPRC run over the
deleteriousness score ``-delta``, and the cohort rules are the D-17
ClinVar convention (SNVs only; strict Pathogenic/Likely_pathogenic vs
Benign/Likely_benign whitelist; >=1 review star; VUS/conflicting
excluded). The registry's ``6mer``/``6-mer`` Tokenizer spelling
inconsistency (6 + 1 rows) is normalized at read time and disclosed —
the registry file itself is never rewritten.

Determinism: sorted model iteration, ``sort_keys=True`` serialization,
a fixed CSV column order, and no live clock — the same inputs emit
byte-identical artifacts. GPU-side forward passes are not asserted
bit-deterministic; byte-determinism is pinned on the stub seam.

Publication gate (resolved OQ 1): the committed
``dnallm-mark/data/vep_zero_shot.json`` artifact and any DATA.md site
link stay gated on real post-E2' runs. Until then the default output
dir is a scratch location and the CI-side shape pin is the generator-
produced fixture at ``tests/fixtures/vep_zero_shot/`` — nothing
registers in tests/test_schemas.py SCHEMA_FILES until the first real
data file lands.

Usage
-----
From the repo root (REPO_ROOT-relative paths; the GPU run needs the
``--group gpu`` environment with dnallm 1.2.1 installed)::

    uv run --group gpu python script/zero_shot_vep.py \\
        --vcf tests/fixtures/vep_zero_shot/cohort.vcf \\
        --reference tests/fixtures/vep_zero_shot/reference.json \\
        --models plant-dnabert-6mer,plant-dnagpt-BPE \\
        --output-dir /tmp/vep-smoke

``--reference`` accepts a JSON chromosome mapping (``{"chr": "ACGT..."}``
— the synthetic-fixture door; the suite's ``evaluate_vcf`` takes the
plain mapping directly) or a FASTA path (parsed by the suite; the
codon-translation sanity channel and the RC control are then
unavailable and reported as null fields, never fabricated).

See also:
    ``dnallm/inference/vep.py`` (suite v1.2.1, read-only) — the scoring
    kernels this driver orchestrates: ``align_variant`` /
    ``clm_log_likelihood`` / ``mlm_slot_log_prob`` / ``score_variant`` /
    ``evaluate_vcf`` / ``VepResult.to_dict``.
    ``script/build_frontier.py`` — the sibling lane's dual-artifact
    emission conventions mirrored here.
    ``tests/test_zero_shot_vep.py`` — the stub-scorer CPU suite and the
    import-boundary source contract.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ===== Configuration =====

#: Registry ``type`` column -> scoring paradigm (suite vep.py accepts
#: exactly "clm"/"mlm"; everything else becomes an exclusion row).
PARADIGM_BY_TYPE: dict[str, str] = {"MLM": "mlm", "CLM": "clm"}

#: Exclusion reasons (skip-as-data: disclosed rows, never drops).
DL_EXCLUDED_REASON = (
    "unsupported architecture class: DL (deep-learning models with "
    "dedicated loaders; outside the zero-shot VEP lane scope)"
)
EMPTY_EXCLUDED_REASON = (
    "missing registry type: models_info 'type' column is empty"
)
NOT_SELECTED_REASON = "not selected (--models filter)"

#: Data-hygiene normalization of the registry Tokenizer column: the
#: 6 ``6mer`` rows and 1 ``6-mer`` row name the same tokenizer kind.
#: Normalized at READ time only — the registry file is never rewritten
#: (flagged for the maintainer in the 06-03 summary).
TOKENIZER_SPELLING_NORMALIZATION: dict[str, str] = {"6-mer": "6mer"}

#: Context-window policy bucketed on the NORMALIZED tokenizer type.
#: Every bucket sits at the suite default (``VepConfig.context_window``
#: = 200) today; this table is the single documented place a per-
#: tokenizer window tightens post-E2' if k-mer token lengths demand it.
SUITE_DEFAULT_CONTEXT_WINDOW = 200
TOKENIZER_CONTEXT_POLICY: dict[str, int] = {
    "singlebase": SUITE_DEFAULT_CONTEXT_WINDOW,
    "BPE": SUITE_DEFAULT_CONTEXT_WINDOW,
    "6mer": SUITE_DEFAULT_CONTEXT_WINDOW,
    "one-hot": SUITE_DEFAULT_CONTEXT_WINDOW,
}

#: Reference input forms: a JSON chromosome mapping (parsed here, the
#: synthetic-fixture door) or a FASTA path (parsed by the suite).
FASTA_SUFFIXES = (".fasta", ".fa", ".fna", ".fst", ".gz")

#: Fixed CSV column order (the dual-artifact convention).
CSV_COLUMNS = (
    "model",
    "paradigm",
    "tokenizer_type",
    "evaluated",
    "skipped",
    "skip_fraction",
    "auroc",
    "auprc",
    "convention",
    "rc_control",
    "sanity",
    "excluded_reason",
)

#: Reverse complement (IUPAC core + N; case-preserving per input char).
_COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")

# The standard genetic code (NCBI table 1), keyed by the 64 base
# triples in T/C/A/G nested order (row strings indexed to match).
_BASES = "TCAG"
_AMINO_ACIDS = (
    "FFLLSSSSYY**CC*W"
    "LLLLPPPPHHQQRRRR"
    "IIIMTTTTNNKKSSRR"
    "VVVVAAAADDEEGGGG"
)
_GENETIC_CODE: dict[str, str] = {
    b1 + b2 + b3: _AMINO_ACIDS[i]
    for i, (b1, b2, b3) in enumerate(
        (x, y, z) for x in _BASES for y in _BASES for z in _BASES
    )
}
_STOP = "*"


# =====================================================================
# The scorer seam (the CI/torch boundary)
# =====================================================================


@dataclass(frozen=True)
class ScoringRequest:
    """One per-model scoring request handed to the scorer seam.

    The default scorer resolves the model source from ``model_row``
    LAZILY (a registry row with no fetchable source — e.g. a
    ``Model_path`` directory that was never fetched and empty remote
    columns — surfaces as that model's loud row-level failure at GPU
    time, never as an enumeration-time drop) and ignores
    ``is_rc_control`` (the RC-ness of a request is fully encoded in
    its transformed VCF + reference); stub scorers use the flag to
    make their deterministic outputs differ between the forward and
    control passes so the reported asymmetry is exercised as real
    arithmetic.

    Attributes:
        model_row: The registry ``models_info`` row (``Model_path`` /
            ``huggingface`` / ``modelscope`` columns) — resolved to a
            load identity by the default scorer only.
        paradigm: "mlm" or "clm" (registry ``type`` column).
        vcf_path: Cohort VCF path (the RC control pass receives the
            transformed cohort written under the output dir).
        reference: Chromosome mapping, or a FASTA path for the suite
            to parse.
        context_window: Policy bucket value for this model.
        is_rc_control: True for the reverse-complement control pass.
    """

    model_row: Mapping[str, Any]
    paradigm: str
    vcf_path: str
    reference: Mapping[str, str] | str
    context_window: int
    is_rc_control: bool = False


#: A scorer turns one request into the suite ``VepResult.to_dict()``
#: shape (records / skip_counts / evaluated / skipped / skip_fraction /
#: metrics / convention). Injectable: CPU tests pass a stub; the GPU
#: run path uses the lazy suite default below.
Scorer = Callable[[ScoringRequest], dict[str, Any]]

#: GPU-path model cache (the RC control reuses the loaded backbone;
#: inference-only, no training state). Keyed by the load identity.
_MODEL_CACHE: dict[tuple[str, str, str], tuple[Any, Any]] = {}


def _suite_scorer(request: ScoringRequest) -> dict[str, Any]:
    """Default scorer: the REAL suite kernels, lazily imported.

    This is the ONLY place ``dnallm`` is imported in this repo's
    script/ tree, and it sits inside a function so importing
    ``zero_shot_vep`` CPU-side (torch absent) stays possible. Model
    loading follows the suite CLI's own idiom (dnallm/cli/vep.py @
    v1.2.1): paradigm -> task type ("generation" for clm, "mask" for
    mlm) -> ``TaskConfig`` -> ``load_model_and_tokenizer``, the pairing
    the suite's paradigm-architecture guard then verifies.

    Args:
        request: The per-model scoring request.

    Returns:
        ``VepResult.to_dict()`` from ``evaluate_vcf``.

    Raises:
        Exception: Whatever the suite raises (model load failure, the
            paradigm-architecture mismatch guard, VCF/reference
            contract violations) — the driver surfaces these as loud
            row-level failures, never silently re-paradigmed.
    """
    # LAZY suite imports — GPU run path only (the CI/torch boundary).
    from dnallm.configuration.configs import TaskConfig
    from dnallm.inference.vep import evaluate_vcf
    from dnallm.models import load_model_and_tokenizer

    model_name, source = _resolve_model_source(request.model_row)
    task_type = "generation" if request.paradigm == "clm" else "mask"
    cache_key = (model_name, source, task_type)
    if cache_key not in _MODEL_CACHE:
        _MODEL_CACHE[cache_key] = load_model_and_tokenizer(
            model_name=model_name,
            task_config=TaskConfig(task_type=task_type),
            source=source,
        )
    model, tokenizer = _MODEL_CACHE[cache_key]
    result = evaluate_vcf(
        model,
        tokenizer,
        request.vcf_path,
        request.reference,
        paradigm=request.paradigm,
        context_window=request.context_window,
    )
    return result.to_dict()


# =====================================================================
# Registry reading (pure, CPU-safe)
# =====================================================================


def _normalize_tokenizer(value: str) -> str:
    """Normalize a registry Tokenizer value (the 6-mer/6mer hygiene)."""
    return TOKENIZER_SPELLING_NORMALIZATION.get(value, value)


def _resolve_model_source(row: Mapping[str, Any]) -> tuple[str, str]:
    """Resolve (model_name, source) from one registry row.

    Precedence: the local ``pipeline/<Model_path>`` directory (the
    fetched-backbone convention), then the ``huggingface`` column, then
    ``modelscope``.

    Args:
        row: One ``models_info`` entry.

    Returns:
        Tuple of (model_name, source) for the suite loader.

    Raises:
        ValueError: If no source column resolves (an unfetchable
            registry row — surfaced as a loud row-level failure).
    """
    model_path = str(row.get("Model_path") or "")
    if model_path:
        local = REPO_ROOT / "pipeline" / model_path
        if local.is_dir():
            return str(local), "local"
    hf = str(row.get("huggingface") or "")
    if hf:
        return hf, "huggingface"
    ms = str(row.get("modelscope") or "")
    if ms:
        return ms, "modelscope"
    raise ValueError(
        "no model source resolves: Model_path directory absent and "
        "huggingface/modelscope columns empty"
    )


# =====================================================================
# Sanity layer: synonym-vs-nonsense by codon translation
# =====================================================================


def _revcomp(sequence: str) -> str:
    """Reverse-complement a nucleotide string (unknown chars pass)."""
    return sequence.translate(_COMPLEMENT)[::-1]


def _translate_codon(codon: str) -> str | None:
    """Translate one uppercase codon; ``None`` outside the genetic code.

    Args:
        codon: Exactly three uppercase characters.

    Returns:
        The one-letter amino acid, ``"*"`` for stop codons, or ``None``
        when the codon contains characters outside ACGT (an ``N`` block
        — unclassified, never guessed).
    """
    return _GENETIC_CODE.get(codon)


def _classify_consequence(
    ref_seq: str, pos0: int, ref: str, alt: str
) -> str | None:
    """Classify one SNV as synonymous / nonsense by codon translation.

    The SYNTHETIC-COHORT convention: codon frame 0 starts at contig
    offset 0 on the + strand (disclosed in the schema ``$comment``).
    Real-cohort consequence classes need transcript annotation — post-
    E2' work; this channel exists to make the synthetic-cohort sanity
    expectation machine-checkable today.

    Args:
        ref_seq: The uppercased reference contig.
        pos0: 0-based variant position.
        ref: Reference allele (single base for classifiable SNVs).
        alt: Alternate allele (single base).

    Returns:
        "synonymous", "nonsense", or ``None`` (missense, non-SNV,
        partial codon at the contig edge, or an ``N`` in the codon).
    """
    if len(ref) != 1 or len(alt) != 1 or pos0 >= len(ref_seq):
        return None
    codon_start = (pos0 // 3) * 3
    codon_ref = ref_seq[codon_start : codon_start + 3]
    if len(codon_ref) != 3 or set(codon_ref) - set("ACGT"):
        return None
    offset = pos0 - codon_start
    codon_alt = codon_ref[:offset] + alt + codon_ref[offset + 1 :]
    aa_ref = _translate_codon(codon_ref)
    aa_alt = _translate_codon(codon_alt)
    if aa_ref is None or aa_alt is None:
        return None
    if aa_ref == aa_alt:
        return "synonymous"
    if aa_alt == _STOP and aa_ref != _STOP:
        return "nonsense"
    return None


def _resolve_contig(sequences: Mapping[str, str], chrom: str) -> str | None:
    """Resolve a VCF CHROM against the reference's naming style.

    Mirrors the suite's ``_resolve_chromosome`` resolution (exact, then
    chr-prefixed, then chr-stripped) but returns ``None`` instead of
    raising: an unresolvable contig leaves the variant unclassified,
    never aborts the run.

    Args:
        sequences: Reference chromosome -> sequence mapping.
        chrom: CHROM value from the cohort records.

    Returns:
        The matching reference key, or ``None``.
    """
    candidates = [chrom]
    if chrom.startswith("chr"):
        candidates.append(chrom[3:])
    else:
        candidates.append(f"chr{chrom}")
    for candidate in candidates:
        if candidate in sequences:
            return candidate
    return None


def _sanity_from_records(
    records: Sequence[Mapping[str, Any]],
    sequences: Mapping[str, str],
) -> dict[str, Any]:
    """Compute the synonym-vs-nonsense sanity block for one model.

    Args:
        records: Per-variant records from the scorer result (only
            scored deltas classify; skipped rows are not evidence).
        sequences: The reference chromosome mapping.

    Returns:
        ``{"synonymous_median", "nonsense_median", "pass"}`` — medians
        null when a class holds no scored variants, ``pass`` null when
        either median is missing (an expectation is only decidable on
        complete evidence, never fabricated).
    """
    by_class: dict[str, list[float]] = {"synonymous": [], "nonsense": []}
    for record in records:
        delta = record.get("delta")
        if delta is None:
            continue
        key = _resolve_contig(sequences, str(record.get("chrom", "")))
        if key is None:
            continue
        cls = _classify_consequence(
            sequences[key].upper(),
            int(record["pos"]) - 1,
            str(record["ref"]),
            str(record["alt"]),
        )
        if cls is not None:
            by_class[cls].append(float(delta))
    syn = median(by_class["synonymous"]) if by_class["synonymous"] else None
    non = median(by_class["nonsense"]) if by_class["nonsense"] else None
    passed = (
        bool(non < syn)
        if syn is not None and non is not None
        else None
    )
    return {
        "synonymous_median": syn,
        "nonsense_median": non,
        "pass": passed,
    }


# =====================================================================
# Reverse-complement control (CLM models only)
# =====================================================================


def _build_rc_cohort(
    records: Sequence[Mapping[str, Any]],
    sequences: Mapping[str, str],
    out_vcf: Path,
) -> dict[str, str]:
    """Write the reverse-complemented cohort VCF; return the RC mapping.

    Each forward record (one per ALT, convention-passing by suite
    construction) becomes one single-ALT row: coordinates transform as
    ``pos0_rc = len(seq) - pos0 - len(ref)`` with reverse-complemented
    alleles, and the label round-trips through the same CLNSIG
    whitelist vocabulary the suite parses. The sidecar lands under the
    output dir as ``{model}.rc.vcf`` — one PER MODEL (LOW-03, phase-06
    review: a fixed name made every CLM model's RC pass in a batch
    overwrite the same file), so each sidecar stays auditable against
    its row; the name never derives from VCF record fields (the suite's
    own path-safety discipline).

    Args:
        records: Forward-pass records from the scorer result.
        sequences: The forward reference chromosome mapping.
        out_vcf: Destination path for the RC cohort VCF.

    Returns:
        The reverse-complemented reference mapping.

    Raises:
        ValueError: If a record's contig does not resolve (the same
            contract the forward pass already enforced — a corrupted
            join, aborting loudly rather than mis-writing rows).
    """
    rc_sequences = {chrom: _revcomp(seq) for chrom, seq in sequences.items()}
    lines = [
        "##fileformat=VCFv4.2",
        *(
            f"##contig=<ID={chrom},length={len(seq)}>"
            for chrom, seq in sorted(rc_sequences.items())
        ),
        (
            '##INFO=<ID=CLNSIG,Number=.,Type=String,Description="ClinVar '
            'clinical significance (label round-trip from the forward '
            'pass)">'
        ),
        (
            '##INFO=<ID=CLNREVSTAT,Number=.,Type=String,Description='
            '"ClinVar review status (>=1 review star)">'
        ),
        (
            '##INFO=<ID=CLNVC,Number=1,Type=String,Description="ClinVar '
            'variant type">'
        ),
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
    ]
    for record in records:
        chrom = str(record["chrom"])
        key = _resolve_contig(sequences, chrom)
        if key is None:
            raise ValueError(
                f"RC transform: contig '{chrom}' not in the reference "
                f"(available: {sorted(sequences)})"
            )
        seq = sequences[key]
        pos0 = int(record["pos"]) - 1
        ref = str(record["ref"])
        alt = str(record["alt"])
        pos0_rc = len(seq) - pos0 - len(ref)
        label = record.get("label")
        clnsig = "Pathogenic" if label == 1 else "Benign"
        lines.append(
            "\t".join(
                (
                    chrom,
                    str(pos0_rc + 1),
                    f"rc{pos0}",
                    _revcomp(ref),
                    _revcomp(alt),
                    ".",
                    ".",
                    "CLNSIG="
                    + clnsig
                    + ";CLNREVSTAT=criteria_provided"
                    + ";CLNVC=single_nucleotide_variant",
                )
            )
        )
    out_vcf.parent.mkdir(parents=True, exist_ok=True)
    out_vcf.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rc_sequences


def _rc_control(
    forward: Mapping[str, Any],
    base_request: ScoringRequest,
    sequences: Mapping[str, str],
    output_dir: Path,
    scorer: Scorer,
    model: str,
) -> dict[str, Any]:
    """Run the reverse-complement control pass and report asymmetry.

    Args:
        forward: The forward scorer result (records + metrics).
        base_request: The forward request (the model row is reused).
        sequences: The forward reference mapping.
        output_dir: Destination directory for the RC cohort VCF sidecar.
        scorer: The scorer seam.
        model: The registry model name — the sidecar is
            ``{model}.rc.vcf``, one per model, so a multi-model batch
            never overwrites a previous model's RC cohort (LOW-03).

    Returns:
        ``{"auroc_forward", "auroc_rc", "asymmetry"}`` — inner nulls
        when the corresponding metrics are unavailable (no scorable
        variants / one label class); asymmetry is the absolute AUROC
        difference, null when either side is missing.
    """
    out_vcf = output_dir / f"{model}.rc.vcf"
    rc_sequences = _build_rc_cohort(
        forward.get("records", []), sequences, out_vcf
    )
    rc_request = ScoringRequest(
        model_row=base_request.model_row,
        paradigm=base_request.paradigm,
        vcf_path=str(out_vcf),
        reference=rc_sequences,
        context_window=base_request.context_window,
        is_rc_control=True,
    )
    rc_result = scorer(rc_request)
    fwd_metrics = forward.get("metrics") or {}
    rc_metrics = rc_result.get("metrics") or {}
    fwd_auroc = fwd_metrics.get("AUROC")
    rc_auroc = rc_metrics.get("AUROC")
    asymmetry = (
        abs(float(fwd_auroc) - float(rc_auroc))
        if fwd_auroc is not None and rc_auroc is not None
        else None
    )
    return {
        "auroc_forward": fwd_auroc,
        "auroc_rc": rc_auroc,
        "asymmetry": asymmetry,
    }


# =====================================================================
# Enumeration + emission
# =====================================================================


def _load_reference(
    reference: Mapping[str, str] | str | Path,
) -> tuple[Mapping[str, str] | str, Mapping[str, str] | None]:
    """Normalize the --reference input.

    Args:
        reference: A chromosome mapping (used directly), a JSON file
            path holding one, or a FASTA path (handed to the suite).

    Returns:
        Tuple of (reference for the scorer, the chromosome mapping
        when available for the driver-owned sanity/RC channels —
        ``None`` for the FASTA form, which the suite parses itself).

    Raises:
        ValueError: If a ``.json`` reference cannot be parsed or is
            not a string-keyed string mapping.
    """
    if isinstance(reference, Mapping):
        return reference, reference
    path = Path(reference)
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in data.items()
        ):
            raise ValueError(
                f"Reference JSON '{path}' must map chromosome names to "
                "sequence strings."
            )
        return data, data
    return str(path), None


def build_rows(
    registry: Mapping[str, Mapping[str, Any]],
    vcf_path: Path,
    reference: Mapping[str, str] | str | Path,
    output_dir: Path,
    models_filter: set[str] | None = None,
    scorer: Scorer = _suite_scorer,
) -> list[dict[str, Any]]:
    """Enumerate the registry and score every non-excluded model.

    Args:
        registry: The ``models_info`` mapping (key -> row).
        vcf_path: The cohort VCF.
        reference: Chromosome mapping, JSON path, or FASTA path.
        output_dir: Destination for the RC sidecar (and, from
            ``emit``, the dual artifacts).
        models_filter: Optional set of model names to evaluate
            (non-selected rows are emitted as not-selected exclusions
            — the output still carries one row per registry entry).
        scorer: The scorer seam (stub in CPU tests; the lazy suite
            default on the GPU path).

    Returns:
        The deterministic row list (sorted by model name).
    """
    sequences, mapping = _load_reference(reference)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for model in sorted(registry):
        row_in = registry[model]
        row: dict[str, Any] = {column: None for column in CSV_COLUMNS}
        row["model"] = model
        tokenizer_type = _normalize_tokenizer(str(row_in.get("Tokenizer", "")))
        row["tokenizer_type"] = tokenizer_type or None
        model_type = str(row_in.get("type", ""))
        if model_type not in PARADIGM_BY_TYPE:
            if model_type == "DL":
                row["excluded_reason"] = DL_EXCLUDED_REASON
            elif not model_type:
                row["excluded_reason"] = EMPTY_EXCLUDED_REASON
            else:
                row["excluded_reason"] = (
                    f"unknown registry type: {model_type!r}"
                )
            rows.append(row)
            continue
        paradigm = PARADIGM_BY_TYPE[model_type]
        row["paradigm"] = paradigm
        if models_filter is not None and model not in models_filter:
            row["excluded_reason"] = NOT_SELECTED_REASON
            rows.append(row)
            continue
        try:
            context_window = TOKENIZER_CONTEXT_POLICY.get(
                tokenizer_type, SUITE_DEFAULT_CONTEXT_WINDOW
            )
            request = ScoringRequest(
                model_row=row_in,
                paradigm=paradigm,
                vcf_path=str(vcf_path),
                reference=sequences,
                context_window=context_window,
            )
            result = scorer(request)
        except Exception as exc:  # noqa: BLE001 — row-level isolation
            # Loud row-level failure (the plan's never-silent contract):
            # the paradigm guard, a model-load failure, or a cohort
            # contract violation lands HERE as a disclosed reason, and
            # the run continues to the next model.
            print(
                f"[zero_shot_vep] ERROR scoring {model} "
                f"({paradigm}): {exc}",
                file=sys.stderr,
            )
            row["excluded_reason"] = f"evaluation failed: {exc}"
            rows.append(row)
            continue
        metrics = result.get("metrics") or {}
        row["evaluated"] = int(result["evaluated"])
        row["skipped"] = int(result["skipped"])
        row["skip_fraction"] = float(result["skip_fraction"])
        row["auroc"] = metrics.get("AUROC")
        row["auprc"] = metrics.get("AUPRC")
        row["convention"] = result.get("convention")
        if mapping is not None:
            row["sanity"] = _sanity_from_records(
                result.get("records", []), mapping
            )
            if paradigm == "clm":
                row["rc_control"] = _rc_control(
                    result, request, mapping, output_dir, scorer, model
                )
            else:
                row["rc_control"] = None
        else:
            # FASTA reference: the codon-translation sanity channel and
            # the RC control need the mapping form — null, disclosed,
            # never fabricated.
            row["sanity"] = {
                "synonymous_median": None,
                "nonsense_median": None,
                "pass": None,
            }
            row["rc_control"] = (
                {"auroc_forward": None, "auroc_rc": None, "asymmetry": None}
                if paradigm == "clm"
                else None
            )
        rows.append(row)
    return rows


def _csv_cell(value: Any) -> str:
    """One CSV cell: nulls empty, nested objects compact JSON, rest str.

    The convention/rc_control/sanity objects serialize as sorted
    compact JSON so the CSV row stays a single flat line while the
    nested disclosure remains machine-parseable.
    """
    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def emit(rows: Sequence[Mapping[str, Any]], output_dir: Path) -> None:
    """Write the deterministic dual artifacts.

    Args:
        rows: The row list from ``build_rows``.
        output_dir: Destination for ``vep_zero_shot.json`` +
            ``vep_zero_shot.csv``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "vep_zero_shot.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {"rows": [dict(row) for row in rows]},
            handle,
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        )
    csv_path = output_dir / "vep_zero_shot.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            writer.writerow(
                [_csv_cell(row[column]) for column in CSV_COLUMNS]
            )


def run_zero_shot_vep(
    registry_path: Path,
    vcf_path: Path,
    reference: Mapping[str, str] | str | Path,
    output_dir: Path,
    models_filter: set[str] | None = None,
    scorer: Scorer = _suite_scorer,
) -> list[dict[str, Any]]:
    """The driver entry: enumerate, score, emit.

    Args:
        registry_path: ``models_info.json`` path.
        vcf_path: The cohort VCF.
        reference: Chromosome mapping, JSON path, or FASTA path.
        output_dir: Destination for the dual artifacts.
        models_filter: Optional model-name subset to evaluate —
            validated against the registry keys: unknown names abort
            the run with every offender listed (a typo must not
            silently produce an all-not-selected artifact, LOW-04);
            known unselected names keep their skip-as-data rows.
        scorer: The scorer seam.

    Returns:
        The emitted rows.

    Raises:
        TypeError: If the registry does not parse to a JSON object
            (ruff TRY004: the isinstance shape check raises TypeError;
            a malformed-JSON parse error propagates from ``json.load``).
    """
    with Path(registry_path).open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    if not isinstance(registry, dict):
        raise TypeError(
            f"Registry '{registry_path}' must be a JSON object mapping "
            "model names to rows."
        )
    # --models filter validation (LOW-04, phase-06 review): an unknown
    # name previously matched no registry key, producing 62 not-selected
    # rows and exit 0 — a typo'd multi-model list was invisible in the
    # artifact. Refuse fail-fast listing every unknown name (the
    # run_sweep WR-07 filter discipline); KNOWN unselected names keep
    # their skip-as-data not-selected rows.
    if models_filter is not None:
        unknown = sorted(models_filter - set(registry))
        if unknown:
            sys.exit(
                "[Error] --models name(s) not in the registry: "
                + ", ".join(unknown)
                + " (known names are the models_info.json keys)"
            )
    rows = build_rows(
        registry,
        Path(vcf_path),
        reference,
        Path(output_dir),
        models_filter=models_filter,
        scorer=scorer,
    )
    emit(rows, Path(output_dir))
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry (REPO_ROOT-relative argparse; see the module banner)."""
    parser = argparse.ArgumentParser(
        prog="zero_shot_vep",
        description=(
            "Registry batch driver over the DNALLM suite VEP kernels: "
            "one row per models_info entry (exclusions disclosed), "
            "CLM/MLM scoring with synonym-vs-nonsense sanity and a "
            "CLM-only reverse-complement control, dual CSV+JSON "
            "emission."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "pipeline" / "models_info.json",
        help="models_info registry (default: pipeline/models_info.json)",
    )
    parser.add_argument(
        "--vcf",
        type=Path,
        required=True,
        help="ClinVar-shaped cohort VCF (parsed by the suite's "
        "scikit-allel reader)",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        required=True,
        help="JSON chromosome mapping or FASTA path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Destination for vep_zero_shot.{json,csv} (scratch until "
        "the post-E2' publication gate opens)",
    )
    parser.add_argument(
        "--models",
        default=None,
        help="Comma-separated model names to evaluate (default: every "
        "MLM/CLM registry entry); unknown names abort the run listing "
        "every offender — a typo never silently yields an "
        "all-not-selected artifact",
    )
    args = parser.parse_args(argv)
    models_filter = None
    if args.models:
        models_filter = {
            name.strip()
            for name in args.models.split(",")
            if name.strip()
        }
    rows = run_zero_shot_vep(
        args.registry,
        args.vcf,
        args.reference,
        args.output_dir,
        models_filter=models_filter,
    )
    excluded = sum(1 for row in rows if row["excluded_reason"] is not None)
    for row in rows:
        if row["excluded_reason"] is not None:
            print(
                f"[zero_shot_vep] {row['model']}: EXCLUDED — "
                f"{row['excluded_reason']}"
            )
        else:
            sanity = row["sanity"] or {}
            print(
                f"[zero_shot_vep] {row['model']}: paradigm="
                f"{row['paradigm']} evaluated={row['evaluated']} "
                f"skipped={row['skipped']} "
                f"skip_fraction={row['skip_fraction']:.4f} "
                f"auroc={_fmt(row['auroc'])} "
                f"auprc={_fmt(row['auprc'])} "
                f"sanity_pass={_fmt(sanity.get('pass'), boolean=True)}"
            )
    print(
        f"[zero_shot_vep] {len(rows)} rows ({len(rows) - excluded} "
        f"evaluated, {excluded} excluded-with-reason) -> "
        f"{args.output_dir / 'vep_zero_shot.json'}"
    )
    return 0


def _fmt(value: Any, boolean: bool = False) -> str:
    """Format a nullable row field for the per-model summary line."""
    if value is None:
        return "null"
    if boolean:
        return str(bool(value)).lower()
    return f"{float(value):.4f}"


if __name__ == "__main__":
    sys.exit(main())
