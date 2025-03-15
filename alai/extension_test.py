import pytest

try:
    from alai.extension import Package, find_package
except ImportError:
    HAS_EXTENSION = False
else:
    HAS_EXTENSION = True


@pytest.mark.skipif(not HAS_EXTENSION, reason='no extension')
def test_find_package():
    pkg = find_package('pacman')
    assert isinstance(pkg, Package)
    assert pkg.name == 'pacman'
    assert len(pkg.depends) == 12
