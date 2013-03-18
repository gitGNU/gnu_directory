
import sys

import debian.deb822
import pandas as pd

if __name__ == '__main__':
    packages = debian.deb822.Packages.iter_paragraphs(sys.stdin)
    df = pd.DataFrame([dict(p) for p in packages])
    store = pd.HDFStore('pkg.h5')

    # No 'Source' field means that it has the same value as the 'Package'
    # field. Set this explicitly.
    nosrc = df['Source'].isnull()
    df['Source'][nosrc] = df[nosrc]['Package']
    assert sum(pd.isnull(df['Source'])) == 0

    print df

    store = pd.HDFStore('pkg.h5')
    store['packages'] = df
    store.close()

