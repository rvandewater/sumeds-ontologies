"""Tests of ``scripts/build_ontology_packs.py`` on small synthetic inputs.

The LOINC fixture follows the column layout of the official LOINC Table Core
but every row is made up; no LOINC content is used.
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

try:  # The end-to-end check needs a suMEDS release with ontology rules.
    from sumeds import EnrichmentConfig, OntologyPacks, enrich_metadata
except ImportError:  # pragma: no cover - depends on the installed suMEDS
    EnrichmentConfig = OntologyPacks = enrich_metadata = None

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_ontology_packs.py"


@pytest.fixture(scope="module")
def build():
    spec = importlib.util.spec_from_file_location("build_ontology_packs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop(spec.name, None)


CORE_HEADER = [
    "LOINC_NUM",
    "COMPONENT",
    "PROPERTY",
    "TIME_ASPCT",
    "SYSTEM",
    "SCALE_TYP",
    "METHOD_TYP",
    "CLASS",
    "CLASSTYPE",
    "LONG_COMMON_NAME",
    "SHORTNAME",
    "EXTERNAL_COPYRIGHT_NOTICE",
    "STATUS",
    "VersionFirstReleased",
    "VersionLastChanged",
]
SYNTHETIC = [
    ["90001-1", "Analyte A", "MCnc", "Pt", "Bld", "Qn", "", "SYNTH", "1",
     "Synthetic analyte A, made up", "Synth A", "", "ACTIVE", "9.01", "9.02"],
    ["90002-9", "Analyte B", "MCnc", "Pt", "Bld", "Qn", "", "SYNTH", "1",
     "Synthetic analyte B, \"quoted\"", "Synth B", "", "DEPRECATED", "9.01", "9.01"],
    ["91003-6", "Analyte C", "Prid", "Pt", "Bld", "Nom", "", "SYNTH", "1",
     "Synthetic analyte C", "Synth C", "Made-up third-party notice", "ACTIVE",
     "9.01", "9.03"],
    ["1-8", "Analyte D", "Num", "Pt", "^Patient", "Qn", "", "SYNTH", "2",
     "Synthetic analyte D", "Synth D", "", "TRIAL", "9.02", "9.02"],
]  # fmt: skip


@pytest.fixture
def loinc_download(tmp_path: Path) -> Path:
    root = tmp_path / "Loinc_9.03"
    core = root / "LoincTableCore"
    core.mkdir(parents=True)
    with (core / "LoincTableCore.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        writer.writerow(CORE_HEADER)
        writer.writerows(SYNTHETIC)
    (core / "MapTo.csv").write_text(
        '"LOINC","MAP_TO","COMMENT"\n"90002-9","90001-1",""\n'
    )
    (root / "LoincLicense_0.0.txt").write_text("Synthetic license text for tests.\n")
    return root


def test_loinc_pack_keeps_fields_and_license(
    build, loinc_download: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(build, "COMPRESS_ABOVE_BYTES", 10)
    output = tmp_path / "ontologies"
    crosswalk = output / "crosswalks" / "demo"
    crosswalk.mkdir(parents=True)
    (crosswalk / "labs.csv").write_text(
        "itemid,loinc_code,source\n1,90001-1,x\n2,90002-9,y\n3,99999-9,z\n"
    )
    monkeypatch.setattr(
        build,
        "CROSSWALKS",
        {
            "demo": {
                "labs": {
                    "key_column": "itemid",
                    "code_column": "loinc_code",
                    "vocabulary": "LOINC",
                }
            }
        },
    )
    assert (
        build.main(
            [
                "--output",
                str(output),
                "loinc",
                "--loinc-table",
                str(loinc_download / "LoincTableCore" / "LoincTableCore.csv"),
                "--loinc-release-date",
                "2099-01-01",
                "--loinc-archive",
                "Loinc_9.03.zip",
                "1 MB",
                "0" * 32,
            ]
        )
        == 0
    )
    pack = output / "LOINC" / "9.03"
    manifest = json.loads((pack / "manifest.json").read_text())
    assert manifest["release"] == "9.03" and manifest["compression"] == "gzip"
    assert manifest["excluded_external_copyright"] == 1
    assert manifest["status_counts"] == {"ACTIVE": 1, "DEPRECATED": 1, "TRIAL": 1}
    assert manifest["fields"]["code"] == "LOINC_NUM"
    assert manifest["sources"][0]["md5"] == "0" * 32
    assert (
        pack / "LoincLicense_0.0.txt"
    ).read_text() == "Synthetic license text for tests.\n"
    assert (pack / "MapTo.csv").read_bytes() == (
        loinc_download / "LoincTableCore" / "MapTo.csv"
    ).read_bytes()
    assert "Regenstrief Institute" in (pack / "LOINC_short_license.txt").read_text()
    rows = {}
    for shard in manifest["shards"].values():
        assert shard["file"].endswith(".csv.gz")
        text = gzip.decompress((pack / shard["file"]).read_bytes()).decode()
        for row in csv.DictReader(io.StringIO(text, newline="")):
            rows[row["LOINC_NUM"]] = row
    assert set(rows) == {"90001-1", "90002-9", "1-8"}
    source = {row[0]: dict(zip(CORE_HEADER, row)) for row in SYNTHETIC}
    for code, row in rows.items():
        assert list(row) == list(manifest["columns"])
        assert all(row[name] == source[code][name] for name in row)

    names = list(csv.DictReader((crosswalk / "labs.csv").open(encoding="utf-8")))
    assert [row["loinc_long_common_name"] for row in names] == [
        "Synthetic analyte A, made up",
        'Synthetic analyte B, "quoted"',
        "",
    ]
    table = json.loads((crosswalk / "manifest.json").read_text())["tables"]["labs"]
    assert table["loinc_check"] == {
        "found": 1,
        "deprecated": ["90002-9"],
        "missing": ["99999-9"],
    }
    assert (crosswalk / "LOINC_short_license.txt").is_file()

    # The built pack validates LOINC codes and supplies LONG_COMMON_NAME.
    if enrich_metadata is None:
        pytest.skip("suMEDS with ontology rules is not installed")
    rules = {
        "schema": "sumeds-rules/0.1",
        "crosswalk": [
            {
                "id": "labs",
                "pattern": "^LAB//(?P<key>[0-9]+)$",
                "table": "demo/labs",
                "key_column": "itemid",
                "code_column": "loinc_code",
                "vocabulary": "LOINC",
                "validate": "pack",
            }
        ],
    }
    import polars as pl

    result = enrich_metadata(
        pl.LazyFrame({"code": ["LAB//1", "LAB//3"], "description": [None, None]}),
        EnrichmentConfig(rules=rules, ontology_source=str(output)),
    ).collect()
    assert result["description"].to_list() == ["Synthetic analyte A, made up", None]
    assert OntologyPacks(str(output)).lookup("LOINC", ["1-8"])["1-8"].ancestors == ()


def test_loinc_target_requires_a_table(build, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        build.main(["--output", str(tmp_path), "LOINC"])
    with pytest.raises(SystemExit):
        build.main(["--output", str(tmp_path), "SNOMED"])


def test_order_files_and_truncation(build) -> None:
    lines = [
        f"{'00001':5} {'I50':7} 0 {'Heart failure':60} Heart failure",
        f"{'00002':5} {'I5023':7} 1 {'Acute on chr systolic hrt fail':60} "
        "Acute on chronic  systolic (congestive) heart failure",
    ]
    rows = build.order_rows("\n".join(lines))
    assert rows == [
        ("I50", "0", "Heart failure"),
        ("I5023", "1", "Acute on chronic systolic (congestive) heart failure"),
    ]
    assert build.dotted("I5023", 3) == "I50.23"
    assert build.dotted("E8889", 4) == "E888.9"
    codes = {"I50", "I50.23", "E888", "E888.9"}
    assert build.truncation_parent("I50.23", codes) == "I50"
    assert build.truncation_parent("I50", codes) == ""
    assert build.truncation_parent("E888.9", codes) == "E888"


def test_pcs_tables_and_rtf_tabular(build) -> None:
    xml = b"""<ICD10PCS.tabular><pcsTable>
      <axis pos="1" values="1"><title>Section</title><label code="0">Medical and Surgical</label></axis>
      <axis pos="2" values="1"><title>Body System</title><label code="D">Gastrointestinal System</label></axis>
      <axis pos="3" values="1"><title>Operation</title><label code="T">Resection</label></axis>
      <pcsRow codes="2">
        <axis pos="4" values="1"><title>Body Part</title><label code="J">Appendix</label></axis>
        <axis pos="5" values="2"><title>Approach</title><label code="0">Open</label><label code="4">Percutaneous Endoscopic</label></axis>
        <axis pos="6" values="1"><title>Device</title><label code="Z">No Device</label></axis>
        <axis pos="7" values="1"><title>Qualifier</title><label code="Z">No Qualifier</label></axis>
      </pcsRow></pcsTable></ICD10PCS.tabular>"""
    labels = build.pcs_labels(xml)
    assert labels == {
        "0": "Medical and Surgical",
        "0D": "Gastrointestinal System",
        "0DT": "Resection",
        "0DTJ": "Appendix",
        "0DTJ0": "Open",
        "0DTJ0Z": "No Device",
        "0DTJ4": "Percutaneous Endoscopic",
        "0DTJ4Z": "No Device",
    }
    rtf = (
        r"{\rtf1\ansi{\fonttbl{\f0 Times;}}"
        r"\par {\*\bkmkstart 401}{\*\bkmkend 401}401\tab Essential hypertension"
        r"\par 401.9\tab Unspecified\par 001-139\tab Infectious\par V58.61\tab Long-term"
        r" (current) use of anticoagulants\par E888.9\tab Fall\'e9 }"
    )
    entries = build.tabular_entries(
        rtf.encode("cp1252"), r"(?:\d{3}|V\d{2})(?:\.\d{1,2})?|E\d{3}(?:\.\d)?"
    )
    assert entries == {
        "401": "Essential hypertension",
        "401.9": "Unspecified",
        "V58.61": "Long-term (current) use of anticoagulants",
        "E888.9": "Fallé",
    }
