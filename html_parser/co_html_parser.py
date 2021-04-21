from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase


class coParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        # self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)|^(CONSTITUTION OF KENTUCKY)',
        #                     'sec_head': r'^([^\s]+[^\D]+)',
        #                     'junk': '^(Text)', 'ol': r'^(\(1\))', 'head4': '^(NOTES TO DECISIONS)','nd_nav':'^1\.'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name

        self.watermark_text = """Release {0} of the Official Code of Kentucky Annotated released {1}.
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
        This document is not subject to copyright and is in the public domain.
        """

        self.start_parse()

    def create_page_soup(self):

        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """

        with open(f'../transforms/co/occo/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')



    def get_class_name(self):

        """
                    - Find the textutil generated class names for each type of tag (h1, h2, ....)
                      using re pattern specified in self.tag_type_dict
        """
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            if tag_class:
                self.class_regex[key] = tag_class.get('class')[0]

        print(self.class_regex)
        print('updated class dict')


    def remove_junk(self):
        """
                 - Delete the junk tags (empty tags,span tags and unwanted meta tags)
                 - Add new meta tags for storing release related information of parsed html
                 - Rename <br> tags
             """

        for junk_tag in self.soup.find_all(class_=self.class_regex['junk']):
            junk_tag.decompose()


        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()

        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)

        print('junk removed')



    def set_appropriate_tag_name_and_id(self, tag_name, header_tag, chap_nums, prev_id, sub_tag, class_name):
        if re.search('constitution', self.html_file_name):
            header_tag.name = tag_name
            header_tag.attrs = {}
            header_tag["class"] = class_name
            if prev_id:
                header_tag['id'] = f"{prev_id}{sub_tag}{chap_nums}"
            else:
                header_tag['id'] = f"{self.title_id}{sub_tag}{chap_nums}"
        # else:
        #     header_tag.name = tag_name
        #     header_tag.attrs = {}
        #     header_tag["class"] = class_name
        #     if prev_id:
        #         header_tag['id'] = f"{prev_id}{sub_tag}{chap_nums}"
        #     else:
        #         header_tag['id'] = f"t{self.title_id}{sub_tag}{chap_nums}"

    def replace_tags(self):
        snav = 0
        cnav = 0
        anav = 0
        pnav = 0
        chapter_id_list = []
        header_list = []
        note_list = []
        cur_id_list = []
        repeated_header_list = []
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search('constitution\.us', self.html_file_name):
                        self.title_id = "constitution-us"
                    else:
                        self.title_id = "constitution-co"

                    header_tag.name = "h1"
                    header_tag.attrs = {}
                    # header_tag.wrap(self.soup.new_tag("nav"))


                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE', header_tag.text.strip(),re.I):
                        tag_name = "h2"
                        prev_id = None
                        chap_num = None
                        sub_tag = None

                        if re.search(r'^(ARTICLE)', header_tag.text.strip()):
                            chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[A-Z]+))', header_tag.text.strip()).group(
                                "ar").zfill(2)
                            sub_tag = "-ar"
                            class_name = "articleh2"

                            self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                                    class_name)

                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[\s]+','',header_tag.text.strip())
                        sub_tag = 'c'
                        class_name = "chapterh2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["art_head"]]:
                    if re.search(r'^(ARTICLE)', header_tag.text.strip()):
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[I,V,X]{0,3}))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

    def recreate_tag(self):
        for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
            current_p_tag = p_tag.text.strip()
            if re.search('^§', current_p_tag):
                if re.search('^§',p_tag.find_next("b").text.strip()):
                    p_tag_text = re.sub(r'^§ \d+\.','',current_p_tag)

                    p_tag.string = p_tag_text
                    p_tag.find_next("b").name = "h3"




                # else:
                #     print()
















    # writting soup to the file
    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"/home/mis/cic-code-co/transforms/co/occo/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    # add css file
    def css_file(self):
        head = self.soup.find("head")
        style = self.soup.head.find("style")
        style.decompose()
        css_link = self.soup.new_tag("link")
        css_link.attrs[
            "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
        css_link.attrs["rel"] = "stylesheet"
        css_link.attrs["type"] = "text/css"
        head.append(css_link)

    def start_parse(self):

        """
                     - set the values to instance variables
                     - check if the file is constitution file or title file
                     - based on file passed call the methods to parse the passed htmls
        """

        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.css_file()


        if re.search('constitution', self.html_file_name):
            self.class_regex = {'ul': '^(§ )|^(ARTICLE)', 'head2': '^(§ )|^(ARTICLE)',
                                'title': '^Declaration of Independence|^Constitution of the State of Colorado|^COLORADO COURT RULES',
                                'sec_head': r'^([^\s]+[^\D]+)|^(Section)',
                                'junk': '^Statute text', 'ol': r'^(\(1\))',
                                'head4': '^(NOTES TO DECISIONS)|^(Compiler’s Notes.)','art_head': '^ARTICLE'}

            self.get_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
        #     self.create_main_tag()
        #     self.create_ul_tag()
        #     self.create_chapter_section_nav()
        #     self.create_ref_link_to_notetodecision_nav()
        #     self.create_ul_tag_to_notes_to_decision()
        #     self.create_and_wrap_with_div_tag()
        #     self.add_citation1()
        #     self.add_watermark_and_remove_class_name()
        #
        # else:
        #     self.get_class_name()
        #     self.remove_junk()
        #     self.replace_tags()
        #     self.create_main_tag()
        #     self.create_ul_tag()
        #     self.create_chapter_section_nav()
        #     self.create_ref_link_to_notetodecision_nav()
        #     self.create_ul_tag_to_notes_to_decision()
        #     self.create_and_wrap_with_div_tag()
        #     self.wrap_with_ordered_tag()
        #     self.create_numberical_ol()
        #     self.add_citation1()
        #     self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)

