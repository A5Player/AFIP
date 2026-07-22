from afip.dashboard_ui.authority_snapshot import enrich_profiles

def test_config_policy_enrichment(tmp_path):
    cfg=tmp_path/'config'; cfg.mkdir()
    (cfg/'four_profile_demo.json').write_text('{"profiles":[{"profile_id":"P3","capital_per_unit":200,"maximum_units":3,"lot_per_unit":0.01,"sizing_authority":"CAPITAL_TIER_TABLE"}]}', encoding='utf-8')
    rows=enrich_profiles([{"profile_id":"P3"}], tmp_path)
    assert rows[0]["capital_per_unit"] == 200
    assert rows[0]["maximum_units"] == 3
    assert rows[0]["lot_per_unit"] == 0.01
    assert rows[0]["sizing_authority"] == "CAPITAL_TIER_TABLE"
