"""
Carve stratified 10% dev splits for Dev-empty benchmark tasks (F1 / REV-01).

[RED skeleton — behavior lands with the implementation commit; see
tests/test_dev_splits.py for the contract.]

See also:
    pipeline/run_finetune.py
    pipeline/datasets_info.json
    script/convert_registry.py
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

# ===== Configuration =====

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "pipeline" / "datasets_info.json"
DATASETS_ROOT = REPO_ROOT / "pipeline" / "datasets"
SEED = 42


class TaskSkip(Exception):
    """A malformed/inconsistent dataset aborts its task; the run continues."""


def parse_args():
    raise NotImplementedError


def select_dev_indices(labels, seed=SEED):
    raise NotImplementedError


def carve_stratified_dev(rows, seed=SEED):
    raise NotImplementedError


def read_csv_rows(csv_path, task_name):
    raise NotImplementedError


def parse_labels(rows, label_idx, task_name):
    raise NotImplementedError


def write_csv(path, header, rows):
    raise NotImplementedError


def apply_registry_update(registry, name, train_count, dev_count):
    raise NotImplementedError


def write_registry(path, registry):
    raise NotImplementedError


def split_task(name, entry, registry, datasets_root=DATASETS_ROOT):
    raise NotImplementedError


def run_check(registry, datasets_root=DATASETS_ROOT):
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
