# Crosswalk tables

Dataset-specific tables that map a part of a MEDS code (an item id, a lab name,
a literal code) to a vocabulary code. `crosswalk` rules in a
`sumeds-rules/0.1` file read them by `table: <dataset>/<name>`, which is
`crosswalks/<dataset>/<name>.csv` here. They are fetched, verified against the
sha256 in `crosswalks/<dataset>/manifest.json` (`sumeds-crosswalk/0.1`), and
cached exactly like pack shards, so ETL repositories no longer need to ship
them.

| Table | Key column | Rows | Vocabulary | Built from | Suggested pattern |
|---|---|---:|---|---|---|
| `eicu/lab_loinc` | `labname` | 50 | LOINC | WeavEHR (MIT) + mimic-code `d_labitems_to_loinc.csv` (MIT) + eicu-code (MIT), from eICU_MEDS `code-descriptions` | `^LAB//RESULT//(?P<key>.+?)//` |
| `hirid/observation_loinc` | `variable_name` (or `variableid`) | 82 | LOINC | exact LOINC name matches of HiRID variable names (HiRID variable sheet, HIRID-ICU-Benchmark `varref.tsv`, MIT), from HIRID_MEDS `metadata-descriptions`; names from `varref.tsv` | `^OBSERVATION//(?P<key>.+?)//` |
| `nwicu/loinc_parents` | `itemid` | 50 | LOINC | WeavEHR (MIT) to MIMIC-IV to mimic-code (MIT) bridge, from NWICU_MEDS `metadata-descriptions` | `^LAB//(?P<key>[0-9]+)//` |
| `zigong/nursing_vitals_loinc` | `code` | 6 | LOINC | HL7 FHIR R4 vital-signs profile (CC0) | `^(?P<key>NURSING//[A-Z_]+)$` |

Each manifest records the origin (repository, branch, commit, path), the
sources and license of every table, and every row keeps its own `source`
columns. All 188 LOINC codes in these tables are present and not DEPRECATED in
LOINC 2.83 (`loinc_check` in the manifests).

Notes:

- `eicu/lab_loinc`: eICU codes are `LAB//RESULT//{labname}//{unit}`. Use the
  lazy pattern, which stops at the first `//`. It is exact for every lab name
  of the full eICU-CRD 2.0 release, because no name contains `//` or ends in
  `/`. Do not cut at the last `//` instead: some units start with `/`, so
  those codes would yield the name plus a trailing `/` and miss the table.
- `hirid/observation_loinc`: HiRID MEDS codes are
  `OBSERVATION//{variable name ?? variableid}//{unit}`. `variable_name` is the
  `description` of the non-pharma rows of the public HIRID-ICU-Benchmark
  `varref.tsv` (commit bee7700, MIT; source per row in `variable_name_source`);
  all 82 ids have one. Key one rule on `variable_name` with
  `^OBSERVATION//(?P<key>.+?)//` (names contain `/` but never `//`) and,
  for the id fallback, a second rule on `variableid` with
  `^OBSERVATION//(?P<key>[0-9]+)//`.

## Format

- One CSV per table, any columns; the rule names its `key_column` and
  `code_column` and may filter with `where: {column: value}`.
- A table with LOINC codes has a `loinc_long_common_name` column holding the
  LOINC `LONG_COMMON_NAME` verbatim, as LOINC Section 10 requires extracted
  codes to carry one unmodified LOINC display name. It is filled at build time
  from the suMEDS LOINC pack built from the official LOINC Table (never from
  Athena, whose names can be truncated):
  `python3 scripts/build_ontology_packs.py --output ontologies crosswalks`.

## LOINC notice

This material contains content from LOINC (http://loinc.org). LOINC is
copyright © Regenstrief Institute, Inc. and the Logical Observation Identifiers
Names and Codes (LOINC) Committee and is available at no cost under the license
at http://loinc.org/license. LOINC® is a registered United States trademark of
Regenstrief Institute, Inc.

The notice is also in `LOINC_short_license.txt` beside each table and in each
manifest (`notice`). The full license is
[`../LOINC/2.83/LoincLicense_5.8.txt`](../LOINC/2.83/LoincLicense_5.8.txt).
suMEDS maintainers rebuild the LOINC pack, and with it these name columns, for
each LOINC release; users fetch them and never need a LOINC account.
