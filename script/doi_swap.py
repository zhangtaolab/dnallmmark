"""Prepared Zenodo DOI swap: README link + .gitleaks.toml allowlist in ONE run (SC-7, WR-01).

Purpose
-------
When Zenodo record 19135551 is published (it is preview-token-only /
public-404 as of 2026-10-11), the repository's load-bearing dataset
download link must move from the preview-token URL to the public record
DOI, and the record-scoped gitleaks allowlist that exists solely to
suppress the intentional token must be dropped. WR-01 (the same-commit
rule): those two edits belong in ONE commit — a token link left in the
README with no allowlist fails the secret scan; an allowlist left with no
token link is dead suppression surface. This script makes the same-commit
rule true BY CONSTRUCTION: one run edits exactly both targets, or neither
(partial application aborts before any write).

**The MAINTAINER executes this script** when record 19135551 goes public,
then commits both files together. No agent polls Zenodo and no automated
swap exists — this module is the prepared, documented mechanism only.

Behavior
--------
``check_public(url)``
    A short-timeout ``urllib.request`` GET: HTTP 200 -> public (True);
    any ``HTTPError`` (404 while the record is still in preview),
    ``URLError``, or timeout -> not public (False). The check is
    INJECTABLE (``main(..., checker=...)``) so tests run it against
    stubbed verdicts and a local socket, never the network.

``rewrite_readme(text, doi_url)``
    Replaces the tokenized Zenodo markdown-link target
    (``https://zenodo.org/records/19135551?preview=1&token=<jwt>``) with
    the public DOI URL and removes the load-bearing HTML comment block
    that documents the token. Raises ``SwapError`` if either pattern is
    absent (a README already swapped, or one restructured).

``rewrite_gitleaks(text)``
    Removes the ``[[rules.allowlists]]`` block scoped to record 19135551
    (line-scanned: from the allowlist header through its
    ``regexes = [...19135551...]`` line). The ``zenodo-preview-token``
    DETECTION rule itself stays. Raises ``SwapError`` if the block is
    absent.

``apply_swap(readme_path, gitleaks_path, doi_url)``
    Reads BOTH files, computes BOTH rewrites, and writes them only after
    both rewrites SUCCEEDED — both-or-neither at the PATTERN level: a
    missing expected pattern aborts before any write. The guarantee is
    NOT filesystem-level atomicity: an I/O failure between the two
    ``write_text`` calls can still leave the first file applied. That
    partial state is loud, not silent — a re-run aborts because the
    already-swapped file no longer carries its pattern (LOW-09,
    phase-06 review: the previous "impossible by construction" claim
    overclaimed).

Refusals
--------
- Target DOI not public (404): refuses, names record 19135551 and the
  ``--force`` escape hatch (maintainer-only), exits 1, writes nothing.
- Either file missing its expected pattern: aborts, exits 1, writes
  nothing (WR-01 both-or-neither).
- ``--dry-run``: prints the planned edits and writes nothing (the
  public-ness gate still runs first).

Usage (MAINTAINER, when record 19135551 is public)::

    uv run --group dev python script/doi_swap.py \\
        --doi https://doi.org/10.5281/zenodo.19135551

Then review the diff and commit README.md + .gitleaks.toml together in
ONE commit (WR-01). Never commit them separately.

See also:
    - ``README.md`` (the load-bearing link + its comment) and
      ``.gitleaks.toml`` (the record-scoped allowlist) — the two targets.
    - ``tests/test_doi_swap.py`` — the fixture-driven contracts (the real
      files are never touched by the suite).
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ===== Configuration =====

ZENODO_RECORD = "19135551"
README_PATH = REPO_ROOT / "README.md"
GITLEAKS_PATH = REPO_ROOT / ".gitleaks.toml"

# The tokenized preview link (a JWT closed by the markdown ")"): the exact
# class the gitleaks rule detects.
TOKEN_LINK_RE = re.compile(
    r"https://zenodo\.org/records/19135551\?preview=1&token="
    r"[A-Za-z0-9_.\-]+"
)

# The load-bearing HTML comment block naming the token policy.
COMMENT_START = "<!-- Load-bearing link"
COMMENT_END = "-->"

# The .gitleaks.toml allowlist block boundaries (record-scoped).
ALLOWLIST_HEADER = "[[rules.allowlists]]"
ALLOWLIST_RECORD_MARKER = "records/19135551"


class SwapError(Exception):
    """A target file does not carry its expected swap pattern."""


def check_public(url: str, timeout: float = 10.0) -> bool:
    """GET the URL with a short timeout; True iff it answers HTTP 200.

    Args:
        url: The candidate public DOI/record URL.
        timeout: Seconds before giving up (keeps the gate snappy).

    Returns:
        bool: True when the URL is publicly reachable (HTTP 200); False
        on any HTTP error (404 — the preview state), connection error,
        or timeout.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            OSError):
        return False


def rewrite_readme(text: str, doi_url: str) -> str:
    """Rewrite the README's dataset-download block for the public DOI.

    Args:
        text: The README.md content.
        doi_url: The public DOI/record URL replacing the tokenized link.

    Returns:
        str: The rewritten content (tokenized link -> DOI URL; the
        load-bearing HTML comment block removed).

    Raises:
        SwapError: If the tokenized link or the comment block is absent.
    """
    if not TOKEN_LINK_RE.search(text):
        raise SwapError(
            "README.md carries no tokenized Zenodo record-19135551 "
            "preview link — it may already be swapped, or the link was "
            "restructured; refusing to touch either file (WR-01)"
        )
    text = TOKEN_LINK_RE.sub(doi_url, text, count=1)

    start = text.find(COMMENT_START)
    if start == -1:
        raise SwapError(
            "README.md carries no load-bearing link comment — it may "
            "already be swapped; refusing to touch either file (WR-01)"
        )
    end = text.find(COMMENT_END, start)
    if end == -1:
        raise SwapError(
            "README.md's load-bearing link comment is not closed "
            "(no '-->'); refusing to touch either file (WR-01)"
        )
    end += len(COMMENT_END)
    # Swallow the newline that carried the comment so the paragraph
    # following it starts at column 0, as it does today.
    if text[end:end + 1] == "\n":
        end += 1
    return text[:start] + text[end:]


def rewrite_gitleaks(text: str) -> str:
    """Remove the record-19135551-scoped allowlist block from gitleaks.

    The ``zenodo-preview-token`` detection rule itself stays; only its
    allowlist (which exists solely to suppress the intentional preview
    link) is removed.

    Args:
        text: The .gitleaks.toml content.

    Returns:
        str: The content without the record-scoped allowlist block.

    Raises:
        SwapError: If no allowlist block scoped to record 19135551 is
        found.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    removed = False
    while i < len(lines):
        if ALLOWLIST_HEADER in lines[i]:
            # Scan the block: header through the regexes line that names
            # THIS record. A block scoped to a different record is left
            # in place.
            j = i
            block: list[str] = []
            while j < len(lines):
                block.append(lines[j])
                if lines[j].lstrip().startswith("regexes"):
                    break
                j += 1
            block_text = "".join(block)
            if ALLOWLIST_RECORD_MARKER in block_text:
                removed = True
                i = j + 1
                continue  # drop the block
        out.append(lines[i])
        i += 1
    if not removed:
        raise SwapError(
            ".gitleaks.toml carries no allowlist block scoped to record "
            "19135551 — it may already be removed; refusing to touch "
            "either file (WR-01)"
        )
    return "".join(out)


def apply_swap(readme_path: Path, gitleaks_path: Path, doi_url: str) -> None:
    """Apply BOTH edits: both-or-neither at the PATTERN level (WR-01).

    Reads both files, computes both rewrites, and writes them only after
    both succeeded — a MISSING PATTERN aborts before any write, so a
    partial application can never begin. The guarantee stops at the
    pattern level: an I/O failure BETWEEN the two ``write_text`` calls
    can still leave the first file applied; that state is loud, not
    silent — a re-run aborts because the swapped file no longer carries
    its expected pattern (LOW-09, phase-06 review: the previous
    "impossible by construction" wording overclaimed filesystem-level
    atomicity).

    Args:
        readme_path: The README.md to rewrite.
        gitleaks_path: The .gitleaks.toml to strip.
        doi_url: The public DOI/record URL.

    Raises:
        SwapError: If either file lacks its expected pattern — raised
        BEFORE any write.
    """
    readme_text = readme_path.read_text(encoding="utf-8")
    gitleaks_text = gitleaks_path.read_text(encoding="utf-8")
    new_readme = rewrite_readme(readme_text, doi_url)
    new_gitleaks = rewrite_gitleaks(gitleaks_text)
    readme_path.write_text(new_readme, encoding="utf-8")
    gitleaks_path.write_text(new_gitleaks, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="doi_swap",
        description=(
            "Swap the README's Zenodo preview-token link for the public "
            "DOI and drop the record-scoped .gitleaks.toml allowlist — "
            "both in ONE run (WR-01). MAINTAINER-executed when record "
            f"{ZENODO_RECORD} is public."
        ),
    )
    parser.add_argument(
        "--doi", required=True,
        help="the public DOI/record URL replacing the tokenized link "
             "(e.g. https://doi.org/10.5281/zenodo.19135551)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="proceed even when the DOI URL is not reachable/200 "
             "(maintainer-only escape; the default is to refuse)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the planned edits without writing either file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *,
         checker: Callable[[str, float], bool] = check_public,
         readme_path: Path = README_PATH,
         gitleaks_path: Path = GITLEAKS_PATH) -> int:
    """CLI entry point: gate on public-ness, then swap both-or-neither.

    Args:
        argv: CLI arguments (defaults to ``sys.argv[1:]``).
        checker: The public-ness check (injectable for tests).
        readme_path: The README target (injectable for tests).
        gitleaks_path: The .gitleaks.toml target (injectable for tests).

    Returns:
        int: Process exit code (0 success, 1 refusal/abort).
    """
    args = parse_args(argv)
    if not args.force and not checker(args.doi, 10.0):
        print(
            f"[Refused] {args.doi} is not reachable (record "
            f"{ZENODO_RECORD} is still preview-token-only / 404). "
            "The swap runs only when the record is public; override "
            "with --force if you are certain."
        )
        return 1

    if args.dry_run:
        print("[Dry-run] Planned edits (nothing written):")
        print(f"  1. {readme_path}: tokenized record-{ZENODO_RECORD} link "
              f"-> {args.doi}; load-bearing HTML comment removed")
        print(f"  2. {gitleaks_path}: record-{ZENODO_RECORD}-scoped "
              "[[rules.allowlists]] block removed (detection rule stays)")
        print("Commit BOTH files together in one commit (WR-01).")
        return 0

    try:
        apply_swap(readme_path, gitleaks_path, args.doi)
    except SwapError as exc:
        print(f"[Aborted] {exc}")
        return 1
    print("✅ Swapped both targets (WR-01, one commit):")
    print(f"  1. {readme_path}: link -> {args.doi}, comment removed")
    print(f"  2. {gitleaks_path}: record-{ZENODO_RECORD} allowlist removed")
    print("Review the diff, then commit both files in ONE commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
