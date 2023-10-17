import wandb
import pandas as pd
api = wandb.Api()

# flag = 'euler'
flag = 'codeforces'

df_github = None
if flag == 'codeforces':
    github_runs = [
        # WANDB NAMES REDACTED
    ]

    for run_name in github_runs:
        history = api.run(run_name).scan_history(
            keys=None, page_size=10000, min_step=None, max_step=None
        )
        history = [h for h in history]
        if df_github is None:
            df_github = pd.DataFrame(history)
        else:
            df_github = df_github.append(history, ignore_index=True)
    df_merge_on = df_github
    df_merge_on = df_merge_on.drop_duplicates(subset=['metadata.id'])

    df_merge_on.to_csv(f'codeforces_summary_stats.csv')



df_github = None
if flag == 'codeforces':
    github_runs = [
        # WANDB NAMES REDACTED
    ]
else:
    github_runs = [
        # WANDB NAMES REDACTED
    ]

for run_name in github_runs:
    history = api.run(run_name).scan_history(
        keys=None, page_size=10000, min_step=None, max_step=None
    )
    history = [h for h in history]
    if df_github is None:
        df_github = pd.DataFrame(history)
    else:
        df_github = df_github.append(history, ignore_index=True)
print(len(df_github))
run_names_lists = [
    ('gpt-4-0314', [
        # WANDB NAMES REDACTED
    ]),
    ('gpt-3.5-turbo-0301', [
        # WANDB NAMES REDACTED
    ]),
    ('text-davinci-002', [
        # WANDB NAMES REDACTED
    ])
] if flag == 'codeforces' \
    else [
        ('gpt-4-0314', [
            # WANDB NAMES REDACTED
        ]),
        ('gpt-3.5-turbo-0301', [
            # WANDB NAMES REDACTED
        ]),
        ('text-davinci-002', [
            # WANDB NAMES REDACTED
        ])
    ]
df_merge_on = None
for model_name, run_name_list in run_names_lists:
    df_metrics = None
    model_prefix = f'{model_name}_'
    for run_name in run_name_list:
        assert(api.run(run_name).config['codegen_model']['model_name'] == model_name)
        history = api.run(run_name).scan_history(
            keys=None, page_size=10000, min_step=None, max_step=None
        )
        history = [h for h in history]
        if df_metrics is None:
            df_metrics = pd.DataFrame(history)
        else:
            df_metrics = df_metrics.append(history, ignore_index=True)
        

    columns = df_metrics.columns
    metrics_columns = [c for c in columns if 'metrics' in c]
    columns_to_keep = [ model_prefix + c for c in metrics_columns] + [ 'metadata.id' ]
    df_metrics = df_metrics.rename(columns={
        c : model_prefix + c for c in metrics_columns
    })
    if df_merge_on is None:
        df_merge_on = df_metrics
    else:
        df_metrics = df_metrics[columns_to_keep]
        df_merge_on = df_merge_on.merge(df_metrics, how='left', on='metadata.id')
    print(len(df_metrics))
df_merge_on = df_merge_on.merge(df_github, how='left', on='metadata.id',suffixes=('', '_drop'))

df_merge_on = df_merge_on.drop(columns=[c for c in df_merge_on.columns if '_drop' in c or 'Tags' in c or 'Title' in c])

if flag == 'codeforces':
    tags_names_lists = [
        ('gpt-4-0314', [
            # WANDB NAMES REDACTED
        ]),
        ('gpt-3.5-turbo-0301', [ 
            # WANDB NAMES REDACTED
        ]),
        ('text-davinci-002', [ 
            # WANDB NAMES REDACTED            
        ])
    ] 
else:
    tags_names_lists = [
        ('gpt-4-0314', [
            # WANDB NAMES REDACTED
        ]),
        ('gpt-3.5-turbo-0301', [ 
            # WANDB NAMES REDACTED
        ]),
        ('text-davinci-002', [ 
            # WANDB NAMES REDACTED            
        ])
    ] 
df_tags = None
for model_name, tag_name_list in tags_names_lists:
    df_tags_partial = None
    model_prefix = f'{model_name}_'
    for run_name in tag_name_list:
        assert(api.run(run_name).config['codegen_model']['model_name'] == model_name)
        history = api.run(run_name).scan_history(
            keys=None, page_size=10000, min_step=None, max_step=None
        )
        history = [h for h in history]
        if df_tags_partial is None:
            df_tags_partial = pd.DataFrame(history)
        else:
            df_tags_partial = df_tags_partial.append(history, ignore_index=True)

    columns = df_tags_partial.columns
    metrics_columns = [c for c in columns if 'metrics' in c]
    columns_to_keep = [ model_prefix + c for c in metrics_columns] + [ 'metadata.id' ]
    df_tags_partial = df_tags_partial.rename(columns={
        c : model_prefix + c for c in metrics_columns
    })
    if df_tags is None:
        df_tags = df_tags_partial
    else:
        df_tags_partial = df_tags_partial[columns_to_keep]
        df_tags = df_tags.merge(df_tags_partial, how='left', on='metadata.id')


print(len(df_tags))
df_merge_on = df_merge_on.merge(df_tags, how='left', on='metadata.id',suffixes=('', '_drop'))
df_merge_on = df_merge_on.drop(columns=[c for c in df_merge_on.columns if '_drop' in c])

if flag == 'euler':
    difficulty_run_names = [
        # WANDB_NAMES_REDACTED
    ]
    df_difficulty = None
    for run_name in difficulty_run_names:
        history = api.run(run_name).scan_history(
            keys=None, page_size=10000, min_step=None, max_step=None
        )
        history = [h for h in history]
        if df_difficulty is None:
            df_difficulty = pd.DataFrame(history)
        else:
            df_difficulty = df_difficulty.append(history, ignore_index=True)
    print(len(df_difficulty))
    df_merge_on = df_merge_on.merge(df_difficulty, how='left', on='metadata.id',suffixes=('', '_drop'))
    df_merge_on = df_merge_on.drop(columns=[c for c in df_merge_on.columns if '_drop' in c])

    print(df_merge_on[df_merge_on['metadata.id'] == 836])
    df_merge_on = df_merge_on[df_merge_on['metadata.id'] != 836] #april fools

if flag == 'codeforces':
    denom_run_names = [
        # WANDB_NAMES_REDACTED
    ]
else:
    denom_run_names = [
        # WANDB_NAMES_REDACTED
    ]
df_denom = None
for run_name in denom_run_names:
    history = api.run(run_name).scan_history(
        keys=None, page_size=10000, min_step=None, max_step=None
    )
    history = [h for h in history]
    if df_denom is None:
        df_denom = pd.DataFrame(history)
    else:
        df_denom = df_denom.append(history, ignore_index=True)
print(len(df_denom))
df_merge_on = df_merge_on.merge(df_denom, how='left', on='metadata.id',suffixes=('', '_drop'))
df_merge_on = df_merge_on.drop(columns=[c for c in df_merge_on.columns if '_drop' in c])


df_merge_on = df_merge_on.drop_duplicates(subset=['metadata.id'])

df_merge_on.to_csv(f'{flag}.csv')
print(len(df_merge_on))