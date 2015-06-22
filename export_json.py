#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

import export

def main():
    data = export.PkgData()
    everything = {}

    for (name, templates) in export.export_all(data):
        page = []

        try:
            # Force errors.
            templates = list(templates)
        except export.ExportFailure, e:
            export.warn('export failed: %s: %s' % (name, e.message))

        for template in templates:
            tname = template.name
            values = dict(template.values)
            page.append((tname, values))

        everything[name] = page

    json.dump(everything, sys.stdout, indent=2)

if __name__ == '__main__':
    main()

