'To the Cutoff... and Beyond? A Longitudinal Perspective on LLM Data Contamination (ICLR 2024): https://iclr.cc/virtual/2024/poster/17911

Arxiv: http://arxiv.org/abs/2310.10628

Code by Manley Roberts, Himanshu Thakur, and open source code from many authors used under license.
For contact: manley@abacus.ai

Current code makes transparent our procedure for producing datasets and conducting experiments. A small number of files, such as one-off utility files used while collecting dataset features or plotting/analysis code files, have not been included. In addition, a fully updated env install file is not yet available.

The code has some small changes from the exact form used for experiments. For example, we have removed the implementation of a testing function in code_contests/execution/solve_problem.cc in order to better comply with the Codeforces materials license v 0.1. More details in that file.

We have prioritized making the code available for release and transparency; usability improvements including a thorough how-to-install (especially tricky to get the C++ environment configured correctly) will come soon.

For now, requirements.txt, along with a Python 3.10 installation (and the necessary C++ setup which is quite similar to Deepmind's setup https://github.com/google-deepmind/code_contests), should prove sufficient to execute experiments (although it will not be sufficient to replicate dataset scraping or GitHub scraping.)

SPOILER WARNING! Solutions for Project Euler exist in the euler directory. Solutions for problems from both datasets may exist in the csvs.

For now, a few key entry points:
- eval/euler.csv, eval/codeforces_summary_stats.csv, eval/codeforces.csv contain final experimental data on which analyses are conducted.
- eval/chronological_evaluation primarily includes tools for collecting codeforces data (e.g. codeforces_scraper.py) and collecting experimental results (entry point: chronological_evaluation.py).
- eval/chronological_evaluation/summary_stats_codeforcest_tests.ipnyb is an analysis file used to collect summary stats. It also could be useful as a starting point for any reviewer seeking to have a closer look into the results csvs.
- euler directory contains raw project euler data and scrapers. 
- code_contests directory contains tools slightly modified from https://github.com/google-deepmind/code_contests, used for functional correctness tests on codeforces.

Note: Some Codeforces runs contained a few (<5) generated solution completions which did not produce any output from the evaluation handle adapted from Deepmind (even failing to produce failed/test case failed output). In these events, we redo those completions, which will typically lead to a regenerated solution.
