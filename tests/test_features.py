import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.features import (
    jw,
    pincode_match,
    dob_delta_days,
    feature_row,
    phone_match,
    email_match,
    govid_match,
)


def test_pincode_match():
    assert pincode_match('560001', '560001') == 1.0
    assert pincode_match('560001', '560002') == 0.5
    assert pincode_match('560001', '560101') == 0.0


def test_dob_delta_days():
    assert dob_delta_days('1990-01-01', '1990-01-01') == 0
    assert dob_delta_days('1990-01-01', '1990-01-03') == 2
    assert dob_delta_days(None, '1990-01-03') == 9999.0


def test_exact_match_wrappers():
    assert phone_match('123', '123') == 1.0
    assert phone_match('123', '456') == 0.0
    assert email_match('a@b', 'a@b') == 1.0
    assert govid_match('PAN', 'PAN') == 1.0


def test_jw_similarity():
    assert jw('Alice', 'alice') == 1.0
    assert jw(None, 'alice') == 0.0


def test_feature_row_length_and_values():
    q = {
        'full_name': 'Alice Doe',
        'dob': '1990-01-01',
        'phone_e164': '+911234567890',
        'email_norm': 'alice@example.com',
        'gov_id_norm': 'PAN123',
        'addr_line': '123 Main St',
        'city': 'Bangalore',
        'state': 'KA',
        'postal_code': '560001',
    }
    c = {
        'full_name': 'Alice Doe',
        'dob': '1990-01-01',
        'phone_e164': '+911234567890',
        'email_norm': 'alice@example.com',
        'gov_id_norm': 'PAN123',
        'addr_line': '123 Main St',
        'city': 'Bangalore',
        'state': 'KA',
        'postal_code': '560001',
    }
    feats = feature_row(q, c, 0.0)
    assert len(feats) == 10
    assert feats[-2] == 1.0  # pincode match
    assert feats[-1] == 0.0  # dob delta
