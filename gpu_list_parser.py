#!/usr/bin/python3

import re
import sqlite3
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


class GpuParser:
    """ Returns a dict of form { GPU name: score } """

    def __init__(self, url, skroutz_gpu_name_list):
        self.url = url
        self.skroutz_gpu_name_list = skroutz_gpu_name_list

    def parser(self):

        conn = sqlite3.connect('components.db')
        c = conn.cursor()

        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0'

        try:
            q = Request(self.url)
            q.add_header('User-Agent', user_agent)
            html = urlopen(q).read()
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        else:
            soup = BeautifulSoup(html, "html.parser")
            gpu_table = soup.find('table', {'class': 'processors'})
            table_rows = gpu_table.find_all('tr')
            for skroutz_gpu_name in self.skroutz_gpu_name_list:
                found = 0
                for row in table_rows:
                    try:
                        name = row.find_all('td')[0].get_text()
                    except IndexError:
                        continue

                    if re.search(r'[0-9][0-9]?\s*GB', name):
                        correct = re.sub(r'[0-9][0-9]?\s*GB', '', name)
                        name = correct

                    if name.lower().replace(' ', '').strip() == skroutz_gpu_name[1].lower().replace(' ', '').strip():
                        gpu_info = row.find_all('td')[7].get_text().split('/')
                        shaders = gpu_info[0]
                        if 'x' in shaders:
                            index = shaders.find('x')
                            element1 = int(shaders[0:index])
                            element2 = int(shaders[index + 1:])
                            shaders = element1 * element2
                        tmus = gpu_info[1]
                        if 'x' in tmus:
                            index = tmus.find('x')
                            element1 = int(tmus[0:index])
                            element2 = int(tmus[index + 1:])
                            tmus = element1 * element2
                        rops = gpu_info[2]
                        if 'x' in rops:
                            index = rops.find('x')
                            element1 = int(rops[0:index])
                            element2 = int(rops[index + 1:])
                            rops = element1 * element2

                        c.execute("UPDATE gpu SET shaders = ?, tmus = ?, rops = ? WHERE benchmark_name = ?",
                                  (shaders, tmus, rops, skroutz_gpu_name[1],))
                        found = 1
                        break
                if found == 0:
                    c.execute("UPDATE gpu SET shaders = ?, tmus = ?, rops = ? WHERE benchmark_name = ?",
                              (-1, -1, -1, skroutz_gpu_name[1]))
        conn.commit()
        return
