# =====================================================================
# test_doi_swap.py — the prepared Zenodo DOI swap (06-04, SC-7 / WR-01)
#
# Pins the swap's safety contracts over tmp fixtures (the REAL README.md
# and .gitleaks.toml are never touched by this suite):
#
# - refusal: with a stubbed checker reporting 404, the swap refuses,
#   exits non-zero naming record 19135551 + the --force escape, and
#   writes nothing;
# - both-or-neither (WR-01): when either target file lacks its expected
#   pattern, NOTHING is written to either file;
# - applied: with a stubbed public checker (or --force), ONE run rewrites
#   the fixture README (tokenized link -> DOI URL, HTML comment removed)
#   AND removes the fixture .gitleaks.toml's record-19135551 allowlist
#   block while the detection rule itself stays;
# - --dry-run prints the planned edits and writes nothing.
#
# See also:
#     - ``script/doi_swap.py`` — the orchestrator under test.
# =====================================================================

import http.server
import threading
from pathlib import Path

import doi_swap  # conftest puts script/ on sys.path

REPO = Path(__file__).resolve().parents[1]

DOI_URL = "https://doi.org/10.5281/zenodo.19135551"

# A structurally faithful miniature of the real README's load-bearing
# block: one HTML comment (multi-line) immediately followed by the
# tokenized Zenodo markdown link, wrapped in ordinary prose.
README_FIXTURE = """# DNALLM-Mark

Some upstream prose.

<!-- Load-bearing link (do not rotate or strip casually): the Zenodo URL below
     carries an intentional, record-scoped, read-only preview token — maintainer
     decision D-08, see AUDIT.md "Secret-scan evidence". The .gitleaks.toml
     allowlist exists solely to suppress this one link; any change here must
     update that allowlist in the same commit. When Zenodo record 19135551 is
     published, replace this with the public record DOI/URL and drop the
     allowlist rule (tracked as a Phase 6 release item in .planning/ROADMAP.md). -->
Before starting benchmark models on different tasks, users should first download the preseted datasets from [Zenodo](https://zenodo.org/records/19135551?preview=1&token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVhYzE2MTJmLWQzZDMtNDMxZC04ZTc3LTkyNzk1MTQzMmIxOCIsImRhdGEiOnt9LCJyYW5kb20iOiJhZTc1OTk5N2FjNzA3MjczNzJiYzE4MGM5NDA2ZDg5YiJ9.Btz9VeF52JLK1fzuMXcBJ8ZtD1aR9sHWwNSyc20eahZjgidmlWaRZ6lImsA5Pnw8Ei9vjyGpdXCeY8JdhlntlQ), then extract the datasets to `pipeline/datasets/` directory.

Some downstream prose.
"""

# A structurally faithful miniature of the real .gitleaks.toml: the
# detection rule stays after the swap; only its record-scoped allowlist
# block is removed.
GITLEAKS_FIXTURE = """title = "DNALLM-Mark secret scan"

[extend]
useDefault = true

[[rules]]
id = "zenodo-preview-token"
description = "Zenodo record URL carrying a JWT token parameter"
regex = '''zenodo\\.org/records/[0-9]+\\?[^ )"']*token=eyJ[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]{10,}\\.[A-Za-z0-9_-]{10,}'''
keywords = ["zenodo"]

    [[rules.allowlists]]
    description = "Intentional Zenodo record-19135551 preview link (maintainer decision 2026-10-08, D-08)"
    condition = "AND"
    paths = ['''^README\\.md$''']
    regexes = ['''zenodo\\.org/records/19135551\\?preview=1&token=''']
"""


def stub_checker(public: bool):
    """Build an injectable public-ness checker returning a fixed verdict."""

    def _check(url, timeout=10.0):
        _ = url, timeout
        return public

    return _check


def write_fixtures(tmp_path):
    """Write README.md + .gitleaks.toml fixtures; return their paths."""
    readme = tmp_path / "README.md"
    gitleaks = tmp_path / ".gitleaks.toml"
    readme.write_text(README_FIXTURE, encoding="utf-8")
    gitleaks.write_text(GITLEAKS_FIXTURE, encoding="utf-8")
    return readme, gitleaks


def run_main(tmp_path, *, public=True, force=False, dry_run=False,
             readme_text=None):
    """Invoke doi_swap.main over tmp fixtures with a stubbed checker.

    Args:
        tmp_path: pytest tmp dir.
        public: the stubbed checker verdict.
        force: pass --force.
        dry_run: pass --dry-run.
        readme_text: override the README fixture content (for negative
            cases).

    Returns:
        tuple: ``(readme_path, gitleaks_path, exit_code_or_None)`` — the
        exit is None when main returned normally.
    """
    readme, gitleaks = write_fixtures(tmp_path)
    if readme_text is not None:
        readme.write_text(readme_text, encoding="utf-8")
    argv = ["--doi", DOI_URL]
    if force:
        argv.append("--force")
    if dry_run:
        argv.append("--dry-run")
    code = doi_swap.main(argv, checker=stub_checker(public),
                         readme_path=readme, gitleaks_path=gitleaks)
    return readme, gitleaks, code


# ===== Refusal while the record is not public =====


def test_refuses_on_404_without_touching_files(tmp_path, capsys):
    """A 404 (record not public yet) refuses: non-zero exit naming the
    record and the --force escape, and NEITHER fixture file changes."""
    readme, gitleaks, code = run_main(tmp_path, public=False)
    assert code == 1
    out = capsys.readouterr().out
    assert "19135551" in out
    assert "--force" in out
    assert readme.read_text(encoding="utf-8") == README_FIXTURE
    assert gitleaks.read_text(encoding="utf-8") == GITLEAKS_FIXTURE


def test_refusal_message_names_the_target_doi(tmp_path, capsys):
    """The refusal also names the DOI URL it checked, so the maintainer
    can see which URL 404'd."""
    _, _, code = run_main(tmp_path, public=False)
    assert code == 1
    assert DOI_URL in capsys.readouterr().out


# ===== Applied swap: both targets in one run =====


def test_public_check_applies_both_edits_in_one_run(tmp_path):
    """With the checker reporting public, ONE run rewrites the README
    (tokenized link -> DOI URL; load-bearing HTML comment removed) AND
    removes the .gitleaks.toml record-scoped allowlist block."""
    readme, gitleaks, code = run_main(tmp_path, public=True)
    assert code == 0

    readme_text = readme.read_text(encoding="utf-8")
    assert f"[Zenodo]({DOI_URL})" in readme_text
    assert "preview=1&token=" not in readme_text
    assert "Load-bearing link" not in readme_text
    assert "<!--" not in readme_text
    # The surrounding prose survives.
    assert "Before starting benchmark models" in readme_text
    assert "Some upstream prose." in readme_text
    assert "Some downstream prose." in readme_text

    gitleaks_text = gitleaks.read_text(encoding="utf-8")
    assert "[[rules.allowlists]]" not in gitleaks_text
    assert "records/19135551" not in gitleaks_text
    # The detection rule itself stays.
    assert 'id = "zenodo-preview-token"' in gitleaks_text
    assert "[[rules]]" in gitleaks_text


def test_force_overrides_the_404_refusal(tmp_path):
    """--force proceeds despite a 404 checker verdict (maintainer-only
    escape, documented in the docstring)."""
    readme, gitleaks, code = run_main(tmp_path, public=False, force=True)
    assert code == 0
    assert f"[Zenodo]({DOI_URL})" in readme.read_text(encoding="utf-8")
    assert "[[rules.allowlists]]" not in gitleaks.read_text(encoding="utf-8")


# ===== Both-or-neither (WR-01) =====


def test_missing_readme_link_writes_neither_file(tmp_path):
    """A README without the tokenized link aborts the whole swap — the
    .gitleaks.toml fixture must remain untouched (both-or-neither)."""
    plain = "# DNALLM-Mark\n\nNo Zenodo link here at all.\n"
    readme, gitleaks, code = run_main(tmp_path, public=True,
                                      readme_text=plain)
    assert code == 1
    assert readme.read_text(encoding="utf-8") == plain
    assert gitleaks.read_text(encoding="utf-8") == GITLEAKS_FIXTURE


def test_missing_allowlist_block_writes_neither_file(tmp_path):
    """A .gitleaks.toml without the record-scoped allowlist aborts the
    whole swap — the README fixture must remain untouched."""
    readme, gitleaks = write_fixtures(tmp_path)
    stripped = "\n".join(
        line for line in GITLEAKS_FIXTURE.splitlines()
        if "[[rules.allowlists]]" not in line
        and "records/19135551" not in line
    ) + "\n"
    gitleaks.write_text(stripped, encoding="utf-8")
    code = doi_swap.main(["--doi", DOI_URL], checker=stub_checker(True),
                         readme_path=readme, gitleaks_path=gitleaks)
    assert code == 1
    assert readme.read_text(encoding="utf-8") == README_FIXTURE
    assert gitleaks.read_text(encoding="utf-8") == stripped


# ===== Dry run =====


def test_dry_run_prints_plan_and_writes_nothing(tmp_path, capsys):
    """--dry-run reports both planned edits without writing either
    file."""
    readme, gitleaks, code = run_main(tmp_path, public=True, dry_run=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "README.md" in out
    assert ".gitleaks.toml" in out
    assert DOI_URL in out
    assert readme.read_text(encoding="utf-8") == README_FIXTURE
    assert gitleaks.read_text(encoding="utf-8") == GITLEAKS_FIXTURE


def test_dry_run_still_refuses_on_404(tmp_path):
    """The public-ness gate runs before the dry-run report."""
    _, _, code = run_main(tmp_path, public=False, dry_run=True)
    assert code == 1


# ===== The real files stay untouched (SC-7 non-execution) =====


def test_real_readme_and_gitleaks_are_untouched():
    """The swap is PREPARED, not executed: the real README still carries
    the tokenized preview link and its comment, and the real .gitleaks.toml
    still carries the record-scoped allowlist."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "zenodo.org/records/19135551?preview=1&token=" in readme
    assert "Load-bearing link" in readme
    gitleaks = (REPO / ".gitleaks.toml").read_text(encoding="utf-8")
    assert "[[rules.allowlists]]" in gitleaks
    assert "records/19135551" in gitleaks


# ===== Checker wiring =====


def test_real_checker_reports_not_public_for_the_current_record():
    """The production urllib checker returns False for a 404 URL (no
    network needed: a closed local port fails fast) and True for a 200
    responder (a local socket fixture)."""
    class OK(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, format, *args):  # stdlib signature shadow
            _ = format, args

    server = http.server.HTTPServer(("127.0.0.1", 0), OK)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        assert doi_swap.check_public(f"http://127.0.0.1:{port}/record") is True
    finally:
        server.shutdown()
    # A port with no listener refuses the connection -> not public.
    assert doi_swap.check_public("http://127.0.0.1:1/record") is False


def test_cli_wires_flags():
    """The CLI parses --doi/--force/--dry-run into the namespace main
    consumes."""
    args = doi_swap.parse_args(["--doi", DOI_URL, "--force", "--dry-run"])
    assert args.doi == DOI_URL
    assert args.force is True
    assert args.dry_run is True
