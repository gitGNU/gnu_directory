#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import debian.deb822
import pandas as pd

#from IPython.core import ultratb
#sys.excepthook = ultratb.FormattedTB(mode='Verbose',
#     color_scheme='Linux', call_pdb=1)

class BadFormat(Exception):
    pass

def read_copyright(fh):
    paras = debian.deb822.Deb822.iter_paragraphs(fh)

    try:
        header = paras.next()

        header = dict(header)
        paras = [(p.keys()[0], dict(p)) for p in paras]
    except (KeyError, TypeError, StopIteration):
        raise BadFormat('not in DEP-5 format?')
        return

    if 'Format' not in header:
        raise ValueError('no Format field')
        return

    files = []
    licences = []
    #file_fields = set([
    #    'Authors', 'Files', 'Comment', 'Copyright', 'Disclaimer', 'Homepage',
    #    'License', 'License-Alias', 'Upstream-Authors', 'X-Comment',
    #    'X-Notes'])

    for (type, d) in paras:
        type = type.replace('Licence', 'License')

        if 'Licence' in d:
            # !!!
            d['License'] = d['Licence']
            del d['Licence']

        if type == 'Files':
            if 'License' not in d:
                raise ValueError('no license: ' + repr(d))
                return

            #keys = set(d.keys())
            #assert keys <= file_fields, keys
            files.append(d)
        elif type == 'License':
            # XXX constrain permissible keys here?
            #print d.keys()
            licences.append(d)
        else:
            # Be conservative. Missing license information is a problem.
            raise ValueError('bad para: ' + type)

    return (header, files, licences)

def import_one(pkgname, fh):
    try:
        (header, files, licences) = read_copyright(fh)
    except BadFormat:
        print 'info: not readable'
        return None
    except ValueError, e:
        print 'err:', e
        #print 'err:', repr(e)
        return None

    header['_srcpkg'] = pkgname
    header['_license'] = header.get('License', '').split('\n')[0]

    if 'Upstream-Name' in header:
        # Make spaces breakable (!).
        # Conceivably other characters need replacing.
        header['Upstream-Name'] = \
            header['Upstream-Name'].replace(u'\xa0', ' ')
            #copy_summary['Upstream-Name'].replace('\xc2\xa0', ' ')
        if '@' in header['Upstream-Name']:
            header['Upstream-Name'] = pkgname

    copy_summary = pd.DataFrame([header])
    #print copy_summary.T.to_string()
    #print

    for d in files:
        d['_srcpkg'] = pkgname
        d['_license'] = d['License'].split('\n')[0]

    for d in licences:
        d['_srcpkg'] = pkgname
        d['_license'] = d['License'].split('\n')[0]

    copy_files = pd.DataFrame(files)
    licence = pd.DataFrame(licences)
    return (copy_summary, copy_files, licence)

def get_pkgname(path):
    (dir, base) = os.path.split(path)

    if base in ('current', 'copyright'):
        return get_pkgname(dir)
    else:
        return base

def main(paths):
    summaries = []
    files = []
    licenses = []

    for path in paths:
        pkgname = get_pkgname(path)
        print pkgname, path
        data = import_one(pkgname, file(path))

        if data is not None:
            (summary, file_, license) = data
            summaries.append(summary)
            files.append(file_)
            licenses.append(license)

        print

    summaries = pd.concat(summaries)
    files = pd.concat(files)
    licenses = pd.concat(licenses)

    #from IPython import embed
    #embed()

    #from IPython.core.debugger import Pdb
    #Pdb().set_trace()

    store = pd.HDFStore('cp.h5')
    store['cp_summary'] = summaries
    store['cp_files'] = files
    store['licenses'] = licenses
    store.close()

if __name__ == '__main__':
    main(sys.argv[1:])

