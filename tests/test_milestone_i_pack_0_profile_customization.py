from pathlib import Path
from afip.profile_customization import ProfileCustomizationRuntime
from afip.dashboard_ui import DashboardUIRuntime


def test_custom_name_and_preset_preview(tmp_path):
    r=ProfileCustomizationRuntime(tmp_path/'profiles.json').preview({'profile_name':'My Gold Plan','base_profile':'CONSERVATIVE'})
    assert r.status=='READY' and r.profile.profile_name=='My Gold Plan' and r.profile.maximum_units==1


def test_save_and_version_history(tmp_path):
    rt=ProfileCustomizationRuntime(tmp_path/'profiles.json')
    a=rt.save({'profile_id':'gold','profile_name':'Gold','base_profile':'BALANCED'})
    b=rt.save({**a.profile.as_dict(),'maximum_units':3})
    assert b.profile.version==2 and len(rt.repository.history('gold'))==1


def test_duplicate_activate_archive_and_account_assignment(tmp_path):
    rt=ProfileCustomizationRuntime(tmp_path/'profiles.json')
    rt.save({'profile_id':'base','profile_name':'Base','base_profile':'CONSERVATIVE'})
    copy=rt.duplicate('base','Night Gold')
    assigned=rt.assign_account(copy.profile.profile_id,'XM-123')
    active=rt.activate(assigned.profile.profile_id)
    archived=rt.archive(active.profile.profile_id)
    assert assigned.profile.assigned_account_id=='XM-123' and active.profile.active and archived.profile.archived and not archived.profile.active


def test_profile_remains_separate_from_account_and_mt5(tmp_path):
    p=ProfileCustomizationRuntime(tmp_path/'profiles.json').preview({'profile_name':'Separate'}).profile.as_dict()
    assert p['profile_is_account'] is False and p['profile_is_mt5'] is False and p['unit_lot_size']==0.01


def test_validation_blocks_unsafe_configuration(tmp_path):
    r=ProfileCustomizationRuntime(tmp_path/'profiles.json').preview({'profile_name':'X','maximum_units':10,'capital_per_unit':0})
    assert r.status=='REVIEW' and len(r.validation_items)>=2


def test_dashboard_contains_bilingual_profile_customization(tmp_path):
    html=DashboardUIRuntime().render_html({'broker':'XM','symbol':'GOLD#','mode':'PAPER','profile_name':'Custom Gold','profile_storage_path':str(tmp_path/'profiles.json')})
    assert 'Profile Customization' in html and 'การปรับแต่งโปรไฟล์' in html and 'Custom Gold' in html
