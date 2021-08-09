"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the start_parse method is called by parser base
    - this method based on the file type(constitution files or title files) decides which methods to run
"""
from bs4 import BeautifulSoup, Doctype, element
import re
from datetime import datetime
from parser_base import ParserBase


class idParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.tag_type_dict = {'head1': r'^(Title|TITLE)\s*\d', 'ul':r'^Idaho Code Title \d','head3': r'^§?\s?\d+-\d+\.|^§\s?\d+-\d+-\d+\.',
                              'head4': '^STATUTORY NOTES',
                             'junk': 'Title \d', 'normalp': '^Editor\'s note',
                              'article': r'^Article \d$|^Part \d$'}



        self.watermark_text = """Release {0} of the Official Code of Idaho Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on {2}. 
        This document is not subject to copyright and is in the public domain.
        """


        self.meta_tags = []
        self.tag_to_unwrap = []
        self.headers_class_dict = {'JUDICIAL DECISIONS': 'jdecisions',
                                   'OPINIONS OF THE ATTORNEY GENERAL': 'opinionofag',
                                   'RESEARCH REFERENCES': 'rreferences'}
        self.start_parse()

    def create_page_soup(self):
        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """
        with open(f'../transforms/id/ocid/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
        for key, value in self.tag_type_dict.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.tag_type_dict.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.tag_type_dict.values())
            if tag_class:
                self.tag_type_dict[key] = tag_class.get('class')[0]

        print(self.tag_type_dict)
        print('updated class dict')

    def remove_junk(self):
        """
            - Delete the junk tags (empty tags and unwanted meta tags)
            - Add new meta tags for storing release related information of parsed html
        """
        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()
        junk_p_tags = self.soup.find_all(class_=self.junk_tag_class)
        for junk_tag in junk_p_tags:
            junk_tag.decompose()

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.tag_type_dict["junk"])
         if re.search(r'^(Licensed to the People of Idaho, Public Resource|^[« •]Title \d+[«•]*)',text_junk.text.strip())]
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.tag_type_dict["ul"])
         if re.search(r'^Idaho Code (Title|Ch\.|§)|^Idaho Code Pt\. (\d+)?([IVX]+)?|Idaho Code \d+-\d+|'
                      r'Licensed to the People of Idaho, Public Resource|•Title \d+•',text_junk.text.strip())]
        [p_tag.i.unwrap() for p_tag in self.soup.find_all() if p_tag.i]
        [p_tag.a.unwrap() for p_tag in self.soup.find_all() if p_tag.a]



        if title := re.search(r'Title\s(?P<title>\d+)',
                              self.soup.find('p', class_=self.tag_type_dict['head1']).get_text(), re.I):

            self.title = title.group('title').zfill(2)

        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)

        print("junk removed")

    def replace_tags(self):
        """
            - create dictionary with class names as keys with associated tag name as its value
            - find all the tags in html with specified class names from dict
              and replace tag with associated tag name (p1 -> h1)
            - based on tag name find or build id for that tag
            - create watermark tag and append it with h1 to first nav tag
        """
        sec_count = 1
        sec_head_id = []
        sub_sec_count = 1
        sub_sec_id = []
        cite_count = 1
        cite_id = []
        case_note_id = []
        case_note_count = 1
        self.snav_count = 1
        self.case_note_head = []

        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.tag_type_dict['head1']]:
                if re.search(r'(Title|TITLE)\s(?P<title>\d+)',header_tag.get_text()):
                    header_tag.name = "h1"
                    header_tag["id"] = f't{self.title}'
                    self.snav_count = 1
                    header_tag.wrap(self.soup.new_tag("nav"))

                elif chap_head := re.search(r'Part\s?(?P<c_title>(\d+)?([IVX]+)?)', header_tag.get_text()):
                    header_tag.name = "h2"
                    if header_tag.find_previous("h2"):

                        prev_id = header_tag.find_previous("h2",class_='chapterh2').get("id")
                    else:
                        prev_id = header_tag.find_previous("h1").get("id")

                    header_tag["id"] = f'{prev_id}p{chap_head.group("c_title").zfill(2)}'
                    header_tag["class"] = "parth2"
                    sec_count = 1
                    self.snav_count = 1


                elif chap_head := re.search(r'(Chapter(s?)|CHAPTER(s?))\s(?P<c_title>\d+[a-zA-Z]?)',header_tag.get_text()):
                    header_tag.name = "h2"
                    header_tag["id"] = f't{self.title}c{chap_head.group("c_title").zfill(2)}'
                    sec_count = 1
                    header_tag["class"] = "chapterh2"
                    self.snav_count = 1

            elif header_tag.get("class") == [self.tag_type_dict['head3']]:
                if sec_head := re.search(r'^§?(\s?)(?P<sec_id>\d+-\d+[a-zA-Z]?(-\d+)?)\.?', header_tag.get_text()):
                    header_tag.name = "h3"
                    if header_tag.find_previous("h2"):
                        header_tag_id = f'{header_tag.find_previous("h2").get("id")}s{sec_head.group("sec_id")}'
                    else:
                        header_tag_id = f'{header_tag.find_previous("h1").get("id")}s{sec_head.group("sec_id")}'

                    if header_tag_id in sec_head_id:
                        header_tag['id'] = f'{header_tag_id}.{sec_count}'
                        sec_count += 1
                    else:
                        header_tag['id'] = f'{header_tag_id}'
                    sec_head_id.append(header_tag_id)
                    case_note_count = 1

            elif header_tag.get("class") == [self.tag_type_dict['head4']]:
                if sec_head := re.search(r'^(ARTICLE|Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                    if re.search(r'^(ARTICLE)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                        prev_head_id = header_tag.find_previous(lambda tag: tag.name in ["h2","h3"] and tag.get("class") != "articleh3" ).get("id")
                        header_tag['id'] = f'{prev_head_id}a{sec_head.group("sec_id")}'

                    elif re.search(r'^(Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                        header_tag['id'] = f'{header_tag.find_previous("h4").get("id")}a{sec_head.group("sec_id")}'
                    header_tag.name = "h3"
                    header_tag["class"] = "articleh3"
                    case_note_count = 1


                elif header_tag.get_text().isupper():
                    header_tag.name = "h4"
                    header_tag_text = re.sub(r'[\s]*', '', header_tag.get_text())
                    if header_tag.find_previous("h3"):
                        casenote_id = f'{header_tag.find_previous("h3").get("id")}-{header_tag_text}'
                    else:
                        casenote_id = f'{header_tag.find_previous(["h2","h1"]).get("id")}-{header_tag_text}'

                    if casenote_id in case_note_id:
                        header_tag["id"] = f'{casenote_id}.{case_note_count}'
                        case_note_count += 1
                    else:
                        header_tag["id"] = f'{casenote_id}'

                    case_note_id.append(casenote_id)
                    sub_sec_count = 1
                    cite_count = 1

                else:

                    if re.search(r'^History\.', header_tag.get_text()):
                        header_tag.name = "h5"
                        header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-history'

                    elif not re.search(r'^Part|^I\.C\.|^Chapter|^Sec\.|^This',header_tag.get_text()):
                        header_tag.name = "h5"
                        header_tag_text = re.sub(r'[\s.]*', '', header_tag.get_text()).lower()


                        subsec_head_id = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        if subsec_head_id in sub_sec_id:
                            header_tag[
                                "id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}{sub_sec_count}'
                            sub_sec_count += 1
                        else:
                            header_tag["id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        sub_sec_id.append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag.get_text().lower())


            if header_tag.get("class") == [self.tag_type_dict['ul']]:
                if re.search(r'^\d+-\d+[a-zA-Z]?[a-zA-Z]?(-\d+)?\.?\s[“[a-zA-Z]+|^\d+-\d+[a-zA-Z]?[a-zA-Z]?(-\d+)?\s?[—,]\s?\d+-\d+[a-zA-Z]?(-\d+)?\.?\s[“[a-zA-Z]',header_tag.get_text()) or (re.search(r'^\d+\.|Chapter \d+[a-zA-Z]?[.—,-]',header_tag.get_text()) and not header_tag.find_previous("h3")) :
                    header_tag.name = "li"

                elif header_tag.b and not re.search(r'^Cited',header_tag.b.get_text()):
                    header_tag.name = "h5"

                    if re.search(r'^History\.',header_tag.get_text()):
                        header_tag["id"] = f'{header_tag.find_previous(["h4","h3"]).get("id")}-history'
                    else:

                        header_tag_text = re.sub(r'[\s]*','',header_tag.b.get_text()).lower()

                        subsec_head_id = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        if subsec_head_id in sub_sec_id :
                            header_tag["id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}{sub_sec_count}'
                            sub_sec_count += 1
                        else:
                            header_tag["id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        sub_sec_id .append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag.get_text().lower())

                elif header_tag.get_text() == 'Chapter':
                    header_tag.find_previous("nav").append(header_tag)



                elif re.search(r'^Cited', header_tag.get_text()):
                    header_tag.name = "h4"
                    headertag_text = re.sub(r'[\s]*','',header_tag.get_text()).lower()
                    if header_tag.find_previous("h3"):
                        cite_head_id = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}'
                    else:
                        cite_head_id = f'{header_tag.find_previous(["h2","h1"]).get("id")}-{headertag_text}'

                    if cite_head_id in cite_id:
                        header_tag["id"] = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}.{cite_count}'
                        cite_count += 1
                    else:
                        header_tag["id"] = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}'

                    sub_sec_count = 1
                    cite_id.append(cite_head_id)

                elif sec_head := re.search(r'^(ARTICLE|Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                    header_tag['id'] = f'{header_tag.find_previous("h4").get("id")}a{sec_head.group("sec_id")}'
                    header_tag.name = "h3"
                    header_tag["class"] = "articleh3"


            elif 'head' in  self.tag_type_dict:
                if header_tag.get("class") == [self.tag_type_dict['head']]:
                    header_tag.name = "h5"

                    if re.search(r'^History\.', header_tag.get_text()):
                        header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-history'
                    else:
                        header_tag_text = re.sub(r'[\s.]*', '', header_tag.get_text()).lower()
                        if header_tag.find_previous("h4"):
                            subsec_head_id = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}'
                            if subsec_head_id in sub_sec_id:
                                header_tag[
                                    "id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}{sub_sec_count}'
                                sub_sec_count += 1
                            else:
                                header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}'
                        else:
                            subsec_head_id = f'{header_tag.find_previous(["h3","h2","h1"]).get("id")}-{header_tag_text}'

                            if subsec_head_id in sub_sec_id:
                                header_tag[
                                        "id"] = f'{subsec_head_id}{sub_sec_count}'
                                sub_sec_count += 1
                            else:
                                header_tag["id"] = f'{subsec_head_id}'

                        sub_sec_id.append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag.get_text().lower())

            if len(header_tag.get_text(strip=True)) == 0:
                header_tag.extract()

        print('tags replaced')


    def create_ul_tag_and_case_note_nav(self):

        for case_note_tag in self.soup.findAll(class_="p2"):
            if case_note_tag.get_text().lower() in self.case_note_head and not case_note_tag.get("id"):
                case_note_tag.name = "li"

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

    def create_chapter_section_nav(self):

        for list_item in self.soup.find_all("li"):
            if sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?)\s*[.—,]', list_item.get_text()) :
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h2').get('id')}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count = 1
                list_item[
                    "id"] = f"{list_item.find_previous('h2').get('id')}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1

            elif sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?-(?P<p_id>\d{1})\d{2})\.', list_item.get_text()) :
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count =1
                list_item["id"] = f"{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1
            elif sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?-(?P<p_id>\d{2})\d{2})\.', list_item.get_text()) :
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count =1
                list_item["id"] = f"{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1


            elif chap_list := re.search(r'^(Chapter\s?)*(?P<chap_id>\d+[a-zA-Z]?)\.?,?', list_item.get_text()):
                if not list_item.find_previous("h3"):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#t{self.title}c{chap_list.group('chap_id').zfill(2)}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list
                    list_item["id"] = f"t{self.title}c{chap_list.group('chap_id').zfill(2)}-cnav{self.snav_count:02}"
                    self.snav_count += 1

            else:
                list_item_text = re.sub(r'[\s.]*', '', list_item.get_text()).lower()
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h4').get('id')}-{list_item_text}"
                nav_list.append(nav_link)
                list_item.contents = nav_list

        print("anchor tag added")




    def create_main_tag(self):
        """
                    - wrap all contents inside main tag(Except chapter index)
                """

        section_nav_tag = self.soup.new_tag("main")
        first_chapter_header = self.soup.find("h2")
        for main_tag in self.soup.findAll():
            if main_tag.find_next("h2") == first_chapter_header:
                continue
            elif main_tag == first_chapter_header:
                main_tag.wrap(section_nav_tag)
            else:
                if main_tag.name == "span" and not main_tag.get("class") == "gnrlbreak" :
                    continue
                elif main_tag.name == "b" or main_tag.name == "i":
                    continue
                else:
                    section_nav_tag.append(main_tag)

        print("main tag is created")


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
                        if not sec_header:
                            print()

        print('wrapped div tags')


    def recreate_tag(self):
        for p_tag in self.soup.findAll("p",class_=self.tag_type_dict["head3"]):
            current_p_tag = p_tag.get_text()
            if re.search(r'^§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\.', current_p_tag):
                if head_text := re.search(r'^(?P<alpha>§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\..+)—', current_p_tag):
                    p_text = re.sub(r'^(§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\..+)—', '', current_p_tag)
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = head_text.group('alpha')
                    new_p_tag["class"] = [self.tag_type_dict['head3']]
                    p_tag.insert_before(new_p_tag)
                    p_tag.string = p_text
                    p_tag["class"] = [self.tag_type_dict['ul']]

        for p_tag in self.soup.findAll("p",class_=self.tag_type_dict["ul"]):
            current_p_tag = p_tag.get_text()
            if re.search(r'^Cited', p_tag.get_text()) and p_tag.b:
                head_text = p_tag.b.get_text()
                p_text = re.sub(r'^Cited', '', current_p_tag)
                new_p_tag = self.soup.new_tag("p")
                new_p_tag.string = head_text
                new_p_tag["class"] = [self.tag_type_dict['ul']]
                p_tag.insert_before(new_p_tag)
                p_tag.string = p_text
                p_tag["class"] = [self.tag_type_dict['ul']]


            if re.search(r'^\([a-z]\).+\([a-z]\)\s*', current_p_tag):
                alpha = re.search(r'^(?P<text1>\((?P<alpha1>[a-z])\).+)(?P<text2>\((?P<alpha2>[a-z])\)\s*.+)',
                                  current_p_tag)
                if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)', p_tag.find_next_sibling().text.strip()).group(
                        "alpha3")
                    if ord(alpha.group("alpha2")) == ord(alpha.group("alpha1")) + 1:
                        if ord(nxt_alpha) == ord(alpha.group("alpha2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ul']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

            if p_tag.b:
                head_text = p_tag.b.get_text()
                head_text1 = re.sub(r'[\[\]]+','',current_p_tag)

                p_text = re.sub(rf'{head_text1}', '', current_p_tag)
                new_p_tag = self.soup.new_tag("p")
                new_p_tag.string = head_text
                self.tag_type_dict['head'] = 'p10'
                new_p_tag["class"] = [self.tag_type_dict['head']]
                p_tag.insert_before(new_p_tag)
                p_tag.string = p_text
                p_tag["class"] = []


            if re.search(r'^\(\d+\).+\(\d\)\s*', p_tag.get_text().strip()):
                alpha = re.search(r'^(?P<text1>\((?P<alpha1>\d+)\).+)(?P<text2>\((?P<alpha2>\d+)\)\s*.+)',
                                  p_tag.get_text().strip())

                if re.match(r'^\(\d+\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>\d+)\)', p_tag.find_next_sibling().text.strip()).group(
                        "alpha3")
                    if int(alpha.group("alpha2")) == int(alpha.group("alpha1")) + 1:
                        if int(nxt_alpha) == int(alpha.group("alpha2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict["ul"]]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

        for p_tag in self.soup.findAll("p", class_=self.tag_type_dict["head4"]):
            if p_tag.b:
                p_text = str(p_tag)

                if re.search(r'<p class="p7">.+<b>.+</b></p>$',p_text):
                    p_tag["class"] = [self.tag_type_dict["ul"]]
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = p_tag.b.get_text().strip()
                    new_p_tag["class"] = [self.tag_type_dict["head4"]]
                    p_tag.insert_after(new_p_tag)
                    head_text = re.search(r'<p class="p7">(?P<h_text>.+)<b>.+</b></p>$', p_text).group('h_text')
                    p_tag.string = head_text



        print('tags are recreated')



    def convert_paragraph_to_alphabetical_ol_tags1(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        cap_alpha = 'A'
        ol_head = 1
        num_count = 1
        alpha_ol = self.soup.new_tag("ol", Class="alpha")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        ol_list = []
        innr_roman_ol = None
        cap_alpha_cur_tag = None
        new_alpha = None
        ol_head1 = 1
        main_sec_alpha1 = 'a'
        flag = 0
        cap_alpha_head = "A"
        num_count1= 1


        for p_tag in self.soup.find_all():
            if p_tag.b:
                p_tag.b.unwrap()
            if p_tag.i:
                p_tag.i.unwrap()

            current_tag_text = p_tag.text.strip()
            if p_tag.name == "h3":
                num_cur_tag = None



            if re.search(rf'^\({ol_head}\)|^\({ol_head1}\)', current_tag_text):
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = 'A'
                main_sec_alpha = "a"
                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")

                    p_tag.wrap(num_ol)
                    prev_head_id = p_tag.find_previous(["h5","h4", "h3"]).get("id")

                    if alpha_cur_tag:
                        alpha_cur_tag.append(num_ol)
                        prev_head_id = alpha_cur_tag.get("id")
                        prev_num_id = f'{prev_head_id}'
                        p_tag["id"] = f'{prev_head_id}{ol_head}'
                    else:
                        prev_num_id = f'{prev_head_id}ol{ol_count}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'

                    if prev_head_id in ol_list:
                        ol_count += 1
                    else:
                        ol_count = 1
                    ol_list.append(prev_head_id)

                else:
                    num_ol.append(p_tag)
                    p_tag["id"] = f'{prev_num_id}{ol_head}'


                p_tag.string = re.sub(rf'^\({ol_head}\)|^\({ol_head1}\)', '', current_tag_text)
                ol_head += 1
                ol_head1 += 1

                if re.search(r'^\(\d+\)(\s)?\([a-z]\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)?\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)', current_tag_text)
                    prevnum_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"

                elif re.search(r'^\(\d+\)(\s)?\([A-Z]\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)?\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    # alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)', current_tag_text)
                    prev_id = f'{prev_head_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"



            # a
            elif re.search(rf'^\(\s*{main_sec_alpha}\s*\)|^{main_sec_alpha}\.|^\(\s*{main_sec_alpha1}\s*\)', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                roman_count = 1
                num_count = 1
                ol_head1 = 1

                if re.search(r'^\(a\)|^a\.', current_tag_text) :
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    p_tag.wrap(alpha_ol)
                    if num_cur_tag:
                        prevnum_id = num_cur_tag.get("id")
                        num_cur_tag.append(alpha_ol)
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                        flag = 0
                    else:
                        flag = 1
                        prevnum_id =p_tag.find_previous(["h4", "h3"]).get("id")
                        p_tag["id"] = f'{p_tag.find_previous(["h4", "h3"]).get("id")}ol{ol_count}{main_sec_alpha1}'
                else:

                    alpha_ol.append(p_tag)

                    if flag:
                        p_tag["id"] = f'{p_tag.find_previous(["h4", "h3"]).get("id")}ol{ol_count}{main_sec_alpha1}'
                    else:
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'


                p_tag.string = re.sub(rf'^\(\s*{main_sec_alpha}\s*\)|^\(\s*{main_sec_alpha1}\s*\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)


                if re.search(r'^\(\w\)\s?\([ivx]+\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s?\([ivx]+\)', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                    inner_li_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head-1}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    innr_roman_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, innr_roman_ol)
                    prev_alpha = p_tag

                if re.search(r'^\(\w\)\s?\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s?\(1\)', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>1)\)', current_tag_text)
                    prev_head_id = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    inner_li_tag[
                        "id"] = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    num_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, num_ol)
                    ol_head = 2
                    # prev_alpha = p_tag


            #i
            elif re.search(r'^\([ivx]+\)',current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(i\)',current_tag_text):
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
                        prev_alpha_id = f'{prev_num_id}{cur_tag}'
                        p_tag["id"] = f'{prev_num_id}{cur_tag}'


                p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)','', current_tag_text)
                # num_count = 1


            # 1
            elif re.search(rf'^{num_count}\.', current_tag_text) and p_tag.get('class') == [self.tag_type_dict['ul']] and p_tag.name != "li":
                p_tag.name = "li"
                cap_alpha = "A"
                num_tag = p_tag

                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    prev_id = p_tag.find_previous(["h5","h4", "h3"]).get("id")

                    if alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)
                else:
                    num_ol1.append(p_tag)


                if alpha_cur_tag:
                    p_tag["id"] = f'{prev_id}{num_count}'
                else:
                    p_tag["id"] = f'{prev_id}ol{ol_count}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1


            elif re.search(rf'^{num_count}\.|^{num_count1}\.', current_tag_text) and p_tag.get('class') == [self.tag_type_dict['ul']] and p_tag.name != "li":
                p_tag.name = "li"
                num_tag = p_tag
                cap_alpha = "A"

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    prev_id = p_tag.find_previous(["h4", "h3"]).get("id")
                    if re.search(r'^ARTICLE [IVX]+', p_tag.find_previous("h3").get_text().strip()):
                        prev_id = cap_alpha_head_tag.get("id")
                        cap_alpha_head_tag.append(num_ol1)
                    elif alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)


                else:
                    num_ol.append(p_tag)

                if re.search(r'^ARTICLE [IVX]+', p_tag.find_previous("h3").get_text().strip()):
                    p_tag["id"] = f'{prev_id}{num_count1}'
                elif alpha_cur_tag:
                    p_tag["id"] = f'{prev_id}{num_count}'
                else:
                    p_tag["id"] = f'{prev_id}ol{ol_count}{num_count}'

                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1

                p_tag.string = re.sub(rf'^{num_count1}\.', '', current_tag_text)
                num_count1 += 1


            #(A)
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
                p_tag["id"] = f'{prev_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                cap_alpha = chr(ord(cap_alpha) + 1)

            #A
            elif re.search(rf'^{cap_alpha_head}\.\s', current_tag_text):
                p_tag.name = "li"
                cap_alpha_head_tag = p_tag
                cap_alpha1 = cap_alpha
                num_count1 = 1

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    print(p_tag)

                    p_tag.wrap(cap_alpha_ol)
                    prev_id = p_tag.find_previous("h3").get("id")
                    # p_tag.find_previous("li").append(cap_alpha_ol)

                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{prev_id}{cap_alpha_head}'
                p_tag.string = re.sub(rf'^{cap_alpha_head}\.', '', current_tag_text)
                cap_alpha_head = chr(ord(cap_alpha_head) + 1)




            elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
                curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
                p_tag.name = "li"
                if re.search(r'^\(i{2,3}\)', current_tag_text):
                    if p_tag.find_next_sibling():
                        if re.search(r'^\(j{2,3}\)', p_tag.find_next_sibling().get_text().strip()):
                            alpha_cur_tag = p_tag
                            alpha_ol.append(p_tag)
                            prev_alpha_id = f'{prev_num_id}{curr_id}'
                            p_tag["id"] = f'{prev_num_id}{curr_id}'
                            roman_count = 1
                            p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)
                        else:
                            innr_roman_ol.append(p_tag)
                            p_tag["id"] = f'{prev_alpha.get("id")}{curr_id}'
                    else:
                        alpha_cur_tag = p_tag
                        alpha_ol.append(p_tag)
                        prev_alpha_id = f'{prev_num_id}{curr_id}'
                        p_tag["id"] = f'{prev_num_id}{curr_id}'
                        roman_count = 1
                        p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)


                else:
                    alpha_cur_tag = p_tag
                    alpha_ol.append(p_tag)
                    prev_alpha_id = f'{prev_num_id}{curr_id}'
                    p_tag["id"] = f'{prev_num_id}{curr_id}'
                    roman_count = 1
                    p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)

            if re.search(r'^History|^Cross references:|^OFFICIAL COMMENT', current_tag_text) or p_tag.name in ['h3', 'h4','h5']:
                ol_head = 1
                ol_head1 = 1
                num_count = 1
                num_cur_tag = None
                new_alpha = None
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                alpha_cur_tag = None
                cap_alpha_head = "A"
                num_count1 = 1


        print('ol tags added')


    def add_citation(self):
        tag_id = None
        target = "_blank"

        for tag in self.soup.find_all(["p"]):
            if re.search(r"§*\s?\d+-\d{3,4}\s*[A-Z]?|"
                         r"OAG \d+-\d+|"
                         r"Idaho Const\., Art\. [IXV][.,](\s§\s\d+\.)?"
                        , tag.text.strip()):
                text = str(tag)


                for match in [x[0] for x in re.findall(r'(§*\s?\d+-\d+\s*[A-Z]?|\s\d+-\d{3,4}\s*[A-Z]?|'
                                                    r'OAG \d+-\d+|'
                                                    r'Idaho Const\., Art\. [IXV][.,](\s§\s\d+\.)?)',
                                                    tag.get_text())]:
                    inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|^<li\sclass="\w\d+"\sid=".+">|</li>$', '',
                                         text, re.DOTALL)


                    if re.search(r"§*\s?\d+-\d{3,4}\s*[A-Z]?", match.strip()):
                        tag.clear()
                        cite_num = re.search(r'§*\s?(?P<title>\d+)-(?P<chap>\d+\s*[A-Z]?)', match.strip())
                        if len(cite_num.group('chap')) == 3:
                            chap_num = cite_num.group('chap')[:1]
                        elif len(cite_num.group('chap')) == 4:
                            chap_num = cite_num.group('chap')[:2]
                        else:
                            chap_num = '0'
                        sec_num = re.search(r'§*\s?(?P<sec>\d+-\d+\s*[A-Z]?)', match.strip()).group('sec')

                        if self.title == cite_num.group("title"):

                            tag_id = f'#t{cite_num.group("title").zfill(2)}c{chap_num.zfill(2)}s{sec_num}'
                            target = "_self"
                        else:
                            tag_id = f'idaho.title.{cite_num.group("title").zfill(2)}.html#t{cite_num.group("title").zfill(2)}c{chap_num.zfill(2)}s{sec_num}'
                            target = "_blank"

                        class_name = "ocid"
                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                        text = re.sub(fr'\s{re.escape(match)}', format_text, inside_text, re.I)
                        tag.append(text)

                    else:
                        tag.clear()
                        if re.search(r'OAG \d+-\d+',match.strip()):
                            class_name = "OAG"
                        elif re.search(r'Idaho Const\., Art\. [IXV][.,](\s§\s\d+\.)?',match.strip()):
                            class_name = "id_code"
                        else:
                            class_name = "id_code"




                        format_text = f'<cite class="{class_name}">{match}</cite>'
                        text = re.sub(fr'\s{re.escape(match)}', format_text, inside_text, re.I)
                        tag.append(text)


        print("citation added")

    def add_watermark_and_remove_class_name(self):
        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p','h5']:
                del tag["class"]

        watermark_tag = self.soup.new_tag('p', Class='transformation')
        watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                              datetime.now().date())
        nav_tag = self.soup.find("nav")
        if nav_tag:
            nav_tag.insert(0, watermark_tag)

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

        title_tag = self.soup.find("title")
        title_tag.string = "IDCODE"



    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))

        with open(f"/home/mis/cic-code-id/transforms/id/ocid/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)


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
        self.get_class_name()
        self.remove_junk()
        self.recreate_tag()
        self.replace_tags()
        self.create_main_tag()
        self.create_ul_tag_and_case_note_nav()
        self.create_chapter_section_nav()
        self.create_and_wrap_with_div_tag()
        self.add_citation()
        self.convert_paragraph_to_alphabetical_ol_tags1()
        self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)
