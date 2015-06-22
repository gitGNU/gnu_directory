#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd

if __name__ == '__main__':
    store = pd.HDFStore('pkg.h5')
    print store.handle
    print store['packages']
