#!/usr/bin/env python
# -*- coding: utf-8 -*-

from debian import changelog
import pandas as pd
import os
import sys
from dateutil import parser

def import_one(pkgname, fh):
    try:
        c = changelog.Changelog(fh)
        date = parser.parse(c.date).strftime('%Y-%m-%d')
        df = pd.DataFrame([{'_srcpkg':c.package, 'version':c.version, 'date':date, 'author':c.author}])
    except:
        return
    return (df)

def get_pkgname(path):
    (dir, base) = os.path.split(path)

    if base in ('current', 'changelog.txt'):
        return get_pkgname(dir)
    else:
        return base

def main(paths):
    versions = []

    for path in paths:
        pkgname = get_pkgname(path)
        print pkgname, path
        data = import_one(pkgname, file(path))

        if data is not None:
            versions.append(data)
            
    versions = pd.concat(versions)
    print versions
    store = pd.HDFStore('cl.h5')
    store['cl_versions'] = versions
    store.close()

if __name__ == '__main__':
    main(sys.argv[1:])

