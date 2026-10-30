# suMEDS ontology packs and crosswalks

This folder is the static repository that `suMEDS` enrichment fetches from
(`https://raw.githubusercontent.com/rvandewater/sumeds-ontologies/<tag>/ontologies`,
where each suMEDS release pins one release tag and the sha256 of its
`index.json`). A run downloads `index.json`, the manifest of each vocabulary
its rules need, and only the shards that hold the matched codes and their
ancestors. Every file is
checked against the sha256 in its manifest (and every manifest against
`index.json`) and cached under `${XDG_CACHE_HOME:-~/.cache}/sumeds/ontologies/`.

| Pack | Release | Rows | Shards | Size | Source | License |
|---|---|---:|---:|---:|---|---|
| `ICD10CM` | `fy2016-fy2027` | 99,085 | 26 (first character) | 9.7 MB CSV | CDC/NCHS ICD-10-CM order files FY2016 to FY2027 and the April 1, 2023 update | Public domain (U.S. Government work) |
| `ICD10PCS` | `fy2016-fy2027` | 197,789 | 136 (first two characters) | 13.0 MB CSV | CMS ICD-10-PCS order files and code tables FY2016 to FY2027, April 1, 2025 and 2026 updates | Public domain (U.S. Government work) |
| `ICD9CM` | `v32` | 17,541 | 12 (first character) | 1.2 MB CSV | CMS ICD-9-CM v32 (final) long descriptions; NCHS FY2012 tabular list for headers | Public domain (U.S. Government work) |
| `ICD9Proc` | `v32` | 4,648 | 10 (first character) | 0.25 MB CSV | as ICD9CM, procedure files | Public domain (U.S. Government work) |
| `LOINC` | `2.83` | 105,050 | 99 (first two characters) | 2.9 MB gzip (17.1 MB CSV) | LOINC 2.83 (2026-08-19) LOINC Table Core, `MapTo.csv` | LOINC license, see [`LOINC/2.83/LoincLicense_5.8.txt`](LOINC/2.83/LoincLicense_5.8.txt) |

The exact download URLs, fiscal years and sha256 of every input are recorded in
each `manifest.json` (`sources`).

## Pack format (`sumeds-ontology-pack/0.1`)

- `<VOCAB>/<release>/manifest.json`: `vocabulary` (OMOP `vocabulary_id`),
  `release`, `columns`, `fields` (which columns hold the code, description, and
  parent), `shard_key_length`, `shards` (`file`, `rows`, `bytes`, `sha256`;
  gzip shards also `csv_bytes`, `csv_sha256`), `sources`, `license`, `build`.
- Shards are CSV files (`<key>.csv`, or `<key>.csv.gz` when `compression` is
  `gzip`) holding every code whose first `shard_key_length` characters are the
  key. A parent is always a prefix of its child, so a code's ancestors sit in
  the shards of its own prefixes.
- Codes use the OMOP `concept_code` format: ICD-10-CM and ICD-9 with dots
  (`I50.23`, `401.9`, `E888.9`, `39.61`), ICD-10-PCS without (`0DTJ4ZZ`).
- ICD packs have the columns `code, description, parent, first_year,
  last_year`. `parent` is the nearest shorter truncation present in the pack
  (3-character ICD-10-CM categories, ICD-9 categories before the dot, and PCS
  sections are roots). `first_year`/`last_year` are the first and last fiscal
  year whose release contains the code, so retired codes still resolve; they
  are empty for the single final ICD-9 release. Descriptions come from the
  latest release containing the code.
- ICD-10-PCS also contains every 1- to 6-character prefix of a valid code (OMOP
  has hierarchy concepts for partial codes). A prefix row stores only its own
  axis label from the PCS tables; suMEDS joins the labels root first with
  ` @ ` (`description_path` in the manifest), e.g. `0DTJ4` = `Medical and
  Surgical @ Gastrointestinal System @ Resection @ Appendix @ Percutaneous
  Endoscopic`. This keeps the pack under 15 MB.
- The LOINC pack is a subset of the official LOINC Table Core with the original
  field names and unchanged contents: `LOINC_NUM, COMPONENT, PROPERTY,
  TIME_ASPCT, SYSTEM, SCALE_TYP, METHOD_TYP, CLASS, LONG_COMMON_NAME, SHORTNAME,
  STATUS, VersionLastChanged`. All statuses are kept (ACTIVE 92,435, TRIAL
  5,432, DISCOURAGED 2,212, DEPRECATED 4,971), so older dataset codes still
  validate; the 7,355 records with an `EXTERNAL_COPYRIGHT_NOTICE` are excluded.
  `MapTo.csv` (deprecated code to replacement) is copied unchanged beside it.
  As the plain CSV exceeds 15 MB, its shards are stored gzip-compressed.

## Rebuilding

```bash
# Public-domain packs: downloads the pinned CMS/CDC files, verifies their sha256.
python3 scripts/build_ontology_packs.py --output ontologies ICD10CM ICD10PCS ICD9CM ICD9Proc
# LOINC, from the official download (needs a free loinc.org account):
python3 scripts/build_ontology_packs.py --output ontologies LOINC \
  --loinc-table Loinc_2.83/LoincTableCore/LoincTableCore.csv \
  --loinc-release-date 2026-08-19 \
  --loinc-archive Loinc_2.83.zip "88.52 MB" 057ddf203164705d5a4c3604257060a4
# Crosswalk manifests (also refreshed by the LOINC target):
python3 scripts/build_ontology_packs.py --output ontologies crosswalks
```

Rebuilds are deterministic: the same inputs give byte-identical shards.

## Governance

- Only public-domain vocabularies and vocabularies whose license allows
  redistribution are hosted here. ICD-10-CM, ICD-10-PCS and ICD-9-CM are U.S.
  Government works. LOINC is redistributed under its license (below).
- Licensed vocabularies that may not be redistributed (SNOMED CT, CPT4, WHO
  ICD-10, ICD-10-CN, ICD-O-3, ATC, and others) are never copied here. Rules
  validate them against the user's own OHDSI Athena download
  (`validate: athena`) or only tag codes (`validate: none`).
- **LOINC maintenance contract.** suMEDS is the single maintained copy of LOINC
  content for the MEDS ETLs. Its maintainers rebuild the LOINC pack from the
  official download for each LOINC release (twice a year) and record the
  release, its date, and the checksums of the archive and extracted files in
  the manifest. Users fetch the pack and never need a LOINC account. Every copy
  carries the full license and the notice below.

## LOINC notice

This material contains content from LOINC (http://loinc.org). LOINC is
copyright © Regenstrief Institute, Inc. and the Logical Observation Identifiers
Names and Codes (LOINC) Committee and is available at no cost under the license
at http://loinc.org/license. LOINC® is a registered United States trademark of
Regenstrief Institute, Inc.

The full license is [`LOINC/2.83/LoincLicense_5.8.txt`](LOINC/2.83/LoincLicense_5.8.txt).
