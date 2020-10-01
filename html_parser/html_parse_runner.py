import importlib
import argparse
import os


class HtmlParseRunner:

    @staticmethod
    def start_parser(state_key):
        # parser_class = getattr(importlib.import_module(f'{state_key}_html_parser'),
        #                            f'{state_key.upper()}ParseHtml')
        # parser_class()
        from parser_base import ParserBase
        parser_base = ParserBase()
        parser_base.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--state_key", help="State of which parser should be run", required=True, type=str)
    parser.add_argument("--input_file_name", help="file which needs to be parsed",  type=str)
    parser.add_argument("--release_number", help="release which file belongs to", required=True, type=str)
    parser.add_argument("--release_date", help="release which file belongs to", required=True, type=str)
    args = parser.parse_args()
    os.environ.setdefault('input_file_name', args.input_file_name if args.input_file_name else '')
    os.environ.setdefault('release_number', args.release_number)
    os.environ.setdefault('release_date', args.release_date)
    HtmlParseRunner.start_parser(args.state_key.lower())
