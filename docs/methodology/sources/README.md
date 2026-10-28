# Regulatory sources

Copies of the texts K-CVA's methodology relies on, so that a citation and
its formula can be checked against the exact version that was read. The
[source register](../README.md#source-register) says what each text is used
for and how far it was read. Selected texts only: a registered source is
copied when a rule or a scope decision relies on it, and only the parts
needed.

These are documentation copies, not the authentic texts. The authentic EU
texts are those published in the Official Journal of the European Union.

**Do not edit or reformat these files**, and never replace one: their hashes
are registered below, and a changed byte breaks the record. A newer version
is added as a new file next to the old one, with its own row.
`.gitattributes` keeps them out of line-ending normalization.

## Files

| File | Source ID | Document | Version | Retrieved from | Retrieved | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `CRR_575-2013_consolidated_2026-06-26_extract_Art162_TitleVI.pdf` | `CRR` | Regulation (EU) No 575/2013, consolidated text: page 1, pages 243 to 246 (Article 162) and pages 580 to 616 (Part Three, Title VI, Articles 381 to 386, to the start of Part Four), 42 pages | 26.06.2026, version 021.001 | <https://publications.europa.eu/resource/celex/02013R0575-20260626> (PDF/A-2a manifestation) | 2026-10-24 | `10488f8083c126faa940a4eb8c1a89600a8fe61dbc701fd70378c9583da2d715` |

Page numbers cited for the CRR are those printed on its pages (for example
*02013R0575 — EN — 26.06.2026 — 021.001 — 611*), not the position in the
extract.

`CRR3` (Regulation (EU) 2024/1623) is registered but not copied: it was read
for its date of application and the list of its points amending Title VI,
whose consolidated result is in the `CRR` copy. It was retrieved as XHTML from
<https://publications.europa.eu/resource/celex/32024R1623> on 2026-10-24
(SHA-256 `22715503986fac39f70062c737ad60181358a002f17c36ef5297601dd783dff8`).

## How the copy was made

- The full consolidated text was retrieved as PDF/A-2a from the Publications
  Office: 895 pages, SHA-256
  `6796302ed4213bcba4d4b9b17dc48aefcaf7ef586b875c30c8c71a7689288ecf`.
  EUR-Lex itself could not be reached from the environment used.
- Page 1, pages 243 to 246 and pages 580 to 616 were cut from it with
  pypdf 6.17.0, which copies pages without changing their content.
- Checked: the text of every page (`pdftotext -layout`) equals the same page
  of the full file; pages 611 to 614 rendered at 50 dpi differ from the full
  file only in anti-aliasing (at most 16 of 255 grey levels), and the
  formulas of Article 384, which are images absent from the text layer, are
  present on pages 611, 612 and 615.
- The consolidated text dated 1 January 2027 (version 022.001, 900 pages,
  SHA-256 `ce1ae96a5c437a56026584bb1271f63160725c60c08a43f993e84976ad12cbca`)
  was compared for Title VI: after removing soft hyphens and joining lines
  its text equals the registered version's apart from hyphenation and line
  breaks. It is not copied or registered.

To check the file against its hash, from the repository root:

```sh
python -c "import glob,hashlib;[print(hashlib.sha256(open(f,'rb').read()).hexdigest(),f) for f in sorted(glob.glob('docs/methodology/sources/*')) if not f.endswith('README.md')]"
```

## Terms of use

The copies are not covered by the repository's MPL-2.0 licence; each stays
under its publisher's terms.

| Publisher | Terms | Checked |
| --- | --- | --- |
| European Union (Publications Office) | Commission Decision 2011/833/EU on the reuse of Commission documents: documents published by the Commission or by the Publications Office on its behalf are available for commercial or non-commercial reuse without charge (Article 4), under conditions that may include acknowledging the source and not distorting the original meaning (Article 6) | Articles 1, 2, 4 and 6 read on 2026-10-24 from <https://publications.europa.eu/resource/celex/32011D0833> |

At registration on 2026-10-24, the repository was private and non-commercial,
and making it public needed these terms checked again. It is public (verified
on 2026-10-28), and the check was made on 2026-10-28 for #108: Articles 2, 4
and 6 of Decision 2011/833/EU were read again from
<https://publications.europa.eu/resource/celex/32011D0833> (XHTML, SHA-256
`2d5bc877b9a5aad948af21c680aca1d3409f41df5dd0dcc57ef9b1b225f60982`).
Article 4 makes documents available for commercial or non-commercial reuse,
without charge and without an individual application. The conditions Article 6
lists are acknowledging the source, not distorting the original meaning and
the Commission's non-liability. The copy is an unedited extract of
a text the Publications Office published (Article 2(1)(a)), with its source,
version and retrieval recorded above, so public distribution is within those
terms. This is the project's reading of the terms, not legal advice.
