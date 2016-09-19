#!/usr/bin/python3

import json
import sqlite3
import re

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class SkroutzCpuParser:
    """ Returns a list of CPU names from Skroutz """

    def __init__(self, url):
        self.url = url

    def parser(self):
        # Connect to database
        conn = sqlite3.connect('components.db')
        c = conn.cursor()

        accept = 'application/vnd.skroutz+json; version=3'
        authent_token = 'Bearer kQfzl4Z7dXM7pf6xylSh5ZXmtWHdE9oyVEWU8ShcX/G0roI8b4hnlHrkPHw8d137ho6fqHVNpVJcKPJGgdf5A=='

        try:
            q = Request(self.url)
            q.add_header('Accept', accept)
            q.add_header('Authorization', authent_token)
            html = urlopen(q).read()
            data = json.loads(html.decode())

            for i in range(0, 25):
                # Break if there are no other items in last page
                if data['meta']['pagination']['page'] >= data['meta']['pagination']['total_pages']:
                    try:
                        data['skus'][i]['plain_spec_summary']
                    except IndexError:
                        conn.commit()
                        conn.close()
                        return True
                summary = data['skus'][i]['plain_spec_summary']
                skroutz_cpu_name = data['skus'][i]['display_name']
                skroutz_cpu_url = data['skus'][i]['web_uri']
                skroutz_cpu_price = float(data['skus'][i]['price_min'])
                skroutz_cpu_pn = data['skus'][i]['pn']
                # type matches the cpu to the correct wikipedia cpu list page

                if 'AMD' in skroutz_cpu_name:
                    if 'FX' in skroutz_cpu_name:
                        type = 'AMD FX'
                    else:
                        type = 'AMD A'
                elif 'Intel' or 'Dell' in skroutz_cpu_name:
                    # Dell cpus got no Intel in skroutz display name, so it's added
                    type = summary.split(", ")[0]
                    type = 'Intel ' + type
                    # Removes unecessary Dual Core from some cpus
                    type = type.replace('Dual Core', '')
                    type = type.strip()

                # Xeon are server cpus, thus ignore them
                if 'Xeon' in skroutz_cpu_name or 'Χeon' in skroutz_cpu_name:
                    continue

                # Matching example: Μικροαρχιτεκτονική: K10
                try:
                    microarchitecture = \
                    re.search(r'Μικροαρχιτεκτονική: [A-Z]*[a-z]*[0-9]*[ ]*[A-Z]*[a-z]*[0-9]*', summary).group(0).split(': ')[1]
                except AttributeError:
                    microarchitecture = -1

                # INSERT OR IGNORE to avoid duplicates
                c.execute("INSERT OR IGNORE INTO cpu VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (skroutz_cpu_name, type, skroutz_cpu_pn, skroutz_cpu_price,
                           'null', 'null', 'null', 'null', microarchitecture, 'null', skroutz_cpu_url))
            conn.commit()
            conn.close()
            return False
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print('Error message: ', e.msg)
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
