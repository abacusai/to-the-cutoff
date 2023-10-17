# Code by Manley Roberts, Himanshu Thakur, and open source code from many authors used under license.

Associated with 'Data Contamination Through the Lens of Time (arxiv preprint)': http://arxiv.org/abs/2310.10628

This is a code dump designed to make transparent our procedure for producing datasets and conducting experiments. A small number of files, such as one-off utility files used while collecting dataset features or plotting/analysis code files, have not been included. In addition, a fully updated env install file is not yet available.

The code has some small changes from the exact form used for experiments. For example, we have removed the implementation of a testing function in code_contests/execution/solve_problem.cc in order to better comply with the Codeforces materials license v 0.1. More details in that file.

We have prioritized making the code available for release and transparency; usability improvements including a thorough how-to-install (especially tricky to get the C++ environment configured correctly) will come soon.

SPOILER WARNING! Solutions for Project Euler exist in the euler directory. Solutions for problems from both datasets may exist in the csvs.

For now, a few key entry points:
- eval/euler.csv, eval/codeforces_summary_stats.csv, eval/codeforces.csv contain final experimental data on which analyses are conducted.
- summary_stats_codeforcest_tests.ipnyb is an analysis file used to collect summary stats. It also could be useful as a starting point for any reviewer seeking to have a closer look into the results csvs.
- eval/chronological_evaluation primarily includes tools for collecting codeforces data (e.g. codeforces_scraper.py) and collecting experimental results (entry point: chronological_evaluation.py).
- euler directory contains raw project euler data and scrapers. 
- code_contests directory contains tools slightly modified from https://github.com/google-deepmind/code_contests, used for functional correctness tests on codeforces.
