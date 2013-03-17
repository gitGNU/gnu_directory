
import pandas as pd

store = pd.HDFStore('pkg.h5')
print store.handle
print store['packages']
