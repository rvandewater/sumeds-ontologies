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
| `v0.2.0` | reads the LOINC hierarchy | LOINC 2.83 multiaxial hierarchy (ComponentHierarchyBySystem) for the pack's terms; ICD-9 procedure headers 84.8 and 92.4, which the v0.1.0 builder missed; all other files unchanged |

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
| `LOINC` | 2.83 | LOINC Table Core, the matching `MapTo.csv` rows and the ComponentHierarchyBySystem rows of the pack's terms, from loinc.org | [LOINC license](ontologies/LOINC/2.83/LoincLicense_5.8.txt), notice below |

The ICD-10-CM and ICD-9-CM files are not public-domain works as a whole. CDC/NCHS and
CMS publish all ICD files at no cost and without a license agreement, and they are
redistributed here unchanged. ICD-10-CM and ICD-9-CM are U.S. clinical modifications of
WHO classifications: WHO owns and publishes ICD-10 and authorized NCHS to develop
ICD-10-CM ([CDC](https://www.cdc.gov/nchs/icd/icd-10-cm/index.html)), so content taken
from ICD-10 or ICD-9 remains WHO's copyright. ICD-10-PCS was developed for CMS and
contains no WHO content. Each manifest's `license` field records what the publisher
states.

Every crosswalk table records its origin, sources and their licenses in its
manifest and per row; [References](#references) gives BibTeX for each source.

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

## Hierarchies, and why not from an Athena download

suMEDS adds parent codes from the packs: ICD codes get every shorter code of
the same vocabulary present in the pack, LOINC terms every LOINC Part on their
paths in the official multiaxial hierarchy. Both are built from the
publishers' files, not from an OHDSI Athena download, although Athena holds
the same hierarchies:

- Athena repackages each vocabulary under that vocabulary's own license, so an
  Athena download gives no extra redistribution rights. OHDSI's own content
  (OMOP vocabularies, concept ids) is Apache-2.0, but the hierarchies datasets
  need belong to the source vocabularies.
- ICD: the pack parents equal Athena's `Is a` relationships for every current
  ICD-10-CM and ICD-9-CM code, and Athena's `CONCEPT_ANCESTOR` has none for
  these non-standard vocabularies. Building from CMS and CDC/NCHS also keeps
  the packs current: the Athena release of 27 February 2026 had ICD-10-CM
  FY2026 and LOINC 2.80.
- LOINC: the license allows LOINC Parts and Part hierarchies to be used only as
  presented in the LOINC distribution (Section 5) and requires every Part
  number to carry its Part name (Section 10.3). The pack therefore keeps the
  official `ComponentHierarchyBySystem` rows unchanged, not Athena's derived
  relationships and names.
- SNOMED CT, CPT4, ATC, WHO ICD-10 and ICD-O-3 hierarchies may not be
  redistributed at all; suMEDS reads them from the user's own Athena download.

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

The hierarchy is read from
`AccessoryFiles/ComponentHierarchyBySystem/ComponentHierarchyBySystem.csv` of
the same download (`--loinc-hierarchy` to override).

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

## References

Cite the sources of a crosswalk table when you use it. Each manifest records the
exact files and commits; per row, the `source` columns say which source a
mapping came from.

| Table | Sources (BibTeX keys below) |
|---|---|
| `eicu/lab_loinc` | WeavEHR mappings `brauckmann2025weavehr`; mimic-code `d_labitems_to_loinc.csv` `johnson2018mimiccode`; eicu-code `eicucode`; eICU-CRD `pollard2018eicu` |
| `hirid/observation_loinc` | HiRID-ICU-Benchmark `varref.tsv` `yeche2021hiridbenchmark`; HiRID `faltys2021hirid`, `hyland2020circulatory` |
| `nwicu/loinc_parents` | WeavEHR NWICU and MIMIC-IV mappings `brauckmann2025weavehr`; mimic-code `johnson2018mimiccode`; MIMIC-IV `johnson2023mimiciv`; NWICU `moukheiber2024nwicu` |
| `zigong/nursing_vitals_loinc` | HL7 FHIR R4 vital-signs profile `hl7fhirr4vitals`; Zigong database `xu2022zigongdata`, `xu2022critical` |
| every table | LOINC `mcdonald2003loinc`; PhysioNet, for the PhysioNet datasets `goldberger2000physionet` |

```bibtex
@software{brauckmann2025weavehr,
  author  = {Brauckmann, Paul and Laser, Tobias and Rockenschaub, Patrick and Porschen, Christian},
  title   = {{WeavEHR}},
  version = {0.0.1},
  year    = {2025},
  url     = {https://github.com/aidh-ms/WeavEHR},
  note    = {MIT license; mappings used at commit 210a539}
}

@article{johnson2018mimiccode,
  author  = {Johnson, Alistair E. W. and Stone, David J. and Celi, Leo A. and Pollard, Tom J.},
  title   = {The {MIMIC} Code Repository: enabling reproducibility in critical care research},
  journal = {Journal of the American Medical Informatics Association},
  volume  = {25},
  number  = {1},
  pages   = {32--39},
  year    = {2018},
  doi     = {10.1093/jamia/ocx084},
  note    = {Repository MIT-LCP/mimic-code (MIT license), v2.4.0, commit 570ef01}
}

@misc{eicucode,
  title        = {{eicu-code}},
  howpublished = {\url{https://github.com/MIT-LCP/eicu-code}},
  note         = {MIT Laboratory for Computational Physiology; MIT license}
}

@article{pollard2018eicu,
  author  = {Pollard, Tom J. and Johnson, Alistair E. W. and Raffa, Jesse D. and Celi, Leo A. and Mark, Roger G. and Badawi, Omar},
  title   = {The {eICU} Collaborative Research Database, a freely available multi-center database for critical care research},
  journal = {Scientific Data},
  volume  = {5},
  pages   = {180178},
  year    = {2018},
  doi     = {10.1038/sdata.2018.178}
}

@misc{yeche2021hiridbenchmark,
  author        = {Y{\`e}che, Hugo and Kuznetsova, Rita and Zimmermann, Marc and H{\"u}ser, Matthias and Lyu, Xinrui and Faltys, Martin and R{\"a}tsch, Gunnar},
  title         = {{HiRID-ICU-Benchmark} -- A Comprehensive Machine Learning Benchmark on High-resolution {ICU} Data},
  year          = {2021},
  eprint        = {2111.08536},
  archivePrefix = {arXiv},
  doi           = {10.48550/arXiv.2111.08536},
  note          = {Repository ratschlab/HIRID-ICU-Benchmark (MIT license), varref.tsv at commit bee7700}
}

@misc{faltys2021hirid,
  author    = {Faltys, Martin and Zimmermann, Marc and Lyu, Xinrui and H{\"u}ser, Matthias and Hyland, Stephanie and R{\"a}tsch, Gunnar and Merz, Tobias},
  title     = {{HiRID}, a high time-resolution {ICU} dataset (version 1.1.1)},
  publisher = {PhysioNet},
  year      = {2021},
  doi       = {10.13026/nkwc-js72}
}

@article{hyland2020circulatory,
  author  = {Hyland, Stephanie L. and Faltys, Martin and H{\"u}ser, Matthias and Lyu, Xinrui and Gumbsch, Thomas and Esteban, Crist{\'o}bal and Bock, Christian and Horn, Max and Moor, Michael and Rieck, Bastian and Zimmermann, Marc and Bodenham, Dean and Borgwardt, Karsten and R{\"a}tsch, Gunnar and Merz, Tobias M.},
  title   = {Early prediction of circulatory failure in the intensive care unit using machine learning},
  journal = {Nature Medicine},
  volume  = {26},
  number  = {3},
  pages   = {364--373},
  year    = {2020},
  doi     = {10.1038/s41591-020-0789-4}
}

@article{johnson2023mimiciv,
  author  = {Johnson, Alistair E. W. and Bulgarelli, Lucas and Shen, Lu and Gayles, Alvin and Shammout, Ayad and Horng, Steven and Pollard, Tom J. and Hao, Sicheng and Moody, Benjamin and Gow, Brian and Lehman, Li-wei H. and Celi, Leo A. and Mark, Roger G.},
  title   = {{MIMIC-IV}, a freely accessible electronic health record dataset},
  journal = {Scientific Data},
  volume  = {10},
  pages   = {1},
  year    = {2023},
  doi     = {10.1038/s41597-022-01899-x}
}

@misc{moukheiber2024nwicu,
  author    = {Moukheiber, Dana and Temps, William and Molgi, Bhadrappa and Li, Yikuan and Lu, Alice and Nannapaneni, Prasanth and Chahin, Abdulrahman and Hao, Sicheng and {Torres Fabregas}, Felipe and Celi, Leo Anthony and Wong, Adrian and Lloyd, Maxwell and {Borrat Frigola}, Xavier and Lee, Hyung-Chul and Schneider, Daniel and Pollard, Tom and Luo, Yuan and Kho, Abel and Mark, Roger},
  title     = {Northwestern {ICU} ({NWICU}) database (version 0.1.0)},
  publisher = {PhysioNet},
  year      = {2024},
  doi       = {10.13026/s84w-1829}
}

@misc{xu2022zigongdata,
  author    = {Xu, Ping and Chen, Lin and Zhang, Zhongheng},
  title     = {Critical care database comprising patients with infection at {Zigong Fourth People's Hospital} (version 1.1)},
  publisher = {PhysioNet},
  year      = {2022},
  doi       = {10.13026/xpt9-z726}
}

@article{xu2022critical,
  author  = {Xu, Ping and Chen, Lin and Zhu, Yuanfang and Yu, Shuai and Chen, Rangui and Huang, Wenbin and Wu, Fuli and Zhang, Zhongheng},
  title   = {Critical Care Database Comprising Patients With Infection},
  journal = {Frontiers in Public Health},
  volume  = {10},
  pages   = {852410},
  year    = {2022},
  doi     = {10.3389/fpubh.2022.852410}
}

@misc{hl7fhirr4vitals,
  author       = {{HL7 International}},
  title        = {{FHIR} Release 4 (v4.0.1): Observation Vital Signs profile},
  year         = {2019},
  howpublished = {\url{https://hl7.org/fhir/R4/observation-vitalsigns.html}},
  note         = {CC0}
}

@article{mcdonald2003loinc,
  author  = {McDonald, Clement J. and Huff, Stanley M. and Suico, Jeffrey G. and Hill, Gilbert and Leavelle, Dennis and Aller, Raymond and Forrey, Arden and Mercer, Kathy and DeMoor, Georges and Hook, John and Williams, Warren and Case, James and Maloney, Pat},
  title   = {{LOINC}, a universal standard for identifying laboratory observations: a 5-year update},
  journal = {Clinical Chemistry},
  volume  = {49},
  number  = {4},
  pages   = {624--633},
  year    = {2003},
  doi     = {10.1373/49.4.624}
}

@article{goldberger2000physionet,
  author  = {Goldberger, Ary L. and Amaral, Luis A. N. and Glass, Leon and Hausdorff, Jeffrey M. and Ivanov, Plamen Ch. and Mark, Roger G. and Mietus, Joseph E. and Moody, George B. and Peng, Chung-Kang and Stanley, H. Eugene},
  title   = {{PhysioBank}, {PhysioToolkit}, and {PhysioNet}: Components of a New Research Resource for Complex Physiologic Signals},
  journal = {Circulation},
  volume  = {101},
  number  = {23},
  pages   = {e215--e220},
  year    = {2000},
  doi     = {10.1161/01.CIR.101.23.e215}
}
```

The ICD packs cite their publishers' files (CDC/NCHS, CMS) by URL and sha256 in
each manifest's `sources`.

## Licenses

The builder script and tests are MIT licensed ([LICENSE](LICENSE)). The data
keep the license of their source, as listed above and in each manifest.

This material contains content from LOINC (http://loinc.org). LOINC is
copyright © Regenstrief Institute, Inc. and the Logical Observation Identifiers
Names and Codes (LOINC) Committee and is available at no cost under the license
at http://loinc.org/license. LOINC® is a registered United States trademark of
Regenstrief Institute, Inc.
