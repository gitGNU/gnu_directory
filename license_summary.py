# summary of the License: fields found in Files: clauses

import pandas as pd

store = pd.HDFStore('cp.h5')
cpf = store['cp_files']

def histogram(values):
    hist = {}

    for v in values:
        v_ = v.lower()
        hist[v_] = hist.get(v_, 0) + 1

    return hist

licenses = histogram(cpf['_license'])

for (k, v) in sorted(licenses.iteritems(), key=lambda x: x[1], reverse=True):
    print '%-40s %6d' % (k.encode('utf8'), v)

