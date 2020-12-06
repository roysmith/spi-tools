#!/usr/bin/env python

"""Utility to dump the parsoid parsed text of a page"""

import argparse
import requests
import json

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('page_title')
    args = parser.parse_args()
    response = requests.get(f'http://{SITE}/api/rest_v1/page/html/' + args.page_title)
    text = response.text
    print(text)


if __name__ == '__main__':
    main()
