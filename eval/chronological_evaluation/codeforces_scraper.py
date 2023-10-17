# -*- coding: utf-8 -*-

# Some tools adapted from https://github.com/ethancaballero/description2code and heavily modified by authors of this work. Missing cite of this work from main paper; will address in future draft.

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
from pyppeteer import launch
import pyppeteer
import time
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm

# A few manually removed cases
#['1773', 'K'],  ['1666', 'H'], ['1510', 'G'], ['1510', 'A'], ['1267', 'F'], ['1267', 'A'], several 1090/1089, ['949', 'F'], ['528', 'E'], ['497', 'D'], are omitted due to non-standard (PDF) formatting. Also ['1773', 'C'], ['1666', 'G'], ['1510', 'E'], ['1267', 'C'], '936', 'E']  omitted due to slow page access, and '1663' as the April Fools contest. 1639 due to lack of permission to view the submissions. 1773 because submissions are private.

NUMBER_OF_PAGES=89
# Note: update the 89 to however many pages are at http://codeforces.com/problemset to get all problems


async def get_cases(contest_id, submission_id, index, raw_html_content):
    if submission_id == -1:
        return [], []
    try:
        browser = await launch()
        page = await browser.newPage()
        url = f'https://codeforces.com/contest/{contest_id}/submission/{submission_id}'
        await page.goto(url, {'waitUntil' : ['domcontentloaded', 'load']})

        # https://techoverflow.net/2020/09/27/how-simulate-click-using-pyppeteer/
        #https://stackoverflow.com/questions/52904802/how-to-click-a-button-on-a-website-using-puppeteer-without-any-class-id-as 
        await page.waitForSelector('.click-to-view-tests', {'timeout': 10000}) 
        await page.waitFor(2000)
        await page.click('.click-to-view-tests')
        await page.waitForSelector('.diagnostics-result-comment-view', {'timeout': 10000}) 
        await page.waitFor(2000)
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        num_output = raw_html_content.count('<div class="output">')
        num_input = raw_html_content.count('<div class="input">')
        assert(num_output == num_input)
        public_cases = []
        private_cases = []
        test_cases = soup.find_all("div", class_="roundbox borderTopRound")
        if len(test_cases) == 0:
            await browser.close()
            return None, None
        for test_case in test_cases:
            input_details = test_case.find_all("pre", class_="input")[0]
            input_string = input_details.string
            output_details = test_case.find_all("pre", class_="output")[0]

            output_string = output_details.string
            if output_string is None:
                output_string = ''

            if len(public_cases) < num_input:
                public_cases.append((input_string, output_string))
            else:
                if '...' in input_string or '...' in output_string:
                # test case is truncated, can't use it.
                    pass
                else:
                    private_cases.append((input_string, output_string))

        flag = True
        return public_cases, private_cases
    finally:

        await browser.close()
    return None, None


def sub_strip(matchobj):   
    return matchobj.group(0).replace("\u2009", "")

def get_problem_list(url):
    page = requests.get(url)
    if str(page) == "<Response [503]>":
        while str(page) == "<Response [503]>":
            time.sleep(0.5)
            page = requests.get(url)
    html_content = page.text

    soup = BeautifulSoup(html_content, "html.parser") # making soup

    messages = []

    text = soup.select("body a")

    for row in text:
        message = ""
        raw = str(row)
        body = re.search(' href="/problemset/problem/(.*)">', raw)

        if body != None:
            w = body.group(1)
            message = str(w)
            c = message.split('/')
            messages.append(c)

    return messages

def get_solution_ids(name, language):
    print(language)
    
    d = {'JSESSIONID': 'FBAAF89D197D7A5C7E95C536A7D31A7A-n1', '39ce7': 'CFtRZMGC'}

    url = 'http://codeforces.com/problemset/status/' + name[0] + '/problem/' + name[1]

    c = requests.get(url, cookies = d)
    if str(c) == "<Response [503]>" or "403 Forbidden" in c.text:
        while str(c) == "<Response [503]>" or "403 Forbidden" in c.text:
            time.sleep(0.5)
            c = requests.get(url)

    m = re.search('meta name="X-Csrf-Token" content="(.*)"', c.text)
    if not m:
        print(c.text)
        raise Exception('unable to get csrf token')

    csrf_token = m.groups(1)[0]


    #'''
    if language == 'python':
        print("python_search")
        c = requests.post(url,
        data = {'csrf_token':csrf_token, 'action':'setupSubmissionFilter', 'frameProblemIndex':'A', 'verdictName':'OK', 'programTypeForInvoker':'python.2', 'comparisonType':'NOT_USED', 'judgedTestCount':'', '_tta':'199'},  
        headers = {'X-Csrf-Token':csrf_token},
        cookies = d
        )
    else:
        assert(False)

    page = requests.get(url, cookies = d)
    if str(page) == "<Response [503]>" or "403 Forbidden" in page.text:
        while str(page) == "<Response [503]>" or "403 Forbidden" in page.text:
            time.sleep(0.5)
            page = requests.get(url)
    html_content = page.text

    soup = BeautifulSoup(html_content, "html.parser") 

    messages = []

    text = soup.select("body a")

    for row in text:
        message = ""
        raw = str(row)
        body = re.search('submissionid="(.*)" t', raw)
        if body != None:
            w = body.group(1)
            message = str(w)
            messages.append(message)
    return messages

def get_description(i, problems_dict):
    descriptions = []
    left_out = []
    failed_to_download_d = []

    url = 'http://codeforces.com/problemset/problem/' + str(i[0]) + '/' + str(i[1])

    print(url)

    page = requests.get(url)

    if str(page) == "<Response [503]>" or "403 Forbidden" in str(page.text) or ('Statement is not available on English language' not in str(page.text) and 'time limit per test</div>' not in str(page.text)) or re.search('"message":"requests limit exhausted"', str(page.text)) != None:
        while str(page) == "<Response [503]>" or "403 Forbidden" in str(page.text) or ('Statement is not available on English language' not in str(page.text) and 'time limit per test</div>' not in str(page.text)) or re.search('"message":"requests limit exhausted"', str(page.text)) != None:
            print(url)
            time.sleep(0.5)
            page = requests.get(url)

    html_content = page.text

    contest_id = str(i[0])
    entry = str(i[1])
    metadata = problems_dict[f'{contest_id}_{entry}']

    if html_content==None:
        failed_to_download_d.append(i)

    if 'Statement is not available on English language' in html_content or 'April Fools Day Contest' in html_content or 'Microsoft Q# Coding Contest' in html_content or 'VRt Contest 2019 (marathon)' in html_content or 'VK Cup 2018 - Wild-card Round 2' in html_content or 'AIM Tech Mini Marathon 1' in html_content or 'VK Cup 2017 - Wild Card Round 2' in html_content:
        return [], [], [], metadata, 0, 0, ''

    #print html_content

    time_limit_seconds_list = []
    mem_limit_mb_list = []

    if re.search('src="http://codeforces.com/predownloaded', html_content.replace("\\", "")) == None and re.search('src="http://espresso.codeforces.com', html_content.replace("\\", "")) == None and re.search('"message":"Problem is not visible now. Please try again later."', html_content) == None and re.search('Statement is not available', html_content) == None:




        index_of_time_limit = html_content.find('time limit per test</div>')
        if index_of_time_limit < 0:
            raise Exception("Couldn't find time limit")
        else:
            index_of_next_seconds = html_content.find(' s', index_of_time_limit + len('time limit per test</div>'))
            if index_of_next_seconds < 0:
                raise Exception("Couldn't find time limit")
            time_limit_string = html_content[index_of_time_limit + len('time limit per test</div>'):index_of_next_seconds]
            time_limit_seconds = float(time_limit_string.replace('<span class="tex-font-style-bf">',''))

        time_limit_seconds_list.append(time_limit_seconds)

        index_of_mem_limit = html_content.find('memory limit per test</div>')
        if index_of_mem_limit < 0:
            raise Exception("Couldn't find memory limit")
        else:
            index_of_next_mb = html_content.find(' megabyte', index_of_mem_limit + len('memory limit per test</div>'))
            if index_of_next_mb < 0:
                index_of_next_mib = html_content.find(' mebibyte', index_of_mem_limit + len('memory limit per test</div>'))
                if index_of_next_mib < 0:
                    index_of_next_mb = html_content.find(' MB', index_of_mem_limit + len('memory limit per test</div>'))
                    if index_of_next_mb < 0:
                        raise Exception("Couldn't find mem limit")
                    else:
                        mem_limit_string = html_content[index_of_mem_limit + len('memory limit per test</div>'):index_of_next_mb]
                        mem_limit_mb = float(mem_limit_string.replace('<span class="tex-font-style-bf">',''))
                else:
                    mem_limit_string = html_content[index_of_mem_limit + len('memory limit per test</div>'):index_of_next_mib]
                    mem_limit_mib = float(mem_limit_string.replace('<span class="tex-font-style-bf">',''))
                    mem_limit_mb = float(bitmath.MiB(mem_limit_mib).to_MB())
            else:
                mem_limit_string = html_content[index_of_mem_limit + len('memory limit per test</div>'):index_of_next_mb]
                mem_limit_mb = float(mem_limit_string.replace('<span class="tex-font-style-bf">',''))

        mem_limit_mb_list.append(mem_limit_mb)


        body = re.findall('</div></div><div>(.+?)<script type="text/javascript">', html_content, flags=re.S)
        
        w = body[0]
        old_w = w
        w = w.replace('class="upper-index">', 'class="upper-index">^')
        # At some point, I thought I needed to specially handle negative exponents here.
        # I have not explicitly done this, but it seems that including html2text addresses this to an extent.
        w = re.sub('class="upper-index">(.+?)</sup>', sub_strip, w, re.S)

        w = w.replace("</p>", "\n</p>")
        w = w.replace("<br", "\n<br")

        w = w.replace("</div>", "\n</div>")
        w = w.replace("</center>", "\n</center>")

        w = BeautifulSoup(w, "html.parser").get_text()
        w = w.replace("All submissions for this problem are available.", "")

        w = re.sub('Read problems statements in (.+?)\\\\n', '', w, re.M)
        w = re.sub('Subtasks(.+?)Example', 'Example', w, re.S)

        w = w.replace("\\u003C","<")
        w = w.replace("\\u003E",">")

        w = w.replace("\n\n\n\n\n\n","\n\n\n")
        w = w.replace("\n\n\n\n","\n\n\n")

        w = w.replace("\\","\\\\")

        w = html2text.html2text(w)
        w = LatexNodes2Text().latex_to_text(w)
        descriptions.append(w)
    else:
        left_out.append(i)

    return descriptions, left_out, failed_to_download_d, metadata, time_limit_seconds_list, mem_limit_mb_list, html_content


def get_solutions(contest, solution_ids):
    solutions = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=50) as executor:
        future_to_url = {executor.submit(get_solution, contest, i): i for i in solution_ids}
        for future in concurrent.futures.as_completed(future_to_url):
            data = future.result()

            if data[2] == None:
                solutions[data[0]] = data[1]

    return solutions

def get_solution(contest, solution_id):
    url = 'http://codeforces.com/contest/' + str(contest[0]) + '/submission/' + str(solution_id)
    
    page = requests.get(url)
    if str(page) == "<Response [503]>":
        while str(page) == "<Response [503]>":
            time.sleep(0.5)
            page = requests.get(url)
    html_content = page.text

    soup = BeautifulSoup(html_content, "html.parser")

    text = soup.select("body > div > div > div > div > pre")

    failed_to_download = None
    solution = None


    if len(text)==0:
        failed_to_download = solution_id
    else:
        body = BeautifulSoup(str(text[0]), "html.parser").get_text()

        body = body.replace("\\","\\\\")
        solution = body.encode('utf-8').decode('unicode-escape')

    return solution_id, solution, failed_to_download



def download_all_challenge_names(filename):
    target = open(filename, 'w')

    problem_list = []

    for i in range(0,NUMBER_OF_PAGES):
        a = 'http://codeforces.com/problemset/page/' + str(i+1)
        l = get_problem_list(a)
        for jdx, j in enumerate(l):
            if jdx % 2 == 0:
                problem_list.append(j)
    target.write(str(problem_list))


async def download_descriptions_solutions(filename):

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

    for entry in problems_list:
        contest_id = entry['contestId']
        index = entry['index']
        problems_dict[f'{contest_id}_{index}'] = entry
        problems_dict[f'{contest_id}_{index}']['solvedCount'] = problem_stats_dict[f'{contest_id}_{index}']


    root_dir = 'codeforces_data'

    f = open(filename, 'r')

    all_names = []

    for line in f:
        raw = eval(str(line))

    a = ""
    b = ""

    all_names = raw

    language = []

    save_list = [

    ]

    for idx, i in tqdm(enumerate(all_names)):
        contest_id = str(i[0])
        index = str(i[1])
        path = f'./codeforces_folder/codeforces_{contest_id}_{index}.json'
        if not os.path.isfile(path):
            
            return_vals  = get_description(i, problems_dict)
            if len(return_vals[0]) == 0:
                descriptions, left_out, failed_to_download_d, metadata, time_limit_seconds_local, mem_limit_mb_local, raw_html_content = return_vals
                with open(path, 'w') as f:
                    json.dump([
                        {
                        'name': metadata['name'],
                        'omitted_for_description_contents': True,
                        # 'description': description,
                        'cf_contest_id': metadata['contestId'],
                        'cf_index': metadata['index'],
                        # 'cf_rating': metadata['rating'] if 'rating' in metadata else 0,
                        # 'difficulty': metadata['difficulty'] if 'difficulty' in metadata else 0,
                        # 'cf_tags': metadata['tags'],
                        # # 'time_limit_nano': ,
                        # 'time_limit_seconds': time_limit_seconds_local[0],
                        # 'memory_limit_bytes': mem_limit_mb_local[0],

                        # 'public_cases': public_cases,
                        # 'private_cases': private_cases
                    }
                    ], f, indent=4)  
                continue
            else:
                descriptions, left_out, failed_to_download_d, metadata, time_limit_seconds_local, mem_limit_mb_local, raw_html_content = return_vals
            print(i)
            if i not in left_out:
                # if not os.path.exists(root_dir):
                #     os.makedirs(root_dir)

                description = descriptions[0]

                contest_id = str(i[0])
                index = str(i[1])

                pg = 1
                submission_id = None
                public_cases = None
                while public_cases is None:
                    if submission_id == -1:
                        break
                    url = f'https://codeforces.com/contest/{contest_id}/status/{index}/page/{pg}?order=BY_ARRIVED_DESC'
                    print(url)
                    c = requests.get(url) 
                    if str(c) == "<Response [503]>" or "403 Forbidden" in c.text:
                        while str(c) == "<Response [503]>" or "403 Forbidden" in c.text:
                            time.sleep(0.5)
                            c = requests.get(url)
                    
                    soup = BeautifulSoup(c.text, "html.parser")
                    rows = [r for r in soup.find_all("tr")]
                    # print(rows)
                    row_i = 0
                    while row_i < len(rows):
                        row = rows[row_i]
                        if row is not None:
                            if len(row.find_all("span", class_="verdict-accepted")) > 0:
                                found = row.find_all("a", class_="view-source")
                                if len(found) == 0:
                                    # no submissions public
                                    submission_id = -1
                                    break
                                else:
                                    submission_id = found[0].text
                                    public_cases, private_cases = None, None
                                    iterations_tried = 0
                                    while public_cases is None:
                                        try:
                                            public_cases, private_cases = await get_cases(contest_id, submission_id, index, raw_html_content)
                                        except asyncio.exceptions.IncompleteReadError:
                                            print('IncompleteRead - outer')
                                            time.sleep(0.5)
                                        except asyncio.exceptions.InvalidStateError:
                                            print('InvalidState - outer')
                                            time.sleep(0.5)
                                        except pyppeteer.errors.PageError:
                                            print('pageerror - outer')
                                            time.sleep(0.5)
                                        except:
                                            print('other - outer')
                                            time.sleep(0.5)
                                        iterations_tried += 1
                                    if public_cases is not None:
                                        break

                            else:
                                public_cases, private_cases = [], []
                        row_i += 1
                    pg += 1

                print(public_cases, private_cases)
                new_save = {
                    'name': metadata['name'],
                    'description': description,
                    'cf_contest_id': metadata['contestId'],
                    'cf_index': metadata['index'],
                    'cf_rating': metadata['rating'] if 'rating' in metadata else 0,
                    'difficulty': metadata['difficulty'] if 'difficulty' in metadata else 0,
                    'cf_tags': metadata['tags'],
                    # 'time_limit_nano': ,
                    'time_limit_seconds': time_limit_seconds_local[0],
                    'memory_limit_bytes': mem_limit_mb_local[0],

                    'public_cases': public_cases,
                    'private_cases': private_cases
                }

                ids_l = []
                print(language)
                for l in language:
                    print("l")
                    print(l)
                    ids = get_solution_ids(i, l)
                    ids_l.append(ids)
                    solutions = get_solutions(i, ids)

                    solution_dir = save_dir + "/solutions_" + l

                    if not os.path.exists(solution_dir):
                        os.makedirs(solution_dir)


                    print('len(solutions)')
                    print(len(solutions))
                    '''
                    if len(solutions) != 50:
                        hdghfdhgf
                        '''
                    for jdx, j in enumerate(solutions):
                        print((len(solutions[j])))
                        if len(solutions[j]) < 10000:
                            solution_file_path = solution_dir + "/" + j + ".txt"
                            solution_file = open(solution_file_path, 'w')
                            solution_file.write(solutions[j])

            with open(path, 'w') as f:
                json.dump([new_save], f, indent=4)   

            import gc; gc.collect()

    
parser = argparse.ArgumentParser()
args = parser.parse_args()

# GET list of problems and save in challenges_all.txt
# '''
# download_all_challenge_names('challenges_all.txt')
#'''
# USE challenges_all.txt to scrape
async def main():
    await download_descriptions_solutions('challenges_all.txt')
asyncio.get_event_loop().run_until_complete(main())
