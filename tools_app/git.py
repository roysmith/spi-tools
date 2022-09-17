# Utilities for interfacing with git source control.

import sh

def get_info():
    """Returns a string describing the current state of the checked-out
    source tree.  The exact format of the string is unspecified,
    other than being suitable for display to an end user as a
    tracking and error-reporting aid.

    """
    # pylint: disable=too-many-function-args

    data, dirty = get_status()
    head = data['branch.head']
    oid = data['branch.oid']
    dirty_flag = '+' if dirty else ''
    tag_list = get_tags(oid)
    tags = f" [{', '.join(tag_list)}]" if tag_list else ""
    return f"{head} ({oid}{dirty_flag}{tags})"


def get_status():
    """Returns a (data, dirty) tuple, where data is a dict containing the status fields
    and dirty is True if there are any uncommitted changes pending.

    """
    output = sh.git('--no-pager', 'status', '--porcelain=v2', '-b')
    dirty = False
    data = {}
    for line in output:
        if line.startswith('#'):
            _, key, value = line.rstrip().split(' ', 2)
            data[key] = value
        else:
            dirty = True
    return (data, dirty)


def get_tags(oid):
    """Returns a list of tags which point to the oid (which should be a string).

    """
    output = sh.git('--no-pager', 'tag', '--points-at', oid)
    return [tag.rstrip() for tag in output]
