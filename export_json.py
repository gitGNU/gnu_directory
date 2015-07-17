#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

import export
import re

def filename(s, extension):
    s_ = re.sub('[^A-Za-z0-9_+.-]', '_', s)
    assert s_, s
    return s_ + '.' +extension

def output(path, xs):
    with open(path, 'w') as f:
            f.write(xs)

def main():
    data = export.PkgData()
    everything = {}

    for (name, templates) in export.export_all(data):
        page = []

        try:
            # Force errors.
            templates = list(templates)
        except export.ExportFailure, e:
            export.warn('export failed: %s: %s' % (name.encode('utf-8').strip(), e.message.encode('utf-8').strip()))

        for template in templates:
            tname = template.name
            values = dict(template.values)
            page.append((tname, values))

        if page != []:
            #name=page[0][1]['Name']
            print name
            fn=filename(name, 'json')
            data = json.dumps(page, sort_keys=True, indent=4, separators=(',', ': '))
            output('output/'+fn, data)

if __name__ == '__main__':
    main()

