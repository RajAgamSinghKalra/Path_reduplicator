import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.normalization import norm_email, norm_postal_code, canonical_identity_text


def test_norm_email_gmail_plus_dot():
    assert norm_email('Foo.Bar+spam@gmail.com') == 'foobar@gmail.com'


def test_norm_email_other_provider():
    assert norm_email('User+spam@example.com') == 'user+spam@example.com'


def test_norm_postal_code_validation():
    assert norm_postal_code('560001') == '560001'
    assert norm_postal_code('560 001') == '560001'
    assert norm_postal_code('056000') == ''
    assert norm_postal_code('56000A') == ''


def test_canonical_identity_text_normalises_postal_code():
    t1 = canonical_identity_text('Alice', None, None, None, None, None, None, None, '560 001', 'IN')
    t2 = canonical_identity_text('Alice', None, None, None, None, None, None, None, '560001', 'IN')
    assert t1 == t2
