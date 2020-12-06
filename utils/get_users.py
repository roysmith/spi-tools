#!/usr/bin/env python

import argparse
import re
import mwclient

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('prefix', nargs='*')
    args = parser.parse_args()
    prefixes = args.prefix

    pattern = re.compile('D[xyz][a-z]{2}[0-9]{3,4}$')

    site = mwclient.Site(SITE, clients_useragent="User:RoySmith/get_users.py")
    usernames = []
    for prefix in prefixes:
        for user in site.allusers(start=args.prefix):
            name = user['name']
            if not name.startswith(prefix):
                break
            if pattern.match(name):
                usernames.append(name)

    for result in site.users(usernames, prop='editcount|registration'):
        # OrderedDict([('userid', 14010558), ('name', 'Dxhf1988'), ('editcount', 0), ('registration', '2011-02-16T02:09:31Z')])
        print('*{{checkuser|%(name)s}} editcount=%(editcount)d registration=%(registration)s' % result)



if __name__ == '__main__':
    main()
