import multiprocessing
from os import listdir
import os
import traceback


class ParserBase:
    def __init__(self):
        self.cpu_count = None
        self.release_number = os.environ.get("release_number")
        self.release_date = os.environ.get("release_date")
        self.release_label = None
        self.html_file_name = None

    def start(self):
        if input_file_name := os.environ.get('input_file_name'):
            from ga_html_parser import GAParseHtml
            ga_parser = GAParseHtml()
            ga_parser.start_parse(input_file_name)
        else:
            self.cpu_count = multiprocessing.cpu_count()
            print(self.cpu_count)
            input_files_list = listdir(f'../transforms/ga/ocga/r{self.release_number}/raw/')
            self.run_with_multiprocessing_pool(input_files_list)

    def run_with_multiprocessing_pool(self, files_list):
        with multiprocessing.Pool(self.cpu_count) as pool:
            pool.map_async(self.wrapper_function, files_list)
            pool.close()
            pool.join()

    def wrapper_function(self, files_list):
        logger = multiprocessing.get_logger()
        try:
            from ga_html_parser import GAParseHtml
            ga_parser = GAParseHtml()
            ga_parser.start_parse(files_list)
        except Exception as e:
            exceptioon = f'{e}\n--------------------------------\n' \
                         f'{self.html_file_name}'
            logger.error(exceptioon, traceback.format_exc())

    def start_parse(self, input_file_name):
        raise NotImplemented
