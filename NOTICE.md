# Licensing and provenance

Copyright 2026 Daniele Penza and contributors.

## License decision

The maintainer selected **MPL-2.0** for MKT-K-CVA on 2026-10-24 in issue #4's
implementation discussion. Code, documentation, workflows and configuration
are covered by [LICENSE](LICENSE), unless a separate notice states otherwise.
Repository visibility remains private; this change does not publish the project.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

## Imported files

The PR #1 imports below came from
[CCR-K-SFTs at 3b7aaf09ae16d9ca60ad7b4dedd6ee9461c451af](https://github.com/danielep71/CCR-K-SFTs/tree/3b7aaf09ae16d9ca60ad7b4dedd6ee9461c451af).
Its [LICENSE](https://github.com/danielep71/CCR-K-SFTs/blob/3b7aaf09ae16d9ca60ad7b4dedd6ee9461c451af/LICENSE)
and [NOTICE.md](https://github.com/danielep71/CCR-K-SFTs/blob/3b7aaf09ae16d9ca60ad7b4dedd6ee9461c451af/NOTICE.md)
record MPL-2.0 and Copyright 2026 Daniele Penza and contributors.
The table compares source blobs with local baseline
`20cb34ebd101564bbe973b047dc648aa98793b51`; subsequent edits remain in Git history.

| Local file | Source blob | Local adaptation |
| --- | --- | --- |
| `.github/ISSUE_TEMPLATE/bug.yml` | `ca7047bd1601be618b6629035f7d1572f4191f42` | Repository name, synthetic-data warning without the then-unavailable security link, and generic validation command. |
| `.github/ISSUE_TEMPLATE/config.yml` | `02923b4b84f29994dcf32797e62e9f542eba415e` | Repository-specific governance link; security link deferred until policy exists. |
| `.github/ISSUE_TEMPLATE/documentation.yml` | `3c365964f947271a5941c380e54c04d337cda20c` | Default-branch wording, local documentation path and generic validation command. |
| `.github/ISSUE_TEMPLATE/enhancement.yml` | `6230c99253975c5b51db5e6d74fb7152a1fc3cef` | Byte-identical at the audited baseline. |
| `.github/label-policy.json` | `9a01bf04667b70450cd1478e97aa750104d6e2fa` | Byte-identical at the audited baseline. |
| `.github/labels.json` | `ddc870f6e876664045581d1394fcc7f06f3d9b04` | Byte-identical at the audited baseline. |
| `.github/scripts/labels-drift.mjs` | `0b63699d11e3fbcb74d3f001bc3b80e15dd71a24` | Byte-identical at the audited baseline. |
| `.github/scripts/labels-sync.mjs` | `9eea86137a937f163a54b259772acb4b6919ee7b` | Byte-identical at the audited baseline. |
| `.github/workflows/issue-triage.yml` | `c42b10b29aeea934b04a199adfa3625f108ef9cb` | Documentation pointer changed to ISSUE_LABELS.md. |
| `.github/workflows/labels-drift.yml` | `23d2162b63d295863338a1843d804ad6e1fade32` | Byte-identical at the audited baseline. |
| `.github/workflows/labels-sync.yml` | `4029f5e63a5cb9531736c351daabf31323468f35` | Byte-identical at the audited baseline. |
| `tools/check_issues.py` | `bfc773248d135a58a37e2e1ef9f8ab9cc0175cbd` | Repository default and documentation pointers changed. |
| `tools/test_check_issues.py` | `31556737b8efc7901faef0c4d2a8b6dfd8fe9b17` | Repository identifier changed. |

The upstream notice traces the label catalogue and issue forms to K-SACCR
revision `7397382a638817b1f8bf47348205de7a1928cb78` (catalogue) and
`00bb72d1bf5ec9252b8ca5ba3adc567d948be15d` (forms/scripts);
label sync workflow to `f4b4e0f6026236885050eb00ed564ce382fc7836`;
drift workflow to `6d1f11301e12bb8512b41596f59bd42287e92773`.
Preserve that upstream attribution as well as the immediate SFTs source.

## Documentation design references

- docs/ISSUE_LABELS.md was written locally to describe the imported catalogue
  and workflows; PR #21 added governance and dependency-closure links.
- docs/GOVERNANCE.md was written using SFTs governance at
  `c13e1167e779ab1816db9d8c81e140abddbf6c66`,
  blob `bab2ca28c0e48cda98a58698003bbad65de1c9e4`.
  Rules and controls were adapted to MKT-K-CVA. SFTs attributes the process
  structure to K-Risk-Engines `8942d070c80097762534ad6fb09e9c38b101da83`.
- docs/REPOSITORY_STRUCTURE.md and docs/PUBLIC_API.txt use the architecture
  and inventory conventions of SFTs source blob
  `7f0efeb4295330a7061c661fbada828950fae220`. CVA scope, decision register and
  directory guides were written locally. SFTs attributes its architecture
  structure to K-SACCR `00bb72d1bf5ec9252b8ca5ba3adc567d948be15d`.
- SECURITY.md uses the reporting-policy organization of SFTs, with local scope
  and actual/pending controls. Its source security-policy blob is
  `82a02d24d456c2a15bae53ecfb84d44f8dd88977`; the reporting address was independently
  confirmed by the maintainer for this repository.
- LICENSE is the unchanged MPL-2.0 text, source blob
  `d0a1fa1482eea82e19510e7920cbe3a03e41f691`.

No SFT formulas, regulatory decisions or tested-host claims are imported.

## Future imports and external material

Record source URL, immutable commit or blob, file paths, applicable license,
copyright notices and local changes in the same PR as every import.
Preserve source notices; flag unclear permissions before importing.
Runtime tools and GitHub Actions retain their own licenses and are not
relicensed by this notice. Action revisions are pinned in workflow files.
No third-party tool source is vendored by this change.

Regulatory texts, market data and other third-party material keep their own
terms. Do not treat this project's license as permission to copy them.
Record source-specific permissions in the methodology source register (#8).
Use synthetic fixtures only; see [SECURITY.md](SECURITY.md).

## Source-control and VBA conventions (#5)

Adapted from CCR-K-SFTs under its MPL-2.0 notice (Copyright 2026 Daniele Penza
and contributors). Immutable source blobs read on 2026-10-24:

| Source path | Source blob | Local changes |
| --- | --- | --- |
| `.editorconfig` | `796627a20faf1abc607a080fc2092ee31da54fd3` | Reduced to local scope; preserved source/evidence, no workbook exception, retained archive controls. |
| `.gitattributes` | `7db14cc639696dd108955f8a0c896b20226a0449` | Reduced to local scope; preserved source/evidence, no workbook exception, retained archive controls. |
| `.gitignore` | `b2e5e7a8bb04b0c3ccfdb0b2ae5fdf0c1a027365` | Reduced to local scope; preserved source/evidence, no workbook exception, retained archive controls. |
| `docs/VBA_HOUSE_STYLE.md` | `70fedf63cc19c4c55466d02bf918bb4f9e63745c` | Rewritten for CVA; local issue links, untested host status, explicit outcome/cleanup and import/export contracts. |
| `INSTALLATION.md` | `07467f7d20bea9e7fe025875fb87ca0c92335974` | Rewritten for CVA; local issue links, untested host status, explicit outcome/cleanup and import/export contracts. |

Source repository: https://github.com/danielep71/CCR-K-SFTs . Its upstream
conventions trace to K-SACCR revision `00bb72d1bf5ec9252b8ca5ba3adc567d948be15d`
as recorded in the original provenance notice. No SFT formula, workbook or
host-test claim was imported.

## Repository CI (#6)

The integrity runner, workflow, checksum lock and drift CLI regression tests
were written locally, as were the integrity runner's whitespace tests in
tools/test_check_repository.py (#37). The imported label reconciler now has an
import-safe CLI guard; drift comparison uses its structured plan instead of
parsing Markdown. The original source attribution above remains applicable.

Actionlint 1.7.12 is downloaded from the official rhysd/actionlint release;
platform archive SHA-256 digests are recorded in tools/actionlint-lock.json
from GitHub release metadata checked on 2026-10-24. It retains its upstream
MIT license; no binary or source is vendored. Existing action pins are retained.
actions/setup-node was first pinned to a v6 commit resolved on the same date;
PR #34 updated every use to the v7.1.0 commit
`949feb2413d6458794dcd2491c4babbbce0c15c1`.

## VBA static checks (#9)

Adapted from CCR-K-SFTs under its MPL-2.0 notice (Copyright 2026 Daniele Penza
and contributors), read at commit `dc293037111816ec1c9768a4aa890919892ebcef`
on 2026-10-24:

| Local file | Source blob | Local changes |
| --- | --- | --- |
| `tools/vba_lexer.py` | `f7c765bed0e937ff9eb9b457d957d1f7ecde0f2a` | Documentation pointers. |
| `tools/check_vba_source.py` | `ca9be39e521d6a62ff87a450bb4c202773d78fae` | `CVA_` facade prefix; every `Option Base` rejected; documentation pointers. |
| `tools/check_vba_conditionals.py` | `2e150008b51f162b0707907e403c310b70efaa53` | Each colon-separated statement checked for a `Declare` without `PtrSafe` (#56); documentation pointers. |
| `tools/check_vba_jumps.py` | `07974e1f78b9269014c876b2c9b04c8cbe4fbd2f` | Documentation pointers. |
| `tools/check_vba_public_api.py` | `8637f6190c3dcbf5459ba48761081783c36f9e94` | Public variables and public `Declare` rejected in standard modules; documentation pointers. |
| `tools/test_check_vba.py` | `8a6f9f3e9131f4295a836d72f4a696739e3c6dc7` | Fixtures renamed without SFT names; fixtures for the changed rules and for the dependency check. |

CCR-K-SFTs adapted its checks from K-SACCR at
`00bb72d1bf5ec9252b8ca5ba3adc567d948be15d`, which took the jump,
conditional-compilation and public-API checks from EXCEL-VBA-PROJECT-TEMPLATE
at `b903fe44ef6a032c4689870b83745afa1c22490d`; preserve that attribution.
`tools/check_vba_dependencies.py` and its fixtures were written locally. No
SFT formula, module name, fixture value or regulatory decision is imported.
