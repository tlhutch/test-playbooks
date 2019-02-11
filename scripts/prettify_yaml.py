#!/usr/bin/env python
"""Prettify a YAML document"""

import yaml
import sys
import os


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage: %s [<filename>, ...]" % sys.argv[0])
        sys.exit(1)

    for filename in sys.argv[1:]:
        assert os.path.isfile(filename)
        assert os.path.splitext(filename)[1] in ['.yaml', '.yml']

        # open for read
        stream = file(filename, 'r')
        data = yaml.load(stream)
        stream.close()

        print(yaml.dump(data))
        yesno = input("\nSave changes? [y|n] ").lower() == 'y'
        if yesno:
            stream = file(filename, 'w')
            stream.write(yaml.dump(data))
            stream.close()
