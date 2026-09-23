from __future__ import annotations

import dataclasses
import json
import types
from pathlib import Path
from typing import Any, Mapping, TypeVar, get_args, get_origin, get_type_hints


class ConfigError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class DatasetConfig:
    name: str
    view: str
    manifest_hash: str
    train_fraction: float = 1.0
    tune_role: str = "tune"
    calibration_role: str = "cal"


@dataclasses.dataclass(frozen=True)
class PreprocessingConfig:
    max_length: int = 512
    canonicalization: str = "crlf_to_lf"
    ast_relation: str = "leaf_path_radius4"
    ast_radius: int = 4
    dfg_version: str = "limited-rd-v1"
    structural_context: str = "full_function"
    annotation_masking: str = "a_priori_v1"
    cache_hash: str = "smoke"
    topology: str = 'clean'
    dfg_symmetry: bool = False
    degree_normalization: bool = False


@dataclasses.dataclass(frozen=True)
class ModelConfig:
    variant: str
    checkpoint: str = "microsoft/codebert-base"
    revision: str = "UNRESOLVED"
    structural_layers: tuple[int, ...] = (2, 5, 8, 11)
    relations: tuple[str, ...] = ("ast", "dfg")
    gate_mode: str = "token"
    beta_init: float = 0.10
    gate_init: str = "zero"
    head_dropout: float = 0.1
    structural_dropout: float = 0.0
    gate_sharing: str = 'none'
    freeze_beta: bool = False
    regvd_hidden_size: int = 128
    regvd_layers: int = 2
    regvd_window_size: int = 5


@dataclasses.dataclass(frozen=True)
class TrainingConfig:
    seed: int = 42
    epochs: int = 5
    effective_batch_size: int = 32
    microbatch_size: int = 4
    gradient_accumulation: int = 8
    pretrained_lr: float = 2e-5
    new_module_lr_multiplier: float = 1.0
    optimizer: str = "adamw"
    adam_betas: tuple[float, float] = (0.9, 0.999)
    adam_epsilon: float = 1e-8
    weight_decay: float = 0.01
    warmup_fraction: float = 0.1
    scheduler: str = "linear"
    grad_clip_norm: float = 1.0
    loss: str = "weighted_bce"
    precision: str = "bf16_if_supported"
    activation_checkpointing: bool = True
    validation_frequency: str = "epoch"
    selection_metric: str = "average_precision"
    min_epochs: int = 3
    patience: int = 2
    min_delta: float = 0.0001
    max_optimizer_steps: int | None = None


@dataclasses.dataclass(frozen=True)
class EvaluationConfig:
    thresholds: tuple[str, ...] = ("max_f1", "fpr_0.005", "recall_0.80")
    threshold_fit_role: str = "cal"
    bootstrap_replicates: int = 10000
    analysis_seed: int = 20260921


@dataclasses.dataclass(frozen=True)
class ResourcesConfig:
    host_profile: str = "local"
    max_vram_gb: float | str = "measured_device_limit_minus_4"


@dataclasses.dataclass(frozen=True)
class ProvenanceConfig:
    hpo_parent: str | None = None
    protocol_hash: str = "UNRESOLVED"


@dataclasses.dataclass(frozen=True)
class ExperimentConfig:
    protocol_version: str
    experiment_id: str
    dataset: DatasetConfig
    preprocessing: PreprocessingConfig
    model: ModelConfig
    training: TrainingConfig
    evaluation: EvaluationConfig
    resources: ResourcesConfig
    provenance: ProvenanceConfig

    def validate(self, allow_unresolved: bool = False) -> None:
        if self.protocol_version != "1.0":
            raise ConfigError("protocol_version must be '1.0'")
        if self.preprocessing.max_length < 2 or self.preprocessing.max_length > 512:
            raise ConfigError("max_length must be in [2, 512]")
        if not 0 < self.dataset.train_fraction <= 1:
            raise ConfigError("train_fraction must be in (0, 1]")
        if self.training.effective_batch_size != self.training.microbatch_size * self.training.gradient_accumulation:
            raise ConfigError("effective batch must equal microbatch_size * gradient_accumulation")
        if self.training.epochs<=0 or self.training.microbatch_size<=0 or self.training.gradient_accumulation<=0:
            raise ConfigError('positive epoch and batch counts required')
        if self.training.optimizer!='adamw' or self.training.scheduler!='linear':
            raise ConfigError('unregistered optimizer or scheduler')
        if self.training.loss not in {'weighted_bce','unweighted_bce'}:
            raise ConfigError('unknown loss')
        if self.evaluation.threshold_fit_role!='cal':raise ConfigError('threshold fitting must use cal')
        if self.model.gate_sharing not in {'none','head','layer','relation'}:raise ConfigError('unknown gate sharing')
        if self.preprocessing.structural_context not in {'full_function','visible_prefix'}:raise ConfigError('unknown structural context')
        if self.preprocessing.annotation_masking not in {'a_priori_v1','none'}:raise ConfigError('unknown annotation masking')
        if not 0<=self.model.structural_dropout<=1:raise ConfigError('invalid structural dropout')
        if not allow_unresolved:
            blob = json.dumps(dataclasses.asdict(self))
            if "UNRESOLVED" in blob or "resolved_" in blob:
                raise ConfigError("configuration contains unresolved immutable fields")


T = TypeVar("T")


def _matches(value,typ):
    origin=get_origin(typ)
    if origin is types.UnionType:return any(_matches(value,subtype) for subtype in get_args(typ))
    if origin is tuple:
        args=get_args(typ)
        return isinstance(value,tuple) and (all(_matches(v,args[0]) for v in value) if len(args)==2 and args[1] is Ellipsis else len(value)==len(args) and all(_matches(v,t) for v,t in zip(value,args)))
    if typ is float:return type(value) in {float,int}
    if typ in {int,bool,str}:return type(value) is typ
    if typ is type(None):return value is None
    return isinstance(value,typ)


def _construct(cls: type[T], values: Mapping[str, Any]) -> T:
    fields = {f.name: f for f in dataclasses.fields(cls)}
    extra = set(values) - set(fields)
    if extra:
        raise ConfigError(f"unknown keys for {cls.__name__}: {sorted(extra)}")
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for name, value in values.items():
        typ = hints[name]
        if dataclasses.is_dataclass(typ):
            value = _construct(typ, value)
        elif get_origin(typ) is tuple and isinstance(value, list):
            value = tuple(value)
        if not _matches(value,typ):
            raise ConfigError(f'{cls.__name__}.{name} has incorrect type')
        kwargs[name] = value
    try:
        return cls(**kwargs)
    except TypeError as exc:
        raise ConfigError(str(exc)) from exc


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ConfigError("non-JSON YAML requires PyYAML") from exc
        raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")
    parent = raw.pop("extends", None)
    if parent:
        base = _load_mapping((path.parent / parent).resolve())
        raw = _deep_merge(base, raw)
    return raw


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path, allow_unresolved: bool = False) -> ExperimentConfig:
    raw = _load_mapping(Path(path).resolve())
    cfg = _construct(ExperimentConfig, raw)
    cfg.validate(allow_unresolved=allow_unresolved)
    return cfg


def dump_config(config: ExperimentConfig) -> str:
    return json.dumps(dataclasses.asdict(config), indent=2, sort_keys=True) + "\n"
