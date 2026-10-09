"""
Drive the model x task x seed fine-tuning sweep matrix (F2 / REV-02).

RED-phase skeleton: the public API surface below is pinned by
``tests/test_sweep.py``; each function raises NotImplementedError until the
GREEN implementation lands.
"""

import subprocess
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent


def parse_args():
    raise NotImplementedError


def enumerate_matrix(models_filter, tasks_filter, seeds, registry_dir):
    raise NotImplementedError


def build_argv(model, task, seed, output_root):
    raise NotImplementedError


def launch_subprocess(model, task, seed, output_root):
    raise NotImplementedError


def run_matrix(cells, output_root, executor=None):
    raise NotImplementedError


def main():
    raise NotImplementedError
