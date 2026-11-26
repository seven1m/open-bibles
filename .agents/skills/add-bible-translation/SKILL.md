---
name: add-bible-translation
description: Source, license-check, convert, and validate Bible translations for open-bibles. Use when evaluating a candidate edition, adding or replacing a translation, or repairing its text, XML markup, or verse numbering.
---

# Add a Bible translation

## Identify the edition and verify redistribution rights

- Identify the exact edition or revision, language or documented dialect, and intended scope. Prefer a rights holder's release, an archive with a dated scan, or a transcription with a traceable source. Verify the contents of the actual download. A catalog labeled “whole Bible” may ship only the New Testament.
- Trace the file to the original publication or licensed release. Match a title or copyright page, release manifest, revision history, or diagnostic readings against a known copy. Mirrors that share a source count as one witness. A familiar translation name or an old first-publication date can also appear on a modern revision.
- Verify rights for the text in the file and any modern revision, notes, or other material you plan to include. For public-domain claims, record the publication evidence and the relevant jurisdiction when applicable. For libre releases, find the rights holder's grant or a distributor notice that can be traced to it. Confirm redistribution and adaptation are permitted and record attribution, change notices, and share-alike terms.
- Treat a mirror's license label as a clue. A distributor cannot relicense a copyrighted translation without authority. Record conflicting license claims, resolve them against the exact release, and leave the edition out if the right to redistribute remains unverified. Continue with any independently verified candidates.
- Record the exact download and license links. For a repository source, pin its commit or release. For a changing or ambiguous download, record its revision date or checksum.

## Convert and repair

- Use **USFX**, **OSIS**, or **Zefania XML**, with a filename that follows the README's existing conventions. Prefer an upstream export in a supported format when it preserves the edition correctly. For USFM sources, inspect `utils/u2o.py` as a possible path to OSIS and verify that it handles the source's markers.
- Keep an untouched source copy for comparison. Preserve spelling, wording, book order, verse ranges, and meaningful markup such as notes, headings, paragraph breaks, and italics. Use explicit source book, chapter, and verse identifiers during conversion. Reject unexpected structures that would otherwise drop text or turn notes into verse text.
- Correct demonstrable formatting or transcription defects such as leaked markup, merged verses, shifted labels, or stray headings in verse text. Check repairs against the original scan or another verified revision of the same translation. Record the exact reference, the evidence for the repair, and any change to numbering or text. If wording cannot be verified, document the gap.
- Make a nontrivial conversion reproducible with its pinned input and repeatable steps. Keep temporary downloads and one-off inspection output outside the commit.

## Verify the result

- Parse the XML and validate it against the applicable schema when available. Load it through [bible_parser](https://github.com/seven1m/bible_parser), the reader used by the API. Report which checks you ran and any reader limitations.
- Compare book IDs and order, chapter IDs, and verse references against the source. Use a known reference edition as an independent sanity check for the books the editions share. The repository's KJV includes Apocrypha, so compare the relevant canon and report differences by reference. Matching totals alone can hide missing, shifted, or duplicated verses.
- Inspect every unexplained reference difference. Preserve genuine versification differences and verse bridges. Distinguish notes attached to an otherwise blank verse, intentionally omitted verses, bare padding, and actual source gaps. Some readers drop notes and interpret a verse range as its first number.
- When converting, compare the verse text with the source after accounting for markup and any documented repairs. Check representative passages end to end, including boundaries, notes, significant characters, and repaired passages.

## Document the import

- Update the README's aligned translation table and add source and license details. Use the source's edition name and credit line and label the actual extent, such as New Testament or selected books.
- In the PR, link the file source and the license or public-domain evidence. Summarize conversion and repairs, counts from validation, and any remaining source limitations. Follow the repository's PR template.
