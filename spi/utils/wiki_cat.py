#!/usr/bin/env python
"""Grab the text of a wiki page"""

import argparse
import sys
import mwclient

SITE_NAME = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser(description='Grab the text of a wiki page')
    parser.add_argument('page_title')
    args = parser.parse_args()
    site = mwclient.Site(SITE_NAME)
    page = site.pages[args.page_title]
    print(page.text())
    
if __name__ == '__main__':
    main()
