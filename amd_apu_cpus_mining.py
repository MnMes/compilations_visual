#!/usr/bin/python3

import sqlite3
import re
import unicodedata

from bs4 import BeautifulSoup
from pprint import pprint
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class amd_apu_cpus_mining:
    def parser(self, url, pn_list):

        conn = sqlite3.connect('components.db')
        c = conn.cursor()

        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0'

        try:
            q = Request(url)
            q.add_header('User-Agent', user_agent)
            html = urlopen(q).read()
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print('Error message: ', e.msg)
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
        else:
            soup = BeautifulSoup(html, "html.parser")
            # Fixes the id of this cpu by adding a zero
            for pn in pn_list:
                if pn == 'AD3300OJZ22HX':
                    old_pn = pn  # Saves the old cpu pn to find it later in the db
                    pn = pn.replace('0', '00', 1)
                sliced_pn = pn[0:9]
                pn_element = soup.find(text=sliced_pn)  # in BeatifulSoup 4.4 text became string
                if pn_element is None:
                    for column in soup.find_all('td'):  # BeautifulSoup won't find text inside <br> tag
                        if sliced_pn in column.get_text():
                            pn_element = column  # if column with the given pn was found, take the whole element for
                            # research

                # try-except block in case cpu was not found in wikipedia
                try:
                    cpu_row = pn_element.find_parent('tr')
                except AttributeError:
                    c.execute("UPDATE cpu SET core_clock = ?, no_of_cores = ?, l2_l3_cache = ?, "
                              "tdp = ? WHERE pn = ?", (-1, -1, -1, -1, pn))
                    continue

                # Declaring variables for the new cpu and the db
                no_of_cores = -1
                no_of_cores_found = False
                core_clock = -1
                core_clock_found = False
                l_cache = -1
                l2_cache_found = False
                tdp = -1
                tdp_found = False
                unicoded_space = unicodedata.normalize("NFKD", '\xa0')

                while not (no_of_cores_found is True and core_clock_found is True and l2_cache_found is True
                           and tdp_found is True):
                    # If cell was merged, try to find the previous cell that has the desired info
                    if core_clock_found:
                        cpu_row = cpu_row.find_previous('tr')

                    for i, column in enumerate(cpu_row.find_all('td')):
                        # cpu_row is the row of our cpu and main_cpu_row is the row of the info that is shared
                        if i == 1 and re.search(r'^[0-9][0-9]?$\b',
                                                column.get_text()) and no_of_cores_found is False:
                            no_of_cores = column.get_text()
                            no_of_cores = int(no_of_cores)
                            no_of_cores_found = True
                        elif 'Hz' in column.get_text() and core_clock_found is False:
                            core_clock = column.get_text()
                            index = core_clock.find('GHz')
                            core_clock = core_clock[0:index]
                            # Fix the code of spaces (latin-1) for the sqlite3 db
                            core_clock = core_clock.replace('\xa0', unicoded_space)
                            core_clock = core_clock.strip()
                            core_clock = float(core_clock)
                            core_clock_found = True
                        elif ('MB' in column.get_text() or 'kB' in column.get_text()) and l2_cache_found is False:
                            l2_cache = column.get_text()
                            # Fix the code of spaces (latin-1) for the sqlite3 db
                            l2_cache = l2_cache.replace('\xa0', unicoded_space)
                            if 'MB' in l2_cache:
                                l2_cache = l2_cache.replace('MB', '').strip()
                                if '×' in l2_cache:
                                    index = l2_cache.find('×')
                                    element1 = int(l2_cache[0:index])
                                    element2 = int(l2_cache[index + 1:])
                                    l2_cache = element1 * element2 * 1024
                                else:
                                    l2_cache = int(l2_cache) * 1024
                            elif 'kB' in l2_cache:
                                l2_cache = l2_cache.replace('kB', '')
                                if '×' in l2_cache:
                                    index = l2_cache.find('×')
                                    element1 = int(l2_cache[0:index])
                                    element2 = int(l2_cache[index + 1:])
                                    l2_cache = element1 * element2
                                else:
                                    l2_cache = int(l2_cache)
                            l2_cache_found = True
                            # Try to find l3 cache in the next td
                            l3_cache = 0
                            if 'MB' in cpu_row.find_all('td')[i + 1].get_text() or 'KB' in cpu_row.find_all('td')[
                                        i + 1].get_text():
                                l3_cache = cpu_row.find_all('td')[i + 1].get_text()
                                # Fix the code of spaces (latin-1) for the sqlite3 db
                                l3_cache = l3_cache.replace('\xa0', unicoded_space)
                                if 'MB' in l3_cache:
                                    l3_cache = l3_cache.replace('MB', '').strip()
                                    if '×' in l3_cache:
                                        index = l3_cache.find('×')
                                        element1 = int(l3_cache[0:index])
                                        element2 = int(l3_cache[index + 1:])
                                        l3_cache = element1 * element2 * 1024
                                    else:
                                        l3_cache = int(l3_cache) * 1024
                                elif 'KB' in l3_cache:
                                    l3_cache = l3_cache.replace('KB', '')
                                    if '×' in l3_cache:
                                        index = l3_cache.find('×')
                                        element1 = int(l3_cache[0:index])
                                        element2 = int(l3_cache[index + 1:])
                                        l3_cache = element1 * element2
                                    else:
                                        l3_cache = int(l2_cache)
                            l_cache = l2_cache + l3_cache
                        elif re.search(r'^[0-9]{1,4}\s*W$', column.get_text()) and tdp_found is False:
                            tdp = column.get_text()
                            tdp = tdp.replace('W', '').strip()
                            # Fix the code of spaces (latin-1) for the sqlite3 db
                            tdp = tdp.replace('\xa0', unicoded_space)
                            tdp = int(tdp)
                            tdp_found = True

                if pn == 'AD33000OJZ22HX':
                    pn = old_pn
                c.execute("UPDATE cpu SET core_clock = ?, no_of_cores = ?, l2_l3_cache = ?, "
                          "tdp = ? WHERE pn = ?", (core_clock, no_of_cores, l_cache, tdp, pn))

        conn.commit()
        conn.close()

        return
