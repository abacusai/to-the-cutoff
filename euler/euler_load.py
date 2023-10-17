import pandas as pd
import html2text

from pylatexenc.latex2text import LatexNodes2Text
problems = pd.read_csv('problems.csv')
solutions = pd.read_csv('Solutions.md',sep='. ')

problems = problems.merge(solutions, left_on='ID', right_on='ID')

for i, row in problems.iterrows():
    ID = row['ID']
    with open(f'./html/{ID}.txt', 'r') as f:
        doc = f.read()

    text = html2text.html2text(doc)
    text_equations_unicode = LatexNodes2Text().latex_to_text(text)

    with open(f'./text/{ID}.txt', 'w') as f:
        f.write(text_equations_unicode)
