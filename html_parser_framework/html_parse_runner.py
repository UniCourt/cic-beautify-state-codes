"""
    - run this file with args state_key and path
    -  all the commandline args are mandatory
    - path can be given for single file, all files of single release and all files of state accordingly.
"""

import argparse
import concurrent
import glob
import importlib
import multiprocessing
import re
import traceback
from datetime import datetime

import roman
from loguru import logger
from concurrent.futures import ProcessPoolExecutor
import os
import logging
from bs4 import BeautifulSoup


def start_parsing(arguments):
    """
        - checking all arguments
        - checking the path and based on given path the files are parsed
        - files are parsed : single file , all files of particular release and
        all files of particular state.
    """

    release_number = None
    cpu_count = multiprocessing.cpu_count()
    file_list = []
    state_key = arguments.state_key
    path = arguments.path
    run_after_release = arguments.run_after_release

    script = f'{state_key.lower()}_html_parser'
    class_name = f'{state_key}ParseHtml'
    parser_obj = getattr(importlib.import_module(script), class_name)

    if os.path.exists(path):  # validation for path
        if os.path.isfile(path):  # checking given path is file or not.
            input_file_name = os.path.basename(path)
            release_number = re.search(r'/r(?P<rid>\d+)', os.path.dirname(path)).group("rid")
            soup_obj = parser_obj(state_key, path, release_number, input_file_name).run()
            id_dictionary = getting_header_id_dict(state_key, release_number)
            add_cite_to_file(soup_obj[0], soup_obj[1], state_key, release_number, input_file_name, id_dictionary)

        else:
            subdirectories_files = [x for x in glob.glob(f'{path}/**', recursive=True) if os.path.isfile(x)]
            if run_after_release:
                run_after_release = int(run_after_release)
                for file in subdirectories_files:
                    release_number = int(re.search(r'(?P<rnum>\d+)$', os.path.dirname(file)).group("rnum"))
                    if release_number >= run_after_release:
                        file_list.append(file)
            else:
                file_list += subdirectories_files
    else:
        logging.exception("Invalid path", f'{path}')

    with ProcessPoolExecutor(cpu_count) as executor:
        future_list = []
        for file in file_list:
            release_number = re.search(r'(?P<r_num>\d+)$', os.path.dirname(file)).group("r_num")
            future_obj = [executor.submit(parser_obj(state_key, file, release_number, os.path.basename(file)).run)]
            future_list.append({future_obj[0]: [os.path.basename(file), release_number]})

        executor.shutdown(wait=True)
        id_dictionary = getting_header_id_dict(state_key, release_number)

        for item in future_list:
            for future_obj in concurrent.futures.as_completed(item.keys()):
                try:
                    s, m = future_obj.result()
                    add_cite_to_file(s, m, state_key, item[future_obj][1],
                                     os.path.basename(item[future_obj][0]), id_dictionary)
                except Exception as exc:
                    exception_on = f'{exc}\n------------------------\n' \
                                   f'{item[future_obj][0]}'
                    logging.exception(exception_on, traceback.format_exc())


def getting_header_id_dict(state_key, release_number):
    id_dictionary = {}
    id_files = os.listdir(f'{state_key}_cite_id/{state_key}{release_number}')
    for file in id_files:
        with open(f'{state_key}_cite_id/{state_key}{release_number}/{file}') as f:
            for line in f:
                (key, value) = line.split()
                id_dictionary[key] = value
    return id_dictionary


def add_cite_to_file(soup_obj, meta_tag, state_key, release_number, input_file_name, id_dictionary):
    cite_parser_obj = getattr(importlib.import_module('regex_pattern'), f'CustomisedRegex{state_key}')()
    soup = BeautifulSoup(soup_obj, "html.parser")

    cite_p_tags = []
    for tag in soup.findAll(
            lambda tag: getattr(cite_parser_obj, "cite_tag_pattern").search(tag.get_text()) and tag.name in ['p', 'li']
                        and tag not in cite_p_tags and not tag.a and tag.parent.name != 'ul'):
        cite_p_tags.append(tag)
        text = str(tag)

        for match in set(x[0] for x in getattr(cite_parser_obj, "cite_pattern").findall(tag.text.strip())):

            inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>|<p.+>|^<li id="[a-z.A-Z\d-]+">|</li>$', '',
                                 text, re.DOTALL)
            id_reg = getattr(cite_parser_obj, "cite_pattern").search(match.strip())

            if re.search(r'^(?P<name>[a-zA-Z.]+\.)(?P<tid>(\d+(\.\w)*)|(\d+\w*)|(\d+[A-Z]?\.\d+[A-Z]?))\.html$',
                         input_file_name.strip()):
                file_name_pattern = re.search(
                    r'^(?P<name>[a-zA-Z.]+\.)(?P<tid>(\d+(\.\w)*)|(\d+\w*)|(\d+[A-Z]?\.\d+[A-Z]?))\.html$',
                    input_file_name.strip())
                title_id = file_name_pattern.group("tid").zfill(2)
                file_name = file_name_pattern.group("name")
            else:
                file_name = f"{re.search(r'^(?P<name>[a-zA-Z.]+)constitution', input_file_name.strip()).group('name')}title."
                title_id = None

            if state_key == "NC":
                if re.search(r'^\d{3}[A-Z]*', id_reg.group("title").strip()):
                    cite_title_id = id_reg.group("title").strip()
                elif re.search(r'^\d{2}[A-Z]*', id_reg.group("title").strip()):
                    cite_title_id = f'0{id_reg.group("title").strip()}'
                else:
                    cite_title_id = f'00{id_reg.group("title").strip()}'
            elif state_key == 'VA':
                if re.search(r'^\d\.\d[A-Z]?', id_reg.group("title").strip()):
                    title_reg = re.search(r'^(?P<id1>\d)\.(?P<id2>\d[A-Z]?)', id_reg.group("title").strip())
                    if id_reg.group("title").strip() in ['2.1', '2.2', '3.1', '3.2', '4.1', '5.1', '6.1', '7.1', '6.2']:
                        cite_title_id = f'0{title_reg.group("id1")}.{title_reg.group("id2")}'
                    else:
                        cite_title_id = f'0{title_reg.group("id1")}.0{title_reg.group("id2")}'
                else:
                    cite_title_id = id_reg.group("title").strip().zfill(2)
            else:
                cite_title_id = id_reg.group("title").strip().zfill(2)

            if id_reg.group("ol"):
                ol_id = re.sub(r'[() ]+', '', id_reg.group("ol"))
                cite_pattern = f'{id_reg.group("cite")}ol1{ol_id}'
            else:
                cite_pattern = id_reg.group("cite")

            if cite_pattern in id_dictionary:
                cite_id = id_dictionary[cite_pattern]
                if state_key == "KY":
                    t_id = re.search(r'^t0?(?P<tid>[IVXL]+)', cite_id).group("tid")
                    cite_title_id = roman.fromRoman(t_id.upper())
                    cite_title_id = f'{cite_title_id:02}'
                if cite_title_id == title_id:
                    target = "_self"
                    a_id = f'#{cite_id}'
                else:
                    target = "_blank"
                    a_id = f'{file_name}{cite_title_id}.html#{cite_id}'
                tag.clear()
                text = re.sub(fr'\s{re.escape(match)}',
                              f' <cite class="oc{state_key.lower()}"><a href="{a_id}" target="{target}">{match}</a></cite>',
                              inside_text, re.I)

                tag.append(BeautifulSoup(text, features="html.parser"))

            elif not os.path.exists(
                    f'{state_key}_cite_id/{state_key}{release_number}/{state_key}{release_number}_{cite_title_id}_ids.txt'):
                logger.error(f"parsing {file_name}{cite_title_id}.html is incomplete....unable to add citation")

        for match in set(
                x[0] for x in getattr(cite_parser_obj, "code_pattern").findall(tag.text.strip())):
            inside_text = re.sub(r'^<p.*>|</p>$|^<li id="[a-z.A-Z\d-]+">|</li>$', '', text, re.DOTALL)
            tag.clear()
            text = re.sub(re.escape(match), f'<cite class="{state_key.lower()}_code">{match}</cite>', inside_text, re.I)
            tag.append(BeautifulSoup(text, features="html.parser"))

    for li_tag in soup.findAll("li"):
        if re.search(r'^<li.+><li.+>', str(li_tag).strip()):
            li_tag_text = re.sub(r'^\[<li.+>|</li>]$', '', str(li_tag.contents))
            li_tag.clear()
            li_tag.append(BeautifulSoup(li_tag_text, features="html.parser"))

    soup_str = str(soup.prettify())
    for tag in meta_tag:
        cleansed_tag = re.sub(r'/>', ' />', str(tag))
        soup_str = re.sub(rf'{tag}', rf'{cleansed_tag}', soup_str, re.I)

    with open(
            f"../../cic_code_framework/transforms//{state_key.lower()}/oc{state_key.lower()}"
            f"/r{release_number}/{input_file_name}", "w") as file:
        soup_str = re.sub(r'<span class.*?>\s*</span>|<p>\s*</p>|<b>\s*</b>', '', soup_str)
        file.write(soup_str)

    print("cite added", input_file_name)


if __name__ == '__main__':
    """
        - Parse the command line args
        - set environment variables using parsed command line args
        - Call start parsing method with args as arguments
    """
    start_time = datetime.now()
    logger.info(start_time)
    parser = argparse.ArgumentParser()
    parser.add_argument("--state_key", help="State of which parser should be run", required=True, type=str)
    parser.add_argument("--path", help="file path which needs to be parsed", required=True, type=str)
    parser.add_argument("--run_after_release", help="particular files which needs to be parsed", type=str)
    args = parser.parse_args()
    start_parsing(args)
    logger.info(datetime.now() - start_time)
