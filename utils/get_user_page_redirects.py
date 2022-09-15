#!/usr/bin/env python

# One-off script for Wikipedia:Sockpuppet investigations/Khirurg.
# Find all the User pages which are redirected to the corresponding
# UserTalk page.  Only considers users above some threshold of
# experience.

import argparse
import pywikibot


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    site = pywikibot.Site('en', 'wikipedia')
    for user in site.allusers(group='extendedconfirmed'):
        print(user)

if __name__ == '__main__':
    main()
