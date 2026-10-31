# Repository integrity

Run from a Git checkout with Python 3.12.14, Node.js 24.22.1 and Git on PATH,
after installing the hash-locked Python packages once:

```sh
python -m pip install --require-hashes --only-binary=:all: -r tools/requirements.txt
python tools/check_repository.py
```

This is the local and CI entry point. It exits nonzero on any failed check.
Python needs only the packages in [tools/requirements.txt](../tools/requirements.txt),
each pinned with the hash of every wheel, so pip installs nothing it has not
been told the hash of and builds nothing from source; Node uses only built-in
modules, and no npm package is required. The declared versions are the CI baseline; local
versions are recorded in evidence. Issue triage uses the same pinned Python
version; all label fixture, detection and reconciliation jobs explicitly set up
the same pinned Node version. The first run downloads actionlint 1.7.12
from its official release and verifies the platform archive against
[the checksum lock](../tools/actionlint-lock.json). Later runs reverify the cached
archive and extract only the named executable. Supported tooling platforms are
Linux, Windows and macOS on x64/ARM64. This is not Excel host certification.

The command checks issue configuration, all Python tooling tests, the
[Python quality gates](#python-quality-gates) (gates `ruff` and `mypy`), canonical
label self-tests, drift self-tests and CLI evidence regressions, the format of
the numerical [test-case files](methodology/TEST_CASES.md#checking) (gate
`test-cases`), the [changelog and `VERSION`](../CHANGELOG.md#date-and-version-rules)
(gate `changelog`: headings, dates, order, link references, and no `VERSION`
before a dated release, then equal to the newest; nothing is tagged or
published), the static [VBA checks](#vba-static-checks), Python/Node/JSON syntax, [relative Markdown links and their anchors](#markdown-links)
(gate `markdown-links`), the
[workflow rules](#workflow-rules) (gate `workflow-rules`),
workflow syntax/expressions with actionlint, and whitespace in all committed
content plus local staged/unstaged changes. The committed check compares HEAD
with Git's empty tree, so it works in clean and shallow CI checkouts without
fetching parent history. Untracked files must be staged to enter local checks.
Git's whitespace rules and binary-file handling apply.
Actionlint's optional ShellCheck and Pyflakes integrations are explicitly off
so local and hosted validation have the same declared dependencies. No VBA
compiler, CVA engine, numerical certification or live issue audit is implied.
Live issue triage retains its separate workflow. The Traffic history workflow
is repository analytics, not CI ([TRAFFIC.md](TRAFFIC.md)); its merge script
is tested by the Python tooling tests and the workflow by actionlint.

`test-results/integrity/` contains individual logs and a JSON report with the
actual checkout commit, dirty flag, tracked-file SHA-256 digests, tool versions,
commands and exit codes. Stage intended new files before a local run so they
are included in tracked-file checks. A dirty local run describes those files,
not an immutable clean commit. CI tests GitHub's PR merge checkout and records
the PR head separately. Evidence is uploaded even on failure, named with the
checkout SHA, run ID and attempt, and retained for 30 days. Setup failures may
prevent report creation; upload then fails rather than claiming evidence exists.
Download selected evidence before expiry if it must be retained under #11.

The stable job/check name is **Repository integrity**. It runs without path
filters on PRs targeting main/release/**, pushes to those branches, and manual
dispatch. It has contents:read only and does not receive a write token. Main and release/** rulesets require this check from GitHub Actions with strict
up-to-date enforcement, configured under #12. Release creation alone is exempt;
subsequent updates require checks. See [settings evidence](REPOSITORY_SETTINGS.md).
The controlled failing/passing exercise of #13 is recorded in
[GOVERNANCE.md](GOVERNANCE.md#demonstrated-enforcement).

## VBA static checks

Five gates apply the mechanical rules of [VBA_HOUSE_STYLE.md](VBA_HOUSE_STYLE.md)
and the placement, dependency and API rules of
[REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) to the `.bas`, `.cls` and
`.frm` files Git tracks, staged ones included. Each prints how many components
it examined. The current tree includes the two test modules delivered under
#10: `TEST_Harness.bas` and `TEST_Examples.bas`; no production CVA component
exists yet. A PASS says only that the tracked source satisfies the mechanical
rules checked by that gate, not that it compiles or runs in Excel (#11). The
valid and invalid fixtures for every rule are in `tools/test_check_vba.py`,
run by the Python tooling tests.

| Gate | Checks |
| --- | --- |
| `vba-source` | Components only in their homes (`src/core/`, `src/modules/`, `src/classes/`, `src/workbook/`, `src/forms/`, `tests/modules/`, `examples/modules/`, no subdirectories), named with their role's prefix (`CORE_`, `CVA_`, `C`, `M_`, `ThisWorkbook` or `sh`, `frm`, `TEST_`, `Example`), at most 31 characters, `VB_Name` equal to the file name and unique ignoring case; ASCII only, no byte-order mark; `Option Explicit`, and `Option Private Module` in `src/core/` and `tests/modules/`; no `Option Base`, tab, trailing white space or unclosed string literal; each form beside its `.frx`; stored with LF and checked out with CRLF; no committed workbook (`check_vba_source.py`). |
| `vba-conditionals` | Every `#If` block evaluates in each modeled host; a project `#Const`, an unknown symbol or an unbalanced block fails; a `Declare` reachable under VBA7 is `PtrSafe` (`check_vba_conditionals.py`). |
| `vba-jumps` | Every `GoTo`, `GoSub` and `Resume` target is a label of the same procedure, labels are unique per procedure and every procedure is closed, in each modeled host; a member call such as `Application.Goto` is not a jump (`check_vba_jumps.py`). |
| `vba-public-api` | Every procedure and module-level declaration states its visibility; a standard module declares no public variable and no public `Declare`; the public declarations of `src/modules/` and [PUBLIC_API.txt](PUBLIC_API.txt) match one to one with their signatures; no public name collides (`check_vba_public_api.py`). |
| `vba-dependencies` | `src/core/` and `src/classes/` name no Excel or UI global or type, use no `[...]` evaluation, no VBA file, file-metadata, registry, environment, process, form-loading or system-clock statement or function, no native `Declare`, no external object model (`Scripting` other than `Dictionary`, `ADODB`, `MSXML2` and similar) or file-system type, declared or created with `New`, no `CallByName`, `Evaluate`, `ExecuteExcel4Macro` or `AddressOf`, no `CreateObject` other than `"Scripting.Dictionary"` and no `GetObject`, and name no facade, adapter, form, test or example component; `src/core/` standard modules hold no module-level or `Static` variable and no `Static` procedure; `examples/modules/` name only the facade, not core, model classes, adapters, forms or tests (`check_vba_dependencies.py`). |

**Three different checks.** A static PASS is neither a compilation nor a
validation:

| Check | Where | What it proves |
| --- | --- | --- |
| Static checks | `python tools/check_repository.py`, locally and in CI | The source files follow the rules above |
| Compilation | Excel: **Debug > Compile VBAProject** on the [intended host](../INSTALLATION.md#host-policy) (#11) | The project compiles: names, calls, types, arguments |
| Numerical validation | The regression scaffold (#10) against fixtures defined under #8 | A rule computes the documented result |

**Modeled hosts.** `vba-conditionals`, `vba-jumps` and `vba-public-api` read
each component once per compilation environment, with the branches of every
`#If` that environment compiles: `vba7-win64`, the intended 64-bit Excel, plus
`vba7-win32` and the pre-VBA7 `vba6-win32`, so that a branch written for them
is still checked. As in VBA, `Win32` is true in all three and `VBA6` is true
under VBA7 too. The symbols are `VBA6`, `VBA7`, `Win32` and `Win64`; `Mac`,
any other symbol and a project `#Const` fail closed. `vba-dependencies` reads
every branch at once for references, so a host call in an inactive branch is
still rejected, and applies its core-state rules in each environment, so that
alternative procedure headers in exclusive branches cannot hide a
module-level declaration.

**Not checked, left to review and to compiling in Excel:**

- procedure contracts, units, `UPDATED` dates and section layout;
- names of procedures, variables, constants and enumerations, and the subject
  words of component names;
- `ByVal`, `Variant` use, indentation depth, line length and the two blank
  lines between procedures;
- the error-number range, error handling and cleanup patterns, including the
  scope of `On Error Resume Next`;
- formulas in the facade or adapters; `vba-dependencies` matches names, not
  calls, so a host object reached through a variable passed in, a qualified
  member such as `Item.Range` or a shadowed name is not resolved, and a
  constant that happens to start with a component prefix is reported.
  Tracked component names and the `CVA_`, `CORE_` and `TEST_` prefixes match
  in any case, as VBA resolves them; `M_`, `sh`, `frm` and `Example` names of
  components not yet tracked match only as the house style writes them,
  since `m_Total` is an ordinary identifier. Statements are read without
  numeric line labels, an explicit `Call` and `VBA.` library qualifiers,
  `Type` and `Enum` members as names rather than statements, and single-line
  `If ... Then ... Else ...` branches as statements of their own. Reading
  the clock (`Now`, `Date`, `Timer`) is not reported; whether core results
  may depend on it belongs to the methodology (#8);
- calls: whether a called procedure exists, is visible and gets the right
  arguments. Compiling in Excel checks direct calls.
- **Dynamic calls** outside `src/core/` and `src/classes/`: no check resolves
  a target named in a string or chosen at run time, such as
  `Application.Run`, `CallByName`, `Application.OnTime`, `Application.OnKey`,
  a control's `OnAction`, `Evaluate` or one passed with `AddressOf`. Compiling
  does not check them either, so each needs a test that runs it.
  `Option Private Module` and `Private` do not stop `Application.Run`; the
  public API inventory is a contract, not an access control.
- a comment continued with ` _` onto the next line is read as code by the
  environment-aware checks; do not continue comments.

**Source and adaptations.** The lexer and the source, conditional, jump and
public-API checks are adapted from CCR-K-SFTs, which adapted them from
K-SACCR and EXCEL-VBA-PROJECT-TEMPLATE ([NOTICE.md](../NOTICE.md)). Changed
here: the `CVA_` facade prefix and `examples/modules/` home; every
`Option Base` rejected, not only `Option Base 1`; public variables and public
`Declare` statements rejected in standard modules, so the supported kinds are
those listed in REPOSITORY_STRUCTURE.md; a `GoTo`, `GoSub` or `Resume`
after a dot read as a member call, not a jump; fixtures without SFT names. The
dependency check and its fixtures are written for this repository. The
Python quality gates use this repository's own configuration. The test-case format
checker (#10) and the changelog check (#17) were adopted later; see
[NOTICE.md](../NOTICE.md).

## Python quality gates

`pyproject.toml` configures both gates for the Python in `tools/`; the
versions come from the hash-locked [tools/requirements.txt](../tools/requirements.txt).

- **Ruff** (`python -m ruff check tools`) with an explicit rule selection, so
  a new Ruff default cannot change the gate: pycodestyle (`E`, `W`), Pyflakes
  (`F`), import order (`I`), bugbear (`B`), pyupgrade (`UP`), simplify
  (`SIM`), Ruff's own rules (`RUF`), Pylint errors and warnings (`PLE`,
  `PLW`) and the security rules (`S`). Lines may be 120 characters, the width
  the tooling is written to.
- **mypy** (`python -m mypy`) in strict mode for Python 3.12, with
  unreachable-code warnings, over every module in `tools/`.

Every exception, with its reason:

| Exception | Scope | Reason |
| --- | --- | --- |
| `S603`, `S607` | All tools | The tools run fixed argument lists (`git`, `node`, the interpreter), never a shell or a command built from input; finding `git` and `node` on `PATH` is the documented setup |
| `S101` | `tools/test_*.py` | unittest helpers may assert |
| `E501` | `tools/test_check_vba.py` | The VBA fixtures reproduce real source lines; wrapping them would change the fixture |
| `S310` (3 lines) | `check_issues.py`, `check_repository.py` | The URLs opened are the HTTPS GitHub API and the HTTPS release URL from the actionlint lock |
| `S105` (1 line) | `check_vba_conditionals.py` | A VBA expression token compared with `"("`, not a password |

Git's SHA-1 blob id in `check_excel_run.py` is computed with
`usedforsecurity=False`: it names a file, it secures nothing.

## Markdown links

**Relative links, every run.** `tools/check_links.py` (gate `markdown-links`)
reads every tracked Markdown file with markdown-it-py, a CommonMark parser
(hash-locked in [tools/requirements.txt](../tools/requirements.txt)), with
GitHub's tables and strikethrough. Code blocks, code spans, Setext headings,
reference-style links, character references and images inside links are
therefore read as GitHub reads them, not approximated with patterns. Each
relative link or image must name a file that exists. When the link has a
`#fragment` and points to Markdown, the anchor must exist there too: a heading
or an explicit `<a id="…">` or `<a name="…">`. Links to other file types are
checked for the file only.

A heading's anchor follows GitHub's slug rule, applied to the heading as
rendered:

1. The heading is rendered: code spans keep their text; links (reference-style
   ones included) and images become their text; HTML tags and emphasis markers
   are removed; character references such as `&amp;` become their character;
   the line break of a two-line Setext heading is a newline.
2. The text is lower-cased.
3. Unicode letters, marks, decimal digits, connector punctuation (such as
   `_`), `-` and spaces are kept, and every other character, a newline
   included, is dropped. An emoji is dropped, but the U+FE0F that may follow it
   is a mark and stays.
4. Each space becomes `-`.
5. A repeated slug gets `-1`, `-2` and so on, in order, skipping any slug an
   earlier heading already produced: `Foo`, `Foo`, `Foo-1` give `foo`,
   `foo-1` and `foo-1-1`.

Every anchor of the Markdown on main was compared with GitHub's own rendering
on 2026-10-31 (155 anchors, no difference); `tools/test_check_links.py` pins
the rule and its edge cases.

**External links, weekly.** The *External links* workflow
(`.github/workflows/external-links.yml`) runs `tools/check_external_links.py`
every Monday and on manual dispatch, after installing the hash-locked
`tools/requirements.txt` as Repository integrity does. It never runs on pull
requests, and it is not a required check: an outside site can be down without any change here. It
requests each http(s) URL from an inline link or image (a badge inside a link
included), an autolink or a reference definition once, HEAD and then GET if HEAD fails with an error status or a
network error, and reports:

- **broken**: a 4xx other than 401, 403 or 429, or a server or network error
  after one retry. A broken link fails the run, so it shows in the Actions
  list; fix it or explain it in a pull request;
- **unverified**: 401, 403 or 429, when the site refuses automated clients,
  and pages that need a signed-in maintainer (`SIGN_IN_REQUIRED`, currently
  the repository settings pages), which are not requested;
- passing links are counted but not listed.

## Workflow rules

`tools/check_workflows.py` parses every workflow in `.github/workflows/` as
YAML and fails when one breaks a rule. A duplicated YAML key is itself an
error, so a later key cannot silently replace an earlier one.

| Rule | Why |
| --- | --- |
| Top-level `permissions` is an explicit mapping with no write scope (`{}` or `read-all` also pass) | No job gets the default token permissions by omission |
| A job may hold a write scope only if `WRITE_ALLOWED` in the checker names that job and scope | Each write permission is reviewed where it is granted; adding one changes the checker |
| Every job sets `timeout-minutes` from 1 to 60, except one that calls a reusable workflow, which cannot | A stuck job cannot run for GitHub's default six hours |
| Every `uses:` names an action or reusable workflow at a full 40-character commit SHA | Tags and branches can move |
| Every `actions/checkout` step sets `persist-credentials: false` | The token is not left in the checkout for later steps |
| `repository-integrity.yml` runs on `pull_request` and `push` without `paths` or `paths-ignore`, its job `integrity` has no `if:` and keeps the name `Repository integrity` | The required check must report on every pull request and push it protects |

The current allowlist: `codeql.yml` job `analyze` may write `security-events`;
`labels-sync.yml` job `reconcile` may write `issues`; `traffic-history.yml`
job `collect` may write `contents`. Fixtures for every
rule are in `tools/test_check_workflows.py`.

## Code scanning

The *CodeQL* workflow (`.github/workflows/codeql.yml`) is GitHub code
scanning in **advanced setup**. GitHub's default setup must stay off: the two
cannot run together, and an enabled default setup makes this workflow's
uploads fail.

- **Triggers:** pushes and pull requests to `main` and `release/**`, and
  every Sunday.
- **Languages:** `python` (the tooling), `javascript-typescript` (the label
  scripts in `.github/scripts/`) and `actions` (the workflows), one matrix
  job each, without a build (`build-mode: none`). The VBA source is not
  scanned; CodeQL does not support VBA.
- **Queries:** `security-extended`.
- **Gate:** a first job reads the repository's visibility from the API
  (`gh api "repos/$GITHUB_REPOSITORY" --jq .visibility`), because a
  scheduled event may not carry the repository payload. The analysis runs only
  for a public repository, the case in which this plan can upload results.
- **Permissions:** only the `analyze` job holds `security-events: write`, to
  upload its results; the gate reads with `contents: read`.

Alerts appear on the repository's Security tab. CodeQL is not a required
check; triage its alerts like any other finding.

## Dependency updates

Dependabot checks GitHub Actions and the Python lock (`pip`, directory
`/tools`) weekly, targets release/0.1.0, assigns
@danielep71 and uses existing ci/P3 labels. Configuration becomes active when
present on the default branch. PRs have no milestone; create/link an issue with
the milestone when work needs tracking. There is no automatic approval, merge
or alert dismissal. Review release notes, provenance and the complete action
SHA, run integrity checks, and follow the final-head review policy.

For a Python update, check that every changed `--hash` belongs to the new
version on PyPI and that the lock still lists wheels for each supported
platform; `--only-binary=:all:` refuses a version that has none.

Runtime baselines and actionlint's checksum lock are manually reviewed updates;
Dependabot does not update that custom lock. Obtain replacement archive digests
from the official release metadata/checksums, inspect the release and update all
supported platform entries together. Actions pins remain full commit SHAs.
