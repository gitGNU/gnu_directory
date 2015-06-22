#!/usr/bin/env python
# -*- coding: utf-8 -*-

# summary of the License: fields found in Files: clauses

import pandas as pd

def histogram(values):
    hist = {}

    for v in values:
        v_ = v.lower()
        hist[v_] = hist.get(v_, 0) + 1

    return hist

if __name__ == '__main__':
    store = pd.HDFStore('cp.h5')
    cpf = store['cp_files']

    licenses = list(histogram(cpf['_license']))

    for (k, v) in sorted(licenses, key=lambda x: x[1], reverse=True):
        print '%-40s %6d' % (k.encode('utf8'), v)

