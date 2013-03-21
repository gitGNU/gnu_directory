
import json
import sys

import export

def main():
    everything = json.load(sys.stdin)

    def _export():
        for (name, valuess) in everything.iteritems():
            print name
            templates = []

            for (tname, values) in valuess:
                template = export.Template(
                    tname.decode('utf8'), values.items())
                templates.append(template)

            yield (name, templates)

    export.output_multi('converted', _export())

if __name__ == '__main__':
    main()

