import roman
from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase


class COParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^Art.', 'head2': '^ARTICLE|^Article|^Part',
                            'title': '^(TITLE|Title)|^(CONSTITUTION OF KENTUCKY)',
                            'sec_head': r'^\d+(\.\d+)*-\d+-\d+\.', 'part_head': '^PART\s\d+',
                            'junk': '^Annotations', 'ol': r'^(\(1\))', 'head4': '^ANNOTATION', 'nd_nav': '^1\.',
                            'Analysis': '^I\.', 'editor': '^Editor\'s note', }
        self.title_id = None
        self.soup = None
        self.meta_tags = []
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
        :return:/home/mis/cic-beautify-state-codes/transforms/co/occo
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
        [text_junk.decompose() for text_junk in self.soup.find_all("p") if
         re.search(r'^——————————', text_junk.text.strip())]

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
        sec_head_list = []
        ann_count = 1
        count = 1
        section_head = []
        sec_count = 1
        part_head = []
        part_count = 1
        art_head = []
        art_count = 1
        subsec_head = []
        subsec_count = 1
        subpart_head = []
        subpart_count = 1

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
                        chap_num = re.search(r'^((ARTICLE|Article)\s*(?P<ar>[A-Z]+|[IVX]+))',
                                             header_tag.text.strip()).group(
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
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    if re.search(r'^(ARTICLE)', header_tag.text.strip()):
                        tag_name = "h2"
                        if header_tag.find_previous("h2", class_='amendmenth2'):
                            prev_id = header_tag.find_previous("h2", class_='amendmenth2').get("id")
                        else:
                            prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[I,V,X]+))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)
                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^(Section|SECTION)\s*[0-9]+(\.\d+)*[a-z]*\.', header_tag.text.strip()):
                        chap_num = re.search(r'^(Section|SECTION)\s*(?P<ar>[0-9]+(\.\d+)*[a-z]*)\.',
                                             header_tag.text.strip()).group(
                            "ar").zfill(2)
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2").get("id")
                        sub_tag = "-s"
                        class_name = "section"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)
                elif header_tag.get("class") == [self.class_regex["amd"]]:
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)
                elif header_tag.get("class") == [self.class_regex["head4"]] or header_tag.name == "h4":
                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[I,V,X]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'
                    elif re.search(r'^[A-HJ-UW-Z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[I,V,X]+\.',
                                                                                                        tag.text.strip())).get(
                            "id")
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
                        if re.search(r'^Editor’s note:|Cross references:|Law reviews:|ANNOTATION|OFFICIAL COMMENT',
                                     header_tag.text.strip()):
                            header_tag.name = "h4"
                            if header_tag.find_previous("h3"):
                                prev_id = header_tag.find_previous("h3").get("id")
                                chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                                if chap_num in subsec_head:
                                    header_tag["id"] = f'{prev_id}-{chap_num}.{subsec_count}'
                                    subsec_count += 1
                                else:
                                    header_tag["id"] = f'{prev_id}-{chap_num}'
                            else:
                                chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                                header_tag["id"] = f't{self.title_id}-{chap_num}'
                            subsec_head.append(chap_num)

                        else:
                            header_tag.name = "p"


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
                    if re.search(r'^(TITLE|Title)\s(?P<title_id>\d+)', header_tag.text.strip()):
                        self.title_id = re.search(r'^(TITLE|Title)\s(?P<title_id>\d+)', header_tag.text.strip()).group(
                            'title_id').zfill(2)
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag["id"] = f't{self.title_id}'
                        header_tag.wrap(self.soup.new_tag("nav"))

                    if re.search(r'^SUBPART\s*(?P<id>\d+)', header_tag.text.strip()):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="parth2").get("id")
                        chap_num = re.search(r'^SUBPART\s*(?P<id>\d+)', header_tag.text.strip()).group(
                            "id").zfill(2)
                        sub_tag = "-sp"
                        class_name = "subparth2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)
                        sec_count = 1

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE|^Article', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        if header_tag.find_previous("h2", class_="gnrlh2"):
                            prev_id = header_tag.find_previous("h2", class_="gnrlh2").get("id")
                        else:
                            prev_id = None
                        chap_num = re.search(r'^((ARTICLE|Article)\s*(?P<ar>\d+(\.\d+)*))',
                                             header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"
                        if chap_num in art_head:
                            new_chap_num = f'{chap_num}.{art_count}'
                            art_count += 1
                        else:
                            new_chap_num = chap_num
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, new_chap_num, prev_id, sub_tag,
                                                             class_name)
                        sec_count = 1
                        section_head = []
                        part_count = 1
                        art_head.append(chap_num)

                    elif re.search(r'^(PART|Part)\s*(?P<ar>\d+)', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")
                        chap_num = re.search(r'^(PART|Part)\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        chap = f'{prev_id}{chap_num}'

                        if chap in part_head:
                            new_chap_num = f'{chap_num}.{part_count}'
                            part_count += 1
                        else:
                            new_chap_num = chap_num
                        sub_tag = "-p"
                        class_name = "parth2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, new_chap_num, prev_id, sub_tag,
                                                             class_name)
                        sec_count = 1
                        part_head.append(chap)



                    elif re.search(r'^(Subpart)\s*(?P<ar>\d+)', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="parth2").get("id")
                        chap_num = re.search(r'^Subpart\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        chap = f'{prev_id}{chap_num}'

                        if chap in subpart_head:
                            new_chap_num = f'{chap_num}.{part_count}'
                            subpart_count += 1
                        else:
                            new_chap_num = chap_num
                        sub_tag = "-s"
                        class_name = "subparth2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, new_chap_num, prev_id, sub_tag,
                                                             class_name)
                        sec_count = 1
                        subpart_head.append(chap)



                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[^0-9A-Za-z]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-"
                        class_name = "gnrlh2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)
                        sec_count = 1

                elif header_tag.get("class") == [self.class_regex["part_head"]] or header_tag.get("class") == \
                        self.class_regex["nav_head"]:
                    if re.search(r'\w+', header_tag.text.strip()):
                        header_tag["class"] = "nav_head"

                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.*(\.\d+)*', header_tag.text.strip(), re.I):
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")

                        if re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.\d+\.', header_tag.text.strip()):
                            chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+\.\d+)',
                                                 header_tag.text.strip()).group(
                                "sid").zfill(2)

                            if chap_num in section_head:
                                new_chap_num = f'{chap_num}.{sec_count}'
                                sec_count += 1
                            else:
                                new_chap_num = chap_num
                        else:
                            chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*(\.\d+)*',
                                                 header_tag.text.strip()).group(
                                "sid").zfill(2)
                            if chap_num in section_head:
                                new_chap_num = f'{chap_num}.{sec_count}'
                                sec_count += 1
                            else:
                                new_chap_num = chap_num
                        sub_tag = "-s"
                        class_name = "section"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, new_chap_num, prev_id, sub_tag,
                                                             class_name)
                        section_head.append(chap_num)
                        subsec_count = 1
                        subsec_head = []

                elif header_tag.get("class") == [self.class_regex["head4"]] or header_tag.name == "h4":

                    if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"

                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[IVX]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'



                    elif re.search(r'^[A-HJ-UW-Z]\.\s"?[A-Z][a-z]+', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[IVX]+\.',
                                                                                                        tag.text.strip())).get(
                            "id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        if header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())):

                            prev_id = header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                            chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                            header_tag["id"] = f'{prev_id}-{chap_num}'
                        else:
                            header_tag["class"] = [self.class_regex['ol']]


                    else:

                        if re.search(r'^Editor\'s note:|Cross references:|Law reviews:|ANNOTATION|OFFICIAL COMMENT',
                                     header_tag.text.strip()):
                            header_tag.name = "h4"
                            if header_tag.find_previous("h3"):
                                prev_id = header_tag.find_previous("h3").get("id")
                                chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                                if chap_num in subsec_head:
                                    header_tag["id"] = f'{prev_id}-{chap_num}.{subsec_count}'
                                    subsec_count += 1
                                else:
                                    header_tag["id"] = f'{prev_id}-{chap_num}'
                            else:
                                chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                                header_tag["id"] = f't{self.title_id}-{chap_num}'
                            subsec_head.append(chap_num)
                        else:
                            header_tag.name = "p"

                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^Editor’s note:|Cross references:|Law reviews:|ANNOTATION|OFFICIAL COMMENT',
                                 header_tag.text.strip()):
                        header_tag.name = "h4"
                        if header_tag.find_previous("h3"):
                            prev_id = header_tag.find_previous("h3").get("id")
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            if chap_num in subsec_head:
                                header_tag["id"] = f'{prev_id}-{chap_num}.{subsec_count}'
                                subsec_count += 1
                            else:
                                header_tag["id"] = f'{prev_id}-{chap_num}'
                        else:
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            header_tag["id"] = f't{self.title_id}-{chap_num}'
                        subsec_head.append(chap_num)




                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if not re.search(r'^Section', header_tag.text.strip()):
                        header_tag.name = "li"

                elif header_tag.get("class") == [self.class_regex["ol"]]:
                    if re.search(r'^(ARTICLE|Article) [IVX]+', header_tag.text.strip()):
                        header_tag.name = "h3"
                        a_id = re.search(r'^(ARTICLE|Article) (?P<aid>[IVX]+)', header_tag.text.strip()).group("aid")
                        prev_id = header_tag.find_previous(
                            lambda tag: tag.name in ['h3'] and re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.*(\.\d+)*',
                                                                         tag.text.strip())).get(
                            "id")

                        header_tag["id"] = f'{prev_id}a{a_id}'



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
                            header_tag.unwrap()

        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        self.meta_tags.append(stylesheet_link_tag)

    def recreate_tag(self):
        ol_list = []
        num_ol_tag = self.soup.new_tag("ol")
        ol_count = 1

        if re.search('constitution', self.html_file_name):
            for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
                current_p_tag = p_tag.text.strip()
                next_sibling = p_tag.find_next_sibling()
                if re.search('^§', current_p_tag):
                    if re.search('^§', p_tag.find_next("b").text.strip()):
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

                if re.search(r'^\(\d+\)', current_p_tag):
                    if p_tag.find_next().name == "b":
                        alpha_text = re.sub(r'^[^.]+\.', '', current_p_tag)
                        num_text = re.sub(r'\(a\).+', '', current_p_tag)
                        if re.search(r'^\s*\([a-z]\)', alpha_text):
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.class_regex['ol']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                        elif re.search(r'^[\w\s]+:\s*\([a-z]\)', alpha_text):
                            num_text = re.sub(r'\(a\).+', '', current_p_tag)
                            alpha_text = re.search(r'\(a\).+', current_p_tag).group()
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

        else:
            for p_tag in self.soup.find_all():
                if p_tag.get("class") == [self.class_regex["ol"]]:
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
                            if re.search(r'^\[ Editor\'s note:', p_tag.find_next().text.strip()):
                                continue
                            else:
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
                        alpha = re.search(
                            r'^(?P<num_text>\(\d+\)\s*\((?P<alpha1>[a-z]+)\)\s*.+\s*)(?P<alpha_text>\((?P<alpha2>[a-z])\).+)',
                            current_p_tag)
                        if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                            nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                                  p_tag.find_next_sibling().text.strip()).group("alpha3")
                            if ord(alpha.group("alpha2")) == (ord(alpha.group("alpha1"))) + 1:
                                if ord(nxt_alpha) == (ord(alpha.group("alpha2"))) + 1:
                                    alpha_text = alpha.group("alpha_text")
                                    num_text = alpha.group("num_text")
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = alpha_text
                                    new_p_tag["class"] = [self.class_regex['ol']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag.string = num_text

                    if re.search(r'^\([I,V,X]+\)', current_p_tag):
                        if re.search(r'^\((?P<rom1>[IVX]+)\).+\((?P<rom2>[IVX]+)\)', current_p_tag):
                            alpha = re.search(r'^(?P<txt1>\((?P<rom1>[IVX]+)\).+)(?P<txt2>\((?P<rom2>[IVX]+)\).+)',
                                              current_p_tag)
                            if re.match(r'^\([I,V,X]+\)', p_tag.find_next_sibling().text.strip()):
                                nxt_rom = re.search(r'^\((?P<rom3>[IVX]+)\)',
                                                    p_tag.find_next_sibling().text.strip()).group(
                                    "rom3")
                                if int(self.convert_roman_to_digit(alpha.group("rom2"))) == int(
                                        (self.convert_roman_to_digit(alpha.group("rom1"))) + 1):
                                    if int(self.convert_roman_to_digit(nxt_rom)) == int(
                                            (self.convert_roman_to_digit(alpha.group("rom2"))) + 1):
                                        alpha_text = alpha.group("txt2")
                                        num_text = alpha.group("txt1")
                                        new_p_tag = self.soup.new_tag("p")
                                        new_p_tag.string = alpha_text
                                        new_p_tag["class"] = [self.class_regex['ol']]
                                        p_tag.insert_after(new_p_tag)
                                        p_tag.string = num_text

                    if re.search(r'^\(\d+\)\s*(to|and)\s*\(\d+\)\s*', current_p_tag):
                        nxt_tag = p_tag.find_next_sibling(
                            lambda tag: tag.name in ['p'] and re.search(r'^[^\s]', tag.text.strip()))
                        alpha = re.search(
                            r'^(?P<text1>\((?P<num1>\d+)\))\s*(to|and)\s*(?P<text2>\((?P<num2>\d+)\)\s*(?P<rpt_text>.+))',
                            current_p_tag)
                        if re.search(r'^\(\d+\)', nxt_tag.text.strip()):
                            nxt_alpha = re.search(r'^\((?P<num3>\d+)\)', nxt_tag.text.strip()).group(
                                "num3")
                            if int(nxt_alpha) != int(alpha.group("num1")) + 1:
                                if int(alpha.group("num2")) == int(alpha.group("num1")) + 1:
                                    if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                        alpha_text = alpha.group("text2")
                                        num_text = alpha.group("text1")
                                        new_p_tag = self.soup.new_tag("p")
                                        new_p_tag.string = alpha_text
                                        new_p_tag["class"] = [self.class_regex['ol']]
                                        p_tag.insert_after(new_p_tag)
                                        p_tag.string = num_text
                                else:
                                    if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                        alpha_text = alpha.group("text2")
                                        num_text = alpha.group("text1") + alpha.group("rpt_text")
                                        new_p_tag = self.soup.new_tag("p")
                                        new_p_tag.string = alpha_text
                                        new_p_tag["class"] = [self.class_regex['ol']]
                                        p_tag.insert_after(new_p_tag)
                                        p_tag.string = num_text
                                        range_from = int(alpha.group("num1"))
                                        range_to = int(alpha.group("num2"))
                                        count = range_from + 1
                                        for new_p_tag in range(range_from + 1, range_to):
                                            new_p_tag = self.soup.new_tag("p")
                                            new_p_tag.string = f'({count}){alpha.group("rpt_text")}'
                                            new_p_tag["class"] = [self.class_regex['ol']]
                                            p_tag.insert_after(new_p_tag)
                                            p_tag = new_p_tag
                                            count += 1

                    if re.search(r'^\([a-zA-Z]\)\s*(to|and)\s*\([a-zA-Z]\)\s*(Repealed.|\()', current_p_tag):
                        alpha = re.search(
                            r'^(?P<text1>\((?P<num1>[a-zA-Z])\))\s*(to|and)\s*(?P<text2>\((?P<num2>[a-zA-Z])\)\s*(?P<rpt_text>Repealed.|\(.+))',
                            current_p_tag)
                        if re.match(r'^\([a-zA-Z]\)', p_tag.find_next_sibling().text.strip()):
                            nxt_alpha = re.search(r'^\((?P<num3>[a-zA-Z])\)',
                                                  p_tag.find_next_sibling().text.strip()).group(
                                "num3")
                            if ord(alpha.group("num2")) == ord(alpha.group("num1")) + 1:
                                if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                                    alpha_text = alpha.group("text2")
                                    num_text = alpha.group("text1")
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = alpha_text
                                    new_p_tag["class"] = [self.class_regex['ol']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag.string = num_text

                            else:
                                if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                                    alpha_text = alpha.group("text2")
                                    num_text = alpha.group("text1") + alpha.group("rpt_text")
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = alpha_text
                                    new_p_tag["class"] = [self.class_regex['ol']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag.string = num_text
                                    range_from = ord(alpha.group("num1"))
                                    range_to = ord(alpha.group("num2"))
                                    count = range_from + 1
                                    for new_p_tag in range(range_from + 1, range_to):
                                        new_p_tag = self.soup.new_tag("p")
                                        new_p_tag.string = f'({chr(count)}){alpha.group("rpt_text")}'
                                        new_p_tag["class"] = [self.class_regex['ol']]
                                        p_tag.insert_after(new_p_tag)
                                        p_tag = new_p_tag
                                        count += 1

                        else:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.class_regex['ol']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                            range_from = ord(alpha.group("num1"))
                            range_to = ord(alpha.group("num2"))
                            count = range_from + 1
                            for new_p_tag in range(range_from + 1, range_to):
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = f'({chr(count)})'
                                new_p_tag["class"] = [self.class_regex['ol']]
                                p_tag.insert_after(new_p_tag)
                                p_tag = new_p_tag
                                count += 1

                    if re.search(r'^\([a-z]\).+\([a-z]\)\s*', current_p_tag):
                        alpha = re.search(r'^(?P<text1>\((?P<alpha1>[a-z])\).+)(?P<text2>\((?P<alpha2>[a-z])\)\s*.+)',
                                          current_p_tag)
                        if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                            nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                                  p_tag.find_next_sibling().text.strip()).group(
                                "alpha3")
                            if ord(alpha.group("alpha2")) == ord(alpha.group("alpha1")) + 1:
                                if ord(nxt_alpha) == ord(alpha.group("alpha2")) + 1:
                                    alpha_text = alpha.group("text2")
                                    num_text = alpha.group("text1")
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

                if p_tag.get("class") == [self.class_regex["head4"]]:
                    if p_tag.b:
                        if re.search(r'^Editor’s note:|Cross references:|Law reviews:', p_tag.b.text.strip()):
                            header_text = p_tag.b.get_text()
                            p_text = re.search(r':(?P<text>.*)', p_tag.text.strip()).group('text')
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = header_text
                            new_p_tag["class"] = [self.class_regex['head4']]
                            p_tag.insert_before(new_p_tag)
                            p_tag.string = p_text

        print("tags are recreated")

    def convert_roman_to_digit(self, roman_digit):
        value = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
        prev = 0
        ans = 0
        length = len(roman_digit)
        for num in range(length - 1, -1, -1):
            if value[roman_digit[num]] >= prev:
                ans += value[roman_digit[num]]
            else:
                ans -= value[roman_digit[num]]
            prev = value[roman_digit[num]]
        return ans

    # def convert_paragraph_to_alphabetical_ol_tags2(self):
    #     """
    #         For each tag which has to be converted to orderd list(<ol>)
    #         - create new <ol> tags with appropriate type (1, A, i, a ..)
    #         - get previous headers id to set unique id for each list item (<li>)
    #         - append each li to respective ol accordingly
    #     """
    #     main_sec_alpha = 'a'
    #     cap_alpha = 'A'
    #     ol_head = 1
    #     num_count = 1
    #     roman_count = 1
    #     alpha_ol = self.soup.new_tag("ol", type="a")
    #     cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #     inner_ol = self.soup.new_tag("ol", type="i")
    #     roman_ol = self.soup.new_tag("ol", type="I")
    #     num_ol = self.soup.new_tag("ol")
    #     ol_count = 1
    #     ol_list = []
    #     new_num = None
    #     innr_roman_ol = None
    #     cap_alpha_cur_tag = None
    #     new_alpha = None
    #
    #     for p_tag in self.soup.find_all():
    #         if p_tag.b:
    #             p_tag.b.unwrap()
    #         current_tag_text = p_tag.text.strip()
    #
    #         if re.search(rf'^\({ol_head}\)', current_tag_text):
    #             p_tag.name = "li"
    #             cap_alpha = 'A'
    #             num_cur_tag = p_tag
    #             if re.search(r'^\(1\)', current_tag_text):
    #                 if new_alpha:
    #                     num_ol = self.soup.new_tag("ol")
    #                     p_tag.wrap(num_ol)
    #                     new_alpha.append(num_ol)
    #                     new_num = p_tag
    #                 else:
    #                     num_ol = self.soup.new_tag("ol")
    #                     p_tag.wrap(num_ol)
    #                     main_sec_alpha = "a"
    #                 if p_tag.find_previous(["h4", "h3"]):
    #                     prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
    #                 else:
    #                     prev_head_id = p_tag.find_previous(["h2", "h1"]).get("id")
    #
    #                 if prev_head_id in ol_list:
    #                     ol_count += 1
    #                 else:
    #                     ol_count = 1
    #                 ol_list.append(prev_head_id)
    #             else:
    #                 num_ol.append(p_tag)
    #                 if new_num:
    #                     new_num = p_tag
    #                 if new_alpha == None:
    #                     main_sec_alpha = "a"
    #
    #             prev_num_id = f'{prev_head_id}ol{ol_count}{ol_head}'
    #             p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
    #             p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
    #             ol_head += 1
    #
    #             if re.search(r'^\(\d+\)\s\(\w\)', current_tag_text):
    #
    #                 alpha_ol = self.soup.new_tag("ol", type="a")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.string = re.sub(r'^\(\d+\)\s\(\w\)', '', current_tag_text)
    #                 li_tag.append(current_tag_text)
    #                 alpha_cur_tag = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>\w)\)', current_tag_text)
    #                 prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 alpha_ol.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(alpha_ol)
    #                 main_sec_alpha = "b"
    #
    #                 if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_tag_text):
    #                     roman_ol = self.soup.new_tag("ol", type="I")
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
    #                     inner_li_tag.append(current_tag_text)
    #                     li_tag["class"] = self.class_regex['ol']
    #                     rom_cur_tag = li_tag
    #                     cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
    #                                         current_tag_text)
    #                     prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #                     inner_li_tag[
    #                         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #                     roman_ol.append(inner_li_tag)
    #                     alpha_cur_tag.string = ""
    #                     alpha_cur_tag.insert(0, roman_ol)
    #
    #                     if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
    #                         cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #                         inner_li_tag = self.soup.new_tag("li")
    #                         inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '',
    #                                                      current_tag_text)
    #                         # inner_li_tag.append(current_tag_text)
    #                         li_tag["class"] = self.class_regex['ol']
    #                         cur_tag = re.search(
    #                             r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
    #                             current_tag_text)
    #                         prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #
    #                         inner_li_tag[
    #                             "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'
    #                         cap_alpha_ol.append(inner_li_tag)
    #                         rom_cur_tag.string = ""
    #                         rom_cur_tag.append(cap_alpha_ol)
    #                         cap_alpha = "B"
    #
    #         # 1.5
    #         elif re.search(r'^\(\d+\.\d+\)', current_tag_text):
    #             cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)', current_tag_text).group("cid")
    #             p_tag["id"] = f'{prev_num_id}-{cur_tag}'
    #             prev_num_tag = p_tag.find_previous(
    #                 lambda tag: tag.name in ['li'] and re.search(r'^\w+', tag.text.strip()))
    #             if not re.search(r'^\(\d+\.\d+\)', p_tag.find_next().text.strip()):
    #                 prev_num_id = f'{prev_num_id}-{cur_tag}'
    #                 p_tag.name = "div"
    #             p_tag.find_previous("li").append(p_tag)
    #             main_sec_alpha = "a"
    #             num_cur_tag = p_tag
    #
    #             if re.search(r'^\(\d+\.\d+\)\s\(\w\)', current_tag_text):
    #                 alpha_ol = self.soup.new_tag("ol", type="a")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_tag_text)
    #                 alpha_cur_tag = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)\s\((?P<pid>\w)\)', current_tag_text)
    #                 prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 alpha_ol.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(alpha_ol)
    #                 main_sec_alpha = "b"
    #
    #                 if re.search(r'^\(\d+\.\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*', current_tag_text):
    #                     roman_ol = self.soup.new_tag("ol", type="I")
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.append(current_tag_text)
    #                     li_tag["class"] = self.class_regex['ol']
    #                     rom_cur_tag = li_tag
    #                     cur_tag = re.search(r'^\((?P<id1>\d+\.\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
    #                                         current_tag_text)
    #                     prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #                     inner_li_tag[
    #                         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #                     roman_ol.append(inner_li_tag)
    #                     p_tag.insert(1, roman_ol)
    #                     roman_ol.find_previous().string.replace_with(roman_ol)
    #
    #         # a
    #         elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
    #             p_tag.name = "li"
    #             alpha_cur_tag = p_tag
    #             roman_count = 1
    #
    #             if re.search(r'^\(a\)', current_tag_text):
    #                 if num_cur_tag == None:
    #                     alpha_ol = self.soup.new_tag("ol", type="a")
    #                     prev_tag = p_tag.find_previous_sibling()
    #                     p_tag.wrap(alpha_ol)
    #                     prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
    #                     prev_alpha_id = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
    #                     p_tag["id"] = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
    #                     ol_head = 1
    #                     new_alpha = p_tag
    #                 else:
    #                     alpha_ol = self.soup.new_tag("ol", type="a")
    #                     prev_tag = p_tag.find_previous_sibling()
    #                     p_tag.wrap(alpha_ol)
    #                     num_cur_tag.append(alpha_ol)
    #                     prev_alpha_id = f'{prev_num_id}{main_sec_alpha}'
    #                     p_tag["id"] = f'{prev_num_id}{main_sec_alpha}'
    #
    #             else:
    #                 alpha_ol.append(p_tag)
    #                 if new_alpha == None:
    #                     prev_alpha_id = f'{prev_num_id}{main_sec_alpha}'
    #                     p_tag["id"] = f'{prev_num_id}{main_sec_alpha}'
    #                 else:
    #                     new_alpha = p_tag
    #                     ol_head = 1
    #                     prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
    #                     prev_alpha_id = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
    #                     p_tag["id"] = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
    #
    #             p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
    #             main_sec_alpha = chr(ord(main_sec_alpha) + 1)
    #
    #             if re.search(r'^\(\w\)\s*\([I,V,X]+\)', current_tag_text):
    #                 roman_ol = self.soup.new_tag("ol", type="I")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
    #                 li_tag.append(current_tag_text)
    #                 li_tag["class"] = self.class_regex['ol']
    #                 rom_cur_tag = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
    #                 prev_rom_id = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 li_tag["id"] = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 roman_ol.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(roman_ol)
    #
    #
    #
    #                 if re.search(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
    #                     cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '', current_tag_text)
    #                     inner_li_tag.append(current_tag_text)
    #                     li_tag["class"] = self.class_regex['ol']
    #                     cur_tag = re.search(
    #                         r'^\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
    #                         current_tag_text)
    #                     prev_id = rom_cur_tag.get("id")
    #                     inner_li_tag[
    #                         "id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("id3")}'
    #                     cap_alpha_ol.append(inner_li_tag)
    #                     p_tag.insert(1, cap_alpha_ol)
    #                     rom_cur_tag.string = ""
    #                     rom_cur_tag.string.replace_with(cap_alpha_ol)
    #                     cap_alpha = "B"
    #
    #             if re.search(r'^\(\w\)\s*\(\d+\)', current_tag_text):
    #                 num_ol = self.soup.new_tag("ol")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.string = re.sub(r'^\(\w\)\s*\(\d+\)', '', current_tag_text)
    #                 li_tag.append(current_tag_text)
    #                 li_tag["class"] = self.class_regex['ol']
    #                 new_num = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>\d+)\)', current_tag_text)
    #                 prev_rom_id = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 li_tag["id"] = f'{new_alpha.get("id")}{cur_tag.group("pid")}'
    #                 num_ol.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(num_ol)
    #                 ol_head = 2
    #                 cap_alpha = "A"
    #                 new_num = None
    #
    #             if re.search(r'^\(\w\)\s*\([ivx]+\)', current_tag_text):
    #                 innr_roman_ol = self.soup.new_tag("ol", type="i")
    #                 inner_li_tag = self.soup.new_tag("li")
    #                 inner_li_tag.append(current_tag_text)
    #                 inner_li_tag["class"] = self.class_regex['ol']
    #                 new_alpha = inner_li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
    #                 prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 inner_li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 innr_roman_ol.append(inner_li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(innr_roman_ol)
    #
    #         # a.5
    #         elif re.search(r'^\(\w+\.\d+\)', current_tag_text):
    #             roman_count = 1
    #             cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)', current_tag_text).group("cid")
    #             p_tag["id"] = f'{prev_alpha_id}-{cur_tag}'
    #             prev_alpha_id = f'{prev_alpha_id}'
    #             prev_alpha_tag = p_tag.find_previous(
    #                 lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)', tag.text.strip()))
    #
    #             if not re.search(r'^\(\w+\.\d+\)', p_tag.find_next().text.strip()) and re.search(r'^\([A-Z]\)',
    #                                                                                              p_tag.find_next().text.strip()):
    #                 prev_alpha_id = f'{prev_alpha_id}-{cur_tag}'
    #                 p_tag.name = "div"
    #             p_tag.find_previous("li").append(p_tag)
    #             alpha_cur_tag = p_tag
    #
    #             if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)', current_tag_text):
    #                 roman_ol = self.soup.new_tag("ol", type="I")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.append(current_tag_text)
    #                 li_tag["class"] = self.class_regex['ol']
    #                 rom_cur_tag = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
    #                 prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
    #                 li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 roman_ol.append(li_tag)
    #                 p_tag.contents = []
    #                 p_tag.append(roman_ol)
    #
    #                 if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
    #                     cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #                     inner_li_tag = self.soup.new_tag("li")
    #                     inner_li_tag.append(current_tag_text)
    #                     inner_li_tag["class"] = self.class_regex['ol']
    #                     cur_tag = re.search(
    #                         r'^\((?P<cid>\w\.\d+)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
    #                         current_tag_text)
    #                     prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}'
    #
    #                     inner_li_tag[
    #                         "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'
    #
    #                     cap_alpha_ol.append(inner_li_tag)
    #                     p_tag.insert(1, cap_alpha_ol)
    #                     cap_alpha_ol.find_previous().string.replace_with(cap_alpha_ol)
    #                     cap_alpha = "B"
    #
    #         # I
    #         elif re.search(r'^\([IVX]+\)', current_tag_text):
    #             p_tag.name = "li"
    #             rom_cur_tag = p_tag
    #             cap_alpha = "A"
    #             if re.search(r'^\(I\)', current_tag_text):
    #                 prev_cap_alpha_tag = p_tag.find_previous(
    #                     lambda tag: tag.name in ['li'] and re.search(r'^\([A-Z]\)', tag.text.strip()))
    #                 if cap_alpha_cur_tag:
    #                     if not re.search(r'^H', cap_alpha1):
    #                         roman_ol = self.soup.new_tag("ol", type="I")
    #                         p_tag.wrap(roman_ol)
    #                         alpha_cur_tag.append(roman_ol)
    #                         p_tag["id"] = f'{prev_alpha_id}I'
    #                     else:
    #                         cap_alpha_ol.append(p_tag)
    #                         p_tag["id"] = f'{prev_rom_id}I'
    #                         cap_alpha1 = 'A'
    #                 else:
    #                     roman_ol = self.soup.new_tag("ol", type="I")
    #
    #                     p_tag.wrap(roman_ol)
    #                     alpha_cur_tag.append(roman_ol)
    #                     p_tag["id"] = f'{prev_alpha_id}I'
    #                 prev_rom_id = f'{prev_alpha_id}I'
    #                 roman_count += 1
    #             else:
    #                 cur_tag = re.search(r'^\((?P<cid>[IVX]+)\)', current_tag_text).group("cid")
    #                 roman_ol.append(p_tag)
    #                 prev_rom_id = f'{prev_alpha_id}{cur_tag}'
    #                 p_tag["id"] = f'{prev_alpha_id}{cur_tag}'
    #
    #             p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)
    #
    #             if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)', current_tag_text):
    #                 cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #                 li_tag = self.soup.new_tag("li")
    #                 li_tag.string = re.sub(r'^\([I,V,X]+\)\s*\(A\)', '', current_tag_text)
    #                 cap_alpha_cur_tag = li_tag
    #                 cur_tag = re.search(r'^\((?P<cid>[I,V,X]+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
    #                 prev_id = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
    #                 li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #
    #                 if not re.search(r'^\(I\)', current_tag_text):
    #                     prev_tag_id = p_tag.find_previous_sibling().get("id")
    #                     cur_tag_id = re.search(r'^[^IVX]+', prev_tag_id).group()
    #                     prev_rom_id = f'{cur_tag_id}{cur_tag.group("cid")}'
    #                     li_tag["id"] = f'{cur_tag_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
    #                 cap_alpha_ol.append(li_tag)
    #                 p_tag.string = ""
    #                 p_tag.append(cap_alpha_ol)
    #                 roman_count += 1
    #                 cap_alpha = "B"
    #
    #         #  A
    #         elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
    #             p_tag.name = "li"
    #             cap_alpha_cur_tag = p_tag
    #             cap_alpha1 = cap_alpha
    #
    #             if re.search(r'^\(A\)', current_tag_text):
    #                 cap_alpha_ol = self.soup.new_tag("ol", type="A")
    #                 p_tag.wrap(cap_alpha_ol)
    #                 prev_id = p_tag.find_previous("li").get("id")
    #                 p_tag.find_previous("li").append(cap_alpha_ol)
    #
    #             else:
    #                 cap_alpha_ol.append(p_tag)
    #
    #             # print(cap_alpha)
    #             #
    #             # if  cap_alpha in ['I','V','X','L']:
    #             #     print(p_tag)
    #             #     print(ascii(cap_alpha))
    #
    #
    #
    #             p_tag["id"] = f'{prev_id}{cap_alpha}'
    #             p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
    #             cap_alpha = chr(ord(cap_alpha) + 1)
    #
    #         # i
    #         elif re.search(r'^\([ivx]+\)', current_tag_text):
    #             p_tag.name = "li"
    #             rom_cur_tag = p_tag
    #             cap_alpha = "A"
    #             if re.search(r'^\(i\)', current_tag_text):
    #                 innr_roman_ol = self.soup.new_tag("ol", type="i")
    #                 p_tag.wrap(innr_roman_ol)
    #                 p_tag.find_previous("li").append(innr_roman_ol)
    #                 prev_alpha = p_tag.find_previous("li")
    #                 p_tag["id"] = f'{prev_alpha.get("id")}i'
    #             else:
    #                 cur_tag = re.search(r'^\((?P<cid>[ivx]+)\)', current_tag_text).group("cid")
    #                 if innr_roman_ol:
    #                     innr_roman_ol.append(p_tag)
    #                     p_tag["id"] = f'{prev_alpha.get("id")}{cur_tag}'
    #
    #                 else:
    #                     alpha_ol.append(p_tag)
    #                     alpha_cur_tag = p_tag
    #                     p_tag["id"] = f'{prev_num_id}{cur_tag}'
    #             p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)', '', current_tag_text)
    #
    #         # 1.
    #         if re.search(rf'^{num_count}\.', current_tag_text) and p_tag.get('class') == [self.class_regex['ol']]:
    #             p_tag.name = "li"
    #             num_tag = p_tag
    #
    #             if re.search(r'^1\.', current_tag_text):
    #                 num_ol1 = self.soup.new_tag("ol")
    #                 p_tag.wrap(num_ol1)
    #                 prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
    #                 if prev_head_id in ol_list:
    #                     ol_count += 1
    #                 else:
    #                     ol_count = 1
    #                 ol_list.append(prev_head_id)
    #             else:
    #                 num_ol1.append(p_tag)
    #             prev_num_id1 = f'{prev_head_id}ol{ol_count}{num_count}'
    #             p_tag["id"] = f'{prev_head_id}ol{ol_count}{num_count}'
    #             p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
    #             num_count += 1
    #
    #         if re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name != "li" and p_tag.get('class') == [
    #             self.class_regex['ol']]:
    #             p_tag.name = "li"
    #             num_tag = p_tag
    #
    #             if re.search(r'^1\.', current_tag_text):
    #                 num_ol1 = self.soup.new_tag("ol")
    #                 p_tag.wrap(num_ol1)
    #                 prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
    #                 if prev_head_id in ol_list:
    #                     ol_count += 1
    #                 else:
    #                     ol_count = 1
    #                 ol_list.append(prev_head_id)
    #             else:
    #
    #                 num_ol1.append(p_tag)
    #             prev_num_id1 = f'{prev_head_id}ol{ol_count}{num_count}'
    #             p_tag["id"] = f'{prev_head_id}ol{ol_count}{num_count}'
    #             p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
    #             num_count += 1
    #
    #         if re.search(rf'^\d+\w+\.', current_tag_text) and p_tag.name != "li" and p_tag.get("class") != ["nav_head"]:
    #             if int(re.search(rf'^\d+', current_tag_text).group()) == num_count - 1:
    #                 num_ol1.append(p_tag)
    #
    #         # aa
    #         elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
    #             curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
    #             p_tag.name = "li"
    #             alpha_cur_tag = p_tag
    #             alpha_ol.append(p_tag)
    #             prev_alpha_id = f'{prev_num_id}{curr_id}'
    #             p_tag["id"] = f'{prev_num_id}{curr_id}'
    #             roman_count = 1
    #             p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)
    #
    #         if re.search(r'^Source|^Cross references:|^OFFICIAL COMMENT', current_tag_text) or p_tag.name in ['h3',
    #                                                                                                           'h4']:
    #             ol_head = 1
    #             num_count = 1
    #             num_cur_tag = None
    #             new_alpha = None
    #             main_sec_alpha = 'a'
    #
    #     print('ol tags added')

    def convert_paragraph_to_alphabetical_ol_tags2(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        sec_alpha = 'a'
        cap_alpha = 'A'
        inr_cap_alpha = 'A'
        ol_head = 1
        num_count = 1
        roman_count = 1
        ol_count = 1
        cap_roman = 'I'
        small_roman = 'i'

        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_ol = self.soup.new_tag("ol", type="i")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")

        ol_list = []
        new_num = None
        innr_roman_ol = None
        cap_alpha_cur_tag = None
        new_alpha = None
        sec_alpha_cur_tag = None
        num_tag = None
        inr_cap_alpha_cur_tag = None
        alpha_cur_tag = None

        for p_tag in self.soup.find_all():
            if p_tag.b:
                p_tag.b.unwrap()
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^\({ol_head}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha = 'A'
                num_cur_tag = p_tag
                prev_alpha = p_tag
                if re.search(r'^\(1\)', current_tag_text):
                    if new_alpha:
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)
                        new_alpha.append(num_ol)
                        new_num = p_tag
                    else:
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)
                        main_sec_alpha = "a"
                    if p_tag.find_previous(["h4", "h3"]):
                        prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
                    else:
                        prev_head_id = p_tag.find_previous(["h2", "h1"]).get("id")

                    if prev_head_id in ol_list:
                        ol_count += 1
                    else:
                        ol_count = 1
                    ol_list.append(prev_head_id)
                else:
                    num_ol.append(p_tag)
                    if new_num:
                        new_num = p_tag
                    if new_alpha == None:
                        main_sec_alpha = "a"

                prev_num_id = f'{prev_head_id}ol{ol_count}{ol_head}'
                p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
                p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
                ol_head += 1

                if re.search(r'^\(\d+\)\s\(a\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s\(a\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>a)\)', current_tag_text)
                    prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"

                    if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        li_tag["class"] = self.class_regex['ol']
                        rom_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
                                            current_tag_text)
                        prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                        inner_li_tag[
                            "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                        roman_ol.append(inner_li_tag)
                        alpha_cur_tag.string = ""
                        alpha_cur_tag.insert(0, roman_ol)
                        cap_roman = "II"

                        if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '',
                                                         current_tag_text)
                            # inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.class_regex['ol']
                            cur_tag = re.search(
                                r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                current_tag_text)
                            prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'
                            cap_alpha_ol.append(inner_li_tag)
                            rom_cur_tag.string = ""
                            rom_cur_tag.append(cap_alpha_ol)
                            cap_alpha = "B"

                if re.search(r'^\(\d+\)\s\(i\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s\(i\)', '', current_tag_text)
                    rom_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>i)\)', current_tag_text)
                    prev_num_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    innr_roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(innr_roman_ol)

            # 1.5
            elif re.search(r'^\(\d+\.\d+\)', current_tag_text):
                # p_tag.name = "li"
                cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)', current_tag_text).group("cid")
                p_tag["id"] = f'{prev_num_id}-{cur_tag}'
                prev_num_tag = p_tag.find_previous(
                    lambda tag: tag.name in ['li'] and re.search(r'^\w+', tag.text.strip()))
                if not re.search(r'^\(\d+\.\d+\)', p_tag.find_next().text.strip()):
                    prev_num_id = f'{prev_num_id}-{cur_tag}'
                    p_tag.name = "div"
                p_tag.find_previous("li").append(p_tag)
                main_sec_alpha = "a"
                num_cur_tag = p_tag

                if re.search(r'^\(\d+\.\d+\)\s\(\w\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)\s\((?P<pid>\w)\)', current_tag_text)
                    prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"
                    cap_roman = "I"

                    if re.search(r'^\(\d+\.\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.append(current_tag_text)
                        li_tag["class"] = self.class_regex['ol']
                        rom_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<id1>\d+\.\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
                                            current_tag_text)
                        prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                        inner_li_tag[
                            "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                        roman_ol.append(inner_li_tag)
                        p_tag.insert(1, roman_ol)
                        roman_ol.find_previous().string.replace_with(roman_ol)
                        cap_roman = "II"

            # a
            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                roman_count = 1
                cap_roman = "I"

                if re.search(r'^\(a\)', current_tag_text):
                    if num_cur_tag == None:
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        prev_tag = p_tag.find_previous_sibling()
                        p_tag.wrap(alpha_ol)
                        prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
                        ol_head = 1
                        new_alpha = p_tag
                    else:
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        prev_tag = p_tag.find_previous_sibling()

                        p_tag.wrap(alpha_ol)
                        num_cur_tag.append(alpha_ol)
                        prev_alpha_id = f'{prev_num_id}{main_sec_alpha}'
                        p_tag["id"] = f'{prev_num_id}{main_sec_alpha}'

                else:
                    alpha_ol.append(p_tag)
                    if new_alpha == None:
                        prev_alpha_id = f'{prev_num_id}{main_sec_alpha}'
                        p_tag["id"] = f'{prev_num_id}{main_sec_alpha}'
                    else:
                        new_alpha = p_tag
                        ol_head = 1
                        prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{main_sec_alpha}'

                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(r'^\(\w\)\s*\([I,V,X]+\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    li_tag["class"] = self.class_regex['ol']
                    rom_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                    prev_rom_id = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    li_tag["id"] = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    cap_roman = "II"

                    if re.search(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        li_tag["class"] = self.class_regex['ol']
                        cur_tag = re.search(
                            r'^\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                            current_tag_text)
                        prev_id = rom_cur_tag.get("id")
                        inner_li_tag[
                            "id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("id3")}'
                        cap_alpha_ol.append(inner_li_tag)
                        p_tag.insert(1, cap_alpha_ol)
                        rom_cur_tag.string = ""
                        rom_cur_tag.string.replace_with(cap_alpha_ol)
                        cap_alpha = "B"

                if re.search(r'^\(\w\)\s*\(\d+\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\(\d+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    li_tag["class"] = self.class_regex['ol']
                    new_num = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>\d+)\)', current_tag_text)
                    prev_rom_id = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    ol_head = 2
                    cap_alpha = "A"
                    new_num = None

                if re.search(r'^\(\w\)\s*\([ivx]+\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s*\([ivx]+\)', '', current_tag_text)

                    inner_li_tag["class"] = self.class_regex['ol']
                    prev_alpha = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                    prev_rom_id = f'{alpha_cur_tag.get("id")}'
                    inner_li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                    innr_roman_ol.append(inner_li_tag)
                    p_tag.contents = []
                    p_tag.append(innr_roman_ol)

            # a.5
            elif re.search(r'^\(\w+\.\d+\)', current_tag_text):
                p_tag.name = "li"
                roman_count = 1
                cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)', current_tag_text).group("cid")
                p_tag.string = re.sub(r'^\(\w+\.\d+\)', '', current_tag_text)
                p_tag["id"] = f'{prev_alpha_id}-{cur_tag}'
                prev_alpha_id = f'{prev_alpha_id}'
                prev_alpha_tag = p_tag.find_previous(
                    lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)', tag.text.strip()))

                if not re.search(r'^\(\w+\.\d+\)', p_tag.find_next().text.strip()) and re.search(r'^\([A-Z]\)',
                                                                                                 p_tag.find_next().text.strip()):
                    prev_alpha_id = f'{prev_alpha_id}-{cur_tag}'
                    # p_tag.name = "div"

                alpha_ol.append(p_tag)
                # p_tag.find_previous("li").append(p_tag)
                alpha_cur_tag = p_tag

                if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\.\d+\)\s*\([I,V,X]+\)', '', current_tag_text)
                    # li_tag.append(current_tag_text)
                    li_tag["class"] = self.class_regex['ol']
                    rom_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                    prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    # p_tag.insert_after(roman_ol)
                    p_tag.append(roman_ol)
                    cap_roman = "II"

                    if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.append(current_tag_text)
                        inner_li_tag["class"] = self.class_regex['ol']
                        cur_tag = re.search(
                            r'^\((?P<cid>\w\.\d+)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                            current_tag_text)
                        prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                        inner_li_tag[
                            "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'

                        cap_alpha_ol.append(inner_li_tag)
                        p_tag.insert(1, cap_alpha_ol)
                        cap_alpha_ol.find_previous().string.replace_with(cap_alpha_ol)
                        cap_alpha = "B"

            # I
            elif re.search(rf'^\({cap_roman}\)', current_tag_text):
                p_tag.name = "li"
                rom_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(I\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(roman_ol)
                    if alpha_cur_tag:
                        alpha_cur_tag.append(roman_ol)
                        p_tag["id"] = f'{prev_alpha_id}I'
                    else:
                        p_tag["id"] = f'{p_tag.find_previous("li")}I'
                        p_tag.find_previous("li").append(roman_ol)
                else:
                    roman_ol.append(p_tag)
                    prev_rom_id = f'{prev_alpha_id}{cap_roman}'
                    p_tag["id"] = f'{prev_alpha_id}{cap_roman}'

                p_tag.string = re.sub(rf'^\({cap_roman}\)', '', current_tag_text)
                cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([I,V,X]+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[I,V,X]+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
                    prev_id = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    if not re.search(r'^\(I\)', current_tag_text):
                        prev_tag_id = p_tag.find_previous_sibling().get("id")
                        cur_tag_id = re.search(r'^[^IVX]+', prev_tag_id).group()
                        prev_rom_id = f'{cur_tag_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{cur_tag_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    roman_count += 1
                    cap_alpha = "B"

            #  A
            elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                cap_alpha1 = cap_alpha

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    prev_id = p_tag.find_previous("li").get("id")
                    p_tag.find_previous("li").append(cap_alpha_ol)

                else:
                    cap_alpha_ol.append(p_tag)

                if cap_alpha in ['I', 'V', 'X', 'L']:
                    p_tag["id"] = f'{prev_id}{ord(cap_alpha)}'
                else:
                    p_tag["id"] = f'{prev_id}{cap_alpha}'

                # p_tag["id"] = f'{prev_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                cap_alpha = chr(ord(cap_alpha) + 1)



            # i
            elif re.search(r'^\([ivx]+\)', current_tag_text):
                p_tag.name = "li"
                rom_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(i\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(innr_roman_ol)
                    p_tag.find_previous("li").append(innr_roman_ol)
                    prev_alpha = p_tag.find_previous("li")
                    p_tag["id"] = f'{prev_alpha.get("id")}i'
                else:
                    cur_tag = re.search(r'^\((?P<cid>[ivx]+)\)', current_tag_text).group("cid")
                    if innr_roman_ol:
                        innr_roman_ol.append(p_tag)
                        p_tag["id"] = f'{prev_alpha.get("id")}{cur_tag}'

                    else:
                        alpha_ol.append(p_tag)
                        alpha_cur_tag = p_tag
                        p_tag["id"] = f'{prev_num_id}{cur_tag}'
                p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)', '', current_tag_text)



            elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag


                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_tag:
                        num_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_tag.get("id")

                    else:
                        sec_alpha_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count}{sec_alpha}'
                        num_count = 1

                else:
                    sec_alpha_ol.append(p_tag)
                    if not num_tag:
                        num_count = 1

                p_tag["id"] = f'{sec_alpha_id}{sec_alpha}'
                p_tag.string = re.sub(rf'^{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

            # 1.
            # if re.search(rf'^{num_count}\.', current_tag_text) and p_tag.get('class') == [self.class_regex['ol']]:
            #     p_tag.name = "li"
            #     num_tag = p_tag
            #
            #     if re.search(r'^1\.', current_tag_text):
            #         num_ol1 = self.soup.new_tag("ol")
            #         p_tag.wrap(num_ol1)
            #         prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
            #         if prev_head_id in ol_list:
            #             ol_count += 1
            #         else:
            #             ol_count = 1
            #         ol_list.append(prev_head_id)
            #     else:
            #         num_ol1.append(p_tag)
            #     prev_num_id1 = f'{prev_head_id}ol{ol_count}{num_count}'
            #     p_tag["id"] = f'{prev_head_id}ol{ol_count}{num_count}'
            #     p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
            #     num_count += 1


            elif re.search(rf'^{inr_cap_alpha}\.', current_tag_text) and p_tag.name=="p":
                p_tag.name = "li"
                inr_cap_alpha_cur_tag = p_tag
                num_count = 1

                if re.search(r'^A\.', current_tag_text):
                    inr_cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inr_cap_alpha_ol)
                    prev_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count}'

                else:
                    inr_cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_id}{inr_cap_alpha}'
                p_tag.string = re.sub(rf'^^{inr_cap_alpha}\.', '', current_tag_text)
                inr_cap_alpha = chr(ord(inr_cap_alpha) + 1)


            elif re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name != "li" and p_tag.get('class') == [
                self.class_regex['ol']]:
                p_tag.name = "li"
                num_tag = p_tag

                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(num_ol1)
                        prev_head_id = sec_alpha_cur_tag.get('id')
                        sec_alpha = 'a'
                    elif inr_cap_alpha_cur_tag:
                        inr_cap_alpha_cur_tag.append(num_ol1)
                        prev_head_id = inr_cap_alpha_cur_tag.get('id')
                    elif alpha_cur_tag:
                        alpha_cur_tag.append(num_ol1)
                        prev_head_id = alpha_cur_tag.get('id')
                    else:
                        prev_head_id = p_tag.find_previous(["h4", "h3"]).get("id")
                        if prev_head_id in ol_list:
                            ol_count += 1
                        else:
                            ol_count = 1
                        ol_list.append(prev_head_id)
                else:

                    num_ol1.append(p_tag)

                    if sec_alpha_cur_tag:
                        sec_alpha = 'a'

                prev_num_id1 = f'{prev_head_id}ol{ol_count}{num_count}'
                p_tag["id"] = f'{prev_head_id}ol{ol_count}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1

                if re.search(r'^\d+\.\s*?a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\d+\.\s*?a\.', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^(?P<cid>\d+)\.\s*?a\.', current_tag_text)
                    prev_id = f'{num_tag.get("id")}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{num_tag.get("id")}{cur_tag.group("cid")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol)

                    sec_alpha = "b"





            if re.search(rf'^\d+\w+\.', current_tag_text) and p_tag.name != "li" and p_tag.get("class") != ["nav_head"]:
                if int(re.search(rf'^\d+', current_tag_text).group()) == num_count - 1:
                    num_ol1.append(p_tag)

            # aa
            elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
                curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                alpha_ol.append(p_tag)
                prev_alpha_id = f'{prev_num_id}{curr_id}'
                p_tag["id"] = f'{prev_num_id}{curr_id}'
                roman_count = 1
                p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)

            if re.search(r'^Source|^Cross references:|^OFFICIAL COMMENT|^(ARTICLE|Article) [IVX]+',
                         current_tag_text, re.I) or p_tag.name in ['h3',
                                                                   'h4']:
                ol_head = 1
                num_count = 1
                num_cur_tag = None
                new_alpha = None
                num_tag = None
                alpha_cur_tag = None
                sec_alpha_cur_tag = None
                inr_cap_alpha_cur_tag = None
                main_sec_alpha = 'a'
                sec_alpha = 'a'

                if re.search(r'^(ARTICLE|Article) [IVX]+', current_tag_text,re.I):
                    ol_count += 1

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
                if list_item.find_previous().name == "li" and not list_item.parent.name == "ul":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if ul_tag.find_previous().find_previous().name == "h1":
                        ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.wrap(self.soup.new_tag("nav"))

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
        nav_head = []
        nav_count = 1
        for list_item in self.soup.find_all(class_=self.class_regex['ul']):
            if re.search('constitution', self.html_file_name):
                if re.match(r'^(ARTICLE|Article)\s*(?P<ar>[A-Z]+)', list_item.text.strip()):

                    chap_num = re.search(r'^(ARTICLE|Article)\s*(?P<ar>[A-Z]+)', list_item.text.strip()).group(
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
                elif re.search(r'^[0-9a-z]+\.', list_item.text.strip()):
                    prev_id = list_item.find_previous("h2").get("id")

                    chap_num = re.search(r'^(?P<ar>[0-9a-z]+)\.', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-s"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)
                else:
                    if re.search(r'^Section|^SECTION ', list_item.text.strip()):
                        prev_id = list_item.find_previous("h2").get("id")
                        chap_num = re.search(r'^(Section|SECTION)\s?(?P<ar>[0-9a-z]+)\.', list_item.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-s"
                        self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                    elif not re.search(r'^Section|^Article|^SECTION', list_item.text.strip()):
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', list_item.text.strip()).lower()
                        sub_tag = re.search(r'^[a-zA-Z]{2}', list_item.text.strip()).group()
                        sub_tag = f'-{sub_tag.lower()}-'
                        self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


            # title
            else:
                if re.match(r'^Art\.\s*\d+\.|^Article\s?\d+\.', list_item.text.strip()):
                    chap_num = re.search(r'^(Art|Article)\.?\s?(?P<id>\d+(\.\d+)*)\.',
                                         list_item.text.strip()).group(
                        "id").zfill(2)
                    if list_item.find_previous("p", class_="nav_head"):
                        sub_tag = "-ar"
                        prev_id1 = re.sub(r'[^0-9A-Za-z]+', '',
                                          list_item.find_previous("p", class_="nav_head").text.strip()).lower()
                        prev_id = f't{self.title_id}-{prev_id1}'
                    elif list_item.find_previous("h2", class_="gnrlh2"):
                        sub_tag = "-ar"
                        prev_id1 = re.sub(r'\s+', '',
                                          list_item.find_previous("h2", class_="gnrlh2").text.strip()).lower()
                        prev_id = f't{self.title_id}-{prev_id1}'

                    else:
                        sub_tag = "ar"
                        prev_id = None
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                elif re.match(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.*(\.\d+)*', list_item.text.strip()):
                    if re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.\d+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+\.\d+)',
                                             list_item.text.strip()).group(
                            "sid").zfill(2)
                    else:
                        chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+)',
                                             list_item.text.strip()).group(
                            "sid").zfill(2)

                    prev_id = list_item.find_previous("h2").get("id")
                    sub_tag = "-s"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                else:
                    if re.search(r'^Part\s*(?P<id>\d+)', list_item.text.strip()):
                        prev_id1 = list_item.find_previous("h2", class_="articleh2").get("id")
                        prev_id2 = re.search(r'^Part\s*(?P<id>\d+)', list_item.text.strip()).group("id").zfill(2)
                        prev_id = f"{prev_id1}-p{prev_id2}"
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(list_item.text)
                        nav_link["href"] = f"#{prev_id}"
                        nav_list.append(nav_link)
                        list_item.contents = nav_list
                    elif re.search(r'^Subpart\s*(?P<id>\d+)', list_item.text.strip()):
                        prev_id1 = list_item.find_previous("h2", class_="parth2").get("id")
                        prev_id2 = re.search(r'^Subpart\s*(?P<id>\d+)', list_item.text.strip()).group("id").zfill(2)
                        prev_id = f"{prev_id1}-s{prev_id2}"
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(list_item.text)
                        nav_link["href"] = f"#{prev_id}"
                        nav_list.append(nav_link)
                        list_item.contents = nav_list
                    # else:
                    #     print(list_item)
                    #     prev_id = re.sub(r'[\s]+', '', list_item.text.strip()).lower()
                    #     nav_list = []
                    #     nav_link = self.soup.new_tag('a')
                    #     nav_link.append(list_item.text)
                    #     nav_link["href"] = f"#t{self.title_id}-{prev_id}"
                    #     nav_list.append(nav_link)
                    #     list_item.contents = nav_list

        ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for li_tag in self.soup.find_all("li"):
            if not li_tag.get('class'):
                if re.search('constitution', self.html_file_name):
                    if re.search(r'^[I,V,X]+\.', li_tag.text.strip()):
                        if re.search(r'^I\.', li_tag.text.strip()):
                            if not re.search(r'^H\.', li_tag.find_previous().text.strip()):
                                prev_id = li_tag.find_previous("h4").get("id")
                                ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                if li_tag.find_previous().name == "ul":
                                    li_tag.find_previous().decompose()
                                li_tag.wrap(ul_analy_tag)
                            else:
                                innr_ul_analy_tag.append(li_tag)
                                prev_id = prev_id1
                        else:
                            ul_analy_tag.append(li_tag)
                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)', li_tag.text.strip()).group("ar")
                        sub_tag = "-"
                        prev_id1 = f'{prev_id}-{chap_num}'
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)


                    elif re.search(r'^[A-HJ-UW-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            innr_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(innr_ul_analy_tag)
                            prev_li.append(innr_ul_analy_tag)
                            chap_num = "A"
                        else:
                            innr_ul_analy_tag.append(li_tag)
                            chap_num = re.search(r'^(?P<id>[A-HJ-UW-Z])\.', li_tag.text.strip()).group("id")
                        sub_tag = "-"
                        prev_id2 = f'{prev_id1}-{chap_num}'
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id1, None)

                    elif re.search(r'^[1-9]\.', li_tag.text.strip()):
                        if re.search(r'^1\.', li_tag.text.strip()):
                            num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li_tag = li_tag.find_previous("li")
                            li_tag.wrap(num_ul_analy_tag)
                            prev_li_tag.append(num_ul_analy_tag)
                            chap_num = "1"

                        else:
                            chap_num = re.search(r'^(?P<id>[1-9])\.', li_tag.text.strip()).group("id")
                            num_ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id2, None)

                else:
                    if re.search(r'^[A-HJ-UWY-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(ul_analy_tag)
                            prev_li.append(ul_analy_tag)
                            if li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())):
                                prev_id1 = re.sub(r'^#', '', li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())).get("href"))
                            else:
                                prev_id1 = None
                            chap_num = "A"
                        else:
                            chap_num = re.search(r'^(?P<id>[A-HJ-UWY-Z])\.', li_tag.text.strip()).group("id")
                            ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        # print(li_tag)
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

                    if re.search(r'^[I,V,X]+\.', li_tag.text.strip()):
                        if re.search(r'^I\.', li_tag.text.strip()) and re.search(r'^H\.', li_tag.find_previous(
                                "li").text.strip()):
                            ul_analy_tag.append(li_tag)
                            prev_id3 = prev_id1

                        elif re.search(r'^I\.', li_tag.text.strip()):
                            prev_id3 = li_tag.find_previous("h4").get("id")

                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)', li_tag.text.strip()).group("ar")
                        prev_id = prev_id3
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)

    def create_and_wrap_with_div_tag(self):
        """
            - for each h2 in html
            - create new div and append h2 to that div
            - find next tag, if next tag is h3
                - create new div and append h3 to it
                - append that new div to h2 div
                - find next tag of h3, if next tag is h4
                    - create new div and append h4 to that div
                    - append that new div to h3 div
                    - find next tag, if next tag is h5
                        - create new div and append h5 to that div
                        - append that new div to h4 div
                    - if not h5 append that tag to h2 div and so on
                - if not h4 append that tag to h2 div and so on
            - if not h3 append that tag to h2 div and so on
        """
        self.soup = BeautifulSoup(self.soup.prettify(formatter=None), features='lxml')
        for header in self.soup.findAll('h2'):
            new_chap_div = self.soup.new_tag('div')
            sec_header = header.find_next_sibling()
            if not sec_header:
                print()
            header.wrap(new_chap_div)
            if sec_header:
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
                                            if not next_h5_child_tag or next_h5_child_tag.name in ['h3', 'h2', 'h4',
                                                                                                   'h5']:
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
                    if not sec_header:
                        print()

        print('wrapped div tags')

    def create_case_note_nav(self):
        if self.soup.find("p", class_=self.class_regex['ol']):
            for case_tag in self.soup.find_all("p", class_=self.class_regex['ol']):
                if re.search(r'^[IVX]+\.\s[A-Z]+', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[IVX]+)\.', case_tag.text.strip()).group("cid")
                    rom_id = f"{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_link["href"] = f"#{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list


                elif re.search(r'^[A-Z]\.', case_tag.text.strip()) and not re.search(r'(ARTICLE|Article) [IVX]+',
                                                                                     case_tag.find_previous(
                                                                                         "h3").text.strip()) \
                        and case_tag.name == "li":
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid")

                    alpha_id = f"{rom_id}-{case_id}"
                    nav_link["href"] = f"#{rom_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

                elif re.search(r'^[0-9]+\.[a-zA-Z]+', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[0-9]+)\.', case_tag.text.strip()).group("cid")

                    digit_id = f"{alpha_id}-{case_id}"
                    nav_link["href"] = f"#{alpha_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

    def create_case_note_ul(self):
        for case_tag in self.soup.find_all(class_=self.class_regex['ol']):
            if case_tag.a:
                case_tag.name = "li"
                if re.search(r'^[IVX]+\.\s[A-Z]+', case_tag.a.text.strip()):
                    rom_tag = case_tag
                    if re.search(r'^I\.', case_tag.a.text.strip()):
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                    else:
                        rom_ul.append(case_tag)

                elif re.search(r'^[A-Z]\.\s[A-Z][a-z]+', case_tag.a.text.strip()):
                    alpha_tag = case_tag
                    if re.search(r'^A\.', case_tag.a.text.strip()):
                        alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(alpha_ul)
                        rom_tag.append(alpha_ul)
                    else:
                        alpha_ul.append(case_tag)

                elif re.search(r'^[0-9]+\.', case_tag.a.text.strip()):
                    digit_tag = case_tag
                    if re.search(r'^1\.', case_tag.a.text.strip()):
                        digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(digit_ul)
                        alpha_tag.append(digit_ul)
                    else:
                        digit_ul.append(case_tag)

    def add_citation(self):
        class_dict = {'co_code': 'Colo\.\s*\d+',
                      'cocode': 'Colo.+P\.\d\w\s\d+',
                      'co_law': 'Colo\.\s*Law\.\s*\d+|L\.\s*\d+,\s*p\.\s*\d+',
                      'denv_law': '\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+',
                      'COA': '\d{4}\s*COA\s*\d+'}

        cite_p_tags = []
        for tag in self.soup.findAll(lambda tag: re.search(
                r"(\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))(\s*\([a-z]\))(\([I,V,X]+\))|"
                r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))(\s*\([a-z]\))|"
                r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))|"
                r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)", tag.get_text()) and tag.name == 'p'
                                                 and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            text = str(tag)
            for match in set(x[0] for x in re.findall(
                    r"(\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))(\s*\([a-z]\))(\([I,V,X]+\))|"
                    r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))(\s*\([a-z]\))|"
                    r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))|"
                    r"\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)",
                    tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<p>|^<li\sclass="\w\d+"\sid=".+">|</li>$', '',
                                     text.strip(), re.DOTALL)
                if tag.get("class") == [self.class_regex["ul"]]:

                    continue
                else:
                    # tag.clear()
                    if re.search(
                            r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z](\.\d+)*\))(\([I,V,X]+\))',
                            match.strip()):
                        tag.clear()
                        chap_num = re.search(
                            r'§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<part>(?P<part_id>\d)(\d+)*)(\.\d+)*)\s*\((?P<ol_id>\d+(\.\d+)*)\)\s*\((?P<ol_id2>[a-z](\.\d+)*)\)\((?P<ol_id3>[I,V,X]+)\)',
                            match.strip())
                        t_id = chap_num.group("title_id").zfill(2)
                        c_id = chap_num.group("chap_id")
                        s_id = chap_num.group("sec_id").zfill(2)
                        if len(chap_num.group("part")) > 3:
                            p_id1 = chap_num.group("part")
                            p_id = p_id1[:2]
                        else:
                            p_id = chap_num.group("part_id").zfill(2)
                        ol_id = chap_num.group("ol_id")
                        ol_id2 = chap_num.group("ol_id2")
                        ol_id3 = chap_num.group("ol_id3")

                        if t_id != '25.5':
                            if int(t_id) < 45:
                                tag_id_new = self.create_citation(t_id, c_id, s_id, p_id)
                                tag_id = f'{tag_id_new}ol1{ol_id}{ol_id2}{ol_id3}'
                                if self.title_id == t_id:
                                    target = "_self"
                                else:
                                    target = "_blank"

                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                              inside_text, re.I)
                            else:
                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f'<cite class="occo">{match}</cite>',
                                              inside_text, re.I)
                        else:
                            tag_id = self.create_citation(t_id, c_id, s_id, p_id)
                            if self.title_id == t_id:
                                target = "_self"
                            else:
                                target = "_blank"
                            text = re.sub(fr'\s*{re.escape(match)}',
                                          f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                          inside_text, re.I)


                    elif re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+\))*(\s*\([a-z](\.\d+)*\))',
                                   match.strip()):
                        tag.clear()
                        chap_num = re.search(
                            r'§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<part>(?P<part_id>\d)(\d+)*)(\.\d+)*)\s*\((?P<ol_id>\d+(\.\d+)*)\)\s*\((?P<ol_id2>[a-z](\.\d+)*)\)',
                            match.strip())
                        t_id = chap_num.group("title_id").zfill(2)
                        c_id = chap_num.group("chap_id")
                        s_id = chap_num.group("sec_id").zfill(2)
                        if len(chap_num.group("part")) > 3:
                            p_id1 = chap_num.group("part")
                            p_id = p_id1[:2]
                        else:
                            p_id = chap_num.group("part_id").zfill(2)
                        ol_id = chap_num.group("ol_id")
                        ol_id2 = chap_num.group("ol_id2")

                        if t_id != '25.5' and t_id != '26.5':
                            if int(t_id) < 45:
                                tag_id_new = self.create_citation(t_id, c_id, s_id, p_id)
                                tag_id = f'{tag_id_new}ol1{ol_id}{ol_id2}'
                                if self.title_id == t_id:
                                    target = "_self"
                                else:
                                    target = "_blank"

                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                              inside_text, re.I)
                            else:
                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f'<cite class="occo">{match}</cite>',
                                              inside_text, re.I)

                        else:
                            tag_id = self.create_citation(t_id, c_id, s_id, p_id)
                            if self.title_id == t_id:
                                target = "_self"
                            else:
                                target = "_blank"
                            text = re.sub(fr'\s*{re.escape(match)}',
                                          f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                          inside_text, re.I)

                    elif re.search(r'§*\s*\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*(\s*\(\d+(\.\d+)*\))', match.strip()):
                        tag.clear()
                        chap_num = re.search(
                            r'§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<part>(?P<part_id>\d)(\d+)*)(\.\d+)*)\s*\((?P<ol_id>\d+(\.\d+)*)\)',
                            match.strip())
                        t_id = chap_num.group("title_id").zfill(2)
                        c_id = chap_num.group("chap_id")
                        s_id = chap_num.group("sec_id").zfill(2)
                        if len(chap_num.group("part")) > 3:
                            p_id1 = chap_num.group("part")
                            p_id = p_id1[:2]
                        else:
                            p_id = chap_num.group("part_id").zfill(2)
                        ol_id = chap_num.group("ol_id")
                        if t_id != '25.5':
                            if int(t_id) < 45:
                                tag_id_new = self.create_citation(t_id, c_id, s_id, p_id)
                                tag_id = f'{tag_id_new}ol1{ol_id}'
                                if self.title_id == t_id:
                                    target = "_self"
                                else:
                                    target = "_blank"

                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                              inside_text, re.I)
                            else:
                                if tag.cite:
                                    tag.cite.unwrap()
                                    tag.a.unwrap()

                                text = re.sub(fr'\s*{re.escape(match)}', f'<cite class="occo">{match}</cite>',
                                              inside_text, re.I)
                        else:
                            tag_id = self.create_citation(t_id, c_id, s_id, p_id)
                            if self.title_id == t_id:
                                target = "_self"
                            else:
                                target = "_blank"

                                if tag.cite:
                                    tag.cite.unwrap()
                                    tag.a.unwrap()

                            text = re.sub(fr'\s*{re.escape(match)}',
                                          f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                          inside_text, re.I)

                    elif re.search(r'^§*?\s*?\d+(\.\d+)*?-\d+(\.\d+)*?-\d+(\.\d+)*?', match.strip()):
                        tag.clear()
                        chap_num = re.search(
                            r'§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+(\.\d+)*)-(?P<part>(?P<part_id>\d)(\d+)*)(\.\d+)*)',
                            match.strip())
                        t_id = chap_num.group("title_id").zfill(2)
                        c_id = chap_num.group("chap_id")
                        s_id = chap_num.group("sec_id").zfill(2)
                        if len(chap_num.group("part")) > 3:
                            p_id1 = chap_num.group("part")
                            p_id = p_id1[:2]
                        else:
                            p_id = chap_num.group("part_id").zfill(2)

                        if t_id != '25.5' and t_id != '26.5':
                            if int(t_id) < 45:
                                tag_id = self.create_citation(t_id, c_id, s_id, p_id)
                                if self.title_id == t_id:
                                    target = "_self"
                                else:
                                    target = "_blank"
                                text = re.sub(fr'\s*{re.escape(match)}',
                                              f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                              inside_text, re.I)
                            else:
                                text = re.sub(fr'\s{re.escape(match)}', f'<cite class="occo">{match}</cite>',
                                              inside_text, re.I)

                        else:
                            tag_id = self.create_citation(t_id, c_id, s_id, p_id)
                            if self.title_id == t_id:
                                target = "_self"
                            else:
                                target = "_blank"
                            text = re.sub(fr'\s*{re.escape(match)}',
                                          f' <cite class="occo"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                          inside_text, re.I)

                    tag.append(BeautifulSoup(text))
                    tag.html.unwrap()
                    tag.body.unwrap()
                    if tag.p:
                        tag.p.unwrap()

        for tag in self.soup.find_all("p"):
            if re.search(r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                         r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                         r"\d{4}\s*COA\s*\d+|"
                         r"L\.\s*\d+,\s*p\.\s*\d+|"
                         r"Colo.+P\.\d\w\s\d+", tag.text.strip()):

                text = str(tag)
                for key, value in class_dict.items():
                    for match in [x for x in re.findall(value, tag.get_text(), re.I)]:
                        inside_text = re.sub(
                            r'<p\sclass="\w\d+">|</p>|^<li\sclass="\w\d+\sid=".+">|</li>$|<li id=".*?">',
                            '', text, re.DOTALL)
                        tag.clear()
                        text = re.sub(fr'\s{re.escape(match)}', f'<cite class="{key}">{match}</cite>', inside_text,
                                      re.I)
                        tag.append(BeautifulSoup(text))
                        tag.html.unwrap()
                        tag.body.unwrap()
                        if tag.p:
                            tag.p.unwrap()

        for remove_tag in self.soup.findAll(["html", "body", "cite"]):
            if remove_tag.name == "html":
                if not remove_tag.get("lang"):
                    remove_tag.unwrap()
            if remove_tag.name == "cite":
                if remove_tag.cite:
                    remove_tag.cite.decompose()
            if remove_tag.name == "body" and not remove_tag.find_previous().name == "meta":
                remove_tag.unwrap()

        print("cite is created")

    def add_watermark_and_remove_class_name(self):
        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p']:
                del tag["class"]

        for tag in self.soup.findAll():
            # if tag.name and re.search(r'^h\d', tag.name, re.I):
            #     for br_tag in tag.findAll('br'):
            #         new_span = self.soup.new_tag('span', Class='headbreak')
            #         br_tag.replace_with(new_span)

            if len(tag.contents) == 0:
                if tag.name == 'meta':
                    if tag.attrs.get('http-equiv') == 'Content-Style-Type':
                        tag.decompose()
                        continue
                    self.meta_tags.append(tag)

        if re.search('constitution', self.html_file_name):
            watermark_tag = self.soup.new_tag('p', **{"class": "transformation"})
            watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                              datetime.now().date())
            title_tag = self.soup.find("h1")
            if title_tag:
                title_tag.insert_before(watermark_tag)
            for meta in self.soup.findAll('meta'):
                if meta.get('http-equiv') == "Content-Style-Type":
                    meta.decompose()

        else:

            watermark_tag = self.soup.new_tag('p', **{"class": "transformation"})
            watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                              datetime.now().date())
            title_tag = self.soup.find("nav")
            if title_tag:
                title_tag.insert(0, watermark_tag)
            for meta in self.soup.findAll('meta'):
                if meta.get('http-equiv') == "Content-Style-Type":
                    meta.decompose()

    def create_main_tag(self):
        """
                    - wrap all contents inside main tag(Except chapter index)
                """
        if re.search('constitution', self.html_file_name):
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find("h2")
            for main_tag in self.soup.find_all():
                if main_tag.find_next("h2") == first_chapter_header or main_tag.name == "b":
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    section_nav_tag.append(main_tag)
                if main_tag.name == "span":
                    main_tag.find_previous().append(main_tag)
        else:
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find("h2")
            for main_tag in self.soup.findAll():
                if main_tag.find_next("h2") == first_chapter_header:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    if main_tag.name == "span" and not main_tag.get("class") == "gnrlbreak":
                        continue
                    elif main_tag.name == "b":
                        continue
                    else:
                        section_nav_tag.append(main_tag)

        print("main tag is created")

    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))

        for tag in self.meta_tags:

            cleansed_tag = re.sub(r'/>', ' />', str(tag))
            soup_str = re.sub(rf'{tag}', rf'{cleansed_tag}', soup_str, re.I)

        print("validating")

        with open(f"../../cic-code-co-1/transforms/co/occo/r{self.release_number}/{self.html_file_name}",
                  "w") as file:
            file.write(soup_str.replace('&', '&amp;'))

    # add css file
    # def css_file(self):
    #     head = self.soup.find("head")
    #     style = self.soup.head.find("style")
    #     style.decompose()
    #     css_link = self.soup.new_tag("link")
    #     css_link.attrs[
    #         "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
    #     css_link.attrs["rel"] = "stylesheet"
    #     css_link.attrs["type"] = "text/css"
    #     head.append(css_link)

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
        # self.css_file()

        if re.search('constitution', self.html_file_name):
            self.class_regex = {
                'title': '^Declaration of Independence|^Constitution of the State of Colorado|^COLORADO COURT RULES',
                'ul': '^Preamble', 'head2': '^PREAMBLE|^Preamble',
                'sec_head': r'^Section\s*[0-9a-z]+\.',
                'junk': '^Statute text', 'ol': r'^§',
                'head4': '^ANNOTATIONS|^ANNOTATION', 'art_head': '^ARTICLE',
                'amd': '^AMENDMENTS', 'Analysis': '^I\.'}

            self.get_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_and_wrap_with_div_tag()
            self.add_citation()
            self.convert_paragraph_to_alphabetical_ol_tags2()
            self.add_watermark_and_remove_class_name()

        else:
            self.get_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_case_note_nav()
            self.create_case_note_ul()
            self.create_and_wrap_with_div_tag()
            self.convert_paragraph_to_alphabetical_ol_tags2()
            self.add_citation()
            self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)
