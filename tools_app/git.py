# Utilities for interfacing with git souce control.

import sh

def get_info():
    """Returns a string describing the current state of the checked-out
    source tree.  The exact format of the string is unspecified,
    other than being suitable for display to an end user as a
    tracking and error-reporting aid."""
        
    output = sh.git('status', '--porcelain=v2', '-b')
    return parse_output(output)

def parse_output(output):
    dirty = False
    data = {}
    for line in output:
        if line.startswith('#'):
            _, key, value = line.rstrip().split(' ', 2)
            data[key] = value
        else:
            dirty = True
    return f"{data['branch.head']} ({data['branch.oid']}{'+' if dirty else ''})"

