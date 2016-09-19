#!/usr/bin/python3

import sqlite3

from gpu_list_parser import GpuParser
from intel_cpus_mining import intel_cpus_mining
from amd_apu_cpus_mining import amd_apu_cpus_mining
from amd_fx_cpus_mining import amd_fx_cpus_mining
from skroutz_cpu_list_parser import SkroutzCpuParser
from skroutz_gpu_list_parser import SkroutzGpuParser
from cpu_process_parsing import cpu_process_parsing


class CompilationCreator:
    # CPU Parsing
    cpu_list = []

    # CPU list database
    conn = sqlite3.connect('components.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cpu
             (name TEXT PRIMARY KEY, type TEXT, pn TEXT, price REAL,
             core_clock REAL, no_of_cores INT, l2_l3_cache INT, tdp INT, microarchitecture TEXT,
             microarchitecture_value INT, skroutz_url TEXT)''')

    conn.commit()
    conn.close()

    # Skroutz Parsing
    i = 1
    while 1:
        k = SkroutzCpuParser('http://api.skroutz.gr/categories/32/skus?page=%d' % i)
        completed = k.parser()
        if completed:
            break
        i += 1

    conn = sqlite3.connect('components.db')
    c = conn.cursor()

    for row in c.execute('SELECT type, pn, microarchitecture FROM cpu WHERE no_of_cores = ? ORDER BY type', ('null',)):
        cpu_list.append([row[0], row[1], row[2]])

    conn.close()

    same_type_pn_list = []
    intel_cpus_mining = intel_cpus_mining()

    for i, cpu in enumerate(cpu_list):
        if i == len(cpu_list) - 1:
            same_type_pn_list.append(cpu[1])
            if cpu[0] == 'AMD A':
                amd_apu_cpus_mining = amd_apu_cpus_mining()
                amd_apu_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
            elif cpu[0] == 'AMD FX':
                amd_fx_cpus_mining = amd_fx_cpus_mining()
                amd_fx_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
            elif 'Intel' in cpu[0]:
                intel_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
            break
        if cpu[0] != cpu_list[i + 1][0]:
            same_type_pn_list.append(cpu[1])
            if cpu[0] == 'AMD A':
                amd_apu_cpus_mining = amd_apu_cpus_mining()
                amd_apu_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
            elif cpu[0] == 'AMD FX':
                amd_fx_cpus_mining = amd_fx_cpus_mining()
                amd_fx_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
            elif 'Intel' in cpu[0]:
                intel_cpus_mining.parser(
                    'https://en.wikipedia.org/wiki/List_of_%s_microprocessors' % cpu[0].replace(" ", "_"),
                    same_type_pn_list)
                same_type_pn_list.clear()
        else:
            same_type_pn_list.append(cpu[1])

    cpu_process_parsing = cpu_process_parsing()
    cpu_process_parsing.parser(cpu_list)

    conn = sqlite3.connect('components.db')
    c = conn.cursor()

    conn.commit()
    conn.close()

    # GPU Parsing
    gpu_list = []

    # GPU list database
    conn = sqlite3.connect('components.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gpu
             (name TEXT PRIMARY KEY, benchmark_name TEXT, price REAL, memory_bandwidth INT, memory_size REAL,
             shaders INT, tmus INT, rops INT, skroutz_url TEXT)''')

    conn.commit()
    conn.close()

    # Skroutz Parsing
    i = 1
    while 1:
        k = SkroutzGpuParser('http://api.skroutz.gr/categories/55/skus?page=%d' % i)
        completed = k.parser()
        if completed:
            break
        i += 1

    conn = sqlite3.connect('components.db')
    c = conn.cursor()

    for row in c.execute('SELECT name, benchmark_name FROM gpu WHERE shaders = ?', ('null',)):
        gpu_list.append([row[0], row[1]])

    s = GpuParser(
        'https://www.techpowerup.com/gpudb/?mfgr%5B%5D=amd&mfgr%5B%5D=nvidia&mobile=0&released%5B%5D=y14_c&released%5B%5D=y11_14&released%5B%5D=y08_11&generation=&chipname=&interface=&ushaders=&tmus=&rops=&memsize=&memtype=&buswidth=&slots=&powerplugs=&sort=released&q=',
        gpu_list)
    s.parser()

    conn.commit()
    conn.close()

    # Complilations list database
    conn = sqlite3.connect('components.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS compilations
                 (name TEXT PRIMARY KEY, price REAL, cpu_core_clock REAL,
                  cpu_no_of_cores INT, cpu_l2_l3_cache REAL, cpu_tdp INT, cpu_microarchitecture_value INT,
                  gpu_memory_bandwidth INT, gpu_memory_size REAL, gpu_shaders INT, gpu_tmus INT, gpu_rops INT,
                  cpu_skroutz_url TEXT, gpu_skroutz_url TEXT)''')

    conn.commit()
    conn.close()

    conn = sqlite3.connect('components.db')
    c = conn.cursor()

    if cpu_list:
        for cpu_object in cpu_list:
            c.execute('SELECT * FROM cpu WHERE pn = ?', (cpu_object[1],))
            cpu_info = c.fetchone()
            c.execute('SELECT * FROM gpu')
            all_gpu = c.fetchall()
            for gpu_info in all_gpu:
                name = cpu_info[0] + ' + ' + gpu_info[0]
                price = cpu_info[3] + gpu_info[2]
                cpu_core_clock = cpu_info[4]
                cpu_no_of_cores = cpu_info[5]
                cpu_l2_l3_cache = cpu_info[6]
                cpu_tdp = cpu_info[7]
                cpu_microarchitecture_value = cpu_info[9]
                gpu_memory_bandwidth = gpu_info[3]
                gpu_memory_size = gpu_info[4]
                gpu_shaders = gpu_info[5]
                gpu_tmus = gpu_info[6]
                gpu_rops = gpu_info[7]
                cpu_skroutz_url = cpu_info[10]
                gpu_skroutz_url = gpu_info[8]
                c.execute('INSERT OR IGNORE INTO compilations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (name, price, cpu_core_clock, cpu_no_of_cores, cpu_l2_l3_cache, cpu_tdp,
                           cpu_microarchitecture_value, gpu_memory_bandwidth, gpu_memory_size, gpu_shaders,
                           gpu_tmus, gpu_rops, cpu_skroutz_url, gpu_skroutz_url))
    elif gpu_list:
        for gpu_object in gpu_list:
            gpu_info = c.execute('SELECT * FROM gpu WHERE name = ?', (gpu_object[0],))
            for cpu_info in c.execute('SELECT * FROM cpu'):
                name = cpu_info[0] + ' + ' + gpu_info[0]
                price = cpu_info[3] + gpu_info[2]
                cpu_core_clock = cpu_info[4]
                cpu_no_of_cores = cpu_info[5]
                cpu_l2_l3_cache = cpu_info[6]
                cpu_tdp = cpu_info[7]
                cpu_microarchitecture_value = cpu_info[9]
                cpu_skroutz_url = cpu_info[10]
                gpu_core_clock = gpu_info[3]
                gpu_memory_bandwidth = gpu_info[3]
                gpu_memory_size = gpu_info[4]
                gpu_shaders = gpu_info[5]
                gpu_tmus = gpu_info[6]
                gpu_rops = gpu_info[7]
                gpu_skroutz_url = gpu_info[8]
                c.execute('INSERT OR IGNORE INTO compilations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (name, price, cpu_core_clock, cpu_no_of_cores, cpu_l2_l3_cache, cpu_tdp,
                           cpu_microarchitecture_value, gpu_memory_bandwidth, gpu_memory_size, gpu_shaders,
                           gpu_tmus, gpu_rops, cpu_skroutz_url, gpu_skroutz_url))
    conn.commit()
    conn.close()