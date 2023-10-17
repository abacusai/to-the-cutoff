import pandas as pd
import html2text
import requests
from pylatexenc.latex2text import LatexNodes2Text
problems = pd.read_csv('problems.csv')
solutions = pd.read_csv('Solutions.md',sep='. ')

problems = problems.drop(columns=['solution'])

difficulty_list = []
for i, row in problems.iterrows():
    ID = row['ID']

    url = f'https://projecteuler.net/problem={ID}'
    difficulty = None
    while difficulty is None:
        response = requests.get(url)
        if response.status_code == 200:
            html_scrape = str(response.text)
            search_string = 'Difficulty rating: '
            if html_scrape.find(search_string) < 0:
                difficulty = -1
            else:
                start_index = html_scrape.index(search_string) + len(search_string)
                end_index = html_scrape.index('%', start_index + 1)
                difficulty = int(html_scrape[start_index:end_index])
                print(ID, difficulty)

    difficulty_list.append(difficulty if difficulty >= 0 else None)


problems['Difficulty'] = difficulty_list
problems.to_csv('problems.csv')