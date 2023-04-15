import argparse
import os
import pandas as pd
import yaml
import json
import random

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
        
        end_spacing: int = 4,
        end_spacing_metric: str = 'pt',
        
        **kwargs
    ) -> str:
    """
    Converts the current row into a LaTeX block question.


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

    strbuilder.append(r'\begin{' + block_type + r'}')
    strbuilder.append(title)
    strbuilder.append(r'\end{' + block_type + r'}\\')

    strbuilder.append(r'\begin{' + resp_block_type + r'}')
    for resp in responses['responses']:
        resp_new = change_tex_chars(resp)
        if resp in responses['correct']:
            strbuilder.append(rf"\CorrectChoice {resp_new}\\[{end_spacing}{end_spacing_metric}]")
        else:
            strbuilder.append(rf"\choice {resp_new}\\[{end_spacing}{end_spacing_metric}]")

    strbuilder.append(r'\end{' + resp_block_type + r'}' + "\n")

    return "\n".join(strbuilder)

def to_tex_exam(data_df: pd.DataFrame, output_file: str, encoding: str = None):
    """
    Converts the CSV dataframe into a LaTeX exam report.

    :param data_df: The dataframe
    :param output_file: The file to output to (.TeX)
    :param encoding: The encoding to use when outputting
    """

    try: 

        data_df['strquestion'] = data_df.apply(lambda x: tex_helper(x), axis=1)

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

def to_csv_report(data_df: pd.DataFrame, output_file: str, encoding: str = None):

    data_df.to_csv(output_file, encoding=encoding)

def main():
    """
    Main script executable.
    """
    parser = argparse.ArgumentParser(description='Read CSV file with optional screen name filter')
    parser.add_argument('file_path', type=str, help='Path to the CSV file')
    parser.add_argument('--presenter', type=str, help='Presenter name to filter (optional)', default=None)
    parser.add_argument('--output_path', type=str, help='Path for output file (optional)', default=os.getcwd())
    parser.add_argument('--transform', type=str, help='Transform to apply (optional)', default='yaml')
    parser.add_argument('--encoding', type=str, help='Encoding for reading and writing (optional)', default='utf-8')
    
    # subparser for individual commands
    transform_parser = parser.add_subparsers(dest='transform')

    # LaTeX transform
    parser_tex = transform_parser.add_parser('tex', help='Convert to LaTeX')
    parser_tex.add_argument('--block_type', type=str, help='LaTeX block type to use for question title', default='question')
    parser_tex.add_argument('--resp_block_type', type=str, help='LaTeX block type to use for question responses', default='oneparcheckboxes')
    parser_tex.add_argument('--remove_start_len', type=int, help='How far into the string to look when removing the question prefix', default=4)
    parser_tex.add_argument('--end_spacing', type=int, help='The amount of space to add after each response option', default=4)
    parser_tex.add_argument('--end_spacing_metric', type=str, help='The metric for end_spacing', default='pt')
    
    # HTML transform
    parser_html = transform_parser.add_parser('html', help='Convert to HTML')

    # YAML transform
    parser_yaml = transform_parser.add_parser('yaml', help='Convert to YAML')

    # JSON transform
    parser_json = transform_parser.add_parser('json', help='Convert to JSON')

    # CSV transform
    parser_csv = transform_parser.add_parser('csv', help='Convert to CSV')

    # TOML transform
    parser_csv = transform_parser.add_parser('toml', help='Convert to TOML')

    args = parser.parse_args()
    
    data_df = read_csv_file(args.file_path, presenter=args.presenter, encoding=args.encoding)

    name, _ = os.path.splitext(args.file_path)

    # check transform type
    if args.transform == 'tex':
        to_tex_exam(data_df, os.path.join(args.output_path, f'{name}.tex'), encoding=args.encoding)
    elif args.transform == 'yaml':
        to_yaml_report(data_df, os.path.join(args.output_path, f'{name}.yaml'), encoding=args.encoding)
    elif args.transform == 'json':
        to_json_report(data_df, os.path.join(args.output_path, f'{name}.json'), encoding=args.encoding)
    elif args.transform == 'csv':
        to_csv_report(data_df, os.path.join(args.output_path, f'{name}.csv'), encoding=args.encoding)
    elif args.transform == 'html':
        to_html_report(data_df, os.path.join(args.output_path, f'{name}.html'), encoding=args.encoding)
    else:
        raise ValueError("You can't use that type of output transform, look at the docs for help.")

if __name__ == '__main__':
    main()