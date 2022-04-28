#!/usr/bin/env python

"""Utility to dump CU logs."""

import argparse
import requests
import json

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target')
    args = parser.parse_args()
    request_data = {'action': 'query',
                    'format': 'json',
                    'list': 'checkuserlog',
                    'culuser': 'RoySmith',
                    'culdir': 'newer',
                    'culfrom': '2021-10-16T20:21:14.000Z',
                    'culto': '2021-10-17T20:21:14.000Z',
                    }

    r = requests.get(f'https://{SITE}/w/api.php', data=request_data)
    print(r.url)
    print(r.text)


if __name__ == '__main__':
    main()
