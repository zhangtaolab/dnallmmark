# =====================================================================
# test_flops_counter.py — CPU stub tests for pipeline/flops_counter.py
# (Phase 7, PIPE-01; plan 07-01 Task 2/Task 3)
#
# The FlopsCounter port keeps torch behind the lazy ``_torch_nn`` seam so
# this module is exercisable in the torch-free dev/CI lane: no GPU, no
# dnallm (PIPE-01 success criterion 2). Every hook body reads only
# duck-typed attributes (``.shape`` tuple, ``.numel()``, ``out_features``,
# ``kernel_size``, ``q_proj``, ``config``, ``name_or_path``), so the stub
# harness below reproduces the dispatch + arithmetic without torch:
#
#   - ``_StubNN``        — the torch.nn stand-in monkeypatched over the seam
#   - ``_StubModule``    — duck-typed nn.Module (register_forward_hook,
#                          removable handles, per-instance ``_forward_hooks``,
#                          direct ``_parameters``)
#   - ``_T``             — duck-typed tensor (shape tuple / numel / dim)
#   - ``_StubModel``     — duck-typed HF model (named_modules,
#                          named_parameters, parameters, name_or_path, config)
#
# Hooks fire through ``module.fire(...)``, which invokes every registered
# closure with a (module, inputs, outputs) triple — the same call signature
# a real forward pass uses.
#
# Usage:
#     uv run --group dev pytest tests/test_flops_counter.py -q
# =====================================================================

import json
import math
import subprocess
import sys
from pathlib import Path

import flops_counter
import pytest
from artifact_loader import load_json_artifact
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "schemas" / "flops_report.json"


# ===== Stub harness =====


class _T:
    """Duck-typed tensor: the exact surface every ported hook reads."""

    def __init__(self, *shape):
        self.shape = tuple(shape)

    def numel(self):
        count = 1
        for dim in self.shape:
            count *= dim
        return count

    def dim(self):
        return len(self.shape)

    def unsqueeze(self, _dim):
        return _T(1, *self.shape)

    def to(self, _device):
        return self


class _Device:
    type = "cpu"


class _Param:
    def __init__(self, numel):
        self._numel = numel
        self.device = _Device()

    def numel(self):
        return self._numel


class _Handle:
    """Removable forward-hook handle (torch HookHandle analogue)."""

    def __init__(self, module, hook):
        self._module = module
        self._hook = hook
        self._removed = False

    def remove(self):
        if not self._removed:
            self._module._forward_hooks.remove(self._hook)
            self._removed = True


class _StubModule:
    """Duck-typed nn.Module base: hook registry + direct parameters."""

    def __init__(self, parameters=None):
        self._forward_hooks = []
        self._parameters = dict(parameters or {})

    def register_forward_hook(self, hook):
        self._forward_hooks.append(hook)
        return _Handle(self, hook)

    def fire(self, *inputs, outputs=None):
        """Invoke every registered hook as a real forward pass would."""
        for hook in list(self._forward_hooks):
            hook(self, list(inputs), outputs)

    def named_parameters(self, recurse=False):
        yield from self._parameters.items()

    def parameters(self):
        return iter(self._parameters.values())


class _StubLinear(_StubModule):
    def __init__(self, in_features, out_features):
        super().__init__(
            {
                "weight": _Param(in_features * out_features),
                "bias": _Param(out_features),
            }
        )
        self.in_features = in_features
        self.out_features = out_features


class _StubConv1d(_StubModule):
    def __init__(self, in_channels, out_channels, kernel_size, groups=1):
        super().__init__(
            {"weight": _Param(out_channels * in_channels * kernel_size)}
        )
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = (kernel_size,)
        self.groups = groups


class _StubConv2d(_StubModule):
    def __init__(self, in_channels, out_channels, kernel_size, groups=1):
        super().__init__(
            {
                "weight": _Param(
                    out_channels * in_channels * kernel_size[0] * kernel_size[1]
                )
            }
        )
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = tuple(kernel_size)
        self.groups = groups


class _StubMHA(_StubModule):
    def __init__(self, embed_dim, batch_first=True):
        super().__init__({"in_proj_weight": _Param(3 * embed_dim * embed_dim)})
        self.embed_dim = embed_dim
        self.batch_first = batch_first


class _StubEmbedding(_StubModule):
    def __init__(self, vocab_size, embedding_dim):
        super().__init__({"weight": _Param(vocab_size * embedding_dim)})
        self.num_embeddings = vocab_size
        self.embedding_dim = embedding_dim


class _StubLayerNorm(_StubModule):
    def __init__(self, normalized_shape):
        super().__init__(
            {
                "weight": _Param(normalized_shape),
                "bias": _Param(normalized_shape),
            }
        )


class _StubSiLU(_StubModule):
    pass


class _HFSelfAttentionStub(_StubModule):
    """Any classname in the HF self-attention dispatch list (re-stamped)."""

    def __init__(self, d_model, d_attn):
        super().__init__({"qkv_weight": _Param(3 * d_model * d_attn)})
        self.q_proj = _StubLinear(d_model, d_attn)


class _StubNN:
    """Duck-typed torch.nn: only the classes the dispatch reads."""

    Linear = _StubLinear
    Conv1d = _StubConv1d
    Conv2d = _StubConv2d
    MultiheadAttention = _StubMHA
    Embedding = _StubEmbedding
    LayerNorm = _StubLayerNorm
    SiLU = _StubSiLU
    GELU = _StubSiLU
    ReLU = _StubSiLU


class _StubConfig:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


class _StubModel:
    """Duck-typed HF model over an explicit (name, module) list."""

    def __init__(self, modules, name_or_path="", config=None):
        self._module_list = list(modules)
        self.name_or_path = name_or_path
        self.config = config if config is not None else _StubConfig()

    def named_modules(self):
        yield from self._module_list

    def parameters(self):
        for _name, module in self._module_list:
            yield from module.parameters()

    def named_parameters(self):
        for name, module in self._module_list:
            for pname, param in module.named_parameters():
                yield (f"{name}.{pname}" if name else pname), param


@pytest.fixture
def stub_nn(monkeypatch):
    """Route flops_counter's lazy torch.nn seam at the stub module."""
    monkeypatch.setattr(flops_counter, "_torch_nn", lambda: _StubNN)
    return _StubNN


def _reclass(module, classname):
    """Re-stamp a stub module's class name (classname-string dispatch)."""
    module.__class__ = type(classname, (module.__class__,), {})
    return module


def _make_counter(
    modules,
    name_or_path="",
    config=None,
    include_norm=False,
    include_act=False,
    include_embed=False,
):
    model = _StubModel(modules, name_or_path=name_or_path, config=config)
    counter = flops_counter.FlopsCounter(
        model,
        include_norm=include_norm,
        include_act=include_act,
        include_embed=include_embed,
    )
    return counter, model


def _load_schema():
    assert SCHEMA_PATH.is_file(), "schemas/flops_report.json not published (D-27)"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _minimal_report():
    return {
        "schema_version": 1,
        "num_tokens": 10,
        "all_tokens": 10000,
        "num_params": 8448,
        "total_flops_G": 0.00011008,
        "total_flops_exact": 110080,
        "total_flops_per_token": 11008.0,
        "total_flops_all_tokens": 110080000.0,
        "computation_size_ratio": 1.3020833333333333,
        "config": {
            "include_norm": True,
            "include_act": True,
            "include_embed": True,
        },
        "layer_details": {"mlp.fc": 81920},
        "uncovered_layers": [],
    }


# ===== Tracer end-to-end proof (round-trip) =====


def test_round_trip_stub_calibration_schema_and_loadback(stub_nn, tmp_path):
    """Stub calibration -> flops_report.json -> schema-valid -> tolerant
    loader returns the identical dict (the plan's PIPE-03 contract pin)."""
    embed = _StubEmbedding(vocab_size=100, embedding_dim=32)
    attn = _reclass(_HFSelfAttentionStub(d_model=32, d_attn=32), "BertSelfAttention")
    linear = _StubLinear(32, 64)
    norm = _StubLayerNorm(32)
    modules = [
        ("embeddings.word_embeddings", embed),
        ("encoder.attn", attn),
        ("mlp.fc", linear),
        ("mlp.norm", norm),
    ]
    counter, _model = _make_counter(
        modules, include_norm=True, include_act=True, include_embed=True
    )

    # One stub calibration forward: every registered hook fires once.
    embed.fire(_T(2, 10))
    attn.fire(_T(2, 10, 32))
    linear.fire(_T(2, 10, 32))
    norm.fire(_T(2, 10, 32))

    out = tmp_path / "flops_report.json"
    hardware = flops_counter.build_hardware_section("NVIDIA GB10", 42.416, 0.53)
    counter.save_to_json(
        num_tokens=10, all_tokens=10000, filepath=str(out), hardware=hardware
    )

    assert out.is_file(), "save_to_json must write flops_report.json"
    report = load_json_artifact(out)
    assert report is not None
    Draft202012Validator(_load_schema()).validate(report)
    assert report["schema_version"] == 1
    assert report["num_params"] == 8448
    assert report["layer_details"]["encoder.attn.matmul_core"] == 4 * 2 * 100 * 32
    assert report["layer_details"]["mlp.fc"] == 2 * 20 * 32 * 64
    assert report["layer_details"]["mlp.norm"] == 4 * 640
    assert report["uncovered_layers"] == []
    assert report["hardware"] == {
        "gpu_device": "NVIDIA GB10",
        "train_time": 42.416,
        "max_mem_gb": 0.53,
    }
    assert load_json_artifact(out) == report  # deterministic re-read


# ===== Hook arithmetic (legacy formulas, ported verbatim) =====


def test_linear_hook_counts_2NTIF(stub_nn):
    """Legacy formula: 2 * num_tokens * in_features * out_features."""
    linear = _StubLinear(8, 16)
    counter, _model = _make_counter([("mlp.0", linear)])
    linear.fire(_T(2, 5, 8))  # batch=2, tokens=5, in=8, out=16
    assert counter.layer_flops.get("mlp.0") == 2 * 2 * 5 * 8 * 16
    assert counter.total_flops == 2560
    assert counter.uncovered_param_share() == 0.0


def test_hf_self_attn_hook_matmul_core(stub_nn):
    attn = _reclass(_HFSelfAttentionStub(d_model=32, d_attn=48), "EsmSelfAttention")
    counter, _model = _make_counter([("encoder.layer.0.attention", attn)])
    attn.fire(_T(2, 10, 32))
    expected = 4 * 2 * (10**2) * 48
    assert counter.layer_flops.get("encoder.layer.0.attention.matmul_core") == expected


def test_mha_hook_sums_projection_and_attention(stub_nn):
    mha = _StubMHA(embed_dim=32, batch_first=True)
    counter, _model = _make_counter([("attn", mha)])
    mha.fire(_T(2, 10, 32))
    expected = 8 * 2 * 10 * (32**2) + 4 * 2 * (10**2) * 32
    assert counter.layer_flops.get("attn") == expected


def test_conv1d_and_conv2d_hooks(stub_nn):
    conv1 = _StubConv1d(in_channels=8, out_channels=16, kernel_size=3)
    conv2 = _StubConv2d(in_channels=8, out_channels=16, kernel_size=(3, 3))
    counter, _model = _make_counter([("c1", conv1), ("c2", conv2)])
    conv1.fire(_T(1, 8, 10))
    conv2.fire(_T(1, 8, 4, 4))
    assert counter.layer_flops.get("c1") == 2 * 1 * 10 * 8 * 16 * 3
    assert counter.layer_flops.get("c2") == 2 * 1 * 4 * 4 * 8 * 16 * 9


def test_norm_and_activation_hooks_count_4x_numel(stub_nn):
    norm = _StubLayerNorm(32)
    act = _StubSiLU()
    counter, _model = _make_counter(
        [("n", norm), ("a", act)], include_norm=True, include_act=True
    )
    norm.fire(_T(2, 10, 32))
    act.fire(_T(2, 10, 32))
    assert counter.layer_flops.get("n") == 4 * 640
    assert counter.layer_flops.get("a") == 4 * 640


def test_embedding_hook_counts_nothing(stub_nn):
    """Legacy _embedding_hook body is a bare pass — port keeps it."""
    embed = _StubEmbedding(vocab_size=100, embedding_dim=32)
    counter, _model = _make_counter([("e", embed)], include_embed=True)
    embed.fire(_T(2, 10))
    assert counter.total_flops == 0


def test_layer_details_overwrite_while_total_accumulates(stub_nn):
    """Legacy semantics: layer_flops[name] is overwritten per forward pass
    while total_flops accumulates (PATTERNS pin — keep it)."""
    linear = _StubLinear(8, 16)
    counter, _model = _make_counter([("x", linear)])
    linear.fire(_T(2, 5, 8))  # 2*10*8*16 = 2560
    linear.fire(_T(1, 4, 8))  # 2*4*8*16 = 1024
    assert counter.layer_flops.get("x") == 1024
    assert counter.total_flops == 2560 + 1024


# ===== Report shape: schema_version, optional hardware (D-05/D-27) =====


def test_hardware_section_absent_when_not_passed(stub_nn, tmp_path):
    counter, _model = _make_counter([("x", _StubLinear(8, 16))])
    out = tmp_path / "flops_report.json"
    counter.save_to_json(num_tokens=5, all_tokens=50, filepath=str(out))
    report = load_json_artifact(out)
    assert report is not None
    assert "hardware" not in report
    assert report["schema_version"] == 1
    Draft202012Validator(_load_schema()).validate(report)


def test_save_without_tokens_writes_null_extrapolations(stub_nn, tmp_path):
    """num_tokens=None leaves the extrapolations null (schema allows null);
    the ratio guard must not crash on the missing per-token value."""
    counter, _model = _make_counter([("x", _StubLinear(8, 16))])
    out = tmp_path / "flops_report.json"
    counter.save_to_json(num_tokens=None, all_tokens=None, filepath=str(out))
    report = load_json_artifact(out)
    assert report is not None
    assert report["schema_version"] == 1
    assert report["total_flops_per_token"] is None
    assert report["total_flops_all_tokens"] is None
    assert report["computation_size_ratio"] is None
    Draft202012Validator(_load_schema()).validate(report)


def test_save_with_zero_tokens_writes_null_extrapolations(stub_nn, tmp_path):
    """CR-01 (phase-07 review): num_tokens=0 behaves exactly like None —
    the extrapolations go null instead of dividing by zero. The
    calibration slot in run_finetune produces current_tokens == 0 for an
    empty train split, and the legacy ``is not None`` guard crashed the
    post-success flops write there: final_metrics.json was already on
    disk, the trainer_state resume marker was NOT copied, and the blind
    except swallowed the ZeroDivisionError — a cell that records
    "completed" yet silently retrains on every sweep. The raw count is
    echoed verbatim (0), only the derived ratios go null."""
    counter, _model = _make_counter([("x", _StubLinear(8, 16))])
    out = tmp_path / "flops_report.json"
    counter.save_to_json(num_tokens=0, all_tokens=1000, filepath=str(out))
    report = load_json_artifact(out)
    assert report is not None
    assert report["num_tokens"] == 0, "the raw count is echoed verbatim"
    assert report["all_tokens"] == 1000
    assert report["total_flops_per_token"] is None
    assert report["total_flops_all_tokens"] is None
    assert report["computation_size_ratio"] is None
    Draft202012Validator(_load_schema()).validate(report)


def test_build_hardware_section_is_pure_and_nullable():
    assert flops_counter.build_hardware_section() == {
        "gpu_device": None,
        "train_time": None,
        "max_mem_gb": None,
    }
    section = flops_counter.build_hardware_section("5090D", 42.416, 0.53)
    assert section == {"gpu_device": "5090D", "train_time": 42.416, "max_mem_gb": 0.53}


# ===== Uncovered-layer accounting (D-03) =====


def test_param_owning_undispatched_module_is_uncovered(stub_nn):
    mystery = _reclass(_StubModule(parameters={"w": _Param(1000)}), "MysteryLayer")
    linear = _StubLinear(8, 16)  # 8*16 + 16 = 144 params
    counter, _model = _make_counter([("hooked", linear), ("weird", mystery)])
    assert counter.uncovered_layers == [
        {"name": "weird", "classname": "MysteryLayer"}
    ]
    assert counter.uncovered_param_share() == pytest.approx(1000 / 1144)


def test_disabled_optional_branch_lands_in_uncovered(stub_nn):
    """A parameter-owning module whose optional branch is disabled by the
    include flags is uncovered for this counter (D-03 loud reporting)."""
    norm = _StubLayerNorm(32)
    counter, _model = _make_counter([("n", norm)], include_norm=False)
    assert counter.uncovered_layers == [
        {"name": "n", "classname": "_StubLayerNorm"}
    ]
    assert counter.uncovered_param_share() == 1.0


def test_uncovered_share_warning_prints(stub_nn, tmp_path, capsys):
    mystery = _reclass(_StubModule(parameters={"w": _Param(1000)}), "MysteryLayer")
    counter, _model = _make_counter(
        [("hooked", _StubLinear(8, 16)), ("weird", mystery)]
    )
    counter.save_to_json(num_tokens=5, all_tokens=50, filepath=str(tmp_path / "f.json"))
    out = capsys.readouterr().out
    assert "WARNING" in out
    report = load_json_artifact(tmp_path / "f.json")
    assert report is not None
    assert report["uncovered_layers"] == [
        {"name": "weird", "classname": "MysteryLayer"}
    ]


# ===== Schema contract pins (D-27) =====


def test_schema_accepts_fractional_layer_flops():
    """HyenaFilter's verbatim FFT formula yields fractional FLOPs
    (math.log2), so layer_details values must accept numbers — integer
    values remain the common case."""
    schema = _load_schema()
    report = _minimal_report()
    report["layer_details"]["h.fftconv_core"] = 32000 * math.log2(200)
    Draft202012Validator(schema).validate(report)


def test_schema_version_is_pinned_to_1():
    schema = _load_schema()
    report = _minimal_report()
    report["schema_version"] = 2
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(report)


def test_schema_rejects_unknown_top_level_field():
    schema = _load_schema()
    report = _minimal_report()
    report["surprise"] = 1
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(report)


def test_schema_hardware_section_contract():
    schema = _load_schema()
    base = _minimal_report()
    Draft202012Validator(schema).validate(base)  # hardware optional
    base["hardware"] = {
        "gpu_device": None,
        "train_time": None,
        "max_mem_gb": None,
    }
    Draft202012Validator(schema).validate(base)
    base["hardware"] = {"gpu_device": "5090D"}  # missing required keys
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(base)


# ===== Module-level helpers =====


def test_count_split_tokens():
    rows = [{"input_ids": [1, 2]}, {"other": 1}, {"input_ids": [3]}]
    assert flops_counter.count_split_tokens(rows) == (3, 2)
    assert flops_counter.count_split_tokens(None) == (0, 0)


def test_modules_import_in_torch_free_lane():
    """PIPE-01 criterion 2: both modules import with zero torch symbols
    resolved (hermetic subprocess — the dev/CI lane shape)."""
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; sys.path.insert(0, 'pipeline'); "
                "import flops_counter, artifact_loader; "
                "assert 'torch' not in sys.modules, 'torch leaked at import time'; "
                "print('cpu-import-ok')"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "cpu-import-ok" in proc.stdout


# =====================================================================
# Task 3: exotic architecture families, dispatch-order lock,
# remove_hooks, calibration_forward
# =====================================================================


class _PlainProj:
    """Non-nn.Linear projection: in/out features, empty hook list."""

    def __init__(self, in_features, out_features):
        self.in_features = in_features
        self.out_features = out_features
        self._forward_hooks = []


class _Conv1dLike:
    """Non-nn.Conv1d conv attribute: in_channels + kernel_size tuple."""

    def __init__(self, in_channels, kernel_size):
        self.in_channels = in_channels
        self.kernel_size = tuple(kernel_size)


class _SumVal:
    def __init__(self, value):
        self._value = value

    def item(self):
        return self._value


class _CuSeq:
    """cu_seqlens stub: slicing, subtraction, square, sum().item()."""

    def __init__(self, values):
        self.values = list(values)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return _CuSeq(self.values[idx])
        return self.values[idx]

    def __sub__(self, other):
        return _CuSeq([a - b for a, b in zip(self.values, other.values)])

    def __pow__(self, exponent):
        return _CuSeq([v**exponent for v in self.values])

    def sum(self):
        return _SumVal(sum(self.values))


class _MambaMixerStub(_StubModule):
    def __init__(self, d_inner=64, d_state=16, dt_rank=8, kernel=4):
        super().__init__({"mixer": _Param(1024)})
        self.conv1d = _Conv1dLike(d_inner, (kernel,))
        self.ssm_state_size = d_state
        self.time_step_rank = dt_rank


class _Mamba2MixerStub(_StubModule):
    def __init__(self, num_heads=4, head_dim=64, state=128, conv_in=128, kernel=4):
        super().__init__({"mixer": _Param(2048)})
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.ssm_state_size = state
        self.conv1d = _Conv1dLike(conv_in, (kernel,))


class BigBirdBlockSparseAttention:
    """Inner BigBird attention — exact classname (the is_sparse compare)."""

    def __init__(self, d_in, d_q, num_random_blocks=2, block_size=64):
        self.query = _PlainProj(d_in, d_q)
        self.num_random_blocks = num_random_blocks
        self.block_size = block_size


class _BigBirdDenseInner:
    def __init__(self, d_in, d_q):
        self.query = _PlainProj(d_in, d_q)
        self.num_random_blocks = 3
        self.block_size = 64


class _BigBirdAttentionStub(_StubModule):
    def __init__(self, inner):
        super().__init__({"attn": _Param(512)})
        self.self = inner


class _GQAStub(_StubModule):
    def __init__(self, d_model, d_q, sliding_window=None):
        super().__init__({"q": _Param(256)})
        self.q_proj = _PlainProj(d_model, d_q)
        self.config = _StubConfig(sliding_window=sliding_window)


class _FlashStub(_StubModule):
    def __init__(self, sliding_window=None, with_config=True):
        super().__init__({"f": _Param(256)})
        if with_config:
            self.config = _StubConfig(sliding_window=sliding_window)


class _ModernBertAttentionStub(_StubModule):
    def __init__(self, local_attention=128, every_n=3):
        super().__init__({"q": _Param(256)})
        self.config = _StubConfig(
            local_attention=local_attention, global_attn_every_n_layers=every_n
        )


class _Conv1DStub(_StubModule):
    """HF GPT-2 style Conv1D (classname string, not nn.Conv1d)."""

    def __init__(self, nf):
        super().__init__({"weight": _Param(64)})
        self.nf = nf


class _BertUnpadStub(_StubModule):
    def __init__(self, all_head_size=64):
        super().__init__({"q": _Param(256)})
        self.all_head_size = all_head_size


class _CaduceusMambaStub(_StubModule):
    def __init__(self, conv_in=64, kernel=4, out_features=64):
        super().__init__({"m": _Param(512)})
        self.conv1d = _Conv1dLike(conv_in, (kernel,))
        self.out_proj = _PlainProj(out_features, out_features)


class _Caduceus2Mamba2Stub(_StubModule):
    def __init__(self, head_dim=64, hidden_size=256, conv_in=512, kernel=4):
        super().__init__({"m": _Param(512)})
        self.head_dim = head_dim
        self.hidden_size = hidden_size
        self.conv1d = _Conv1dLike(conv_in, (kernel,))
        self.out_proj = _PlainProj(conv_in, conv_in)


class _AttentionStub(_StubModule):
    """Generic classname-Attention module (megadna/enformer/borzoi)."""

    def __init__(self, d, to_v=None, to_rel_k=False, use_tf_gamma=False):
        super().__init__({"a": _Param(256)})
        self.to_q = _PlainProj(d, d)
        if to_v is not None:
            self.to_v = _PlainProj(d, to_v)
        if to_rel_k:
            self.to_rel_k = True
        if use_tf_gamma:
            self.use_tf_gamma = True


# ===== Per-family hook arithmetic =====


def test_mamba_ssm_hook_arithmetic(stub_nn):
    mixer = _reclass(
        _MambaMixerStub(d_inner=64, d_state=16, dt_rank=8, kernel=4), "MambaMixer"
    )
    counter, _model = _make_counter([("backbone.layers.0.mixer", mixer)])
    mixer.fire(_T(1, 10, 64))
    name = "backbone.layers.0.mixer"
    assert counter.layer_flops.get(f"{name}.ssm_core") == 9 * 1 * 10 * 64 * 16
    # conv1d + dt_proj add to the total but not to layer_details
    expected_total = (
        (9 * 1 * 10 * 64 * 16) + (2 * 1 * 10 * 64 * 4) + (2 * 1 * 10 * 8 * 64)
    )
    assert counter.total_flops == expected_total


def test_mamba2_ssd_hook_arithmetic(stub_nn):
    mixer = _reclass(
        _Mamba2MixerStub(num_heads=4, head_dim=64, state=128, conv_in=128, kernel=4),
        "Mamba2Mixer",
    )
    counter, _model = _make_counter([("m", mixer)])
    mixer.fire(_T(1, 10, 256))
    ssd = 4 * 1 * 10 * (4 * 64) * 128
    assert counter.layer_flops.get("m.ssd_core") == ssd
    assert counter.total_flops == ssd + (2 * 1 * 10 * 128 * 4)


def test_hyena_filter_hook_fft_terms(stub_nn, tmp_path):
    filt = _reclass(_StubModule(parameters={"f": _Param(64)}), "HyenaFilter")
    counter, _model = _make_counter([("h", filt)])
    filt.fire(_T(1, 64, 100))  # (batch, d_model, seq_len)
    log2_n = math.log2(2 * 100)
    expected = (
        (5 * 1 * 64 * 100 * log2_n)
        + (5 * 64 * 100 * log2_n)
        + (6 * 1 * 64 * 101)
        + (5 * 1 * 64 * 100 * log2_n)
        + (4 * 1 * 64 * 100)
    )
    assert counter.layer_flops.get("h.fftconv_core") == pytest.approx(expected)
    assert counter.total_flops == pytest.approx(expected)
    # Fractional layer FLOPs (the verbatim log2 terms) stay schema-valid.
    out = tmp_path / "flops_report.json"
    counter.save_to_json(num_tokens=100, all_tokens=10000, filepath=str(out))
    report = load_json_artifact(out)
    assert report is not None
    Draft202012Validator(_load_schema()).validate(report)


def test_bigbird_sparse_hook_arithmetic(stub_nn):
    inner = BigBirdBlockSparseAttention(
        d_in=32, d_q=32, num_random_blocks=2, block_size=64
    )
    attn = _reclass(_BigBirdAttentionStub(inner), "BigBirdAttention")
    counter, _model = _make_counter([("b", attn)])
    attn.fire(_T(2, 100, 32))
    assert counter.layer_flops.get("b.qkv_dynamic_fused") == 3 * (2 * 2 * 100 * 32 * 32)
    effective_seq_len = (5 + 2) * 64
    assert counter.layer_flops.get("b.matmul_core") == 4 * 2 * 100 * effective_seq_len * 32


def test_bigbird_dense_inner_falls_back_to_quadratic(stub_nn):
    attn = _reclass(_BigBirdAttentionStub(_BigBirdDenseInner(d_in=32, d_q=32)), "BigBirdAttention")
    counter, _model = _make_counter([("b", attn)])
    attn.fire(_T(2, 100, 32))
    assert counter.layer_flops.get("b.matmul_core") == 4 * 2 * 100 * 100 * 32
    assert counter.layer_flops.get("b.qkv_dynamic_fused") == 3 * (2 * 2 * 100 * 32 * 32)


def test_gqa_hook_quadratic_without_window(stub_nn):
    attn = _reclass(_GQAStub(d_model=64, d_q=64, sliding_window=None), "LlamaAttention")
    counter, _model = _make_counter([("g", attn)])
    attn.fire(_T(1, 50, 64))
    assert counter.layer_flops.get("g.matmul_core") == 4 * 1 * 2500 * 64


def test_gqa_hook_windowed_for_flash_variant(stub_nn):
    attn = _reclass(
        _GQAStub(d_model=64, d_q=64, sliding_window=128), "GemmaFlashAttention2"
    )
    counter, _model = _make_counter([("g", attn)])
    attn.fire(_T(1, 512, 64))
    assert counter.layer_flops.get("g.matmul_core") == 4 * 1 * 512 * 128 * 64


def test_flash_attn_hook_windowed_for_attention2(stub_nn):
    module = _reclass(_FlashStub(sliding_window=128), "MistralFlashAttention2")
    counter, _model = _make_counter([("f", module)])
    module.fire(_T(1, 512, 64))
    assert counter.layer_flops.get("f.matmul_core") == 4 * 1 * 512 * 128 * 64


def test_flash_attn_hook_quadratic_without_2_suffix(stub_nn):
    module = _reclass(_FlashStub(sliding_window=128), "FlashAttentionBlock")
    counter, _model = _make_counter([("f", module)])
    module.fire(_T(1, 512, 64))
    assert counter.layer_flops.get("f.matmul_core") == 4 * 1 * 512 * 512 * 64


def test_modernbert_local_layer_windowed(stub_nn):
    attn = _reclass(_ModernBertAttentionStub(local_attention=128, every_n=3), "ModernBertAttention")
    counter, _model = _make_counter([("encoder.layers.1.attn", attn)])
    attn.fire(_T(1, 512, 64))
    expected = 4 * 1 * 512 * 128 * 64
    assert counter.layer_flops.get("encoder.layers.1.attn.matmul_core") == expected


def test_modernbert_global_layer_quadratic(stub_nn):
    attn = _reclass(_ModernBertAttentionStub(local_attention=128, every_n=3), "ModernBertAttention")
    counter, _model = _make_counter([("encoder.layers.3.attn", attn)])
    attn.fire(_T(1, 512, 64))
    expected = 4 * 1 * 512 * 512 * 64
    assert counter.layer_flops.get("encoder.layers.3.attn.matmul_core") == expected


def test_hf_conv1d_hook_arithmetic(stub_nn):
    module = _reclass(_Conv1DStub(nf=32), "Conv1D")
    counter, _model = _make_counter([("c", module)])
    module.fire(_T(2, 5, 16))
    assert counter.layer_flops.get("c") == 2 * 2 * 5 * 16 * 32


def test_dnabert2_flash_attn_cu_seqlens_arithmetic(stub_nn):
    module = _reclass(_BertUnpadStub(all_head_size=64), "BertUnpadSelfAttention")
    counter, _model = _make_counter([("u", module)])
    module.fire(_T(1, 12, 64), _CuSeq([0, 10, 12]))
    # seq_lens [10, 2] -> sum of squares 104
    assert counter.layer_flops.get("u.flash_attn_core") == 4 * 64 * 104


def test_caduceus_ssm_hook_config_fallbacks(stub_nn):
    module = _reclass(_CaduceusMambaStub(conv_in=64, kernel=4, out_features=64), "Mamba")
    counter, _model = _make_counter(
        [("c", module)], config=_StubConfig(ssm_cfg={"d_state": 16})
    )
    module.fire(_T(1, 10, 64))
    assert counter.layer_flops.get("c.ssm_core") == 9 * 1 * 10 * 64 * 16
    assert counter.layer_flops.get("c.conv1d_fused") == 2 * 1 * 10 * 64 * 4
    d_model, dt_rank = 256, 16  # defaults; dt_rank = ceil(256 / 16)
    expected_total = (
        (9 * 1 * 10 * 64 * 16)
        + (2 * 1 * 10 * 64 * 4)
        + (2 * 1 * 10 * d_model * (64 * 2))  # in_proj
        + (2 * 1 * 10 * 64 * (dt_rank + 2 * 16))  # x_proj
        + (2 * 1 * 10 * dt_rank * 64)  # dt_proj
        + (2 * 1 * 10 * 64 * 64)  # out_proj
    )
    assert counter.total_flops == expected_total


def test_caduceus2_ssd_hook_arithmetic(stub_nn):
    module = _reclass(
        _Caduceus2Mamba2Stub(head_dim=64, hidden_size=256, conv_in=512, kernel=4),
        "Mamba2",
    )
    counter, _model = _make_counter([("c2", module)])  # config: no ssm_cfg
    module.fire(_T(1, 10, 256))
    n_heads = 256 // 64
    d_state, d_inner = 128, 2 * 256
    ssd = 4 * 1 * 10 * (n_heads * 64) * d_state
    assert counter.layer_flops.get("c2.ssd_core") == ssd
    expected_total = ssd + (2 * 1 * 10 * 512 * 4) + (2 * 1 * 10 * d_inner * 512)
    assert counter.total_flops == expected_total


def test_megadna_branch_hooks_to_q_attention(stub_nn):
    attn = _reclass(_AttentionStub(d=64), "Attention")
    counter, _model = _make_counter(
        [("a", attn)], name_or_path="models/megadna_updated"
    )
    attn.fire(_T(1, 50, 64))
    assert counter.layer_flops.get("a.matmul_core") == 4 * 1 * 2500 * 64


def test_enformer_branch_hooks_rel_k_attention(stub_nn):
    attn = _reclass(
        _AttentionStub(d=64, to_v=32, to_rel_k=True, use_tf_gamma=True), "Attention"
    )
    counter, _model = _make_counter([("a", attn)], name_or_path="models/enformer")
    attn.fire(_T(1, 50, 64))
    expected = (2 * 1 * 2500 * 64) + (2 * 1 * 2500 * 64) + (2 * 1 * 2500 * 32)
    assert counter.layer_flops.get("a.matmul_core") == expected


def test_borzoi_attention_branch_arithmetic(stub_nn):
    attn = _reclass(_AttentionStub(d=64), "Attention")
    counter, _model = _make_counter([("a", attn)], name_or_path="models/borzoi-cc")
    attn.fire(_T(1, 50, 64))
    expected = (4 * 1 * 2500 * 64) + (2 * 1 * 2500 * 64)
    assert counter.layer_flops.get("a.matmul_core") == expected


def test_borzoi_flash_attention_branch(stub_nn):
    flash = _reclass(_StubModule(parameters={"f": _Param(64)}), "FlashAttention")
    counter, _model = _make_counter([("f", flash)], name_or_path="models/flashzoi")
    flash.fire(_T(1, 50, 64))
    expected = 8 * 1 * 50 * (64**2) + 4 * 1 * 2500 * 64
    assert counter.layer_flops.get("f.flash_mha_core") == expected


# ===== Dispatch-order lock + hook lifecycle =====


def test_linear_wins_over_borzoi_branch(stub_nn):
    """Dispatch order pin: every classname branch (incl. Linear) precedes
    the model_path branches, so a Linear — even one whose classname is
    Attention — inside a borzoi-path model takes the Linear hook first."""
    linear_named_attention = _reclass(_StubLinear(32, 64), "Attention")
    counter, _model = _make_counter(
        [("encoder.attn", linear_named_attention)],
        name_or_path="pipeline/models/borzoi-cc",
    )
    linear_named_attention.fire(_T(2, 10, 32))
    expected = 2 * 20 * 32 * 64
    assert counter.layer_flops.get("encoder.attn") == expected
    assert "encoder.attn.matmul_core" not in counter.layer_flops


def test_remove_hooks_empties_handle_list(stub_nn):
    linear = _StubLinear(8, 16)
    counter, _model = _make_counter([("x", linear)])
    assert len(counter.hooks) == 1
    linear.fire(_T(2, 5, 8))
    assert counter.total_flops == 2560
    counter.remove_hooks()
    assert counter.hooks == []
    linear.fire(_T(2, 5, 8))  # detached: nothing fires
    assert counter.total_flops == 2560


# ===== calibration_forward (legacy no_grad single-sample chain) =====


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _StubTorchLib:
    """Duck-typed torch for calibration_forward: tensor/ones_like/no_grad/
    autocast/device/bfloat16 over the stub tensor types."""

    bfloat16 = "bfloat16"

    def __init__(self):
        self.autocast_entries = []

    def tensor(self, data):
        return _T(len(data))

    def ones_like(self, tensor):
        return tensor

    def no_grad(self):
        return _Ctx()

    def autocast(self, device_type=None, dtype=None):
        self.autocast_entries.append((device_type, dtype))
        return _Ctx()

    def device(self, spec):
        return _Device()


class _BackboneStub:
    def __init__(self, inner):
        self.model = inner


class _CallableModel:
    """Model stub: records calls, fails first/always on demand."""

    def __init__(self, fail_first=False, fail_always=False, backbone=None):
        self.calls = []
        self._fail_first = fail_first
        self._fail_always = fail_always
        if backbone is not None:
            self.backbone = backbone
        self.name_or_path = ""

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self._fail_always or (self._fail_first and len(self.calls) == 1):
            raise RuntimeError("stub forward failure")

    def parameters(self):
        return iter([_Param(4)])


def test_calibration_forward_plain_input_ids(monkeypatch):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    model = _CallableModel()
    tokens = flops_counter.calibration_forward(
        model, "plant-dnabert-6mer", False, {"input_ids": [1, 2, 3, 4]}
    )
    assert tokens == 4
    assert len(model.calls) == 1
    args, kwargs = model.calls[0]
    assert args[0].shape == (1, 4)
    assert kwargs == {}


def test_calibration_forward_inputs_embeds(monkeypatch):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    model = _CallableModel()
    tokens = flops_counter.calibration_forward(
        model, "some-model", False, {"inputs_embeds": [[0.0]] * 6}
    )
    assert tokens == 6
    assert len(model.calls) == 1


def test_calibration_forward_evo_backbone_case(monkeypatch):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    inner = _CallableModel()
    model = _CallableModel(backbone=_BackboneStub(inner))
    tokens = flops_counter.calibration_forward(
        model, "evo2_1b_base", False, {"input_ids": [1, 2, 3]}
    )
    assert tokens == 3
    assert len(inner.calls) == 1
    assert len(model.calls) == 0


def test_calibration_forward_bf16_autocast(monkeypatch):
    torch_lib = _StubTorchLib()
    monkeypatch.setattr(flops_counter, "_torch", lambda: torch_lib)
    model = _CallableModel()
    tokens = flops_counter.calibration_forward(
        model, "mistral-dna", True, {"input_ids": [1, 2]}
    )
    assert tokens == 2
    assert torch_lib.autocast_entries == [("cpu", "bfloat16")]


def test_calibration_forward_attention_mask_retry(monkeypatch):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    model = _CallableModel(fail_first=True)
    tokens = flops_counter.calibration_forward(
        model, "some-model", False, {"input_ids": [1, 2, 3, 4, 5]}
    )
    assert tokens == 5
    assert len(model.calls) == 2
    _args, kwargs = model.calls[1]
    assert "attention_mask" in kwargs
    assert kwargs["attention_mask"].shape == (1, 5)


def test_calibration_forward_double_failure_prints_and_returns_tokens(
    monkeypatch, capsys
):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    model = _CallableModel(fail_always=True)
    tokens = flops_counter.calibration_forward(
        model, "some-model", False, {"input_ids": [1, 2]}
    )
    assert tokens == 2
    assert "FLOPs counting forward pass failed" in capsys.readouterr().out


def test_calibration_forward_empty_sample_returns_zero(monkeypatch):
    monkeypatch.setattr(flops_counter, "_torch", lambda: _StubTorchLib())
    model = _CallableModel()
    tokens = flops_counter.calibration_forward(model, "some-model", False, {})
    assert tokens == 0
