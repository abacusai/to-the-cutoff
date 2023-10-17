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

problems_url = 'https://codeforces.com/api/problemset.problems'
r = requests.get(problems_url)
problems_list = r.json()['result']['problems']
problem_stats_list = r.json()['result']['problemStatistics']
problems_dict = {
}

problem_stats_dict = {
}
for entry in problem_stats_list:
    contest_id = entry['contestId']
    index = entry['index']
    problem_stats_dict[f'{contest_id}_{index}'] = entry['solvedCount']

with open('codeforces_solved_counts.json', 'w') as f:
    json.dump(problem_stats_dict, f, indent=4)   
    