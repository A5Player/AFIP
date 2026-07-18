import json
from pathlib import Path
import pytest

from afip.data_catalog import CentralDataCatalog, DatasetRecord


def record(**overrides):
    data = {
        "dataset_id": "market-gold-h1",
        "name": "Gold H1",
        "category": "MARKET_DATA",
        "schema_version": "1.0.0",
        "storage_path": "data/market/gold/h1",
        "owner": "AFIP",
        "producer": "collector",
        "classification": "RESEARCH",
        "lifecycle_status": "ACTIVE",
        "retention_policy": "KEEP_RAW_FOREVER",
        "lineage_parents": (),
        "guides": ("docs/market.md",),
        "tags": ("gold", "h1"),
    }
    data.update(overrides)
    return DatasetRecord(**data)


def test_policy_has_no_execution_authority():
    catalog = CentralDataCatalog()
    assert catalog.policy.get("execution_authority", "NONE") == "NONE"


def test_rejects_execution_authority():
    with pytest.raises(ValueError):
        CentralDataCatalog({"execution_authority": "LIVE"})


def test_register_and_get():
    catalog = CentralDataCatalog()
    item = record()
    catalog.register(item)
    assert catalog.get(item.dataset_id) == item


def test_duplicate_registration_rejected():
    catalog = CentralDataCatalog()
    catalog.register(record())
    with pytest.raises(ValueError):
        catalog.register(record())


def test_explicit_replace_allowed():
    catalog = CentralDataCatalog()
    catalog.register(record())
    catalog.register(record(name="Updated"), replace=True)
    assert catalog.get("market-gold-h1").name == "Updated"


def test_storage_must_be_under_data():
    validation = CentralDataCatalog().validate_record(record(storage_path="runtime/temp"))
    assert validation.status == "INVALID"


def test_missing_guides_is_warning():
    validation = CentralDataCatalog().validate_record(record(guides=()))
    assert validation.status == "WARNING"


def test_filtering_is_deterministic():
    catalog = CentralDataCatalog()
    catalog.register(record(dataset_id="b", tags=("x",)))
    catalog.register(record(dataset_id="a", tags=("x",)))
    assert [x.dataset_id for x in catalog.list_records(tag="x")] == ["a", "b"]


def test_discover_dataset_info(tmp_path):
    root = tmp_path / "data"
    ds = root / "knowledge" / "sample"
    ds.mkdir(parents=True)
    (ds / "dataset_info.json").write_text(json.dumps({
        "dataset_id": "sample",
        "schema_version": "1.0.0",
        "producer": "test",
        "data_classification": "RESEARCH",
    }), encoding="utf-8")
    found = CentralDataCatalog().discover_dataset_info(root)
    assert found[0].storage_path == "data/knowledge/sample"


def test_invalid_dataset_info_is_skipped(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    (root / "dataset_info.json").write_text("{bad", encoding="utf-8")
    assert CentralDataCatalog().discover_dataset_info(root) == ()


def test_lineage_missing_parent_warns():
    catalog = CentralDataCatalog()
    catalog.register(record(lineage_parents=("missing",)))
    validation = catalog.validate_lineage()
    assert validation.status == "WARNING"


def test_snapshot_id_is_deterministic():
    catalog = CentralDataCatalog()
    catalog.register(record())
    a = catalog.build_snapshot()
    b = catalog.build_snapshot()
    assert a["catalog_id"] == b["catalog_id"]


def test_module_contains_no_broker_or_order_calls():
    source = Path("afip/data_catalog/runtime.py").read_text(encoding="utf-8").lower()
    forbidden = ("metatrader5", "order_send(", "order_check(", "mt5.", "broker.login")
    assert not any(token in source for token in forbidden)
