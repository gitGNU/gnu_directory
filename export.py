
import re
import sys

import pandas as pd

class Template(object):
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def __str__(self):
        return '{{%s\n%s\n}}' % (
            self.name,
            '\n'.join(['|' + '%s=%s' % (n, v) for (n, v) in self.values]))

def export(pkgs, cps, cpf, name):
    pkg_cps = cps[cps['Upstream-Name'] == name]
    srcpkg_names = list(pkg_cps['_srcpkg'])
    print srcpkg_names
    binpkgs = pd.concat([
        pkgs[pkgs['Source'] == srcpkg]
        for srcpkg in srcpkg_names])
    print list(binpkgs['Package'])
    homepages = list(binpkgs['Homepage'])
    # XXX: maybe choose the one that appears the most?
    homepage = homepages[0] if homepages else ''

    print Template('Entry', [
        ('Name', srcpkg),
        ('Short description', ''),
        ('Full description', ''),
        ('Homepage', homepage),
        ('User level', ''),
        # XXX get this information from apt-file
        ('Component programs', ''),
        ('VCS checkout command', ''),
        ('Computer languages', ''),
        ('Status', ''),
        ('Is GNU', 'No')])

    print Template('Project license', [
        ('License', ''),
        ('License note', '')])

    print Template('Person', [
        ('Real name', ''),
        ('Role', ''),
        ('Email', ''),
        ('Resource URL', '')])

    print Template('Resource', [
        ('Resource kind', ''),
        ('Resource URL', '')])

    #print Template('Software category', [
    #    ('Resource kind', ''),
    #    ('Resource URL', '')])

def main():
    pkg_store = pd.HDFStore('pkg.h5')
    pkgs = pkg_store['packages']
    pkg_store.close()

    cp_store = pd.HDFStore('cp.h5')
    cpf = cp_store['cp_files']
    cps = cp_store['cp_summary']
    cp_store.close()

    args = sys.argv[1:]

    if len(args) == 0:
        srcps = sorted(set(pkgs['Source']))

        for pkgname in srcps[:100]:
            export(pkgs, cps, cpf, pkgname)
    elif len(args) == 1:
        export(pkgs, cps, cpf, args[0])
    else:
        raise RuntimeError()

if __name__ == '__main__':
    main()

