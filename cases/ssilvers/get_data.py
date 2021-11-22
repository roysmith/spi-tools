#!/usr/bin/env python

import argparse
import mwclient
from datetime import datetime
from time import mktime
from collections import defaultdict
import json

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    site = mwclient.Site(SITE)
    
    ssilvers = get_edits(site, 'Ssilvers')
    somambulant1 = get_edits(site, 'Somambulant1')

    with open('Ssilvers.json', 'w') as f:
        json.dump(ssilvers, f, indent=2)
        
    with open('Somambulant1.json', 'w') as f:
        json.dump(somambulant1, f, indent=2)
        

def get_edits(site, username):
    edits = defaultdict(list)
    for c in site.usercontributions(username):
        title = c['title']
        ts = mktime(c['timestamp'])
        edits[title].append(ts)
    return edits


if __name__ == '__main__':
    main()
