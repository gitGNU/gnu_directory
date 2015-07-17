#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import itertools
import json
import os
import re
import sys
import textwrap

import pandas as pd

import license

# Package fields which refer to download locations.
download_keys = """
    Origin
    Original-Source
    Source
    Source-Code
    X-Origin
    X-Original-Package
    X-Source
    """

def concat(xss):
    all = []

    for xs in xss:
        all.extend(xs)

    return all

def indent(s):
    return ''.join(
            '  %s\n' % line if line else '\n'
            for line in s.splitlines())

def today():
    return datetime.datetime.now().strftime('%Y-%m-%d')

def warn(*x):
    for s in ('warning:',) + x + ('\n',):
        print >>sys.stderr, s,

class ExportFailure(Exception):
    pass

class PkgData(object):
    def __init__(self):
        pkg_store = pd.HDFStore('pkg.h5')
        self.pkgs = pkg_store['packages']
        self.descs = pkg_store['descriptions']
        self.srcs = pkg_store['sources']
        pkg_store.close()

        cp_store = pd.HDFStore('cp.h5')
        self.cpf = cp_store['cp_files']
        self.cps = cp_store['cp_summary']
        self.licenses = cp_store['licenses']
        cp_store.close()

        cl_store = pd.HDFStore('cl.h5')
        self.cl = cl_store['cl_versions']
        cl_store.close()

def nouni(s):
    return s.encode('utf8') if isinstance(s, unicode) else s

class Template(object):
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def __str__(self):
        return '{{%s\n%s\n}}' % (
            nouni(self.name),
            '\n'.join(['|' + '%s=%s' %
                (nouni(n), nouni(v))
                for (n, v) in self.values]))

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

def catechise(s):
    heresies = ["open source", "debian", "(?<!gnu/)linux", "creative commons"]
    pattern = '\\b(%s)\\b' % '|'.join([h.replace(' ', '.') for h in heresies])
    return re.sub(pattern,
        lambda m: '??%s??' % m.group(1).replace('\n', ' '),
        s,
        re.DOTALL | re.IGNORECASE)

def munge_description(s):
    paras = s.split('\n .\n')
    return '\n\n'.join(
        textwrap.fill(para.lstrip().replace('\n', ''), 65)
        for para in paras)

def get_license_map():
    map = {}

    for para in file('license_map').read().split('\n\n'):
        if not para:
            continue

        match = re.match('\[([^\]]+)\]', para)
        assert match, para
        canonical = match.group(1)
        aliases = para[match.end():].lstrip().splitlines()

        for alias in aliases:
            map[alias] = canonical

    return map

def srcpkg_extract_licenses(header, filess, licenses, cl_date, cl_uploader):
    # XXX: generate template from header stanza
    # XXX: flag CC licenses
    # XXX: check all License stanzas were included
    # XXX: exclude licenses for Files: debian/*
    lmap = get_license_map()
    by_name = dict([
        (s['_license'],
            s['License'].split('\n', 1)[1]
            if '\n' in s['License']
            else s['License'])
        for (_idx, s) in licenses.iterrows()])

    for (_ix, files) in filess.iterrows():
        ldesc = files['_license'].strip()
        ltext = files['License']

        if '\n' in ltext:
            # Looks like license text is included directly.
            ltext = munge_description(ltext)
            txt = 'License: %s\n\n%s' % (ldesc, ltext)
        elif ldesc in by_name:
            # License information is a stub. Try to find the corresponding
            # text(s).

            ltext = munge_description(by_name[ldesc])
            txt = 'License: %s\n\n%s' % (ldesc, ltext)
        else:
            parsed = license.parse_licenses(ldesc)
            lnames = list(parsed.flatten())
            missing = set(lnames) - set(by_name.keys())

            if missing:
                raise ExportFailure(
                    'missing license text: ' + ', '.join(missing))

            ltext = '\n'.join('%s:\n\n%s' %
                    (lname, indent(munge_description(by_name[lname])))
                for lname in lnames)
            txt = 'License: %s\n\n%s' % (parsed, ltext)

        canon = lmap.get(ldesc.lower(), 'Other')
        # XXX: Should maybe bail if there's no copyright field.
        cp = ''.join(
            u'© %s\n' % line.lstrip()
            for line in files.dropna().get('Copyright', '').splitlines())
        cp = cp.encode('utf8')
        txt = txt.encode('utf8')

        yield Template('Project license', [
            ('License', canon),
            ('License copyright', cp),
            ('License verified by', 'Debian: %s' % cl_uploader),
            ('License verified date', cl_date),
            ('License note', txt)])

def parse_person(s):
    match = re.match('([^<]+)\s+<([^>]+)>', s)

    if match:
        return (match.group(1), match.group(2))
    else:
        return (s, '')

def extract_people(df):
    # XXX: extract contributors, maintainers
    df = df.dropna()

    if 'Upstream-Contact' in df:
        (name, email) = parse_person(df['Upstream-Contact'])
        yield Template('Person', [
            ('Real name', name),
            ('Role', 'contact'),
            ('Email', email),
            ('Resource URL', '')])

def extract_resources(cp_header):
    cp_header = cp_header.dropna()

    for key in re.findall('\S+', download_keys):
        if key in cp_header:
            yield Template('Resource', [
                ('Resource kind', 'Download'),
                ('Resource URL', cp_header[key])])

def export_srcpkgs(data, name, srcpkg_names):
    """Export a package by reference to its constituent source packages.

    This coordinates all the information that goes into a particular page.
    """

    # Map source package names to binary packages, and also make note
    # of which versions of those source packages we're looking at.
    binpkgs = pd.concat([
        data.pkgs[data.pkgs['_srcpkg'] == srcpkg]
        for srcpkg in srcpkg_names])
    versions = {}

    srcfiles=""
    for srcpkg in srcpkg_names:
        srcfile = data.srcs[data.srcs['_srcpkg'] == srcpkg]['srcfile'].values[0]
        letter = srcfile[0]
        if srcfile[:3] == 'lib':
            letter = srcfile[:4]
        srcfile = 'http://ftp.debian.org/debian/pool/main/%s/%s/%s' % (letter,srcpkg,srcfile)
        srcfiles = srcfiles + srcfile + " "

    for (_i, pkg) in binpkgs.iterrows():
        versions[pkg['_srcpkg']] = pkg['Version']

    if len(binpkgs) == 0:
        warn('no binary packages found for', srcpkg_names)
        return

    binpkg_names = sorted(binpkgs['Package'], key=len)
    homepages = list(binpkgs['Homepage'])
    # XXX: maybe choose the one that appears the most?
    homepage = homepages[0] if homepages else ''
    tags = set(concat(
        [parse_tags(t) for t in binpkgs['Tag'] if not pd.isnull(t)]))
    langs = [s.title() for s in extract_languages(tags)]

    if name in binpkg_names:
        descpkg = name
    else:
        # Heuristic: choose the package with the shortest name.
        # We could try to do something smarter, like look for the common
        # prefix of the descriptions of all the binary packages.
        descpkg = binpkg_names[0]
    try:
        desc = list(data.descs[
            data.descs['Package'] == descpkg]['Description-en'])[0]
        (short_desc, full_desc) = desc.split('\n', 1)
    except:
        full_desc = ''
        short_desc = ''
    full_desc = catechise(munge_description(full_desc))

    yield Template('Entry', [
        ('Name', name.capitalize()),
        ('Short description', short_desc),
        ('Full description', full_desc),
        ('Homepage URL', homepage),
        ('User level', ''),
        # XXX get this information from apt-file
        ('Component programs', ''),
        ('VCS checkout command', ''),
        ('Computer languages', ', '.join(langs)),
        ('Status', ''),
        ('Is GNU', 'No'),
        ('Version identifier', pkg['Version']),
        ('Version download', srcfiles),
        ('Submitted by', 'Debian import'),
        ('Submitted date', today())])

    yield Template('Import', [
        ('Source', 'Debian'),
        ('Source link',
            'http://packages.debian.org/sid/' + srcpkg_names[0]),
        ('Source packages',
             ', '.join('%s %s' % (k, v) for (k, v) in versions.iteritems())),
        ('Date', today())])

    people = []
    res = []

    for srcpkg in srcpkg_names:
        pkg_cps = data.cps[data.cps['_srcpkg'] == srcpkg].ix[0]
        pkg_cpf = data.cpf[data.cpf['_srcpkg'] == srcpkg]
        pkg_licenses = data.licenses[data.licenses['_srcpkg'] == srcpkg]
        people.extend(list(extract_people(pkg_cps)))
        res.extend(list(extract_resources(pkg_cps)))

        pkg_cl = data.cl[data.cl['_srcpkg'] == srcpkg]
        cl_date = pkg_cl['date'][0]
        cl_uploader = pkg_cl['author'][0]
        for template in srcpkg_extract_licenses(
                pkg_cps, pkg_cpf, pkg_licenses, cl_date, cl_uploader):
            # XXX: eliminate duplicates
            yield template

    for template in people:
        # XXX: eliminate duplicates
        yield template

    for template in res:
        # XXX: eliminate duplicates
        yield template

    #yield Template('Software category', [
    #    ('Resource kind', ''),
    #    ('Resource URL', '')])

def filename(s):
    s_ = re.sub('[^A-Za-z0-9_+.-]', '_', s)
    assert s_, s
    return s_ + '.wiki'

def output(path, xs):
    with open(path, 'w') as f:
        for x in xs:
            f.write(str(x) + '\n')

def output_multi(path, xs):
    "Output a bunch of pages to a directory with an index."

    index = {}

    if not os.path.exists(path):
        os.makedirs(path)

    for (name, templates) in xs:
        fname = filename(name)
        fpath = os.path.join(path, fname)
        index[fname] = {'page': name, 'file': fname}
        output(fpath, templates)

    fpath = os.path.join(path, 'index.json')
    json.dump(index, file(fpath, 'w'))

def uname_srcpkgs(data, name):
    pkg_cps = data.cps[data.cps['Upstream-Name'] == name]
    srcpkg_names = list(pkg_cps['_srcpkg'])
    return srcpkg_names

def export_all(data):
    """Export all packages.

    Returns a generator of (name, templates) tuples.
    """

    # First, find all upstream names and the source packages corresponding
    # to them.

    unames = sorted(set(data.cps['Upstream-Name'].dropna()))

    # For source packages with no upstream name, use the source package
    # name as the upstream name.

    no_uname = sorted(set(data.cps[
        data.cps['Upstream-Name'].isnull()]['_srcpkg']))

    packages = itertools.chain(
        ((uname, uname_srcpkgs(data, uname)) for uname in unames),
        ((srcpkg, [srcpkg]) for srcpkg in no_uname))

    for (name, srcpkgs) in packages:
        if not name:
            continue

        if '\n' in name:
            # Seriously?
            warn('bad name: %r' % name)
            continue

        # Generator; exceptions are delayed.
        templates = export_srcpkgs(data, name, srcpkgs)
        yield (name, templates)

def export_all_to_directory(data, outputdir):
    def _export():
        for (name, templates) in export_all(data):
            print (name.encode('utf8') if isinstance(name, unicode) else name)

            try:
                # Force errors.
                templates = list(templates)
            except ExportFailure, e:
                warn('export failed: %s: %s' % (name.encode('utf-8').strip(), e.message.encode('utf-8').strip()))

            yield(name, templates)

    output_multi(outputdir, _export())

def main():
    data = PkgData()
    args = sys.argv[1:]

    if len(args) == 0:
        export_all_to_directory(data, 'output')
    elif len(args) == 1:
        # XXX: assumes argument is an upstream name
        uname = args[0]
        srcpkgs = uname_srcpkgs(data, uname)
        templates = export_srcpkgs(data, uname, srcpkgs)

        for template in templates:
            print template
    else:
        raise RuntimeError()

if __name__ == '__main__':
    main()

