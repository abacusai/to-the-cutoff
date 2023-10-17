# -*- coding: utf-8 -*-
import shutil
import os
import re
import requests
import urllib.request, urllib.error, urllib.parse
from pprint import pprint
from bs4 import BeautifulSoup
import html2text
import time
import argparse
import concurrent.futures
import pandas as pd
from pylatexenc.latex2text import LatexNodes2Text
import bitmath

import asyncio
# from asyncio_tools import gather
from pyppeteer import launch
import pyppeteer
import time
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm

f = open('challenges_all.txt', 'r')

all_names = []

for line in f:
    raw = eval(str(line))

all_names = raw
all_list = []

count = 0
for idx, i in tqdm(enumerate(all_names)):
    contest_id = str(i[0])
    index = str(i[1])

    try:
        with open(f'codeforces_folder/codeforces_{contest_id}_{index}.json','r') as f:
            j = json.load(f)[0]
    except:
        j = None

    all_list.append(j)
    if len(j.keys()) == 0:
        pass
        count += 1
        print(contest_id, index)
        os.remove(f'codeforces_folder/codeforces_{contest_id}_{index}.json')

print(count) 