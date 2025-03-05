from alai.extension import Package, find_package


def test_find_package():
    pkg  = find_package('pacman')
    assert isinstance(pkg, Package)
    assert pkg.name == 'pacman'
    assert len(pkg.depends) == 12
