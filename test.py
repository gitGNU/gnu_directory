#!/usr/bin/env python

import os

import nose.core

if 'NOSE_TESTMATCH' not in os.environ:
    os.environ['NOSE_TESTMATCH'] = '(?:^|[./])test(_|$)'

if 'NOSE_WITH_DOCTEST' not in os.environ:
    os.environ['NOSE_WITH_DOCTEST'] = '1'

if __name__ == '__main__':
    nose.core.run()
