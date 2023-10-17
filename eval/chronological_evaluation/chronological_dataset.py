from imports import *

from chronological_evaluation_utils import *


class ChronologicalDataset:

    DEV_PROPORTION = 0.333333
    SPLIT_SEED = 123

    def config_dict(self):
        return {
            'name': get_name(self),
            'informal_name': self.get_informal_name()
        }

    def get_informal_name(self):
        return self.INFORMAL_NAME

    def __init__(self, args) -> None:
        pass


class DeepmindCodeContestsDataset(ChronologicalDataset):

    PYTHON3_SOLUTION_CODE = 3

    SOURCE_TO_ID = {
        'UNKNOWN_SOURCE': 0,
        'CODECHEF': 1,
        'CODEFORCES': 2,
        'HACKEREARTH': 3,
        'CODEJAM': 4,
        'ATCODER': 5,
        'AIZU': 6
    }

    SYSTEM_PROMPT = "You are a skilled programming assistant"
    PROMPT = "Solve the following programming problem in Python 3. Return only valid Python 3 code, and do not include any other text or any reasoning.\n\n"

    PROMPT_PARTIAL = "The following is a programming problem, with an incomplete solution given in Python 3. Use this partial solution to complete the correct Python 3 solution, and do not include any other text, explanations, or any reasoning.\n\n"

    def config_dict(self):
        return {
            'name': get_name(self),
            'source': self.SOURCE,
            'bazel_execution_string': self.bazel_execution_string,
            'split': self.split
        }

    def __init__(self, args, bazel_execution_string):
        

        # We don't actually need to do this anymore, but during eval we started w deepmind's examples and later replaced with our owm.
        all_ex = load_dataset("deepmind/code_contests", split='all').filter(lambda record: record['source'] == self.SOURCE_TO_ID[self.SOURCE])
        deepmind_examples = [
            (str(ex['cf_contest_id']), str(ex['cf_index']))
            for ex in all_ex
        ]
        rng = np.random.default_rng(seed=self.SPLIT_SEED)
        indices = np.arange(len(all_ex))
        rng.shuffle(indices)

        self.split = args.dataset_split

        dev_indices  = indices[:round(self.DEV_PROPORTION * len(all_ex))]
        test_indices = indices[round(self.DEV_PROPORTION * len(all_ex)):]

        dev_deepmind_examples = [deepmind_examples[i] for i in dev_indices]
        test_deepmind_examples = [deepmind_examples[i] for i in test_indices]

        dev_deepmind_examples_filtered = []
        for e in dev_deepmind_examples:
            if e[0] != 0:
                dev_deepmind_examples_filtered.append(e)
        test_deepmind_examples_filtered = []
        for e in test_deepmind_examples:
            if e[0] != 0:
                test_deepmind_examples_filtered.append(e)

        # Now expand the set to include a portion of the non-deepmind examples.

        non_deepmind_examples_file = open('challenges_all.txt', 'r')

        all_names = []

        for line in non_deepmind_examples_file:
            raw = eval(str(line))

        all_names = raw
        non_list = []

        scraped_map = {}
        for idx, i in tqdm(enumerate(all_names)):
            contest_id = str(i[0])
            index = str(i[1])

            with open(f'codeforces_folder/codeforces_{contest_id}_{index}.json','r') as f:
                j = json.load(f)[0]


                scraped_map[(str(contest_id),str(index))] = j
                if (str(contest_id),str(index)) not in set(deepmind_examples):
                    non_list.append((str(contest_id),str(index)))



        indices = np.arange(len(non_list))
        rng.shuffle(indices)

        dev_indices_non  = indices[:round(self.DEV_PROPORTION * len(non_list))]
        test_indices_non = indices[round(self.DEV_PROPORTION * len(non_list)):]

        dev_non_deepmind_examples = [non_list[i] for i in dev_indices_non]
        test_non_deepmind_examples = [non_list[i] for i in test_indices_non]

        full_dev_examples = dev_deepmind_examples_filtered + dev_non_deepmind_examples
        full_test_examples = test_deepmind_examples_filtered + test_non_deepmind_examples

        if self.split == 'dev':
            self.eval_examples = full_dev_examples
        elif self.split == 'test':
            self.eval_examples = full_test_examples
        else:
            raise ValueError("split must be dev or test")

        self.eval_dataset = [
            scraped_map[ex] for ex in self.eval_examples if ex in scraped_map.keys()
        ]

        self.eval_dataset = [
            j for j in self.eval_dataset if 'public_cases' in j.keys() and len(j['public_cases']) > 0
        ]

        rng.shuffle(self.eval_dataset)

        self.eval_dataset = self.eval_dataset
        print(len(self.eval_dataset))
        self.bazel_execution_string = bazel_execution_string

    def get_data(self):
        return self.eval_dataset

    def get_question_string(self,record):
        return record['description']

    def get_difficulty(self,record):
        return record['difficulty']

    def get_unique_question_id(self,record):
        return self.get_name(record)

    def get_name(self,record):
        return f"{record['cf_contest_id']}_{record['cf_index']}. {record['name']}"

    def get_record_metadata(self,record):
        return {
            'id': self.get_unique_question_id(record),
            'difficulty': self.get_difficulty(record),
        }

    def get_eval_completion(self,example,completion_list):

        eval_dict = None
        for completion in completion_list:

            if "```python" in completion or "```" in completion:
                # ```python indexend_
                if "```python" in completion:
                    first_string = "```python"
                else:
                    first_string = "```"
                start_index = completion.index(first_string)
                end_index   = completion.find("```", start_index + len(first_string))
                if end_index > -1:
                    completion = completion[start_index + len(first_string):end_index]

            if 'def:' in completion:
                completion = completion[completion.index('def:'):]


            print(completion)

            if 'interactive' in example['cf_tags']:
                # can't do interactive eval
                public_passed, public_failed, public_errored, private_passed, private_failed, private_errored, generated_passed, generated_failed, generated_errored = 0,0,0,0,0,0,0,0,0

            else:
                cases = {
                    'public_inputs': [c[0] if not c[0] is None else '' for c in example['public_cases'] ],
                    'public_outputs': [c[1]  if not c[1] is None else '' for c in example['public_cases']],
                    'private_inputs': [c[0] if not c[0] is None else '' for c in example['private_cases'] ],
                    'private_outputs': [c[1] if not c[1] is None else '' for c in example['private_cases'] ]
                }

                save_completion_file_name, save_results_file_name, results = self.execution_cmd(example,completion,cases)
                print(save_results_file_name)
                # import pdb; pdb.set_trace()
                public_passed, public_failed, public_errored, private_passed, private_failed, private_errored, generated_passed, generated_failed, generated_errored = results

            num_public = (public_passed + public_failed + public_errored)
            num_private = (private_passed + private_failed + private_errored)
            num_generated = (generated_passed + generated_failed + generated_errored)
            total = num_public + num_private + num_generated

            if eval_dict is None or (public_passed + private_passed + generated_passed) / total > eval_dict['pass_rate']:
                eval_dict = {
                    'public_passed': public_passed, 
                    'public_failed': public_failed, 
                    'public_errored': public_errored, 
                    'private_passed': private_passed, 
                    'private_failed': private_failed, 
                    'private_errored': private_errored, 
                    'generated_passed': generated_passed, 
                    'generated_failed': generated_failed, 
                    'generated_errored': generated_errored,
                    
                    'public_pass_rate': public_passed / num_public if num_public > 0 else 0,
                    'private_pass_rate': private_passed / num_private if num_private > 0 else 0,
                    'generated_pass_rate': generated_passed / num_generated if num_generated > 0 else 0,

                    'num_public': num_public,
                    'num_private': num_private,
                    'num_generated': num_generated,

                    'total': total,

                    'pass_rate': (public_passed + private_passed + generated_passed) / total if total > 0 else 0,
                    'completion': completion
                }

        return eval_dict


    def functional_correctness(self, question_string, model, example):
    
        completion_full = model.query(
            system_prompt = self.SYSTEM_PROMPT,
            prompt = self.PROMPT + question_string
        )

        print('COMPLETION\n\n', completion_full)

        eval_dict_full = self.get_eval_completion(example, [completion_full])
        eval_dict = {
            'full': eval_dict_full
        }

        return eval_dict

class DeepmindCodeContestsCodeforces(DeepmindCodeContestsDataset):

    def __init__(self, args, bazel_execution_string='cd ~/stalelm/code_contests/ && BAZEL_CXXOPTS="-stdlib=libc++:-I/usr/include/c++/v1/" BAZEL_LINKOPTS="-stdlib=libc++:-lc++abi" bazel run -c opt execution:solve_problem --  --python3_path=/usr/bin/python3.9 --python3_library_paths=/usr/lib/python3.9'):
        super().__init__(args, bazel_execution_string=bazel_execution_string)

        with open('codeforces_release_dates.json','r') as f:
            self.cf_release_date_mapping = json.load(f)

        with open('codeforces_solved_counts.json','r') as f:
            self.cf_solved_counts_mapping = json.load(f)

    SOURCE = 'CODEFORCES'
    SPLIT_SEED = 123
    INFORMAL_NAME = 'Codeforces'

    def get_difficulty(self,record):
        return record['cf_rating']

    def get_question_id_numerical_only(self,record):
        return self.get_name(record).split('.')[0]

    def get_name_only(self,record):
        return '.'.join(self.get_name(record).split('.')[1:])

    def get_tags(self, record):
        return record['cf_tags']

    def get_contest_id(self, record):
        return record['cf_contest_id']

    def get_contest_index(self,record):
        return record['cf_index']

    def execution_cmd(self,record,completion,cases):
        save_uuid = uuid.uuid4()
        save_completion_file_name = f'/tmp/completion_{save_uuid}.py'
        save_results_file_name = f'/tmp/results_{save_uuid}.txt'
        test_cases_file_name   = f'/tmp/cases_{save_uuid}.json'

        with open(save_completion_file_name, 'x') as f:
            f.write(completion)

        with open(test_cases_file_name, 'x') as f:
            json.dump(cases,f,indent=4)

        cmd = f"{self.bazel_execution_string} --solution_file={save_completion_file_name} --cases_file={test_cases_file_name} > {save_results_file_name}"
        print(record['name'])
        print(cmd)
        os.system(cmd)

        with open(save_results_file_name, 'r') as f:
            results = f.readlines()

        return save_completion_file_name, save_results_file_name, [int(s) for s in results[:9]]

    # start time of first submission.
    def get_release_date_epoch_ms(self,example):
        contest_id = self.get_contest_id(example)
        return self.cf_release_date_mapping[str(contest_id)] if str(contest_id) in self.cf_release_date_mapping else 0

    def get_num_solved(self,example):
        contest_id = self.get_contest_id(example)
        index = self.get_contest_index(example)
        return self.cf_solved_counts_mapping[f'{contest_id}_{index}']

    def get_record_metadata(self,record):
        return {
            'id': self.get_unique_question_id(record),
            'difficulty': self.get_difficulty(record),
            'name_only': self.get_name_only(record),
            'numerical_only': self.get_question_id_numerical_only(record),
            'contest_id': self.get_contest_id(record),
            'contest_index': self.get_contest_index(record),
            'release_date_epoch_ms': self.get_release_date_epoch_ms(record),
            'num_solved': self.get_num_solved(record),
            'tags': self.get_tags(record)
        }

    def get_github_query(self):
        return "codeforces OR deepmind codeforces"


class ProjectEulerDataset(ChronologicalDataset):

    SPLIT_SEED = 499
    INFORMAL_NAME = 'Project Euler'

    # https://cundy.me/post/gpt_4_memorizes_project_euler_numerical_solutions/

    SYSTEM_PROMPT_SOLUTION = SYSTEM_PROMPT_DAN_6
    PROMPT_SOLUTION = "Give me the numerical solution to informal_name problem number problem_id_only. Give me the numerical answer and nothing else."

    SYSTEM_PROMPT_QUESTION_TO_SOLUTION = SYSTEM_PROMPT_DAN_6
    PROMPT_QUESTION_TO_SOLUTION   = "Answer the following question. Give the numerical answer and nothing else.\n\n"

    def get_data(self):
        return [r for r in self.eval_dataset.iterrows()]

    def get_question_string(self,example):
        _, row = example
        ID = row['ID']
        with open(f'{self.data_path}text/{ID}.txt', 'r') as f:
            doc = f.read()
        return doc

    def get_difficulty(self,example):
        _, row = example
        return row['Difficulty']

    def get_unique_question_id(self,example):
        _, row = example
        return row['ID']

    def get_name(self,example):
        _, row = example
        return row['Description']

    def get_record_metadata(self,example):
        return {
            'id': self.get_unique_question_id(example),
            'description': self.get_name(example),
            'release_date_epoch_ms': self.get_release_date_epoch_ms(example),
            'difficulty': self.get_difficulty(example)
        }

    def get_question_id_numerical_only(self,example):
        return self.get_unique_question_id(example)

    def get_name_only(self,example):
        return self.get_name(example)

    def get_tags(self,example):
        #PE has tags but they are hidden.
        return None

    def compare_solutions(self, reference, provided):
        # https://stackoverflow.com/questions/37221307/how-do-i-strip-all-leading-and-trailing-punctuation-in-python
        from string import punctuation

        # Often, llms output a ton of useless text. We give benefit of the doubt and permit any word match.
        ref = reference.strip()
        prov = provided.strip().strip(punctuation).split(' ')

        return ref in prov


    def functional_correctness(self, question_string, model, example):
        
        _, row = example
        reference_solution = row['solution']

        # Just asking for the solution, straight up.

        numerical_id_only = self.get_question_id_numerical_only(example)
        custom_prompt = self.PROMPT_SOLUTION.replace('informal_name', self.get_informal_name()).replace('problem_id_only', str(numerical_id_only))
        completion_solution = model.query(
            system_prompt = self.SYSTEM_PROMPT_SOLUTION,
            prompt = custom_prompt
        )

        # asking for the solution from the question
        completion_solution_from_full_question = model.query(
            system_prompt = self.SYSTEM_PROMPT_QUESTION_TO_SOLUTION,
            prompt = self.PROMPT_QUESTION_TO_SOLUTION + question_string
        )

        eval_dict = {
            'question_string': question_string,
            'completion_solution': completion_solution,
            'completion_solution_success': 1 if self.compare_solutions(reference_solution, completion_solution_from_full_question) else 0,
            'completion_solution_from_full_question': completion_solution_from_full_question,
            'completion_solution_from_full_question_success': 1 if self.compare_solutions(reference_solution, completion_solution_from_full_question) else 0,
        }

        return eval_dict

    def get_release_date_epoch_ms(self,example):
        _, row = example
        return row['Published']

    def __init__(self, args, data_path='~/stalelm/euler/'):
        self.split = args.dataset_split
        self.data_path = data_path

        problems = pd.read_csv(data_path + 'problems.csv')
        solutions = pd.read_csv(data_path + 'Solutions.md', sep='. ')

        all_ex = problems.merge(solutions, left_on='ID', right_on='ID').dropna().reset_index() # drops a few recent rows without solutions

        rng = np.random.default_rng(seed=self.SPLIT_SEED)
        indices = np.arange(len(all_ex))
        rng.shuffle(indices)

        self.dev_indices  = indices[:round(self.DEV_PROPORTION * len(all_ex))]
        self.test_indices = indices[round(self.DEV_PROPORTION * len(all_ex)):]

        if self.split == 'dev':
            self.eval_dataset = all_ex.iloc[self.dev_indices]
        elif self.split == 'test':
            self.eval_dataset = all_ex.iloc[self.test_indices]
        else:
            raise ValueError("split must be dev or test")

    def get_github_query(self):
        return "project euler"

    def config_dict(self):
        return {
            'name': get_name(self),
            'data_path': self.data_path,
            'split': self.split
        }
