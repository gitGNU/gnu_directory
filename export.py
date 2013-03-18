
import re
import sys

import numpy
import pandas as pd

def concat(xss):
    all = []

    for xs in xss:
        all.extend(xs)

    return all

class Template(object):
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def __str__(self):
        return '{{%s\n%s\n}}' % (
            self.name,
            '\n'.join(['|' + '%s=%s' % (n, v) for (n, v) in self.values]))

def parse_tags(s):
    return s.replace('\n', '').split(', ')

def extract_languages(tags):
    langs = []

    for tag in tags:
        (a, b) = tag.split('::')

        if a == 'implemented-in':
            langs.append(b)
        elif a == 'devel' and b.startswith('lang:'):
            langs.append(b.split(':')[1])

    return list(set(langs))

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
    tags = set(concat(
        [parse_tags(t) for t in binpkgs['Tag'] if not pd.isnull(t)]))
    print tags
    langs = [s.title() for s in extract_languages(tags)]
    print langs

    print Template('Entry', [
        ('Name', srcpkg),
        ('Short description', ''),
        ('Full description', ''),
        ('Homepage', homepage),
        ('User level', ''),
        # XXX get this information from apt-file
        ('Component programs', ''),
        ('VCS checkout command', ''),
        ('Computer languages', ', '.join(langs)),
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

