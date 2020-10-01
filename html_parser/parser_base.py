"""
    - start method of this file is called by html_parse_runner
    - based on passed arguments start method of html parser is called
"""
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

    def start(self, state_key):
        if input_file_name := os.environ.get('input_file_name'):
            """
                    - if the input_file_name args is passed to the program
                      then start_parse method of html_parser and pass pass the input file name
                """
            from ga_html_parser import GAParseHtml
            ga_parser = GAParseHtml()
            ga_parser.start_parse(input_file_name)
        else:
            self.folder_ = """
                      - if input file name is not passed get all the file name present in the raw files folder
                      - call method run_with_multiprocessing_pool with list of file names present in raw folder
                  """
            self.cpu_count = multiprocessing.cpu_count()
            print(self.cpu_count)
            input_files_list = listdir(f'../transforms/{state_key}/oc{state_key}/r{self.release_number}/raw/')
            self.run_with_multiprocessing_pool(input_files_list)

    def run_with_multiprocessing_pool(self, files_list):
        """
            - create a pool based of number of cores available
            - call wrapper function with one file name at a time
        """
        with multiprocessing.Pool(self.cpu_count) as pool:
            pool.map_async(self.wrapper_function, files_list)
            pool.close()
            pool.join()

    def wrapper_function(self, files_list):
        """
            - call start_parse method of html_parser with passed file name
            - log any errors thrown by html parser
        """
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
