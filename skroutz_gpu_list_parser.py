#!/usr/bin/python3

import json
import re
import sqlite3

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class SkroutzGpuParser:
    """ Returns a list of GPU names from Skroutz """

    def __init__(self, url):
        self.url = url

    def gpu_name_filter(self, s):
        # Filters the gpu names from skroutz to benchmark format

        to_filter = ['amd', 'nvidia', '512mb', 'passive', 'oc']
        to_be_filtered = s.split()
        filtered = []

        for word in to_be_filtered:
            if word.lower() not in to_filter:
                if re.search(r'\bHD[0-9]+\b', word):
                    # HD+number without whitespace in word
                    correct = re.sub(r'HD', 'HD ', word)
                    filtered.append(correct)
                elif re.search(r'\bGTX[0-9]+\b', word):
                    # GTX+number without whitespace in word
                    correct = re.sub(r'GTX', 'GTX ', word)
                    filtered.append(correct)
                elif re.search(r'\bGT[0-9]+\b', word):
                    # GT+number without whitespace in word
                    correct = re.sub(r'GT', 'GT ', word)
                    filtered.append(correct)
                elif '240D' in word:
                    correct = word.replace('240D', '240')
                    filtered.append(correct)
                elif '6530' in word:
                    correct = word.replace('6530', 'HD6530D')
                    filtered.append(correct)
                elif '5800G' in word:
                    correct = word.replace('5800G', '5800')
                    filtered.append(correct)
                elif word == '7870' and 'HD' in filtered:
                    filtered.append(word)
                    filtered.append('GHz Edition')
                else:
                    filtered.append(word)

        name = ' '.join(filtered)
        return name

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

                memory_clock = 0
                memory_bus = 0

                # Break if there are no other items in last page
                if data['meta']['pagination']['page'] >= data['meta']['pagination']['total_pages']:
                    try:
                        data['skus'][i]['plain_spec_summary']
                    except IndexError:
                        conn.commit()
                        conn.close()
                        return True
                summary = data['skus'][i]['plain_spec_summary']
                str_list = summary.split(', ')
                skroutz_gpu_name = data['skus'][i]['display_name']
                skroutz_gpu_price = float(data['skus'][i]['price_min'])
                skroutz_gpu_url = data['skus'][i]['web_uri']
                correct_gpu_name = self.gpu_name_filter(str_list[0])

                # Just looking for the desktop gpus in this thesis, ignore the workstation and
                # supercompuuter/data center ones
                if 'FirePro' in skroutz_gpu_name or 'Quadro' in skroutz_gpu_name or \
                            'NVS' in skroutz_gpu_name or 'Tesla' in skroutz_gpu_name:
                    continue

                # Matching example: Μνήμη: 8.0
                try:
                    if re.search(r'\bΜνήμη: [0-9]+[.]?[0-9] MB*\b', summary):
                        memory_size = \
                            float(re.search(r'\bΜνήμη: [0-9]+[.]?[0-9]*\b', summary).group(0).split(
                                ': ')[
                                1]) / 1024
                    else:
                        memory_size = \
                            float(re.search(r'\bΜνήμη: [0-9]+[.]?[0-9]*\b', summary).group(0).split(
                                ': ')[
                                      1])
                except AttributeError:
                    memory_size = -1

                # Matching example: Ταχύτητα Μνήμης: 1000
                try:
                    memory_clock = int(re.search(r'\bΤαχύτητα Μνήμης: [0-9]+\b', summary).group(0).split(': ')[1])
                except AttributeError:
                    memory_bandwidth = -1

                # Matching example: Memory Bus: 64
                try:
                    memory_bus = int(re.search(r'\bMemory Bus: [0-9]+\b', summary).group(0).split(': ')[1])
                except AttributeError:
                    memory_bandwidth = -1

                if memory_clock != 0 and memory_bus != 0:
                    memory_bandwidth = memory_clock*(memory_bus/8)

                # INSERT OR IGNORE to avoid duplicates
                c.execute("INSERT OR IGNORE INTO gpu VALUES (?,?,?,?,?,?,?,?,?)",
                          (skroutz_gpu_name, correct_gpu_name, skroutz_gpu_price,
                           memory_bandwidth, memory_size, 'null', 'null', 'null', skroutz_gpu_url))
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
