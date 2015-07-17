#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import debian.deb822
import pandas as pd

def pkg(para):
    d = dict(para)
    a = dict()

    if 'Files' in d:
        a['srcfile']=d['Files'].split('\n')[2].split(' ')[3]

    if 'Source' in d:
        # Source fields sometimes have the source version number; strip it.
        a['_srcpkg'] = d['Source'].split(' ')[0]
    else:
        # No 'Source' field means that it has the same value as the 'Package'
        # field.
        a['_srcpkg'] = d['Package']

    return a

if __name__ == '__main__':
    packages = debian.deb822.Packages.iter_paragraphs(sys.stdin)
    df = pd.DataFrame([pkg(p) for p in packages])
    store = pd.HDFStore('pkg.h5')

    print df

    store = pd.HDFStore('pkg.h5')
    store['sources'] = df
    store.close()

