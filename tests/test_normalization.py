import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.normalization import norm_email


def test_norm_email_gmail_plus_dot():
    assert norm_email('Foo.Bar+spam@gmail.com') == 'foobar@gmail.com'


def test_norm_email_other_provider():
    assert norm_email('User+spam@example.com') == 'user+spam@example.com'
