"""
    - run this file with args state_key, input_file_name, release_number and release_date
    - except input_file_name all the commandline args are mandatory
"""
import importlib
import argparse
import os


class HtmlParseRunner:

    @staticmethod
    def start_parser(state_key):
        from parser_base import ParserBase
        parser_base = ParserBase()
        parser_base.start(state_key)


if __name__ == '__main__':
    """
        - Parse the command line args
        - set environment variables using parsed command line args
        - Call start parse method with state_key as arg 
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--state_key", help="State of which parser should be run", required=True, type=str)
    parser.add_argument("--input_file_name", help="file which needs to be parsed",  type=str)
    parser.add_argument("--release_number", help="release which file belongs to", required=True, type=str)
    parser.add_argument("--release_date", help="release which file belongs to", required=True, type=str)
    args = parser.parse_args()
    os.environ.setdefault('input_file_name', args.input_file_name if args.input_file_name else '')
    os.environ.setdefault('release_number', args.release_number)
    os.environ.setdefault('release_date', args.release_date)
    HtmlParseRunner.start_parser(args.state_key)
