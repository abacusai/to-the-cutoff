import argparse
from tqdm import tqdm
from chronological_evaluation_utils import *
from codegen_model import *
from chronological_dataset import *
from metric import *

model_map = {
    'text-davinci-002':         GPTTextDavinci002Model,
    'gpt-3.5-turbo-0314':           ChatGPT35TurboModel,
    'gpt-4-0314':                    ChatGPT4Model,
}

dataset_map = {
    'codeforces':               DeepmindCodeContestsCodeforces,
    'euler':                    ProjectEulerDataset
}

metric_map = {
    'functional_correctness':   FunctionalCorrectnessTest,
    'tags_reproduction':        TagsReproductionTest,
    'title_reproduction_re':       TitleReproductionWithRepromptTest,
    'test_case_count': TestCaseCount
}

class ChronologicalEvaluation:

    def config_dict(self):
        return {
            'name': get_name(self),
            'chronological_dataset': self.chronological_dataset.config_dict(),
            'codegen_model': self.codegen_model.config_dict(),
            'metrics': [
                metric.config_dict() for metric in self.metrics
            ]
        }

    def __init__(self, chronological_dataset, codegen_model, metrics=[], split='dev', args=None):
        self.chronological_dataset = chronological_dataset
        self.codegen_model         = codegen_model
        self.metrics = metrics
        self.split = split
        self.args = args
        self.logger = logging.getLogger(__name__)
        if self.args.debug:
            self.logger.warning("\n======================== DEBUG MODE =======================\n")

        if args.use_wandb and not self.args.debug:
            self.writer = wandb_get_writer(self.config_dict(), args)

    def run_eval(self):
        config = self.config_dict()
        
        # Do evaluation here of metrics
        print(get_name(self.chronological_dataset), get_name(self.codegen_model))

        records = self.chronological_dataset.get_data()
        for i, record in tqdm(enumerate(records), total=len(records)):
            question_string = self.chronological_dataset.get_name_only(record).split(" ")
            try:
                
                log_dict = {}
                log_dict['metadata'] = self.chronological_dataset.get_record_metadata(record)
                log_dict['metrics']  = {}
               
                for metric in self.metrics:
                    question_string = self.chronological_dataset.get_question_string(record)
                    result = metric.compute_metric(question_string, record, self.codegen_model, self.chronological_dataset)
                    log_dict['metrics'][get_name(metric)] = result
                    
                if self.args.use_wandb and not self.args.debug:
                    wandb_log_metrics(log_dict)
                    
                self.logger.info(log_dict)
                
                with open('complete.txt', 'w') as f:
                    f.write(str(log_dict['metadata']['id']))
                    f.write('\n')

                if self.args.debug and (i+1)%5==0:
                    break

            except Exception as e:
                if self.args.ignore_errors:
                    self.logger.error("Failed problem id: {} with error {}".format(str(record["id"]), e))
                else:
                    raise e

        if self.args.use_wandb and not self.args.debug:
            wandb_finish_run(self.writer)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--models', nargs='+', default=model_map.keys())
    parser.add_argument('-d', '--datasets', nargs='+', default=dataset_map.keys())
    parser.add_argument('--metrics',nargs='+', default=metric_map.keys())
    parser.add_argument('--ignore_errors', dest='ignore_errors', action='store_true', default=False)
    parser.add_argument('--debug', dest='debug', action='store_true')
    parser.add_argument('-w', '--use_wandb', dest='use_wandb', action='store_true', default=True)
    parser.add_argument('-wn', '--wandb_run_name', default=None)
    parser.add_argument('--dataset_split', choices=['dev', 'test', 'all'], default='dev')

    args = parser.parse_args()
    print(args)

    # Set up models, metrics and datasets
    models = [
        model_map[m](args) for m in args.models
    ]

    datasets = [
        dataset_map[d](args) for d in args.datasets
    ]


    
    for model in models:
        for dataset in datasets:

            metrics = [
                metric_map[m](args, dataset) for m in args.metrics
            ]

            evaluation = ChronologicalEvaluation(
                chronological_dataset=dataset,
                codegen_model=model,
                metrics=metrics,
                split=args.dataset_split,
                args=args
            )
            
            evaluation.run_eval()
