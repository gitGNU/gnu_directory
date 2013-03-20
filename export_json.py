
import json
import sys

import export

def main():
    data = export.PkgData()
    everything = {}

    for (name, templates) in export.export_all(data):
        page = []

        for template in templates:
            tname = template.name
            values = dict(template.values)
            page.append((tname, values))

        everything[name] = page

    json.dump(everything, sys.stdout, indent=2)

if __name__ == '__main__':
    main()

