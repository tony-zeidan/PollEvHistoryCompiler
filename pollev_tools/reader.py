import argparse
import os
import pandas as pd
import yaml
import json
import random
import configparser
import shutil
from collections import OrderedDict

TEX_CHARS_ESCAPE = ['%']
QUESTION_START_CHARS = [')', '.', ']', '&']

def remove_question_start(s: str, max_len: int):
    """
    Removes the start of a question. 

    a) <- this form

    :param s: The string to modify
    :param max_len: How long a substring the function should look for the characters in

    :return: Modified string
    """
    for x in QUESTION_START_CHARS:
        try:
            ind = s.index(x)
            if ind <= max_len:
                s = s[ind+1:]

                # try to remove starting spaces
                while s[0] == " ":
                    s = s[1:]
                break
        except ValueError:
            pass
        except IndexError:
            pass
    return s

def read_csv_file(
        file_path,
        presenter:str=None,
        rhidden: bool = False,
        rimages: bool = False,
        presenter_col: str = 'Presenter',
        question_col: str = 'Activity title',
        activity_type_col: str = 'Activity type',
        response_col: str = 'Response options',
        multiple_choice_type: str = 'Multiple choice',
        remove_start_len: int = 4,
        response_options_delim: str = " | ", 
        image_in_str: str = '(an image)',
        correct_in_response: str = '(Correct)',
        shuffle: bool = True,
        **kwargs
    ):
    """
    Read a CSV file into pandas and filter by presenter.

    :param file_path: The CSV file path (to read)
    :param presenter: The presenter to filter by
    :param rhidden: Whether or not to remove hidden question titles
    :param kwargs: Any keyword arguments for read_csv

    :return: The read data in a dataframe
    """

    data_df = pd.read_csv(file_path, **kwargs)
    if presenter is not None:
        data_df = data_df[data_df[presenter_col] == presenter]

    data_df = data_df[data_df[activity_type_col] == multiple_choice_type]

    # remove the start of the question title
    data_df[question_col] = data_df[question_col].apply(lambda x: remove_question_start(x, remove_start_len))

    # remove hidden entries
    if rhidden:
        data_df = data_df[data_df[question_col] != "~hidden~"]

    

    # remove image entries
    if rimages:
        data_df = data_df[~(data_df[question_col].str.contains(image_in_str) | data_df[response_col].str.contains(image_in_str))]


    # split and maybe shuffle
    if shuffle:
        def split_shuffle(row):
            lst = row.split(response_options_delim)
            random.shuffle(lst)
            return lst
        
        data_df['split_responses'] = data_df[response_col].apply(split_shuffle)
    else:
        data_df['split_responses'] = data_df[response_col].apply(lambda x: x.split(response_options_delim))

    # remove the question starts
    data_df['split_responses'] = data_df['split_responses'].apply(lambda x: [remove_question_start(x_i, remove_start_len) for x_i in x])

    # check for any correct responses
    data_df['split_correct_responses'] = data_df['split_responses'].apply(lambda x: [x_i.replace(correct_in_response, "") for x_i in x if correct_in_response in x_i])

    # remove the question starts
    data_df['split_responses'] = data_df['split_responses'].apply(lambda x: [x_i.replace(correct_in_response, "") for x_i in x])    

    return data_df


def change_tex_chars(s: str) -> str:
    """
    Escape common LaTeX characters.

    :param s: The string to modify

    :return: String with escaped characters
    """
    for x in TEX_CHARS_ESCAPE:
        s = s.replace(x, f'\\{x}')
        
    return s


def tex_helper(
        row,
        title_col: str = 'Activity title',
        block_type: str = 'question',
        resp_block_type: str = 'oneparcheckboxes',
        resp_opt_block_type: str = 'choice',
        resp_opt_correct_block_type: str = 'CorrectChoice',
        show_correct: bool = True,
        end_spacing: int = 4,
        end_spacing_metric: str = 'pt'
    ) -> str:
    """
    Converts the current row into a LaTeX block question.


    :param block_type: The LaTeX block type to use for the question title
    :param resp_block_type: The LaTeX block type to use for the question responses (wrapped block)
    :param resp_opt_block_type: The LaTeX block type to use for the question response option (if not correct)
    :param resp_opt_correct_block_type: The LaTeX block type to use for the question response option (if correct)
    :param show_correct: Whether or not to show the solutions in the output
    :param end_spacing: The amount of space to add after each response option
    :param end_spacing_metric: The metric for end_spacing

    :return: The string representing the LaTeX block
    """

    strbuilder = []

    title = row[title_col]
    title = change_tex_chars(title)

    strbuilder.append(r'\begin{' + block_type + r'}')
    strbuilder.append(title)
    strbuilder.append(r'\end{' + block_type + r'}\\')

    strbuilder.append(r'\begin{' + resp_block_type + r'}')
    for resp in row['split_responses']:
        resp_new = change_tex_chars(resp)
        if resp in row['split_correct_responses'] and show_correct:
            strbuilder.append(rf"\{resp_opt_correct_block_type} {resp_new}\\[{end_spacing}{end_spacing_metric}]")
        else:
            strbuilder.append(rf"\{resp_opt_block_type} {resp_new}\\[{end_spacing}{end_spacing_metric}]")

    strbuilder.append(r'\end{' + resp_block_type + r'}' + "\n")

    return "\n".join(strbuilder)

def to_tex_exam(data_df: pd.DataFrame, output_file: str, encoding: str = None, show_correct: bool = True, **kwargs):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    :param show_correct: Whether or not to show the solutions in the output
    :param kwargs: keyword arguments for every tex block
    """

    try: 

        lst = data_df.apply(lambda x: tex_helper(x, show_correct=show_correct, **kwargs), axis=1)

        tex_gen = r'''
\documentclass{exam}         
\begin{document}

\begin{questions}
''' + '\n'.join(lst) + r'''
\end{questions}

\end{document}
        '''

        with open(output_file, 'w', encoding=encoding) as out_file:
            
            out_file.write(tex_gen)

    except KeyError:
        raise ValueError("Column couldn't be found, can't continue.")
    
def text_helper(
        row,
        title_col: str = 'Activity title',
        show_correct: bool = True,
        **kwargs
    ) -> str:
    """
    Converts the current row into a LaTeX block question.

    :param row: The current dataframe row
    :param show_correct: Whether or not to show the solutions in the output

    :return: The string representing the LaTeX block
    """

    strbuilder = []

    title = row[title_col]
    title = change_tex_chars(title)

    strbuilder.append(f"Question:\n{title}\n\nOptions:\n")
    
    for resp in row['split_responses']:
        resp_new = resp
        strbuilder.append(f"\t- {resp_new}")

    strbuilder.append("\n")
    if show_correct:
        strbuilder.append("Correct:\n")

        for resp in row['split_correct_responses']:
            strbuilder.append(f"\t- {resp}")

    strbuilder.append("\n\n")

    return "\n".join(strbuilder)
    

def to_txt_exam(data_df: pd.DataFrame, output_file: str, encoding: str = None, show_correct: bool = True, **kwargs):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    :param show_correct: Whether or not to show the solutions in the output
    :param kwargs: keyword arguments for every tex block
    """

    try: 

        lst = data_df.apply(lambda x: text_helper(x, show_correct=show_correct, **kwargs), axis=1)

        text_gen = '\n'.join(lst)

        with open(output_file, 'w', encoding=encoding) as out_file:
            out_file.write(text_gen)

    except KeyError:
        raise ValueError("Column couldn't be found, can't continue.")
    

def html_helper(
        row,
        title_col: str = 'Activity title',
        response_options_class: str = 'options',
        correct_class: str = 'correct',
        incorrect_class: str = 'incorrect',
        show_correct: bool = True,
        **kwargs
    ) -> str:
    """
    Converts the current row into a HTML block.

    :param correct_class: Classname (HTML) for the correct answers
    :param incorrect_class: Classname (HTML) for incorrect answers
    :param show_correct: Whether or not to show the solutions in the output
    :param kwargs: Keyword arguments to pass into get_title_and_responses

    :return: The string representing the LaTeX block
    """

    strbuilder = []

    title = row[title_col]
    title = change_tex_chars(title)

    strbuilder.append(rf'<li>{title}</li>')

    strbuilder.append(f'\t<ol type="a" class="{response_options_class}">')
    for resp in row['split_responses']:
        resp_new = resp
        if resp in row['split_correct_responses']:
            if show_correct:
                strbuilder.append(f'\t\t<li class="{correct_class}">{resp_new}</li>')
            else:
                strbuilder.append(f'\t\t<li>{resp_new}</li>')
        else:
            strbuilder.append(f'\t\t<li class="{incorrect_class}">{resp_new}</li>')

    strbuilder.append('\t</ol>\n')

    return "\n".join(strbuilder)

def to_html_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, quiz_mode: bool = False, encoding: str = None):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    """

    try: 
        name, _ = os.path.splitext(output_file)

        quiz_mode_script = ''
        if quiz_mode:
            quiz_mode_script = "<script type='text/javascript' src='html-js.js'/>"

        html_lst = '\n'.join(data_df.apply(lambda x: html_helper(x, show_correct=show_correct), axis=1))

        html_gen = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha384-KyZXEAg3QhqLMpG8r+Knujsl5/1zwaQ7wxt2NN9138DhxUeK5l/5Vp1+XWlFm_tv" crossorigin="anonymous"></script>
    {quiz_mode_script}
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Raleway&display=swap" />
    <link rel="stylesheet" href="html-styles.css">
    <title>{name}</title>
</head> 
<body>
    <div class='center-container'>
        <div class='center-div'>
            <h1>PollEverywhere Report</h1>
        </div>          
        {html_lst}
    </div>
</body>
</html>
        '''

        with open(output_file, 'w', encoding=encoding) as out_file:
            out_file.write(html_gen)

    except KeyError:
        raise ValueError("Column couldn't be found, can't continue.")
    
def to_markdown_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, encoding: str = None):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    """
    import markdownify

    name, _ = os.path.splitext(output_file)

    html_lst =  '\n'.join(data_df.apply(lambda x: html_helper(x, show_correct=show_correct), axis=1))

    html_gen = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha384-KyZXEAg3QhqLMpG8r+Knujsl5/1zwaQ7wxt2NN9138DhxUeK5l/5Vp1+XWlFm_tv" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Raleway&display=swap" />
    <link rel="stylesheet" href="html-styles.css">
    <title>{name}</title>
</head> 
<body>
    <div class='center-container'>
        <div class='center-div'>
            <h1>PollEverywhere Report</h1>
        </div>          
        {html_lst}
    </div>
</body>
</html>
        '''

    md_str = markdownify.markdownify(html_gen)
    with open(output_file, 'w', encoding=encoding) as out_file:
        out_file.write(md_str)


def dict_helper(row, show_correct: bool = True, question_col: str = 'Activity title'):
    """
    To Dict helper.

    """

    return {
        'title': row[question_col],
        'responses': row['split_responses'],
        'correct': row['split_correct_responses']
    } if show_correct else {
        'title': row[question_col],
        'responses': row['split_responses']
    }
    

def to_dict_style(data_df: pd.DataFrame, show_correct: bool = True, root_name: str = None):
    """
    Converts the CSV dataframe into a DICT report.

    :param data_df: The dataframe
    :param show_correct: Whether or not to show the correct answer
    """

    dct = {}
    i = 1

    def help(row): 
        nonlocal i, dct, show_correct
        dct[f'{i}'] = dict_helper(row, show_correct=show_correct)
        i += 1

    data_df.apply(lambda x: help(x), axis=1)
    
    if root_name is not None:
        new_dct = {
            root_name: dct
        }
    else:
        new_dct = dct

    return new_dct


def to_yaml_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, root_name: str = 'questions', encoding: str = None):
    """
    Output to yaml format.

    :param data_df: The PollEv results
    :param output_file: Filepath to output to (.yaml or .yml must be used)
    :param show_correct: Whether or not to show the solutions in the output
    :param root_name: The key for the root of the tree
    :param encoding: The encoding to write the file with
    """

    dct = to_dict_style(data_df, show_correct=show_correct, root_name=root_name)

    with open(output_file, 'w', encoding=encoding) as out_file:
        yaml.dump(dct, out_file,default_flow_style=False)

def to_json_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, root_name: str = 'questions', encoding: str = None):
    """
    Output to JSON format.

    :param data_df: The PollEv results
    :param output_file: Filepath to output to (.json must be used)
    :param show_correct: Whether or not to show the solutions in the output
    :param root_name: The key for the root of the tree
    :param encoding: The encoding to write the file with
    """

    dct = to_dict_style(data_df, show_correct=show_correct, root_name=root_name)

    with open(output_file, 'w', encoding=encoding) as out_file:
        json.dump(dct, out_file)

def to_toml_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, question_prefix: str = 'question', encoding: str = None):
    """
    Output to TOML format.

    :param data_df: The PollEv results
    :param output_file: Filepath to output to (.toml must be used)
    :param show_correct: Whether or not to show the solutions in the output
    :param question_prefix: The key used in each question
    :param encoding: The encoding to write the file with
    """

    import toml

    dct = to_dict_style(data_df, show_correct=show_correct, root_name = question_prefix)

    with open(output_file, 'w', encoding=encoding) as out_file:
        toml.dump(dct, out_file)

def to_csv_report(data_df: pd.DataFrame, output_file: str, show_correct: bool = True, encoding: str = None):
    """
    Output to CSV format.

    :param data_df: The PollEv results
    :param output_file: Filepath to output to (.csv must be used)
    :param encoding: The encoding to write the file with
    """
    
    data_df.drop(columns=['split_responses', 'split_correct_responses'], errors='ignore').to_csv(output_file, encoding=encoding, index=False)

def update_defaults(args, defaults: dict) -> dict:
    """
    Makes a new dict based on the intersection of the args and defaults.

    :param args: Newly input args (Namespace)
    :param defaults: Dict containing default values
    :return: new defaults
    """

    kw = {}

    args_dct = vars(args)
    for k in defaults.keys():
        if k in args_dct:
            kw[k] = args_dct[k] or defaults[k]
    return kw

def update_defaults_config(defaults, config, section) -> dict:
    """
    Makes a new dict based on the intersection of the args and defaults.

    :param args: Newly input args (Namespace)
    :param defaults: Dict containing default values
    :return: new defaults
    """

    kw = {}
    for k in defaults.keys():
        kw[k] = config.get(section, k, fallback=defaults[k])
        if kw[k] == 'yes' or kw[k] == 'no' or kw=='true' or kw=='false':        # convert booleans from the config file
            kw[k] = config.getboolean(section, k, fallback=defaults[k]) 
    return kw

def main():
    """
    Main script executable.
    """

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_path = config_path = os.path.join(base_dir, "resources") 
    config_path = os.path.join(res_path, "config.ini") 
    styles_path = os.path.join(res_path, "html-styles.css")
    js_path = os.path.join(res_path, "html-js.js")

    # define default values
    default_io_opts = dict(
        output_path = os.getcwd(),
        encoding = 'utf-8',
        transform = 'csv',
        remove_start_len = 5,
        shuffle_responses = True,
        remove_hidden = False,
        remove_images = False,
        show_solutions = True,
        config = config_path
    )

    default_tex_opts = dict(
        block_type = 'question',
        resp_block_type = 'oneparcheckboxes',
        resp_opt_block_type = 'choice',
        resp_opt_correct_block_type = 'CorrectChoice',
        end_spacing = 4,
        end_spacing_metric = 'pt'
    )

    default_html_opts = dict(
        quiz_mode = False
    )

    default_json_opts = dict(
        root_name = 'questions'
    )

    default_yaml_opts = dict(
        root_name = 'questions'
    )

    default_toml_opts = dict(
        question_prefix = 'question'
    )

    default_csv_opts = dict(
        
    )

    default_text_opts = dict(
        
    )

    default_md_opts = dict(
        
    )



    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument('--config_path', type=str, help='Path to the configuration file (optional)', default=default_io_opts['config'])
    config_args, remaining_argv = config_parser.parse_known_args()
    default_io_opts['config'] = config_args.config_path

    try:
        config = configparser.ConfigParser()
        config.read(default_io_opts['config'])

        # i/o and general config
        default_io_opts.update(update_defaults_config(default_io_opts, config, 'pollev_output'))

        # tex defaults options
        if default_io_opts['transform'] == 'tex' and 'pollev_transforms.tex' in config:
            default_tex_opts.update(update_defaults_config(default_tex_opts, config, 'pollev_transforms.tex'))

        elif default_io_opts['transform'] == 'html' and 'pollev_transforms.html' in config:
            default_html_opts.update(update_defaults_config(default_html_opts, config, 'pollev_transforms.html'))

        elif default_io_opts['transform'] == 'yaml' and 'pollev_transforms.yaml' in config:
            default_yaml_opts.update(update_defaults_config(default_yaml_opts, config, 'pollev_transforms.yaml'))

        elif default_io_opts['transform'] == 'json' and 'pollev_transforms.json' in config:
            default_json_opts.update(update_defaults_config(default_json_opts, config, 'pollev_transforms.json'))

        elif default_io_opts['transform'] == 'csv' and 'pollev_transforms.csv' in config:
            default_csv_opts.update(update_defaults_config(default_csv_opts, config, 'pollev_transforms.csv'))

        elif default_io_opts['transform'] == 'toml' and 'pollev_transforms.toml' in config:
            default_toml_opts.update(update_defaults_config(default_toml_opts, config, 'pollev_transforms.toml'))

        elif default_io_opts['transform'] == 'txt' and 'pollev_transforms.txt' in config:
            default_text_opts.update(update_defaults_config(default_text_opts, config, 'pollev_transforms.txt'))
    
        elif default_io_opts['transform'] == 'markdown' and 'pollev_transforms.md' in config:
            default_md_opts.update(update_defaults_config(default_csv_opts, config, 'pollev_transforms.md'))

    except FileNotFoundError:
        parser.set_defaults(transform=default_io_opts['transform'])
        args, _ = parser.parse_known_args(remaining_argv)
        pass

    global_parser = argparse.ArgumentParser(description='Read CSV file with optional screen name filter', add_help=False)
    global_parser.add_argument('--config_path', type=str, help='Path to the configuration file (optional)', default=default_io_opts['config'])
    global_parser.add_argument('--remove_hidden', help='Remove questions with hidden titles', default=default_io_opts['remove_hidden'], action='store_true')
    global_parser.add_argument('--remove_images', help='Remove questions with images in responses or question title', default=default_io_opts['remove_images'], action='store_true')
    global_parser.add_argument('--nosolutions', help='Remove solutions', default=(not default_io_opts['show_solutions']), action='store_true')
    global_parser.add_argument('--presenter', type=str, help='Presenter name to filter (optional)', default=None)
    global_parser.add_argument('--output_path', type=str, help='Path for output file (optional)', default=default_io_opts['output_path'])
    global_parser.add_argument('--encoding', type=str, help='Encoding for reading and writing (optional)', default=default_io_opts['encoding'])
    global_parser.add_argument('--noshuffle', help="Don't shuffle the response options (optional)", default=(not default_io_opts['shuffle_responses']), action='store_true')
    global_parser.add_argument('--remove_start_len', type=int, help='How far into the string to look when removing the question or response prefix (optional)', default=default_io_opts['remove_start_len'])

    # parser for the required file path
    parser = argparse.ArgumentParser(description='Read CSV file with optional screen name filter', parents=[global_parser])
    parser.add_argument('file_path', type=str, help='Path to the CSV file')

    # subparser for individual commands
    transform_parser = parser.add_subparsers(dest='transform', required=False)

    # LaTeX transform
    parser_tex = transform_parser.add_parser('tex', help='Convert to LaTeX', parents=[global_parser], add_help=True)
    parser_tex.add_argument('--block_type', type=str, help='LaTeX block type to use for question title', default=default_tex_opts['block_type'])
    parser_tex.add_argument('--resp_block_type', type=str, help='LaTeX block type to use for question responses', default=default_tex_opts['resp_block_type'])
    parser_tex.add_argument('--resp_opt_block_type', type=str, help='LaTeX block used for a single response (if not correct)', default=default_tex_opts['resp_opt_block_type'])
    parser_tex.add_argument('--resp_opt_correct_block_type', type=str, help='LaTeX block used for a single response (if correct)', default=default_tex_opts['resp_opt_correct_block_type'])
    parser_tex.add_argument('--end_spacing', type=int, help='The amount of space to add after each response option', default=default_tex_opts['end_spacing'])
    parser_tex.add_argument('--end_spacing_metric', type=str, help='The metric for end_spacing', default=default_tex_opts['end_spacing_metric'])
    
    # HTML transform
    parser_html = transform_parser.add_parser('html', help='Convert to HTML', parents=[global_parser], add_help=True)
    parser_html.add_argument('--quiz_mode', help='Change the HTML into an interactable quiz!', default=default_html_opts['quiz_mode'], action='store_true')
    
    # Markdown transform
    parser_markdown = transform_parser.add_parser('markdown', help='Convert to MARKDOWN', parents=[global_parser], add_help=True)

    # YAML transform
    parser_yaml = transform_parser.add_parser('yaml', help='Convert to YAML', parents=[global_parser], add_help=True)
    parser_yaml.add_argument('--root_name', type=str, help='Root name of YAML', default=default_yaml_opts['root_name'])

    # JSON transform
    parser_json = transform_parser.add_parser('json', help='Convert to JSON', parents=[global_parser], add_help=True)
    parser_json.add_argument('--root_name', type=str, help='Root name of JSON', default=default_json_opts['root_name'])

    # CSV transform
    parser_csv = transform_parser.add_parser('csv', help='Convert to CSV', parents=[global_parser], add_help=True)

    # TOML transform
    parser_toml = transform_parser.add_parser('toml', help='Convert to TOML', parents=[global_parser], add_help=True)
    parser_toml.add_argument('--question_prefix', type=str, help='Prefix to use in TOML output (<prefix>.<question num>)', default=default_toml_opts['question_prefix'])

    # TXT transform
    parser_text = transform_parser.add_parser('txt', help='Convert to TXT', parents=[global_parser], add_help=True)

    parser.set_defaults(transform=default_io_opts['transform'])
    args = parser.parse_args(remaining_argv)

    data_df = read_csv_file(args.file_path, presenter=args.presenter, encoding=args.encoding, rhidden=args.remove_hidden, rimages=args.remove_images, shuffle=(not args.noshuffle), remove_start_len=args.remove_start_len)

    name, _ = os.path.splitext(args.file_path)

    show_correct = (not args.nosolutions)

    # check transform type
    
    if args.transform == 'tex':
        to_tex_exam(data_df, os.path.join(args.output_path, f'{name}.tex'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_tex_opts))
    elif args.transform == 'yaml':
        to_yaml_report(data_df, os.path.join(args.output_path, f'{name}.yaml'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_yaml_opts))
    elif args.transform == 'json':
        to_json_report(data_df, os.path.join(args.output_path, f'{name}.json'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_json_opts))
    elif args.transform == 'csv':
        to_csv_report(data_df, os.path.join(args.output_path, f'{name}.csv'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_csv_opts))
    elif args.transform == 'html':
        # Handle HTML differently (placed in it's own directory with the CSS file copied over)

        html_path = os.path.join(args.output_path, f'{name}-html')
        try:
            os.mkdir(html_path)
        except Exception:
            pass
        
        to_html_report(data_df, os.path.join(html_path, f'{name}.html'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_html_opts))
        
        # copy over the CSS and JS file
        try:
            shutil.copyfile(styles_path, os.path.join(html_path, f'html-styles.css'))

            # only copy js if quiz mode
            if args.quiz_mode:
                shutil.copyfile(js_path, os.path.join(html_path, f'html-js.js'))
        except Exception:
            pass
    elif args.transform == 'toml':
        to_toml_report(data_df, os.path.join(args.output_path, f'{name}.toml'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_toml_opts))
    elif args.transform == 'markdown':
        to_markdown_report(data_df, os.path.join(args.output_path, f'{name}.md'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_toml_opts))
    elif args.transform == 'txt':
        to_txt_exam(data_df, os.path.join(args.output_path, f'{name}.txt'), encoding=args.encoding, show_correct=show_correct, **update_defaults(args, default_text_opts))
    
    else:
        raise ValueError("You can't use that type of output transform, look at the docs for help.")

if __name__ == '__main__':
    main()