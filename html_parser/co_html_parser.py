from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase
import roman


class coParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^Art.', 'head2': '^ARTICLE ',
                            'title': '^(TITLE)|^(CONSTITUTION OF KENTUCKY)',
                            'sec_head': r'^\d+(\.\d+)*-\d+-\d+\.', 'part_head': '^PART\s\d+',
                            'junk': '^Annotations', 'ol': r'^(\(1\))', 'head4': '^ANNOTATION', 'nd_nav': '^1\.',
                            'Analysis': '^I\.', 'editor':'^Editor\'s note'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name

        self.watermark_text = """Release {0} of the Official Code of Colorado Annotated released {1}.
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

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]

        [text_junk.decompose() for text_junk in self.soup.find_all("span", class_="Apple-converted-space")]

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
                title_id = header_tag.find_previous("h1").get('id')
                header_tag['id'] = f"{title_id}{sub_tag}{chap_nums}"

        else:
            header_tag.name = tag_name
            header_tag.attrs = {}
            header_tag["class"] = class_name
            if prev_id:
                header_tag['id'] = f"{prev_id}{sub_tag}{chap_nums}"
            else:
                title_id = header_tag.find_previous("h1").get('id')
                header_tag['id'] = f"{title_id}{sub_tag}{chap_nums}"

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
        sec_head_list = []
        ann_count = 1

        count = 1
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):

                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search('constitution\.us', self.html_file_name):
                        self.title_id = "constitution-us"
                    else:
                        self.title_id = "constitution-co"

                    header_tag.name = "h1"
                    header_tag.attrs = {}
                    header_tag["id"] = f'{self.title_id}{count}'
                    count += 1

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = None
                        chap_num = None
                        sub_tag = None


                        chap_num = re.search(r'^((ARTICLE|Article)\s*(?P<ar>[A-Z]+|[IVX]+))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = re.search(r'^[a-zA-Z]{2}', header_tag.text.strip()).group()
                        sub_tag = f'-{sub_tag.lower()}-'
                        class_name = f'{chap_num.lower()}h2'
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["art_head"]]:
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(),re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    if re.search(r'^(ARTICLE)', header_tag.text.strip()):
                        tag_name = "h2"

                        prev_id = header_tag.find_previous("h2", class_='amendmenth2').get("id")
                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[I,V,X]+))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^Section\s*[0-9]+(\.\d+)*[a-z]*\.', header_tag.text.strip()):
                        chap_num = re.search(r'^Section\s*(?P<ar>[0-9]+(\.\d+)*[a-z]*)\.', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2").get("id")

                        sub_tag = "-s"
                        class_name = "section"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["amd"]]:
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(),re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["head4"]]:

                    # if re.search(r'^[I,V,X]+\.|^[A-Z]\.', header_tag.text.strip()):
                    #     tag_name = "h5"
                    #
                    #     prev_id = header_tag.find_previous("h4").get("id")
                    #     chap_num = re.sub(r'[\s.]+', '', header_tag.text.strip()).lower()
                    #     sub_tag = "-"
                    #     class_name = "analysis"



                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[I,V,X]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[A-HJ-UW-Z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[I,V,X]+\.',
                                                                         tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                        # self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                        #                                      class_name)

                    else:
                        header_tag.name = "h4"
                        prev_id = header_tag.find_previous("h3").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()

                        if prev_id in sec_head_list:
                            header_tag["id"] = f'{prev_id}-{chap_num}{ann_count}'
                            header_tag["class"] = "annotation"
                            ann_count += 1

                        else:
                            header_tag["id"] = f'{prev_id}-{chap_num}'
                            header_tag["class"] = "annotation"
                            ann_count = 1


                        sec_head_list.append(prev_id)

                        # self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                        #                                      class_name)

                elif header_tag.name == "h3":
                    prev_id = header_tag.find_previous("h2").get("id")
                    cur_id = re.search(r'^§\s*(?P<id>\d+)\.', header_tag.text.strip()).group("id")
                    header_tag["id"] = f'{prev_id}{cur_id}'

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    header_tag.name = "li"

            # titles
            else:
                prev_tag = self.soup.find(class_=self.class_regex["ul"])
                prev_id1 = prev_tag.find_previous(
                        lambda tag: tag.name in ['p'] and re.search(r'^\w+',
                                                                    tag.text.strip()))
                if prev_id1:
                    if not re.search(r'^Cross references', prev_id1.text.strip()):
                        self.class_regex['nav_head'] = prev_id1['class']

                    else:
                        self.class_regex['nav_head'] = None


                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search(r'^TITLE\s(?P<title_id>\d+)', header_tag.text.strip()):
                        self.title_id = re.search(r'^TITLE\s(?P<title_id>\d+)', header_tag.text.strip()).group(
                            'title_id').zfill(2)
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag["id"] = f't{self.title_id}'
                        header_tag.wrap(self.soup.new_tag("nav"))

                    if re.search(r'^SUBPART\s*(?P<id>\d+)',header_tag.text.strip()):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="parth2").get("id")
                        chap_num = re.search(r'^SUBPART\s*(?P<id>\d+)', header_tag.text.strip()).group(
                            "id").zfill(2)
                        sub_tag = "-sp"
                        class_name = "subparth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)


                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE', header_tag.text.strip(), re.I):
                        tag_name = "h2"

                        if header_tag.find_previous("h2", class_="gnrlh2"):
                            prev_id = header_tag.find_previous("h2", class_="gnrlh2").get("id")
                        else:
                            prev_id = None

                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>\d+(\.\d+)*))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    elif re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")


                        chap_num = re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-p"
                        class_name = "parth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-"
                        class_name = "gnrlh2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)


                elif header_tag.get("class") == [self.class_regex["part_head"]] or header_tag.get("class") == self.class_regex["nav_head"] :
                    if re.search(r'\w+', header_tag.text.strip()):
                        header_tag["class"] = "nav_head"



                # elif header_tag.get("class") == self.class_regex["nav_head"]:
                #     if re.search(r'\w+', header_tag.text.strip()):
                #         header_tag["class"] = "nav_head"
                #
                # elif header_tag.get("class") == [self.class_regex["part_head"]]:
                #     if re.search(r'^PART', header_tag.text.strip(), re.I):
                #         tag_name = "h2"
                #         prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")
                #         chap_num = re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                #             "ar").zfill(2)
                #         sub_tag = "-p"
                #         class_name = "parth2"
                #
                #         self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                #                                              class_name)



                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.*', header_tag.text.strip(), re.I):
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2").get("id")

                        chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', header_tag.text.strip()).group(
                            "sid").zfill(2)
                        sub_tag = "-s"
                        class_name = "section"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)



                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[I,V,X]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[A-HJ-UW-Z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[I,V,X]+\.',
                                                                         tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    else:
                        header_tag.name = "h4"
                        if header_tag.find_previous("h3"):
                            prev_id = header_tag.find_previous("h3").get("id")
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            header_tag["id"] = f'{prev_id}-{chap_num}'
                        else:
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            header_tag["id"] = f't{self.title_id}-{chap_num}'

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if not re.search(r'^Section', header_tag.text.strip()):
                        header_tag.name = "li"


                elif header_tag.get("class") == [self.class_regex["Analysis"]]:
                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        if re.search(r'^I\.', header_tag.text.strip()):
                            header_tag.name = "ul"
                            header_tag["class"] = "leaders"
                            list1 = header_tag.text.splitlines()
                            header_tag.string = ""

                            for i in list1:
                                new_ul_tag = self.soup.new_tag("li")
                                new_ul_tag.string = i
                                header_tag.append(new_ul_tag)

    def recreate_tag(self):
        ol_list = []
        num_ol_tag = self.soup.new_tag("ol")
        ol_count = 1


        for p_tag in self.soup.find_all():
            if p_tag.get("class") == [self.class_regex["ol"]]:
                # if  not re.search('constitution', self.html_file_name):


                current_p_tag = p_tag.text.strip()
                if re.search(r'^\[.+\]\s*\(\d+(\.\d+)*\)', current_p_tag):
                    alpha_text = re.sub(r'^\[.+\]\s*', '', current_p_tag)
                    num_text = re.sub(r'\(1\).+', '', current_p_tag)

                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = alpha_text
                    new_p_tag["class"] = [self.class_regex['ol']]
                    p_tag.insert_after(new_p_tag)
                    p_tag.string = num_text

                if re.search(r'^\(\d+(\.\d+)*\)', current_p_tag):
                    if p_tag.find_next().name == "b":
                        alpha_text = re.sub(r'^[^.]+\.', '', current_p_tag)
                        num_text = re.sub(r'\(a\).+', '', current_p_tag)

                        if re.search(r'^\s*\([a-z]\)', alpha_text):
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.class_regex['ol']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

                        elif re.search(r'^.+\s(?P<alpha>\(a\)+)', current_p_tag):
                            alpha_text = re.search(r'^.+\s(?P<alpha>\(a\).+)', current_p_tag).group("alpha")
                            num_text = re.sub(r'\(a\).+', '', current_p_tag)

                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.class_regex['ol']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text




                if re.search(r'^\(\d+\)\s*\([a-z]+\)\s*.+\s*\([a-z]\)', current_p_tag):

                    alpha = re.search(r'^(?P<num_text>\(\d+\)\s*\((?P<alpha1>[a-z]+)\)\s*.+\s*)(?P<alpha_text>\((?P<alpha2>[a-z])\).+)', current_p_tag)
                    if re.match(r'^\([a-z]\)',p_tag.find_next_sibling().text.strip()):
                        nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',p_tag.find_next_sibling().text.strip()).group("alpha3")

                        if ord(alpha.group("alpha2")) == (ord(alpha.group("alpha1")))+1:
                            if ord(nxt_alpha) == (ord(alpha.group("alpha2")))+1:

                                alpha_text = alpha.group("alpha_text")
                                num_text = alpha.group("num_text")
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = alpha_text
                                new_p_tag["class"] = [self.class_regex['ol']]
                                p_tag.insert_after(new_p_tag)
                                p_tag.string = num_text

                if re.search(r'^\([I,V,X]+\)', current_p_tag):
                    if re.search(r'^\((?P<rom1>[IVX]+)\).+\((?P<rom2>[IVX]+)\)',current_p_tag):
                        alpha = re.search(r'^(?P<txt1>\((?P<rom1>[IVX]+)\).+)(?P<txt2>\((?P<rom2>[IVX]+)\).+)',current_p_tag)
                        if re.match(r'^\([I,V,X]+\)', p_tag.find_next_sibling().text.strip()):
                            nxt_rom = re.search(r'^\((?P<rom3>[IVX]+)\)', p_tag.find_next_sibling().text.strip()).group(
                                "rom3")

                            if int(self.convert_roman_to_digit(alpha.group("rom2"))) == int((self.convert_roman_to_digit(alpha.group("rom1")))+1):
                                if int(self.convert_roman_to_digit(nxt_rom)) == int((self.convert_roman_to_digit(alpha.group("rom2")))+1):

                                    alpha_text = alpha.group("txt2")
                                    num_text = alpha.group("txt1")
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = alpha_text
                                    new_p_tag["class"] = [self.class_regex['ol']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag.string = num_text

            if p_tag.get("class") == [self.class_regex["editor"]]:
                current_p_tag = p_tag.text.strip()
                if re.search(r'^.+:\s*\(1\)', current_p_tag):
                    alpha_text1 = re.search(r'^.+:\s*(?P<text1>\(1\).+)', current_p_tag).group("text1")
                    num_text1 = re.sub(r'\(1\).+', '', current_p_tag)
                    new_p_tag1 = self.soup.new_tag("p")
                    new_p_tag1.string = alpha_text1
                    new_p_tag1["class"] = [self.class_regex['ol']]
                    p_tag.insert_after(new_p_tag1)
                    p_tag.string = num_text1
                    p_tag.name = "h4"
                    p_tag["class"] = [self.class_regex['head4']]

                elif re.search(r'^\(\d+\)', current_p_tag):
                    p_tag["class"] = "p10"



        # for tag in self.soup.find_all(class_= self.class_regex["ol"]):
        #     pattern = re.compile(
        #         r'^\(\d+\)|^\(\d+\)\s\(\D\)|^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)|^\(\d+\.\d+\)|^\(\d+\.\d+\)\s*\(\w\)|'
        #         r'^\(\s*[a-z]\s*\)|^\(\w+\)\s*\([I,V,X]+\)|^\([a-z]\.\d+\)|'
        #         r'^\([I,V,X]+\)|^\([I,V,X]+\)\s*\([A-Z]\)|'
        #         r'^\(\s*[A-Z]\s*\)')
        #
        #     pattern1 = re.compile(r'^((\(\d+(\.\d+)\))*\s*(\([a-z]+(\.\d+)\))*\s*(\([I,V,X]+\))*\s*(\([A-Z]+\))*)')
        #
        #     if re.match(pattern1,tag.text.strip()):
        #         if re.search(r'^\(\d+\)|^\(\d+\)\s\(\D\)|^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)', tag.text.strip()):
        #             pattern1 = re.search(r'^\(\d+\)\s*(\(\D\))*\s*(\([I,V,X]+\))*',tag.text.strip()).group()
        #             span_tag = self.soup.new_tag("span")
        #             span_tag.string = pattern1
        #             tag.string = re.sub(r'^\(\d+\)\s*(\(\D\))*\s*(\([I,V,X]+\))*','',tag.text.strip())
        #             tag.insert(0,span_tag)
        #
        #         elif re.search(r'^\(\s*[a-z]\s*\)|^\(\w+\)\s*\([I,V,X]+\)', tag.text.strip()):
        #             pattern1 = re.search(r'^\(\w+\)(\s*\([I,V,X]+\))*',tag.text.strip()).group()
        #             span_tag = self.soup.new_tag("span")
        #             span_tag.string = pattern1
        #             tag.string = re.sub(r'^\(\w+\)(\s*\([I,V,X]+\))*','',tag.text.strip())
        #             tag.insert(0,span_tag)
        #
        #         elif re.search(r'^\([I,V,X]+\)\s*(\([A-Z]\))*', tag.text.strip()):
        #             pattern1 = re.search(r'^\([I,V,X]+\)\s*(\([A-Z]\))*',tag.text.strip()).group()
        #             span_tag = self.soup.new_tag("span")
        #             span_tag.string = pattern1
        #             tag.string = re.sub(r'^\([I,V,X]+\)\s*(\([A-Z]\))*','',tag.text.strip())
        #             tag.insert(0,span_tag)
        #
        #         elif re.search(r'^\(\s*[A-Z]\s*\)', tag.text.strip()):
        #             pattern1 = re.search(r'^\(\s*[A-Z]\s*\)',tag.text.strip()).group()
        #             span_tag = self.soup.new_tag("span")
        #             span_tag.string = pattern1
        #             tag.string = re.sub(r'^\(\s*[A-Z]\s*\)','',tag.text.strip())
        #             tag.insert(0,span_tag)


        print("tags are recreated")

    def recreate_tag1(self):
        ol_list = []
        num_ol_tag = self.soup.new_tag("ol")
        ol_count = 1
        ul_tag = self.soup.new_tag("ul")

        for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
            current_p_tag = p_tag.text.strip()

            next_sibling = p_tag.find_next_sibling()

            if re.search('^§', current_p_tag):
                if re.search('^§', p_tag.find_next("b").text.strip()):
                    # p_tag.find_next("b").name = "h3"
                    # if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                    #     p_tag.find_next("b").decompose()
                    new_h3_tag = self.soup.new_tag("h3")
                    h3_text = p_tag.find_next("b").text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()


                else:
                    new_h3_tag = self.soup.new_tag("h3")
                    h3_text = "§" + p_tag.find_next("b").text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()

                    if re.search(r'^§', p_tag.text.strip()):
                        p_tag.string = re.sub(r'^§', '', p_tag.text.strip())



            if re.search(r'^\(\d+\)',current_p_tag):
               if p_tag.find_next().name == "b":
                    alpha_text = re.sub(r'^[^.]+\.','',current_p_tag)
                    num_text = re.sub(r'\(a\).+','',current_p_tag)

                    if re.search(r'^\s*\([a-z]\)',alpha_text):

                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = alpha_text
                        new_p_tag["class"] = [self.class_regex['ol']]
                        p_tag.insert_after(new_p_tag)
                        p_tag.string = num_text

                    elif re.search(r'^[\w\s]+:\s*\([a-z]\)',alpha_text):
                        num_text = re.sub(r'\(a\).+', '', current_p_tag)
                        alpha_text = re.search(r'\(a\).+',current_p_tag).group()

                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = alpha_text
                        new_p_tag["class"] = [self.class_regex['ol']]
                        p_tag.insert_after(new_p_tag)
                        p_tag.string = num_text




        for anlys_tag in self.soup.find_all(class_=self.class_regex['Analysis']):
            if re.search(r'^I\.', anlys_tag.text.strip()):
                anlys_tag.name = "ul"
                anlys_tag["class"] = "leaders"
                list1 = anlys_tag.text.splitlines()
                anlys_tag.string = ""

                for i in list1:
                    new_ul_tag = self.soup.new_tag("li")
                    new_ul_tag.string = i

                    anlys_tag.append(new_ul_tag)



    def convert_roman_to_digit(self, roman):
        value = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
        prev = 0
        ans = 0
        length = len(roman)
        for num in range(length - 1, -1, -1):
            if value[roman[num]] >= prev:
                ans += value[roman[num]]
            else:
                ans -= value[roman[num]]
            prev = value[roman[num]]

        return ans

    # def create_and_wrap_with_ol_tag(self):
    #
    #     pattern = re.compile(r'^\(\d+\)|^\(\d+\)\s\(\D\)|^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)|^\(\d+\.\d+\)|^\(\d+\.\d+\)\s*\(\w\)|'
    #                          r'^\(\s*[a-z]\s*\)|^\(\w+\)\s*\([I,V,X]+\)|^\([a-z]\.\d+\)|'
    #                          r'^\([I,V,X]+\)|^\([I,V,X]+\)\s*\([A-Z]\)|'
    #                          r'^\(\s*[A-Z]\s*\)')
    #     ol_list = []
    #     ol_count = 1
    #     num_ol_tag = self.soup.new_tag("ol")
    #     prev_head_id = None
    #     innr_alpha_ol_tag = self.soup.new_tag("ol", type="A")
    #
    #     for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
    #         current_li_tag = p_tag.text.strip()
    #
    #         # (1)
    #         if re.search(rf'^\({ol_count}\)', current_li_tag):
    #             p_tag.name = "li"
    #             num_curr_tag = p_tag
    #
    #             if re.search(r'^\(1\)', current_li_tag):
    #
    #                 if re.match(r'^ARTICLE', p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "br":
    #                     prev_head_id = p_tag.find_previous("h2").get("id")
    #                 else:
    #                     prev_head_id = p_tag.find_previous("h3").get("id")
    #
    #                 num_ol_tag = self.soup.new_tag("ol")
    #                 p_tag.wrap(num_ol_tag)
    #
    #                 if prev_head_id in ol_list:
    #                     ol_count += 1
    #                 else:
    #                     ol_count = 1
    #
    #                 ol_list.append(prev_head_id)
    #                 p_tag["id"] = f'{prev_head_id}ol{ol_count}1'
    #
    #             else:
    #
    #                 if re.search(r'^\((\d+)(\.\d+)*\)(\s*\(\w\))*', p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                         cur_tag = re.search(r'^\((?P<cid>\d+)\)', current_li_tag).group("cid")
    #                         prev_tag = re.search(r'^\((?P<pid>\d+)(\.\d+)*\)(\s*\(\w\))*',
    #                                              p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
    #                             "pid")
    #
    #                         if int(cur_tag) == (int(prev_tag)) + 1:
    #                             num_ol_tag.append(p_tag)
    #                             p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}'
    #
    #                         elif int(cur_tag) == int(prev_tag):
    #                             p_tag.name = "p"
    #                             num_ol_tag.append(p_tag)
    #                             p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}.1'
    #
    #
    #
    #                 elif re.search(r'^\(\D+\)|^\([I,V,X]+\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #
    #                         cur_tag = re.search(r'^\((?P<cid>\d+)\)', current_li_tag).group("cid")
    #                         prev_tag = re.search(r'^\((?P<pid>\d+)\)', p_tag.find_previous(
    #                             lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
    #                                                                          tag.text.strip())).text.strip()).group("pid")
    #
    #                         if int(cur_tag) == (int(prev_tag)) + 1:
    #                             num_ol_tag.append(p_tag)
    #
    #                         p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}'
    #
    #             if re.search(r'^\(\d+\)\s\(\D\)', current_li_tag):
    #                 alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_li_tag)
    #
    #                 cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>\D)\)', current_li_tag)
    #                 prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 alpha_ol_tag.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(alpha_ol_tag)
    #
    #                 if re.search(r'^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)', current_li_tag):
    #                     rom_ol_tag = self.soup.new_tag("ol",type="I")
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.append(current_li_tag)
    #                     li_tag["class"] = self.class_regex['ol']
    #
    #                     cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\D)\)\s*\((?P<id2>[I,V,X]+)\)', current_li_tag)
    #                     inner_li_tag[
    #                         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #
    #                     rom_ol_tag.append(inner_li_tag)
    #                     p_tag.insert(1, rom_ol_tag)
    #                     rom_ol_tag.find_previous().string.replace_with(rom_ol_tag)
    #
    #
    #         # (2.5)
    #         elif re.search(r'^\(\d+\.\d+\)', current_li_tag):
    #             p_tag.name = "p"
    #             # prev_tag1 = p_tag.find_previous(
    #             #     lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
    #             #                                                  tag.text.strip()))
    #
    #             prev_tag = p_tag.find_previous(class_=self.class_regex['ol'])
    #             prev_id  = re.search(r'^\((?P<pid>\d+)\)', p_tag.find_previous(
    #                 lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
    #                                                              tag.text.strip())).text.strip()).group("pid")
    #             cur_tag = re.search(r'^\((?P<cid1>(?P<cid>\d+)\.\d+)\)', current_li_tag)
    #
    #             p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid1")}'
    #
    #             if cur_tag.group("cid") == prev_id:
    #                 prev_tag.append(p_tag)
    #
    #
    #             if re.search(r'^\(\d+\.\d+\)\s*\(\w\)', current_li_tag):
    #
    #                 alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_li_tag)
    #
    #                 cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)\s*\((?P<pid>\w)\)', current_li_tag)
    #                 prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 alpha_ol_tag.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(alpha_ol_tag)
    #
    #                 if re.search(r'^\(\d+\.\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_li_tag):
    #
    #                     rom_ol_tag = self.soup.new_tag("ol", type="I")
    #
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.append(current_li_tag)
    #                     li_tag["class"] = self.class_regex['ol']
    #
    #                     cur_tag = re.search(r'^\((?P<id1>\d+\.\d+)\)\s*\((?P<cid>\w+)\)\s*\((?P<id2>[I,V,X]+)\)',
    #                                         current_li_tag)
    #                     inner_li_tag[
    #                         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #
    #                     rom_ol_tag.append(inner_li_tag)
    #                     p_tag.insert(1, rom_ol_tag)
    #                     rom_ol_tag.find_previous().string.replace_with(rom_ol_tag)
    #
    #
    #
    #         # (a)
    #         elif re.search(r'^\(\s*[a-z]\s*\)', current_li_tag):
    #             p_tag.name = "li"
    #             alpha_cur_tag = p_tag
    #             if re.search(r'^\(a\)', current_li_tag):
    #
    #                 alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #
    #                 if re.search(r'^\(\d+\)|^\(\d+\.\d+\)',
    #                              p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span" or p_tag.find_previous().name == "b":
    #                     prev_tag1 = p_tag.find_previous("li")
    #                     p_tag.wrap(alpha_ol_tag)
    #
    #                     prev_tag1.append(alpha_ol_tag)
    #                     prev_tag_id = f'{prev_tag1.get("id")}ol{ol_count}'
    #                     p_tag["id"] = f'{num_curr_tag.get("id")}a'
    #                 else:
    #                     p_tag.wrap(alpha_ol_tag)
    #
    #             else:
    #
    #                 if re.search(r'^\([I,V,X]+\)|^\(\d+\)\s\(\D\)',
    #                              p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_tag = re.search(r'\(\s*(?P<cid>[a-z])\s*\)', current_li_tag).group("cid")
    #                     prev_tag = re.search(r'^(\(\d+(\.\d+)*\))*\s*\((?P<pid>[a-z])\s*\)',
    #                                          p_tag.find_previous(
    #                                              lambda tag: tag.name in ['li','p'] and re.search(
    #                                                  r'^(\(\d+\))*\s*\((?P<pid>[a-z])\s*\)|^\(\d+\.\d+\)\s*\(\w\)',
    #                                                  tag.text.strip())).text.strip()).group( "pid")
    #
    #
    #                     if ord(cur_tag) == (ord(prev_tag)) + 1:
    #                         alpha_ol_tag.append(p_tag)
    #
    #                     p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #
    #
    #                 elif re.search(r'^\(\s*[a-z]\s*\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_tag = re.search(r'\(\s*(?P<cid>[a-z]+)\s*\)', current_li_tag).group("cid")
    #                     prev_tag = re.search(r'\(\s*(?P<pid>[a-z]+)\s*\)',
    #                                          p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
    #                         "pid")
    #
    #                     if ord(cur_tag) == (ord(prev_tag)) + 1:
    #                         alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #                     elif ord(cur_tag) == (ord(prev_tag)):
    #                         alpha_ol_tag.append(p_tag)
    #                         cur_tag = chr(ord(cur_tag) + 1)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #                     elif ord(cur_tag) == (ord(prev_tag)) + 2:
    #                         alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #
    #                 else:
    #                     prv_p_tag = p_tag.find_previous(class_=self.class_regex['ol'])
    #                     prv_p_tag1 = prv_p_tag.find_previous(class_=self.class_regex['ol'])
    #
    #                     if re.search(r'^\s*\(\d+|\D+|[I,V,X]+',prv_p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                         prv_p_tag1.append(prv_p_tag)
    #
    #
    #                     cur_tag = re.search(r'\(\s*(?P<cid>[a-z])\s*\)', current_li_tag).group("cid")
    #                     prev_tag = re.search(r'^(\(\d+(\.\d+)*\))*\s*\((?P<pid>[a-z])\s*\)',
    #                                          p_tag.find_previous(
    #                                              lambda tag: tag.name in ['li', 'p'] and re.search(
    #                                                  r'^(\(\d+\))*\s*\((?P<pid>[a-z])\s*\)|^\(\d+\.\d+\)\s*\(\w\)',
    #                                                  tag.text.strip())).text.strip()).group(
    #                         "pid")
    #
    #                     if ord(cur_tag) == (ord(prev_tag)) + 1:
    #                         alpha_ol_tag.append(p_tag)
    #                     # else:
    #                     #     print(p_tag)
    #
    #                     p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #
    #             if re.search(r'^\(\w+\)\s*\([I,V,X]+\)', current_li_tag):
    #                 rom_ol_tag = self.soup.new_tag("ol",type="I")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_li_tag)
    #                 li_tag["class"] = self.class_regex['ol']
    #
    #                 cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_li_tag)
    #                 prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 rom_ol_tag.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(rom_ol_tag)
    #
    #         # (aa)(aaa)
    #         elif re.search(r'^\(\s*[a-z]+(\.\d+)*\)', current_li_tag):
    #             p_tag.name = "li"
    #             alpha_ol_tag.append(p_tag)
    #             if re.search(r'^\(\s*[a-z]+(\.\d+)\)', current_li_tag):
    #                 p_tag.name = "p"
    #
    #
    #         # (a.5)
    #         elif re.search(r'^\([a-z]\.\d+\)', current_li_tag):
    #                 p_tag.name = "p"
    #                 prev_tag = p_tag.find_previous(
    #                     lambda tag: tag.name in ['li'] and re.search(r'^\([a-z]\)',
    #                                                                  tag.text.strip()))
    #                 prev_id = re.search(r'^\((?P<pid>[a-z])\)', p_tag.find_previous(
    #                     lambda tag: tag.name in ['li'] and re.search(r'^\([a-z]\)',
    #                                                                  tag.text.strip())).text.strip()).group("pid")
    #                 cur_tag = re.search(r'^\((?P<cid1>(?P<cid>[a-z])\.\d+)\)', current_li_tag)
    #
    #                 p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid1")}'
    #
    #                 if cur_tag.group("cid") == prev_id:
    #                     prev_tag.append(p_tag)
    #
    #
    #
    #                 if re.search(r'^\([a-z]\.\d+\)\s*\([I,V,X]+\)', current_li_tag):
    #
    #                     rom_ol_tag = self.soup.new_tag("ol", type="I")
    #                     li_tag = self.soup.new_tag("li")
    #                     li_tag.append(current_li_tag)
    #                     li_tag["class"] = self.class_regex['ol']
    #
    #                     cur_tag = re.search(r'^\((?P<cid>[a-z]\.\d+)\)\s*\((?P<pid>[I,V,X]+)\)', current_li_tag)
    #                     prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                     li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                     rom_ol_tag.append(li_tag)
    #                     p_tag.contents = []
    #                     p_tag.append(rom_ol_tag)
    #
    #                     if re.search(r'^\([a-z]\.\d+\)\s*\([I,V,X]+\)\s*\([A-Z]\)', current_li_tag):
    #                         innr_alpha_ol_tag = self.soup.new_tag("ol", type="A")
    #                         inner_li_tag = self.soup.new_tag("li")
    #                         inner_li_tag.append(current_li_tag)
    #                         li_tag["class"] = self.class_regex['ol']
    #
    #                         cur_tag = re.search(r'^\((?P<id1>[a-z]\.\d+)\)\s*\((?P<cid>[I,V,X]+)\)\s*\((?P<id2>[A-Z])\)',
    #                                             current_li_tag)
    #                         inner_li_tag[
    #                             "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #
    #                         innr_alpha_ol_tag.append(inner_li_tag)
    #                         p_tag.insert(1, innr_alpha_ol_tag)
    #                         innr_alpha_ol_tag.find_previous().string.replace_with(innr_alpha_ol_tag)
    #
    #
    #
    #         # (I)
    #         elif re.search(r'^\([I,V,X]+\)', current_li_tag):
    #             p_tag.name = "li"
    #
    #             if re.search(r'^\(I\)', current_li_tag):
    #                 rom_ol_tag = self.soup.new_tag("ol",type="I")
    #
    #                 if re.search(r'^\(\d+\)\s\(\D\)|^\(\w+\)|^\(\d+\.\d+\)\s*\(\w\)|^\(\d+\)\s*\([a-z]\)',
    #                              p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span" or p_tag.find_previous().name == "br":
    #                     prev_tag1 = p_tag.find_previous("li")
    #                     p_tag.wrap(rom_ol_tag)
    #                     prev_tag1.append(rom_ol_tag)
    #                     prev_tag_id = f'{prev_tag1.get("id")}ol{ol_count}'
    #                     p_tag["id"] = f'{prev_tag1.get("id")}I'
    #
    #                 elif re.search(r'^Editor\'s note:',p_tag.find_previous().text.strip()):
    #
    #                     prev_tag1 = p_tag.find_previous("li")
    #                     p_tag.wrap(rom_ol_tag)
    #                     prev_tag1.append(rom_ol_tag)
    #
    #
    #                 else:
    #                     p_tag.wrap(rom_ol_tag)
    #
    #             else:
    #
    #
    #                 if re.search(r'^\([I,V,X]+\)', p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
    #                     prev_id = re.search(r'^\((?P<pid>[I,V,X]+)\)',
    #                                         p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
    #                         "pid")
    #                     if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag1.get("id")}{cur_id}'
    #                     else:
    #                         prev_tag = p_tag.find_previous(
    #                             lambda tag: tag.name in ['li'] and re.search(r'^\([a-z](\.\d+)*\)\s*\([I,V,X]+\)',
    #                                                                          tag.text.strip()))
    #                         prev_id = re.search(r'^\([a-z](\.\d+)*\)\s*\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
    #                             lambda tag: tag.name in ['li'] and re.search(r'^\([a-z](\.\d+)*\)\s*\((?P<pid>[I,V,X]+)\)',
    #                                                                          tag.text.strip())).text.strip()).group(
    #                             "pid")
    #
    #                         if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                             rom_ol_tag.append(p_tag)
    #                             p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #
    #
    #
    #                 elif re.search(r'^\(\s*[A-Z]\s*\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
    #                     prev_tag =p_tag.find_previous(lambda tag: tag.name in ['li'] and re.search(r'^\((?P<cid>[I,V,X]+)\)',
    #                                                                      tag.text.strip()))
    #                     prev_id = re.search(r'^\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\((?P<pid>[I,V,X]+)\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #                     if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #                     elif self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 2:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #                     else:
    #                         # print(p_tag)
    #                         prev_tag = p_tag.find_previous(
    #                             lambda tag: tag.name in ['li'] and re.search(r'^\([a-z]\)\s*\([I,V,X]+\)',
    #                                                                          tag.text.strip()))
    #                         prev_id = re.search(r'^\([a-z]\)\s*\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
    #                             lambda tag: tag.name in ['li'] and re.search(r'^\([a-z]\)\s*\((?P<pid>[I,V,X]+)\)',
    #                                                                          tag.text.strip())).text.strip()).group(
    #                             "pid")
    #
    #                         if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                             rom_ol_tag.append(p_tag)
    #                             p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #
    #                 elif re.search(r'^\(\w+\)\s*\([I,V,X]+\)|^\(\s*[A-Z]\s*\)|^\([IVX]\.\d+\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
    #                     prev_tag =p_tag.find_previous(lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)',
    #                                                                     tag.text.strip()))
    #                     prev_id = re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #                     if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #                     elif self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 2:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #
    #
    #
    #                 elif re.search(r'^\(\d+(\.\d)*\)\s*\(\D\)\s*\([I,V,X]+\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
    #                     prev_tag =p_tag.find_previous(lambda tag: tag.name in ['li'] and re.search(r'^\(\d+(\.\d+)*\)\s*\(\D\)\s*\([I,V,X]+\)',
    #                                                                      tag.text.strip()))
    #                     prev_id = re.search(r'^\(\d+(\.\d+)*\)\s*\(\D\)\s*\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\(\d+(\.\d+)*\)\s*\(\D\)\s*\([I,V,X]+\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #                     if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
    #                         rom_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'
    #
    #                 elif p_tag.find_previous(class_=self.class_regex['ol']).name == "p":
    #                     prev_p_tag = p_tag.find_previous(class_=self.class_regex['ol'])
    #                     prev_p_tag.find_previous().append(p_tag.find_previous(class_=self.class_regex['ol']))
    #                     rom_ol_tag.append(p_tag)
    #
    #
    #
    #             if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)', current_li_tag):
    #                 innr_alpha_ol_tag = self.soup.new_tag("ol", type="A")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_li_tag)
    #
    #                 # cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_li_tag)
    #                 # prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 # li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 innr_alpha_ol_tag.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(innr_alpha_ol_tag)
    #
    #         # (I.5)
    #         elif re.search(r'^\([IVX]\.\d+\)', current_li_tag):
    #                 p_tag.name = "p"
    #                 prev_tag = p_tag.find_previous(
    #                     lambda tag: tag.name in ['li'] and re.search(r'^\([IVX]\)',
    #                                                                  tag.text.strip()))
    #                 prev_id = re.search(r'^\((?P<pid>[IVX])\)', p_tag.find_previous(
    #                     lambda tag: tag.name in ['li'] and re.search(r'^\([IVX]\)',
    #                                                                  tag.text.strip())).text.strip()).group("pid")
    #                 cur_tag = re.search(r'^\((?P<cid1>(?P<cid>[IVX])\.\d+)\)', current_li_tag)
    #
    #                 p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid1")}'
    #
    #                 if cur_tag.group("cid") == prev_id:
    #                     prev_tag.append(p_tag)
    #
    #
    #
    #
    #     #(A)
    #
    #         elif re.search(r'^\(\s*[A-Z]\s*\)', current_li_tag):
    #             p_tag.name = "li"
    #             alpha_cur_tag = p_tag
    #             if re.search(r'^\(A\)', current_li_tag):
    #                 innr_alpha_ol_tag = self.soup.new_tag("ol", type="A")
    #
    #
    #                 if re.search(r'^\([I,V,X]+\)|^\([a-z](\.\d+)*\)\s*\([I,V,X]\)|^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)',
    #                              p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span" or p_tag.find_previous().name == "b":
    #                     prev_id = p_tag.find_previous()
    #                     p_tag.wrap(innr_alpha_ol_tag)
    #
    #                     rom_ol_tag.append(innr_alpha_ol_tag)
    #                     prev_tag_id = f'{prev_id.get("id")}ol{ol_count}'
    #                     p_tag["id"] = f'{num_curr_tag.get("id")}A'
    #                 else:
    #                     p_tag.wrap(innr_alpha_ol_tag)
    #
    #
    #             else:
    #
    #                 if re.search(r'^\([I,V,X]+\)',
    #                              p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #
    #                     cur_tag = re.search(r'^\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
    #                     prev_id = re.search(r'^\((?P<pid>[A-Z])\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\([A-Z]\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #
    #                     if ord(cur_tag) == (ord(prev_id)) + 1:
    #                         innr_alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #
    #                 if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)',
    #                              p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #
    #                     cur_tag = re.search(r'^\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
    #                     prev_id = re.search(r'^\([I,V,X]+\)\s*\((?P<pid>[A-Z])\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #
    #                     if ord(cur_tag) == (ord(prev_id)) + 1:
    #                         innr_alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #                 elif re.search(r'^\(\s*[A-Z]\s*\)',
    #                                p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #                     cur_tag = re.search(r'\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
    #                     prev_id = re.search(r'\(\s*(?P<pid>[A-Z]+)\s*\)',
    #                                          p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
    #                         "pid")
    #
    #                     if ord(cur_tag) == (ord(prev_id)) + 1:
    #                         innr_alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #
    #
    #                 elif re.search(r'^\([a-z]\.\d+\)\s*\([I,V,X]+\)\s*\([A-Z]\)',
    #                              p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
    #
    #                     cur_tag = re.search(r'^\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
    #                     prev_id = re.search(r'^\([a-z]\.\d+\)\s*\([I,V,X]+\)\s*\((?P<pid>[A-Z])\)', p_tag.find_previous(
    #                         lambda tag: tag.name in ['li'] and re.search(r'^\([a-z]\.\d+\)\s*\([I,V,X]+\)\s*\([A-Z]\)',
    #                                                                      tag.text.strip())).text.strip()).group("pid")
    #
    #                     if ord(cur_tag) == (ord(prev_id)) + 1:
    #                         innr_alpha_ol_tag.append(p_tag)
    #                         p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'
    #
    #                 elif p_tag.find_previous(class_=self.class_regex['ol']).name == "p":
    #                     prev_p_tag = p_tag.find_previous(class_=self.class_regex['ol'])
    #                     prev_p_tag.find_previous().append(p_tag.find_previous(class_=self.class_regex['ol']))
    #                     innr_alpha_ol_tag.append(p_tag)
    #
    #
    #
    #     print("ol tag created")

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        cap_alpha = 'A'
        small_roman = 'i'
        cap_roman = 'I'
        ol_head = 1
        alpha_ol = self.soup.new_tag("ol", Class="alpha")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_ol = self.soup.new_tag("ol", type="i")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")
        small_letter_inner_ol = self.soup.new_tag("ol", Class="alpha")
        previous_alpha_li = None
        previous_num_li = None
        previous_inner_li = None
        previous_roman_li = None
        alpha_li_id = None
        ol_count = 1
        sub_ol_id = None
        sec_sub_ol = None
        sec_sub_li = None
        sub_alpha_ol = None
        prev_chap_id = None
        ol_list = []


        for p_tag in self.soup.find_all():

            current_tag_text = p_tag.text.strip()
            if re.search(rf'^\({ol_head}\)',current_tag_text):
                p_tag.name = "li"
                main_sec_alpha = "a"
                cap_alpha = 'A'

                num_cur_tag = p_tag

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)

                    prev_head_id = p_tag.find_previous(["h4","h3"]).get("id")
                    if prev_head_id  in ol_list:
                        ol_count += 1
                    else:
                        ol_count = 1
                    ol_list.append(prev_head_id)
                else:
                    num_ol.append(p_tag)

                prev_id = f'{prev_head_id}ol{ol_count}{ol_head}'

                p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
                ol_head += 1



                if re.search(r'^\(\d+\)\s\(\w\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag

                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>\w)\)', current_tag_text)
                    # prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    # li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"

                    if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.append(current_tag_text)
                        li_tag["class"] = self.class_regex['ol']
                        rom_cur_tag= li_tag

                        cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)', current_tag_text)
                        # inner_li_tag[
                        #         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                        roman_ol.append(inner_li_tag)
                        p_tag.insert(1, roman_ol)
                        roman_ol.find_previous().string.replace_with(roman_ol)

                        if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.class_regex['ol']


                            cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                                current_tag_text)
                            # inner_li_tag[
                            #         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                            cap_alpha_ol.append(inner_li_tag)
                            p_tag.insert(1, cap_alpha_ol)
                            cap_alpha_ol.find_previous().string.replace_with(cap_alpha_ol)
                            cap_alpha = "B"


            elif re.search(r'^\(\d+\.\d+\)', current_tag_text):

                cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)', current_tag_text).group("cid")
                p_tag["id"] = f'{prev_id}-{cur_tag}'
                num_cur_tag.append(p_tag)
                main_sec_alpha = "a"
                num_cur_tag = p_tag


                if re.search(r'^\(\d+\.\d+\)\s\(\w\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_tag_text)

                    cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)\s\((?P<pid>\w)\)', current_tag_text)
                    # prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    # li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"




            # a
            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"

                alpha_cur_tag = p_tag

                if re.search(r'^\(a\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    p_tag.wrap(alpha_ol)
                    num_cur_tag.append(alpha_ol)

                else:
                    alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
                main_sec_alpha = chr(ord(main_sec_alpha)+1)


                if re.search(r'^\(\w\)\s*\([I,V,X]+\)', current_tag_text):


                    roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_tag_text)
                    li_tag["class"] = self.class_regex['ol']
                    rom_cur_tag = li_tag

                    cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                            # prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                            # li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)



            elif re.search(r'^\(\w+\.\w+\)', current_tag_text):
                alpha_ol.append(p_tag)
                alpha_cur_tag = p_tag

            # I
            elif re.search(r'^\([IVX]+\)',current_tag_text):
                p_tag.name = "li"
                rom_cur_tag = p_tag
                if re.search(r'^\(I\)',current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(roman_ol)
                    alpha_cur_tag.append(roman_ol)
                    p_tag["id"] = f'{prev_head_id}ol{ol_count}I'
                else:
                    cur_tag = re.search(r'^\((?P<cid>[IVX]+)\)',current_tag_text).group("cid")
                    roman_ol.append(p_tag)
                    p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}'






            #  A

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                p_tag.name = "li"

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    rom_cur_tag.append(cap_alpha_ol)
                else:
                    cap_alpha_ol.append(p_tag)

                cap_alpha = chr(ord(cap_alpha)+1)








            if re.search(r'^Source|^Cross references:',current_tag_text) or p_tag.name in ['h3','h4']:
                ol_head = 1









        print('ol tags added')

    def create_ul_tag(self):

        if re.search('constitution', self.html_file_name):
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            nav_tag = self.soup.new_tag("nav")
            for list_item in self.soup.find_all(class_=self.class_regex['ul']):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)
                    ul_tag.wrap(self.soup.new_tag("nav"))
        else:
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    if re.search(r'^I.',ul_tag.text.strip()):
                        print(ul_tag)
                        print(ul_tag.find_previous())
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    # if ul_tag.find_previous().find_previous().name == "h1":
                    #     ul_tag.find_previous("nav").append(ul_tag)
                    # else:
                    #     ul_tag.wrap(self.soup.new_tag("nav"))

        print("ul tag is created")

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num):
        nav_list = []
        nav_link = self.soup.new_tag('a')
        nav_link.append(list_item.text)

        if re.search('constitution', self.html_file_name):
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                title_id = list_item.find_previous("h1").get("id")
                nav_link["href"] = f"#{title_id}{sub_tag}{chap_num}"
        else:
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                nav_link["href"] = f"#t{self.title_id}-{sub_tag}{chap_num}"

        nav_list.append(nav_link)
        list_item.contents = nav_list

    def create_chapter_section_nav(self):
        count = 0
        for list_item in self.soup.find_all(class_=self.class_regex['ul']):
            if re.search('constitution', self.html_file_name):
                if re.match(r'^ARTICLE', list_item.text.strip()):
                    chap_num = re.search(r'^ARTICLE\s*(?P<ar>[A-Z]+)',
                                         list_item.text.strip()).group(
                        "ar").zfill(2)
                    sub_tag = "-ar"
                    prev_id = None

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                elif re.search(r'^[I,V,X]+\.', list_item.text.strip()):
                    prev_id = list_item.find_previous("h2").get("id")
                    chap_num = re.search(r'^(?P<ar>[I,V,X]+)\.', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-ar"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.search(r'^[I,V,X]+', list_item.text.strip()):
                    prev_id = None
                    chap_num = re.search(r'^(?P<ar>[I,V,X]+)', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-ar"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.search(r'[0-9a-z]+\.', list_item.text.strip()):
                    prev_id = list_item.find_previous("h2").get("id")
                    chap_num = re.search(r'^(?P<ar>[0-9a-z]+)\.', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-s"

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                else:
                    if not re.search(r'^Section|^Article', list_item.text.strip()):
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', list_item.text.strip()).lower()
                        sub_tag = re.search(r'^[a-zA-Z]{2}', list_item.text.strip()).group()
                        sub_tag = f'-{sub_tag.lower()}-'

                        self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


            #title
            else:
                if re.match(r'^Art\.\s*\d+\.', list_item.text.strip()):
                    chap_num = re.search(r'^Art\.\s*(?P<id>\d+(\.\d+)*)\.',
                                         list_item.text.strip()).group(
                        "id").zfill(2)

                    if list_item.find_previous("p", class_="nav_head"):
                        sub_tag = "-ar"
                        prev_id1 = re.sub(r'[\s]+', '', list_item.find_previous("p", class_="nav_head").text.strip()).lower()
                        prev_id = f't{self.title_id}-{prev_id1}'
                    else:
                        sub_tag = "ar"
                        prev_id = None

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.match(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', list_item.text.strip()):
                    chap_num = re.search(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', list_item.text.strip()).group("id").zfill(
                        2)

                    if re.match(r'^Section', list_item.find_previous("p").text.strip()):
                        prev_id = list_item.find_previous("h2", class_="articleh2").get("id")
                    else:
                        # prev_id1 = list_item.find_previous("h2", class_="articleh2").get("id")

                        if re.search(r'^PART\s*(?P<id>\d+)',list_item.find_previous("p", class_="nav_head").text.strip()):
                            prev_id1 = list_item.find_previous("h2", class_="articleh2").get("id")
                            prev_id2 = re.search(r'^PART\s*(?P<id>\d+)',
                                                 list_item.find_previous("p", class_="nav_head").text.strip()).group(
                                "id").zfill(2)
                            prev_id = f"{prev_id1}-p{prev_id2}"
                            prev_id4 = f"{prev_id1}-p{int(prev_id2)+1:02}"

                        elif re.search(r'^SUBPART\s*(?P<id>\d+)',list_item.find_previous("p", class_="nav_head").text.strip()):
                            prev_id1 = prev_id4
                            prev_id2 = re.search(r'^SUBPART\s*(?P<id>\d+)',
                                                 list_item.find_previous("p", class_="nav_head").text.strip()).group(
                                "id").zfill(2)
                            prev_id = f"{prev_id1}-sp{prev_id2}"
                        else:
                            prev_id = list_item.find_previous("h2", class_="parth2").get("id")

                    sub_tag = "-s"

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


        ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for li_tag in self.soup.find_all("li"):
            if not li_tag.get('class'):
                if re.search('constitution', self.html_file_name):
                    # prev_id = li_tag.find_previous("h4").get("id")
                    # chap_num = re.sub(r'[\s.]+', '', li_tag.text.strip()).lower()
                    # sub_tag = "-"
                    # self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)



                    if re.search(r'^[A-HJ-UW-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(ul_analy_tag)
                            prev_li.append(ul_analy_tag)

                            if li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                            tag.text.strip())):
                                prev_id1 = re.sub(r'^#','',li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())).get("href"))
                            else:
                                prev_id1 = None

                            chap_num = "A"
                        else:
                            chap_num = re.search(r'^(?P<id>[A-HJ-UW-Z])\.', li_tag.text.strip()).group("id")
                            ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id1, None)

                    elif re.search(r'^[1-9]\.', li_tag.text.strip()):
                        if re.search(r'^1\.', li_tag.text.strip()):
                            num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(num_ul_analy_tag)
                            prev_li.append(num_ul_analy_tag)
                            prev_id2 = re.sub(r'^#', '', li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[A-Z]+\.',
                                                                            tag.text.strip())).get("href"))
                            chap_num = "1"

                        else:
                            chap_num = re.search(r'^(?P<id>[1-9])\.', li_tag.text.strip()).group("id")
                            num_ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id2, None)

                    if re.search(r'^[I,V,X]+\.',li_tag.text.strip()):
                        if re.search(r'^I\.',li_tag.text.strip()) and re.search(r'^H\.',li_tag.find_previous("li").text.strip()):
                            ul_analy_tag.append(li_tag)
                            prev_id3 = prev_id1

                        elif re.search(r'^I\.',li_tag.text.strip()):
                            prev_id3 = li_tag.find_previous("h4").get("id")

                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)',li_tag.text.strip()).group("ar")
                        prev_id = prev_id3
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)




                else:
                    if re.search(r'^[A-HJ-UW-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(ul_analy_tag)
                            prev_li.append(ul_analy_tag)

                            if li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                            tag.text.strip())):
                                prev_id1 = re.sub(r'^#','',li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())).get("href"))
                            else:
                                prev_id1 = None

                            chap_num = "A"
                        else:
                            chap_num = re.search(r'^(?P<id>[A-HJ-UW-Z])\.', li_tag.text.strip()).group("id")
                            ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id1, None)

                    elif re.search(r'^[1-9]\.', li_tag.text.strip()):
                        if re.search(r'^1\.', li_tag.text.strip()):
                            num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(num_ul_analy_tag)
                            prev_li.append(num_ul_analy_tag)
                            prev_id2 = re.sub(r'^#', '', li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[A-Z]+\.',
                                                                            tag.text.strip())).get("href"))
                            chap_num = "1"

                        else:
                            chap_num = re.search(r'^(?P<id>[1-9])\.', li_tag.text.strip()).group("id")
                            num_ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id2, None)

                    if re.search(r'^[I,V,X]+\.',li_tag.text.strip()):
                        if re.search(r'^I\.',li_tag.text.strip()) and re.search(r'^H\.',li_tag.find_previous("li").text.strip()):
                            ul_analy_tag.append(li_tag)
                            prev_id3 = prev_id1

                        elif re.search(r'^I\.',li_tag.text.strip()):
                            prev_id3 = li_tag.find_previous("h4").get("id")

                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)',li_tag.text.strip()).group("ar")
                        prev_id = prev_id3
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)


    # create div tags
    def create_and_wrap_with_div_tag(self):
        self.soup = BeautifulSoup(self.soup.prettify(formatter=None), features='lxml')
        for header in self.soup.findAll('h2'):
            new_chap_div = self.soup.new_tag('div')
            sec_header = header.find_next_sibling()
            header.wrap(new_chap_div)
            while True:
                next_sec_tag = sec_header.find_next_sibling()
                if sec_header.name == 'h3':
                    new_sec_div = self.soup.new_tag('div')
                    tag_to_wrap = sec_header.find_next_sibling()
                    sec_header.wrap(new_sec_div)
                    while True:
                        next_tag = tag_to_wrap.find_next_sibling()
                        if tag_to_wrap.name == 'h4':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)

                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                if inner_tag.name == 'h5':
                                    new_h5_div = self.soup.new_tag('div')
                                    inner_h5_tag = inner_tag.find_next_sibling()
                                    inner_tag.wrap(new_h5_div)
                                    while True:
                                        next_h5_child_tag = inner_h5_tag.find_next_sibling()
                                        new_h5_div.append(inner_h5_tag)
                                        inner_next_tag = next_h5_child_tag
                                        if not next_h5_child_tag or next_h5_child_tag.name in ['h3', 'h2', 'h4', 'h5']:
                                            break
                                        inner_h5_tag = next_h5_child_tag
                                    inner_tag = new_h5_div
                                new_sub_sec_div.append(inner_tag)
                                next_tag = inner_next_tag
                                if not inner_next_tag or inner_next_tag.name in ['h3',
                                                                                 'h2'] or inner_next_tag.name == 'h4' \
                                        and inner_next_tag.get('class'):
                                    break
                                inner_tag = inner_next_tag
                            tag_to_wrap = new_sub_sec_div
                        elif tag_to_wrap.name == 'h5':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)
                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                new_sub_sec_div.append(inner_tag)
                                next_tag = inner_next_tag
                                if not inner_next_tag or inner_next_tag.name in ['h3', 'h2', 'h4', 'h5']:
                                    break
                                inner_tag = inner_next_tag
                            tag_to_wrap = new_sub_sec_div
                        if not re.search(r'h\d', tag_to_wrap.name):
                            new_sec_div.append(tag_to_wrap)
                        next_sec_tag = next_tag
                        if not next_tag or next_tag.name in ['h3', 'h2']:
                            break
                        tag_to_wrap = next_tag
                    sec_header = new_sec_div
                new_chap_div.append(sec_header)
                if not next_sec_tag or next_sec_tag.name == 'h2':
                    break
                sec_header = next_sec_tag

        print('wrapped div tags')


    # citation
    def add_citation(self):


        class_dict = {'co_code':'Colo\.\s*\d+',
                      'co_law':'Colo\.\s*Law\.\s*\d+|L\.\s*\d+,\s*p\.\s*\d+',
                      'denv_law':'\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+',
                      'COA':'\d{4}\s*COA\s*\d+'}


        #
        # for tag in self.soup.find_all(["p", "li"]):
        #     if re.search(r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
        #                  r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
        #                  r"\d{4}\s*COA\s*\d+|"
        #                  r"L\.\s*\d+,\s*p\.\s*\d+", tag.text.strip()):
        #         # cite_li_tags.append(tag)
        #         text = str(tag)
        #         for key, value in class_dict.items():
        #             for match in [x for x in re.findall(value, tag.get_text(), re.I)]:
        #                 inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>', '', text, re.DOTALL)
        #                 tag.clear()
        #                 text = re.sub(re.escape(match),
        #                               f'<cite class="{key}">{match}</cite>',
        #                               inside_text, re.I)
        #                 tag.append(text)

        for tag in self.soup.find_all(["p","li"]):
            if re.search(r"§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z]\))*(\([I,V,X]+\))*", tag.text.strip()):
                text = str(tag)
                for match in [x[0] for x in re.findall(r"(§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z]\))*(\([I,V,X]+\))*)", tag.get_text())]:
                        inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>', '', text, re.DOTALL)
                        tag.clear()

                        if re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*', match.strip()):
                            chap_num = re.search(r'§*\s*(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<sec_id>\d+(\.\d+)*)', match.strip())
                            t_id = chap_num.group("title_id").zfill(2)
                            c_id = chap_num.group("chap_id").zfill(2)
                            s_id = chap_num.group("sec_id").zfill(2)
                            tag_id = f'gov.co.crs.title.{t_id}.html#t{t_id}c{c_id}s{s_id}'
                            target = "_blank"


                            if re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+(\.\d+)*\))',match.strip()):

                                chap_num = re.search(r'§*\s*(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<sec_id>\d+(\.\d+)*)(?P<ol_id>\s*\(\d+(\.\d+)*\))',
                                    match.strip())
                                t_id = chap_num.group("title_id").zfill(2)
                                c_id = chap_num.group("chap_id").zfill(2)
                                s_id = chap_num.group("sec_id").zfill(2)
                                ol_id = chap_num.group("ol_id")
                                tag_id = f'gov.co.crs.title.{t_id}.html#t{t_id}c{c_id}s{s_id}ol1{ol_id}'
                                target = "_blank"

                                if re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z](\.\d+)*\))', match.strip()):
                                    chap_num = re.search(
                                        r'§*\s*(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<sec_id>\d+(\.\d+)*)(?P<ol_id>\s*\(\d+(\.\d+)*\))(?P<ol_id2>\s*\([a-z](\.\d+)*\))',
                                        match.strip())
                                    t_id = chap_num.group("title_id").zfill(2)
                                    c_id = chap_num.group("chap_id").zfill(2)
                                    s_id = chap_num.group("sec_id").zfill(2)
                                    ol_id = chap_num.group("ol_id")
                                    ol_id2 = chap_num.group("ol_id2")
                                    tag_id = f'gov.co.crs.title.{t_id}.html#t{t_id}c{c_id}s{s_id}ol1{ol_id}{ol_id2}'
                                    target = "_blank"


                                    if re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z](\.\d+)*\))(\([I,V,X]+\))', match.strip()):
                                        chap_num = re.search(
                                            r'§*\s*(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<sec_id>\d+(\.\d+)*)(?P<ol_id>\s*\(\d+(\.\d+)*\))(?P<ol_id2>\s*\([a-z](\.\d+)*\))(?P<ol_id3>\([I,V,X]+\))',
                                            match.strip())
                                        t_id = chap_num.group("title_id").zfill(2)
                                        c_id = chap_num.group("chap_id").zfill(2)
                                        s_id = chap_num.group("sec_id").zfill(2)
                                        ol_id = chap_num.group("ol_id")
                                        ol_id2 = chap_num.group("ol_id2")
                                        ol_id3 = chap_num.group("ol_id3")
                                        tag_id = f'gov.co.crs.title.{t_id}.html#t{t_id}c{c_id}s{s_id}ol1{ol_id}{ol_id2}{ol_id3}'
                                        target = "_blank"


                        text = re.sub(fr'\s{re.escape(match)}',f'<cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',inside_text,re.I)
                        tag.append(text)

        for tag in self.soup.find_all(["p", "li"]):
            if re.search(r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                                 r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                                 r"\d{4}\s*COA\s*\d+|"
                                 r"L\.\s*\d+,\s*p\.\s*\d+", tag.text.strip()):
                        # cite_li_tags.append(tag)
                text = str(tag)
                for key, value in class_dict.items():
                    for match in [x for x in re.findall(value, tag.get_text(), re.I)]:
                        inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>', '', text, re.DOTALL)
                        tag.clear()
                        text = re.sub(re.escape(match),
                                              f'<cite class="{key}">{match}</cite>',
                                              inside_text, re.I)
                        tag.append(text)



        for empty_li in self.soup.find_all("li"):
            text = str(empty_li)
            if re.search(r'^<li class="\w\d+" id=".+">&lt;',text):
                empty_li.unwrap()

        print("cite is created")



    # creating numberical ol
    def create_numberical_ol(self):
        pattern = re.compile(
            r'^\(\d+\)|^\(\d+\)\s\(\D\)|^\(\d+\)\s*\(\D\)\s*\([I,V,X]+\)|^\(\d+\.\d+\)|^\(\d+\.\d+\)\s*\(\w\)|'
            r'^\(\s*[a-z]\s*\)|^\(\w+\)\s*\([I,V,X]+\)|^\([a-z]\.\d+\)|'
            r'^\([I,V,X]+\)|^\([I,V,X]+\)\s*\([A-Z]\)|'
            r'^\(\s*[A-Z]\s*\)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z]\s*\)')
        rom_pattern = re.compile(r'^\([I,V,X]+\)')
        Alpha_pattern = re.compile(r'^\(\s*[A-Z]\s*\)')

        for tag in self.soup.findAll("li", class_=self.class_regex["ol"]):
            if re.match(pattern, tag.text.strip()):
                if re.match(Num_bracket_pattern, tag.text.strip()) or re.match(alpha_pattern, tag.text.strip()) or \
                        re.match(Alpha_pattern, tag.text.strip()) or re.match(rom_pattern, tag.text.strip()):
                    if tag.span:
                        if re.search(pattern, tag.span.text.strip()):
                            tag.span.string = ""


                #     else:
                #         tag_text = re.sub(pattern, '', tag.text.strip())
                #         tag.string = tag_text
                #
                # else:
                #     tag_text = re.sub(r'^\D+\.', '', tag.text.strip())
                #     tag.string = tag_text

    def add_watermark_and_remove_class_name(self):

        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p']:
                del tag["class"]

        watermark_tag = self.soup.new_tag('p', Class='transformation')
        watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                          datetime.now().date())

        title_tag = self.soup.find("nav")
        if title_tag:
            title_tag.insert(0, watermark_tag)

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

        # for all_tag in self.soup.findAll():
        #     if all_tag.get("class"):
        #         all_tag_class = str(all_tag.get("class"))
        #         # print(all_tag_class)
        #         if re.match(r'^\[\'p\d\'\]', all_tag_class.strip()):
        #             del all_tag["class"]
        #
        # for all_li in self.soup.find_all("li"):
        #     if re.search(r'^<li\s*class="p\d"', all_li.text.strip()):
        #         all_li.unwrap()


    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"/home/mis/cic-code-co/transforms/co/occo/r{self.release_number}/{self.html_file_name}",
                  "w") as file:
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
                                'sec_head': r'^Section\s*[0-9a-z]+\.',
                                'junk': '^Statute text', 'ol': r'^(\(1\))',
                                'head4': '^ANNOTATIONS', 'art_head': '^ARTICLE',
                                'amd': '^AMENDMENTS', 'Analysis': '^I\.'}

            self.get_class_name()
            self.remove_junk()
            self.recreate_tag1()
            self.replace_tags()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_and_wrap_with_div_tag()
            # self.create_and_wrap_with_ol_tag()
            self.add_citation()



        else:
            self.get_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_and_wrap_with_div_tag()
            self.convert_paragraph_to_alphabetical_ol_tags()


            # self.create_and_wrap_with_ol_tag()
            # self.add_citation()
            # self.create_numberical_ol()
            # self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)



# --input_file_name gov.co.crs.title.01.html
# --input_file_name gov.co.crs.constitution.co.html