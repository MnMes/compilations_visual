#!/usr/bin/python3

import sqlite3
import re
import unicodedata

from bs4 import BeautifulSoup
from pprint import pprint
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class cpu_process_parsing:
    def parser(self, cpu_type_list):

        microarchitectures = {'K10': 32,
                              'Athlon X2 340': 32,
                              'Jaguar': 28,
                              'Steamroller': 28,
                              'Excavator': 28,
                              'Piledriver': 32,
                              'Haswell': 22,
                              'Skylake': 14,
                              'Ivy Bridge': 22,
                              'Broadwell': 14,
                              'Sandy Bridge': 32}
        # TODO NA FTIAXW TO MATCHING TYPE ME DICT
        conn = sqlite3.connect('components.db')
        c = conn.cursor()
        for cpu in cpu_type_list:
            if cpu[2] in microarchitectures:
                c.execute("UPDATE cpu SET microarchitecture_value = ? WHERE pn = ?",
                          (microarchitectures[cpu[2]], cpu[1]))
            else:
                c.execute("UPDATE cpu SET microarchitecture_value = ? WHERE pn = ?",
                          (-1, cpu[1]))
        conn.commit()
        conn.close()
