
import sys

import debian.deb822
import pandas as pd

def pkg(para):
    d = dict(para)

    if 'Source' in d:
        # Source fields sometimes have the source version number; strip it.
        d['_srcpkg'] = d['Source'].split(' ')[0]
    else:
        # No 'Source' field means that it has the same value as the 'Package'
        # field.
        d['_srcpkg'] = d['Package']

    return d

if __name__ == '__main__':
    packages = debian.deb822.Packages.iter_paragraphs(sys.stdin)
    df = pd.DataFrame([pkg(p) for p in packages])
    store = pd.HDFStore('pkg.h5')

    print df

    store = pd.HDFStore('pkg.h5')
    store['packages'] = df
    store.close()

