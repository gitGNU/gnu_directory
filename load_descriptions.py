
import sys

import debian.deb822
import pandas as pd

if __name__ == '__main__':
    descs = debian.deb822.Packages.iter_paragraphs(sys.stdin)
    df = pd.DataFrame([dict(p) for p in descs])
    store = pd.HDFStore('pkg.h5')
    store['descriptions'] = df
    store.close()

