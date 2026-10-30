# sumeds-ontologies

Versioned ontology packs and dataset crosswalk tables for
[suMEDS](https://github.com/rvandewater/SumMEDS) metadata enrichment of MEDS
datasets. suMEDS fetches only the shards a dataset needs, verifies every file
against sha256 checksums, and caches it, so MEDS ETLs no longer copy
vocabulary tables into their own repositories.

This repository holds data only. Rules that say which dataset codes belong to
which vocabulary live in each ETL (`sumeds-rules/0.1` files); the enrichment
code lives in suMEDS.

## Releases and pinning

- Every release is an immutable git tag `vX.Y.Z`. A published tag is never
  moved or rewritten.
- Each suMEDS release pins one tag **and** the sha256 of that tag's
  `ontologies/index.json`. The index pins every manifest and each manifest every
  shard, so a default suMEDS run is reproducible byte for byte; a moved tag
  would fail with a checksum error instead of silently changing results.
- Bump the minor version when a vocabulary release or crosswalk is added or
  updated, the patch version for documentation-only changes, and the major
  version for a format change (`sumeds-ontologies/*`, `sumeds-ontology-pack/*`
  or `sumeds-crosswalk/*` schema).

| Release | suMEDS | Contents |
|---|---|---|
| `v0.1.0` | first release with ontology rules | ICD-10-CM and ICD-10-PCS FY2016 to FY2027, ICD-9-CM and ICD-9 procedures v32, LOINC 2.83, crosswalks for eICU, HiRID, NWICU and Zigong |

## Contents

See [`ontologies/README.md`](ontologies/README.md) for the pack format, row
counts, sizes, shard layout and the exact source files, and
[`ontologies/crosswalks/README.md`](ontologies/crosswalks/README.md) for the
crosswalk tables.

| Pack | Release | Source | License |
|---|---|---|---|
| `ICD10CM` | FY2016 to FY2027 | CDC/NCHS order files | No license agreement; adapts WHO's ICD-10, which WHO owns (see below) |
| `ICD10PCS` | FY2016 to FY2027 | CMS order files and code tables | No license agreement; developed for CMS, available for public use, no WHO content |
| `ICD9CM`, `ICD9Proc` | v32 (final) | CMS v32 descriptions, NCHS FY2012 tabular list | No license agreement; adapts WHO's ICD-9 (see below) |
| `LOINC` | 2.83 | LOINC Table Core and the matching `MapTo.csv` rows from loinc.org | [LOINC license](ontologies/LOINC/2.83/LoincLicense_5.8.txt), notice below |

The ICD-10-CM and ICD-9-CM files are not public-domain works as a whole. CDC/NCHS and
CMS publish all ICD files at no cost and without a license agreement, and they are
redistributed here unchanged. ICD-10-CM and ICD-9-CM are U.S. clinical modifications of
WHO classifications: WHO owns and publishes ICD-10 and authorized NCHS to develop
ICD-10-CM ([CDC](https://www.cdc.gov/nchs/icd/icd-10-cm/index.html)), so content taken
from ICD-10 or ICD-9 remains WHO's copyright. ICD-10-PCS was developed for CMS and
contains no WHO content. Each manifest's `license` field records what the publisher
states.

Every crosswalk table records its origin, sources and their licenses in its
manifest and per row.

## What may be added

Only content whose license allows public redistribution, with the source and
license recorded in the manifest:

- vocabularies that their publisher distributes at no cost and without a license
  agreement, built from the publisher's own files with pinned sha256 checksums, with
  any third-party copyright (such as WHO's in ICD-10-CM) stated in the manifest;
- vocabularies under a license that permits redistribution, with every notice
  the license requires (as for LOINC);
- crosswalk tables derived only from public, permissively licensed sources.

Never add licensed vocabularies that may not be redistributed, such as SNOMED
CT, CPT4, WHO ICD-10 in English, ICD-O-3 or ATC, and never add content derived
from credentialed EHR data. suMEDS rules validate such vocabularies against the
user's own OHDSI Athena download (`validate: athena`) or only tag them
(`validate: none`).

## Rebuilding from the official sources

The ICD packs are built from the official CMS and CDC/NCHS files,
downloaded once and verified against the sha256 pinned in the builder. Rebuilds
are deterministic: the same inputs give byte-identical shards. Anyone who
prefers not to trust this repository can rebuild the packs and point suMEDS at
the local copy:

```bash
python3 scripts/build_ontology_packs.py --output ontologies ICD10CM ICD10PCS ICD9CM ICD9Proc
git diff --exit-code ontologies          # empty: identical to the release
suMEDS-enrich codes.parquet -o enriched.parquet --rules rules.yaml \
  --ontology-source ./ontologies
```

The ICD sources total about 205 MB; the packs suMEDS fetches by default are a
few shards of a few hundred KB. LOINC cannot be downloaded automatically
(loinc.org requires a free account), so its maintainers rebuild it from the
official download:

```bash
python3 scripts/build_ontology_packs.py --output ontologies LOINC \
  --loinc-table Loinc_2.83/LoincTableCore/LoincTableCore.csv \
  --loinc-release-date 2026-08-19 \
  --loinc-archive Loinc_2.83.zip "88.52 MB" 057ddf203164705d5a4c3604257060a4
```

The `verify-sources` workflow repeats the ICD rebuild on every
release tag and fails if any byte differs.

## Maintenance

- ICD-10-CM and ICD-10-PCS: add each fiscal year's files (published in
  summer, effective October 1) and the April updates.
- LOINC: rebuild for each LOINC release (twice a year). This repository is the
  single maintained copy of LOINC content for the MEDS ETLs, so users never
  need a LOINC account.
- After a release, update `DEFAULT_REF` and `DEFAULT_INDEX_SHA256` in suMEDS
  (`src/sumeds/ontology.py`).

## Licenses

The builder script and tests are MIT licensed ([LICENSE](LICENSE)). The data
keep the license of their source, as listed above and in each manifest.

This material contains content from LOINC (http://loinc.org). LOINC is
copyright © Regenstrief Institute, Inc. and the Logical Observation Identifiers
Names and Codes (LOINC) Committee and is available at no cost under the license
at http://loinc.org/license. LOINC® is a registered United States trademark of
Regenstrief Institute, Inc.
