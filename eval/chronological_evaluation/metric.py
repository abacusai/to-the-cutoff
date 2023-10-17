from imports import *
from chronological_evaluation_utils import *
from tqdm import tqdm
from datetime import datetime
from uuid import uuid4
import wandb
import pandas as pd


class Metric:

    def __init__(self, args, dataset) -> None:
        self.args = args

    def config_dict(self):
        return {
            'name': get_name(self)
        }

    def compute_metric(self, question_string, example, model, dataset):
        raise NotImplementedError


class GitHubPresence(Metric):

	def __init__(self, args, dataset):
		
		self.session = requests.Session()

		self.dataset = dataset

		self.tokens = []
		self.tok = 0
		self.tokens.append(os.environ['GITHUB_API_KEY'])
		self.auth = Auth.Token(self.tokens[self.tok])
		self.g = Github(auth=self.auth)
		log_level = os.environ['LOG_LEVEL']
		logging.basicConfig(level=log_level)

		self.logger = logging.getLogger(__name__)
		self.args = args
		self.relevant_repos = self.get_repos(self.dataset.get_github_query())
		db_path = os.path.join(self.args.save_dir, self.__class__.__name__, "db2")
		if args.precompute:
			self.pre_compute_metric(args)
			print("STAGE 1 complete")
			self.pre_compute_metric_stage_2()
			print("STAGE 2 complete")

		if os.path.exists(db_path):
			self.ix = index.open_dir(db_path)
			
			self.qp = QueryParser("content", schema=self.ix.schema)
		

	def get_reset_time(self):

		a = self.g.get_rate_limit().core.reset
		b = datetime.datetime.now(datetime.timezone.utc)
		a = a.replace(tzinfo=b.tzinfo)
		
		wait_s = (a-b).total_seconds() + 5
		return wait_s

	def get_search_reset_time(self):

		a = self.g.get_rate_limit().search.reset
		b = datetime.datetime.now(datetime.timezone.utc)
		a = a.replace(tzinfo=b.tzinfo)
		
		wait_s = (a-b).total_seconds()
		return wait_s
			
	def find_occurrences(self, pattern, text):
			pattern = re.sub(r'[\W_]', '.', pattern) 
			pattern = r'\s*{}\s*'.format(pattern)
			occurrences = re.findall(pattern, text, re.IGNORECASE)
			return len(occurrences)
		
	def read_files_in_folder(self, folder_path):
		
		file_contents = []

		for root, dirs, files in os.walk(folder_path):

			files = [file for file in files if not file.startswith('.')]
			dirs[:] = [d for d in dirs if not d.startswith('.')]
			
			for file in files:
				file_path = os.path.join(root, file)
				try:
					size = os.path.getsize(file_path)
					if (size > 384000): #GITHUB search omission
						continue
					with open(file_path, 'r', encoding='utf-8') as f:
						content = f.read().strip()
						content = content.rstrip(string.punctuation + string.whitespace)
						file_name_tokens = file.split("/")
						file_name_tokens[-1] = file_name_tokens[-1].split(".")[0]
						file_contents.append('$' + " ".join(file_name_tokens) + '$>>#' + content + '#')
						
				except UnicodeDecodeError:
					pass

		all_content = ' '.join(file_contents)
		return all_content
	
	
	def get_repos(self, query):
		
		from datetime import datetime, timedelta
		import pickle

		query_file_name = "_".join(query.split(" "))
		file_name = os.path.join("resources", query_file_name+".txt")

		relevant_repos = set()

		if os.path.exists(file_name):
			self.logger.info("Found pre-computed repositories for your keywords criteria.")
			with open(file_name, "r") as f:
				relevant_repos = sorted(list(set([x.strip() for x in sorted(list(set(f.readlines())))])))
				self.logger.info("Found {} repos".format(len(relevant_repos)))
		else:
			self.logger.warn("Could not find pre-computed repositories for your keywords criteria. Computing now, this may take a while.")
			
			start = datetime(2007, 1, 1)
			
			progress_file_name = os.path.join("resources", "progress_"+query_file_name+".pkl")
			
			if os.path.exists(progress_file_name):
				with open(progress_file_name, "rb") as f:
					start = pickle.load(f)
			
			now = datetime.now()

			while True:

				start_date_string = start.strftime("%Y-%m-%d")
				
				end = start + timedelta(days=30)

				if end > now:
					break
				
				repos = 0

				end_date_string = end.strftime("%Y-%m-%d")
				outer_query = query + " created:"+start_date_string+".."+end_date_string

				latest_end = start
				try:
					pages = self.g.search_repositories(query=outer_query, sort="forks", order="desc")
					if 'codeforces' in query:
						total_pages = min((1000 // 30)+1, (pages.totalCount // 30) + 1) 
					else:
						total_pages = (pages.totalCount // 30) + 1
				
				except (github.GithubException.GithubException, github.RateLimitExceededException) as e:
					self.logger.info("Sleeping")
					time.sleep(self.get_search_reset_time()+1)
					pages = self.g.search_repositories(query=outer_query, sort="forks", order="desc")
					if 'codeforces' in query:
						total_pages = min((1000 // 30)+1, (pages.totalCount // 30) + 1) 
					else:
						total_pages = (pages.totalCount // 30) + 1

				for i in range(total_pages):
					try:
						page = pages.get_page(i)
						for repo in page:
							created_at = repo.created_at
							latest_end = max(latest_end, datetime(created_at.year, created_at.month, created_at.day))
							repo_full_name = (repo.full_name)
							relevant_repos.add(repo_full_name)
							repos += 1

					except (github.GithubException, github.RateLimitExceededException) as e:
						self.logger.info("Sleeping")
						time.sleep(self.get_search_reset_time()+1)
						i = i - 1
						continue
				
				with open(file_name, "w") as f:
					for line in list(relevant_repos):
						f.write(line)
						f.write("\n") 

				if repos >= 1000:
					start = latest_end + timedelta(days=1) 
				else:
					start = end + timedelta(days=1) 

				self.logger.info("Processed {} repos b/w {} - {}".format(repos, start_date_string, latest_end.strftime("%Y-%m-%d")))
				repos = 0
				with open(progress_file_name, "wb") as f:
					pickle.dump(start, f)

		return sorted(list(set(relevant_repos)))


	def process_repo(self, repo):
			
			repo_name = repo.split("/")[0] + "_" + repo.split("/")[1]
			try:
				repos = self.g.get_repo(repo)
			except github.RateLimitExceededException as e:
				period = self.get_search_reset_time()
				if len(self.tokens == 2):
					self.g = Github(auth=Auth.Token(self.tokens[(self.tok + 1)%2]))
					self.tok = (self.tok + 1) % 2
				try:
					repos = self.g.get_repo(repo)
				except:
					period = self.get_search_reset_time()
					self.logger.info("Sleeping for {} until rate limit resets".format(str(period)))
					time.sleep(period+1)
					repos = self.g.get_repo(repo)

			except github.UnknownObjectException as e:
				return None
			
			if repos.size > 300000: #EXCLUDE REPOS over 300 MB in size
				self.logger.info("Skipping {}".format(repos))
				return None
			
			repo_url = repos.clone_url
			temp_path = tempfile.gettempdir()
			
			local_path = os.path.join(temp_path, str(uuid.uuid4()))
			Repo.clone_from(repo_url, local_path)
			repo_content = self.read_files_in_folder(local_path)
			os.system(f'rm -rf {local_path}')

			forks = 0
			stars = 0
			
			try:
				forks = repos.forks_count
			except:
				pass

			try:
				stars = repos.stargazers_count
			except:
				pass
			
			record = {
				"repository":repo,
				"content":repo_content,
				"forks":forks,
				"stars":stars,
				"first_updated":int(repos.created_at.timestamp()),
				"last_updated":int(repos.updated_at.timestamp())
			}
			
			return record

	def compute_metric(self, question_string, example, model, dataset):
		
		exactify  = lambda x: '"' +  x + '"'

		question_id = str(dataset.get_question_id_numerical_only(example)).strip()
		question_name = str(dataset.get_name_only(example)).strip()

		query = []

		#heuristic to match naming conventions with - or _
		if not question_id.isalnum():
			question_ids = [exactify(question_id.replace("_", "-")), 
							exactify(question_id.replace("-", "_")), 
							exactify(question_id.replace("-", "")), 
							exactify(question_id.replace("_", ""))]
			
			query += question_ids
		
		query.append(exactify(question_id))

		question_names = []
		chars = ["-", "_", " "]
		for i in range(len(chars)):
			for j in range(len(chars)):
				question_names.append(exactify(question_name.replace(chars[i], chars[j])))
		
		query += question_names
		query.append(exactify(question_name))

		query = list(set(query))  
		# self.logger.info(query)
				
		record = {
					"total_repos_occurence": 0,
					"total_in_repo_occurence": 0,
					"total_forks": 0,
					"last_updated":int(datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp()),
					"first_updated":int(datetime.datetime.now().timestamp()),
					"total_stars": 0,
		}

		with self.ix.searcher() as s:
			
			q = self.qp.parse(" OR ".join(query))
			results = s.search(q, limit=None)
			for result in results:
				code = result["code"]
				for term in query:
					term = term[1::-1]
					record['total_in_repo_occurence'] += code.lower().count(term.lower())
				
				record['total_forks'] += result['forks']
				record['total_stars'] += result['stars']
				record['last_updated'] = max(result['last_updated'], record['last_updated'])
				record['first_updated'] = min(result['first_updated'], record['first_updated'])
				record['total_repos_occurence'] += 1

		return record
	
	def pre_compute_metric_stage_2(self):
		
		data_path = os.path.join(self.args.save_dir, self.__class__.__name__, "ds")
		db_path_main = os.path.join(self.args.save_dir, self.__class__.__name__, "db2")
		
		Path(db_path_main).mkdir(parents=True, exist_ok=True)
		schema = Schema(repository=ID(stored=True), content=TEXT(analyzer=StandardAnalyzer(stoplist=None, minsize=0)), code=ID(stored=True), forks=NUMERIC(stored=True), stars=NUMERIC(stored=True), last_updated=NUMERIC(stored=True), first_updated=NUMERIC(stored=True))
		ix = index.create_in(db_path_main, schema)

		files = list(glob(data_path + "/*.json"))
		import pdb; pdb.set_trace()
		
		writer = BufferedWriter(ix, period=None, limit=100, writerargs={"multisegment":True, "procs":4})
		
		for idx, file in tqdm(enumerate(files), total=len(files)):
			with open(file, 'r') as f:
				content = json.load(f)
				for record in content:
					writer.add_document(
						repository=record["repository"],
						content=record["content"],
						code=record["content"],
						forks=record["forks"], 
						stars=record["stars"], 
						last_updated=record["last_updated"], 
						first_updated=record["first_updated"]
					)
		tol = 10
		while True and tol > 0:
			try:
				writer.close()
				return True
			except:
				tol -= 1
				time.sleep(1)
				continue
		
		self.logger.error("Could not commit, please run this again!")
		return False
		
	def pre_compute_metric(self, args):

		from multiprocessing import Manager
		import concurrent.futures
		import os

		m = Manager()
		repos = set()        
		progress_path = os.path.join(args.save_dir, self.__class__.__name__, "progress.txt")
		try:
			with open(progress_path, "r") as f:
				repos = set(f.read().splitlines())
		except:
			print("OOPS - Error")
			pass
		db_path = os.path.join(args.save_dir, self.__class__.__name__, "ds")
		Path(db_path).mkdir(parents=True, exist_ok=True)
		repos_to_process = self.relevant_repos

		if len(repos) > 0:
			repos_to_process = list(set(repos_to_process) - repos)
			

		if not os.path.exists(db_path):
			Path(db_path).mkdir(parents=True, exist_ok=True)
			schema = Schema(repository=ID(stored=True), content=TEXT(analyzer=StandardAnalyzer(stoplist=None, minsize=0)), code=ID(stored=True), forks=NUMERIC(stored=True), stars=NUMERIC(stored=True), last_updated=NUMERIC(stored=True), first_updated=NUMERIC(stored=True))
			ix = index.create_in(db_path, schema)
		else:
		    ix = index.open_dir(db_path)
		    if args.cont:
		        self.logger.info("Continuing last run...")
		        repos_processed = [record["repository"] for record in ix.searcher().documents()]
		        repos_to_process = list(sorted(list(set(self.relevant_repos) - set(repos_processed))))
		self.logger.info("{} repos remaining".format(len(repos_to_process)))

		total_repos = len(repos_to_process)
		num_workers = 4
		save_interval = 100
		counter = 0
		shard = 0
		start = time.time()
		buffer = m.list()

		with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:

			futures = []
			for repo in repos_to_process:
				future = executor.submit(self.process_repo, repo)
				futures.append(future)

			progress_bar = tqdm(total=total_repos)

			for future in concurrent.futures.as_completed(futures):
				try:
					record = future.result()
					if record is not None: 
						buffer.append(record)

					if len(list(buffer)) >= save_interval:
						with open(os.path.join(db_path, "shard_"+str(shard)+".json"), "w") as f:
							json.dump(list(buffer), f, indent=4)

						shard += 1
						for buf in list(buffer):
							
							with open(progress_path, "a") as f:
								f.write(buf["repository"])
								f.write("\n")

						del buffer
						buffer = m.list()

				
				except Exception as e:
					print("HERE", repr(e))
					self.logger.info(f"Exception occurred: {str(e)}")

				progress_bar.update(1)
				counter += 1
				
			progress_bar.close()
		
		self.logger.info("DONE in {}s".format((time.time()-start)))
	


class MetadataReproductionTest(Metric):

	FUNCTIONS = {
		'keyword_match':keyword_recall
	}

	def config_dict(self):
		return {
			'name': get_name(self),
			'prompt': self.PROMPT,
			'system_prompt': self.SYSTEM_PROMPT,
		}



class TagsReproductionTest(MetadataReproductionTest):

    SYSTEM_PROMPT = SYSTEM_PROMPT_DAN_6
    PROMPT = "Can you provide the tags of problem problem_full_name in the informal_name dataset? \n\n"

    def compute_metric(self, question_string, example, model, dataset):

        tags_merged = ' '.join(dataset.get_tags(example))
        problem_name = dataset.get_name(example)

        custom_prompt = self.PROMPT.replace('informal_name', dataset.get_informal_name(
        )).replace('problem_full_name', problem_name)
        response = model.query(
            system_prompt=self.SYSTEM_PROMPT,
            prompt=custom_prompt
        )

        response = response.lower()
        tags_merged = tags_merged.lower()

        if response.find('tags:') != -1:
            response = response[len('tags:'):]

        if response.find('"') != -1 and response.find('"',response.index('"') + len('"')) != -1:
            response = response[response.index('"') + len('""'): response.index('"',response.index('"') + len('"'))]

        print(custom_prompt)
        print('response', response)
        print(tags_merged)

        return_dict = {
            'tags': tags_merged,
            'keyword_match_denominator': keyword_recall_denominator(tags_merged)
        }
        return_dict.update({
            metric_name: metric_function(tags_merged, response) if len(dataset.get_tags(example)) > 0 and len(response.strip()) > 0 else 0
            for metric_name, metric_function in self.FUNCTIONS.items()
        })

        return return_dict


class TitleReproductionWithRepromptTest(MetadataReproductionTest):

    SYSTEM_PROMPT = SYSTEM_PROMPT_DAN_6
    PROMPT = "What is the problem name for problem id: problem_id_only? Respond with the problem name only, nothing else."
    
    REPROMPT_MULTI_WORD = "That's incorrect, it starts with the word 'problem_name_start'. Make your best guess and suggest only one problem name. Respond with the problem name only, nothing else."
    REPROMPT_SINGLE_WORD = "That's incorrect, it starts with the letters problem_name_start. Make your best guess and suggest only one problem name. Respond with the problem name only, nothing else."

    def compute_metric(self, question_string, example, model, dataset):

        conversations = []
        true_name = dataset.get_name_only(example)
        numerical_id_only = dataset.get_question_id_numerical_only(example)
        custom_prompt = self.PROMPT.replace('problem_id_only', str(numerical_id_only))
        response = model.query(
            system_prompt=self.SYSTEM_PROMPT,
            prompt=custom_prompt
        )
        conversations.append(custom_prompt)
        conversations.append(response)

        true_name = true_name.lower()
        response = response.lower()

        if true_name.lower() not in response.lower():

            true_name_tokens = word_tokenize(true_name)

            if len(true_name_tokens)>1:
            
                #reprompt is possible
                first_word = true_name_tokens[0]
                
                custom_prompt = self.REPROMPT_MULTI_WORD.replace('problem_name_start', first_word)
                response = model.query(
                    system_prompt=self.SYSTEM_PROMPT,
                    prompt=custom_prompt
                )
            
            else:
                
                slice_index = random.randint(1, min(len(true_name), 3))

                #reprompt is possible
                first_word = true_name[:slice_index]
                custom_prompt = self.REPROMPT_SINGLE_WORD.replace('problem_name_start', first_word)
                response = model.query(
                    system_prompt=self.SYSTEM_PROMPT,
                    prompt=custom_prompt
                )

            conversations.append(custom_prompt)
            conversations.append(response)
        
        if response.find('title:') != -1:
            response = response[len('title:'):]

        if response.find('"') != -1 and response.find('"',response.index('"') + len('"')) != -1:
            response = response[response.index('"') + len('""'): response.index('"',response.index('"') + len('"'))]
        
        return_dict = {
            'title': true_name,
            'keyword_match_denominator': keyword_recall_denominator(true_name)
        }

        return_dict.update({
            metric_name: metric_function(true_name, response)
            for metric_name, metric_function in self.FUNCTIONS.items()
        })

        return_dict["conversation"] = " ".join(conversations)
        
        return return_dict


class FunctionalCorrectnessTest(Metric):

	def config_dict(self):
		return {
			'name': get_name(self),
			# 'system_prompt': self.SYSTEM_PROMPT,
			# 'prompt': self.PROMPT
		}

	def compute_metric(self, question_string, example, model, dataset):

		return dataset.functional_correctness(question_string, model, example)
		
class TestCaseCount(Metric):

    def config_dict(self):
        return {
            'name': get_name(self),
            # 'system_prompt': self.SYSTEM_PROMPT,
            # 'prompt': self.PROMPT
        }

    def compute_metric(self, question_string, example, model, dataset):

        cases = {
            'public_inputs': [c[0] if not c[0] is None else '' for c in example['public_cases'] ],
            'public_outputs': [c[1]  if not c[1] is None else '' for c in example['public_cases']],
            'private_inputs': [c[0] if not c[0] is None else '' for c in example['private_cases'] ],
            'private_outputs': [c[1] if not c[1] is None else '' for c in example['private_cases'] ]
        }

        lengths = {
            f'max_length_{key}' : max([len(s) for s in seq]) if len(seq) > 0 else -1 for key, seq in cases.items() 
        }
        lengths.update({
            f'min_length_{key}' : min([len(s) for s in seq]) if len(seq) > 0 else -1 for key, seq in cases.items()
        })
        lengths.update({
            f'avg_length_{key}' : sum([len(s) for s in seq])/len(seq) if len(seq) > 0 else -1 for key, seq in cases.items() 
        })

        cases_together = {
            'inputs': cases['public_inputs'] + cases['private_inputs'],
            'outputs': cases['public_outputs'] + cases['private_outputs'],
        }

        lengths.update({
            f'max_length_{key}' : max([len(s) for s in seq]) if len(seq) > 0 else -1 for key, seq in cases_together.items() 
        })
        lengths.update({
            f'min_length_{key}' : min([len(s) for s in seq]) if len(seq) > 0 else -1 for key, seq in cases_together.items()
        })
        lengths.update({
            f'avg_length_{key}' : sum([len(s) for s in seq])/len(seq) if len(seq) > 0 else -1 for key, seq in cases_together.items() 
        })

        lengths.update({
            'all_inputs_lengths': [len(s) for s in cases_together['inputs']],
            'public_lengths': [len(s) for s in cases['public_inputs']],
            'private_lengths': [len(s) for s in cases['private_inputs']]
        })


        return lengths

