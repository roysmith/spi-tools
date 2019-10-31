#!/usr/bin/env python

"""Utility to dump the wikitext of a page"""

import argparse
import mwclient

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('page_title')
    args = parser.parse_args()
    site = mwclient.Site(SITE)
    page = site.pages[args.page_title]
    print(page.text())


if __name__ == '__main__':
    main()
