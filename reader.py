import argparse
import os
import pandas as pd
import yaml
import json
import random
import configparser




TEX_CHARS_ESCAPE = ['%']
QUESTION_START_CHARS = [')', '.', ']', '&']

def read_csv_file(file_path, presenter:str=None, **kwargs):
    """
    Read a CSV file into pandas and filter by presenter.

    :param file_path: The CSV file path (to read)
    :param presenter: The presenter to filter by
    :param kwargs: Any keyword arguments for read_csv

    :return: The read data in a dataframe
    """
    data_df = pd.read_csv(file_path, **kwargs)
    if presenter is not None:
        data_df = data_df[data_df["Presenter"] == presenter]

    data_df = data_df[data_df["Activity type"] == "Multiple choice"]

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
                break
        except ValueError:
            pass
        except IndexError:
            pass
    return s

def get_title_and_responses(
        row,
        title_col: str = 'Activity title',
        remove_start_len: int = 4,
        response_options_col:str = 'Response options',
        response_options_delim: str = " | ", 
        correct_in_response: str = '(Correct)',
        shuffle: bool = True
):
    """
    :param row: Current row of dataframe
    :param title_col: The title with the question name
    :param response_options_col: The column with response options
    :param response_options_delim: The delimiter between response options
    :param correct_in_response: The delimiter that signifies a response is correct
    :param shuffle: Whether to shuffle the responses or not

    :return: Mapping of responses and correct response, and title
    """
    responses = row[response_options_col].split(response_options_delim)  # split the responses
    
    resp_dct = {
        'responses': [],
        'correct': []
    }
    for resp in responses:
        resp = remove_question_start(resp, remove_start_len)

        # remove any spaces at the beginning
        try:
            while resp[0] == " ":
                resp = resp[1:]
        except IndexError:
            pass

        if correct_in_response in resp:
            resp = resp.replace(correct_in_response, "")
            resp_dct['correct'].append(resp)

        resp_dct['responses'].append(resp)

    if shuffle:
        random.shuffle(resp_dct['responses'])
    
    title = row[title_col]
    title = remove_question_start(title, remove_start_len)

    return resp_dct, title

def tex_helper(
        row,
        block_type: str = 'question',
        resp_block_type: str = 'oneparcheckboxes',
        resp_opt_block_type: str = 'choice',
        resp_opt_correct_block_type: str = 'CorrectChoice',
        end_spacing: int = 4,
        end_spacing_metric: str = 'pt',
        **kwargs
    ) -> str:
    """
    Converts the current row into a LaTeX block question.


    :param block_type: The LaTeX block type to use for the question title
    :param resp_block_type: The LaTeX block type to use for the question responses (wrapped block)
    :param resp_opt_block_type: The LaTeX block type to use for the question response option (if not correct)
    :param resp_opt_correct_block_type: The LaTeX block type to use for the question response option (if correct)
    :param remove_start_len: How far into the string to look when removing the question prefix
    :param end_spacing: The amount of space to add after each response option
    :param end_spacing_metric: The metric for end_spacing

    :return: The string representing the LaTeX block
    """

    strbuilder = []

    responses, title = get_title_and_responses(row, **kwargs)
    title = change_tex_chars(title)

    strbuilder.append(r'\begin{' + block_type + r'}')
    strbuilder.append(title)
    strbuilder.append(r'\end{' + block_type + r'}\\')

    strbuilder.append(r'\begin{' + resp_block_type + r'}')
    for resp in responses['responses']:
        resp_new = change_tex_chars(resp)
        if resp in responses['correct']:
            strbuilder.append(rf"\{resp_opt_correct_block_type} {resp_new}\\[{end_spacing}{end_spacing_metric}]")
        else:
            strbuilder.append(rf"\{resp_opt_block_type} {resp_new}\\[{end_spacing}{end_spacing_metric}]")

    strbuilder.append(r'\end{' + resp_block_type + r'}' + "\n")

    return "\n".join(strbuilder)

def to_tex_exam(data_df: pd.DataFrame, output_file: str, encoding: str = None, **kwargs):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    :param kwargs: keyword arguments for every tex block
    """

    try: 

        data_df['strquestion'] = data_df.apply(lambda x: tex_helper(x, **kwargs), axis=1)

        with open(output_file, 'w', encoding=encoding) as out_file:
            
            out_file.write(r"\begin{questions}" + "\n")
            for i, row in data_df.iterrows():
                
                out_file.write(row['strquestion'])

            out_file.write(r"\end{questions}" + "\n")

        data_df.drop(columns=['strquestion'], inplace=True)

    except KeyError:
        raise ValueError("Column couldn't be found, can't continue.")
    

def html_helper(
        row,
        correct_class: str = 'correct',
        incorrect_class: str = 'incorrect',
        **kwargs
    ) -> str:
    """
    Converts the current row into a HTML block.


    :param block_type: The LaTeX block type to use for the question title
    :param resp_block_type: The LaTeX block type to use for the question responses
    :param remove_start_len: How far into the string to look when removing the question prefix
    :param end_spacing: The amount of space to add after each response option
    :param end_spacing_metric: The metric for end_spacing

    :return: The string representing the LaTeX block
    """

    strbuilder = []

    responses, title = get_title_and_responses(row, **kwargs)
    title = change_tex_chars(title)

    strbuilder.append(rf'<li>{title}</li>')

    strbuilder.append('\t<ol type="a">')
    for resp in responses['responses']:
        resp_new = resp
        if resp in responses['correct']:
            strbuilder.append(f"\t\t<li class={correct_class}>{resp_new}</li>")
        else:
            strbuilder.append(f"\t\t<li class={incorrect_class}>{resp_new}</li>")

    strbuilder.append('\t</ol>\n')

    return "\n".join(strbuilder)

def to_html_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    """

    try: 
        name, _ = os.path.splitext(output_file)

        html_lst =  '\n'.join(data_df.apply(lambda x: html_helper(x), axis=1))

        html_gen = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <title>{name}</title>
        </head> 
        <body>
        <h1>PollEverywhere Report</h1>           
        {html_lst}
        </body>
        </html>
        '''

        

        with open(output_file, 'w', encoding=encoding) as out_file:
            out_file.write(html_gen)

    except KeyError:
        raise ValueError("Column couldn't be found, can't continue.")


def yaml_helper(row, **kwargs):


    responses, title = get_title_and_responses(row, **kwargs)

    return {
        'title': title,
        'responses': responses['responses'],
        'correct': responses['correct']
    }
    

def to_dict_style(data_df: pd.DataFrame):
    """
    Converts the CSV dataframe into a YAML report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.yaml)
    :param encoding: The encoding to use when outputting
    """

    dct = {}
    i = 1

    def help(row): 
        nonlocal i
        dct[str(i)] = yaml_helper(row)
        i += 1

    data_df.apply(lambda x: help(x), axis=1)

    return dct


def to_yaml_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):

    dct = to_dict_style(data_df)

    with open(output_file, 'w', encoding=encoding) as out_file:
        yaml.dump(dct, out_file)

def to_json_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):

    dct = to_dict_style(data_df)

    with open(output_file, 'w', encoding=encoding) as out_file:
        json.dump(dct, out_file)

def to_toml_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):
    import toml

    dct = to_dict_style(data_df)

    with open(output_file, 'w', encoding=encoding) as out_file:
        toml.dump(dct, out_file)

def to_csv_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):

    data_df.to_csv(output_file, encoding=encoding)

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
    return kw

def main():
    """
    Main script executable.
    """

    # define default values
    default_io_opts = dict(
        output_path = os.getcwd(),
        encoding = 'utf-8',
        transform = 'csv',
        remove_start_len = 5,
        shuffle_options = True,
        config = 'config.ini'
    )

    default_tex_opts = dict(
        block_type = 'question',
        resp_block_type = 'openparboxes',
        resp_opt_block_type = 'choice',
        resp_opt_correct_block_type = 'CorrectChoice',
        end_spacing = 4,
        end_spacing_metric = 'pt'
    )

    default_html_opts = dict(

    )

    default_json_opts = dict(
        
    )

    default_yaml_opts = dict(
        
    )

    default_toml_opts = dict(
        
    )

    default_csv_opts = dict(
        
    )


    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument('--config_path', type=str, help='Path to the configuration file (optional)', default=None)
    config_args, remaining_argv = config_parser.parse_known_args()

    
    # allow the user to override defaults using the config path
    if config_args.config_path:

        default_io_opts['config'] = config_args.config_path

        try:
            config = configparser.ConfigParser()
            config.read(default_io_opts['config'])

            print(config['pollev_output']['shuffle_options'])

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
                default_toml_opts.update(update_defaults_config(default_csv_opts, config, 'pollev_transforms.toml'))
        
        except FileNotFoundError:
            parser.set_defaults(transform=default_io_opts['transform'])
            args, _ = parser.parse_known_args(remaining_argv)
            pass

    global_parser = argparse.ArgumentParser(description='Read CSV file with optional screen name filter', add_help=False)
    global_parser.add_argument('--config_path', type=str, help='Path to the configuration file (optional)', default=default_io_opts['config'])
    global_parser.add_argument('--presenter', type=str, help='Presenter name to filter (optional)', default=None)
    global_parser.add_argument('--output_path', type=str, help='Path for output file (optional)', default=default_io_opts['output_path'])
    global_parser.add_argument('--encoding', type=str, help='Encoding for reading and writing (optional)', default=default_io_opts['encoding'])
    global_parser.add_argument('--shuffle_options', type=bool, help='Whether to shuffle the response options of questions', default=default_io_opts['shuffle_options'])
    global_parser.add_argument('--remove_start_len', type=int, help='How far into the string to look when removing the question or response prefix', default=default_io_opts['remove_start_len'])

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

    # YAML transform
    parser_yaml = transform_parser.add_parser('yaml', help='Convert to YAML', parents=[global_parser], add_help=True)

    # JSON transform
    parser_json = transform_parser.add_parser('json', help='Convert to JSON', parents=[global_parser], add_help=True)

    # CSV transform
    parser_csv = transform_parser.add_parser('csv', help='Convert to CSV', parents=[global_parser], add_help=True)

    # TOML transform
    parser_toml = transform_parser.add_parser('toml', help='Convert to TOML', parents=[global_parser], add_help=True)

    parser.set_defaults(transform=default_io_opts['transform'])
    args = parser.parse_args(remaining_argv)
    data_df = read_csv_file(args.file_path, presenter=args.presenter, encoding=args.encoding)

    name, _ = os.path.splitext(args.file_path)

    # check transform type
    if args.transform == 'tex':
        to_tex_exam(data_df, os.path.join(args.output_path, f'{name}.tex'), encoding=args.encoding, **update_defaults(args, default_tex_opts))
    elif args.transform == 'yaml':
        to_yaml_report(data_df, os.path.join(args.output_path, f'{name}.yaml'), encoding=args.encoding, **update_defaults(args, default_yaml_opts))
    elif args.transform == 'json':
        to_json_report(data_df, os.path.join(args.output_path, f'{name}.json'), encoding=args.encoding, **update_defaults(args, default_json_opts))
    elif args.transform == 'csv':
        to_csv_report(data_df, os.path.join(args.output_path, f'{name}.csv'), encoding=args.encoding, **update_defaults(args, default_csv_opts))
    elif args.transform == 'html':
        to_html_report(data_df, os.path.join(args.output_path, f'{name}.html'), encoding=args.encoding, **update_defaults(args, default_html_opts))
    elif args.transform == 'toml':
        to_toml_report(data_df, os.path.join(args.output_path, f'{name}.toml'), encoding=args.encoding, **update_defaults(args, default_toml_opts))
    else:
        raise ValueError("You can't use that type of output transform, look at the docs for help.")

if __name__ == '__main__':
    main()