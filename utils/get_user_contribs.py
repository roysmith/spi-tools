#!/usr/bin/env python

"""Utility to dump all the contribs of a user to a local sqlite3 database"""

import argparse
import mwclient
import sqlite3
import time
import datetime

SITE = 'en.wikipedia.org'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    args = parser.parse_args()
    site = mwclient.Site(SITE)

    conn = sqlite3.connect('example.db')
    cur = conn.cursor()
    
    cur.execute('DROP TABLE IF EXISTS  contribs')
    cur.execute(
        '''
        CREATE TABLE contribs (
        title text,
        timestamp text,
        comment text)
        ''')

    count = 0
    for c in site.usercontributions(args.username):
        count += 1
        if count % 1000 == 0:
            print(count)
        title = c['title']
        timestamp = datetime.datetime.fromtimestamp(time.mktime(c['timestamp'])).isoformat(sep=' ', timespec='seconds')
        comment = c['comment']
        params = (title, timestamp, comment)
        cur.execute('INSERT INTO contribs VALUES (?, ?, ?)', params)


    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
