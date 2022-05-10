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
import roman


class WYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.previous = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.class_regex = {'head1': r'Title \d+', 'ul': r'^Chapter \d',
                            'head2': r'^Chapter \d |^Article \d+ ',
                            'head4': 'History\.', 'head3': '^§ \d+-\d+-\d+', 'ol_p': r'^\(\d\)',
                            'head': '^Law reviews\. —',
                            'junk1': '^Annotations$', }


        self.watermark_text = """Release {0} of the Official Code of Wyoming Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
        """
        self.meta_tags = []
        self.tag_to_unwrap = []
        self.c_nav_count = 0
        self.a_nav_count = 0
        self.s_nav_count = 0
        self.head4_count = 1
        self.head3_count = 1
        self.start_parse()

    def create_page_soup(self):
        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """
        with open(f'../transforms/wy/ocwy/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')



    def generate_class_name(self):

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
            - Delete the junk tags (empty tags and unwanted meta tags)
            - Add new meta tags for storing release related information of parsed html
        """
        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()
        junk_p_tags = self.soup.find_all(class_=self.junk_tag_class)
        for junk_tag in junk_p_tags:
            if junk_tag.get('class')[0] == 'Apple-converted-space':
                junk_tag.unwrap()
            junk_tag.decompose()

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk1"]) if
         re.search('^Annotations|^Text|^History', text_junk.text.strip())]

        if title := re.search(r'Title\s(?P<title>\d+)',
                              self.soup.find('p', class_=self.class_regex['head1']).get_text(), re.I):

            self.title = title.group('title')
        else:
            self.title = 'constitution-{0}'.format(re.search(r"\.(?P<title>\w+)\.html",
                                                             self.html_file_name).group("title"))
        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)
        print('junk removed')

        for p_tag in self.soup.find_all(class_="head4"):
            if p_tag.b and re.search(r'^History', p_tag.text.strip()):

                p_tag.b.name = "p"

                p_tag_text = p_tag.text.strip()
                p_tag.clear()
                rept_tag = re.split('\n', p_tag_text)
                for tag_text in rept_tag:
                    if re.search(r'Analysis', tag_text):
                        new_tag = self.soup.new_tag("p")
                        new_tag.string = tag_text
                        p_tag.append(new_tag)
                        new_tag["class"] = "analysis"
                    else:
                        new_tag = self.soup.new_tag("p")
                        new_tag.string = tag_text
                        p_tag.append(new_tag)
                        new_tag["class"] = "analysisnote"

                p_tag.unwrap()


    def recreate_tag(self):

        for p_tag in self.soup.find_all(class_=self.class_regex['head4']):
           if p_tag.b:
               if re.search(r'^History',p_tag.b.text.strip()):
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = p_tag.b.text
                    new_p_tag["class"] = [self.class_regex['head4']]
                    p_tag.insert_before(new_p_tag)
                    del p_tag["class"]
                    p_tag.b.clear()

    def replace_tags(self):
        watermark_p = None
        title_tag = None
        cur_head_list = []
        cur_id_list = []
        alpha = None
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        head4_list = ['Revision of title. —', 'Cross references. —', 'Law reviews. —', 'Editor\'s notes. —',
                      'History.','Effective dates. —']


        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if re.search('constitution\.wy', self.html_file_name):
                    self.title_id  = 'constitution-wy'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id  = 'constitution-us'
                Article_pattern = re.compile(r'^Article\s(?P<chap_id>\d+([A-Z])*) ')
                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^Constitution of the State of Wyoming|^THE CONSTITUTION OF THE UNITED STATES OF AMERICA',header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.wrap(self.soup.new_tag("nav"))
                        header_tag['id'] =  self.title_id
                        watermark_p = self.soup.new_tag('p', Class='transformation')
                        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                                        datetime.now().date())
                        self.soup.find("nav").insert(0, watermark_p)

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^Article \d+\.',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^Article (?P<ar_id>\d+)\.', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"

                    elif re.search(r'^§ \d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^§ (?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"

                    if re.search(r'^AMENDMENTS TO THE CONSTITUTION',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.sub(r'[\s\W]+','', header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"
                    if re.search(r'^Amendment \d+',header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^Amendment (?P<s_id>\d+)', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}am{sec_id.zfill(2)}"
                        header_tag['class'] = "amend"

                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if re.search(r'^§ \d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^§ (?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                    elif re.search(r'^Section \d+', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^Section (?P<s_id>\d+)', header_tag.text.strip()).group('s_id')
                        if re.match(r'^Article', header_tag.find_previous('h2').text.strip()):
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h3',class_='amend').get('id')}s{sec_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["head4"]] or \
                        header_tag.get("class") == [self.class_regex["head"]]:

                    if header_tag.text.strip() in head4_list:
                        header_tag.name = "h4"
                        subsection_id = header_tag.text.strip().lower()
                        subsection_id = re.sub('[\s\W]', '', subsection_id)
                        curr_tag_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{subsection_id}"

                        if curr_tag_id in cur_id_list:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{subsection_id}.1"
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{subsection_id}"

                        cur_id_list.append(header_tag['id'])

                elif header_tag.get("class") == [self.class_regex["ul"]] and not re.search('^(PREAMBLE|Preamble)',header_tag.text.strip()):
                    header_tag.name = "li"

                    if header_tag.find_previous().name == "li":
                        ul_tag.append(header_tag)

                    else:
                        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        header_tag.wrap(ul_tag)

                        if Article_pattern.search(ul_tag.text.strip()):
                            ul_tag.find_previous("nav").append(ul_tag)
                        else:
                            nav_tag = self.soup.new_tag("nav")
                            ul_tag.wrap(nav_tag)

                if header_tag.get("class") == [self.class_regex["head"]]:
                    if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[IVX]+)\.', header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous('h3').get('id')}-{tag_text}"
                        header_tag['class'] = 'casehead'
                        alpha = 'A'

                    elif alpha:
                        if re.search(fr'^{alpha}\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[A-Z])\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casehead').get('id')}-{tag_text}"
                            header_tag['class'] = 'casesub'
                            alpha = chr(ord(alpha) + 1)

                    elif re.search(r'^[0-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[0-9])\.', header_tag.text.strip()).group('c_id').lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h5', class_='casesub').get('id')}-{tag_text}"

            else:
                title_pattern = re.compile(r'^(Title)\s(?P<title_id>\d+)')
                chapter_pattern = re.compile(r'^(Chapter)\s(?P<chap_id>\d+([A-Z])*) ')
                section_pattern = re.compile(r'^§*\s*(?P<sec_id>\d+(\.\d+)*-\d+(\.[A-Z]+)*-\d+(\.\d+)*)')
                SUBCHAPTER_pattern = re.compile(r'^(?P<ar_id>[A-Z])\. ')
                SUBCHAPTER_pattern1 = re.compile(r'^Division (?P<ar_id>\d+)\. ')
                part_pattern = re.compile(r'^Part\s*(?P<p_id>\d+([A-Z])*)')
                article_pattern = re.compile(r'^(ARTICLE|Article) (?P<s_id>[IVX]+)')
                article_pattern1 = re.compile(r'^(Article|Revised Article|Articles)\s(?P<s_id>\d+([A-Z])*(\.*[A-Z])*)[\.\s]')
                section_pattern1 = re.compile(r'^Section (?P<s_id>[0-9]+)')
                section_pattern2 = re.compile(r'^Section (?P<s_id>[A-Z])')

                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if title_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag.wrap(self.soup.new_tag("nav"))
                        self.title_id = title_pattern.search(header_tag.text.strip()).group('title_id').zfill(2)
                        header_tag['id'] = f"t{self.title_id}"
                        watermark_p = self.soup.new_tag('p', Class='transformation')
                        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                                        datetime.now().date())
                        self.soup.find("nav").insert(0, watermark_p)

                elif header_tag.get("class") == [self.class_regex["head2"]] or \
                        header_tag.get("class") == [self.class_regex["head"]]:
                    self.head3_count = 1
                    if chapter_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = chapter_pattern.search(header_tag.text.strip()).group('chap_id')
                        header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"
                        header_tag["class"] = "chapter"
                    elif re.search(r'^Revised Article \d',header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = re.search(r'^Revised Article (?P<s_id>\d)',header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{chapter_id.zfill(2)}"
                        header_tag["class"] = "article"
                    elif article_pattern1.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = article_pattern1.search(header_tag.text.strip()).group('s_id')
                        header_tag['id'] = f"{header_tag.find_previous('h2',class_='chapter').get('id')}a{chapter_id.zfill(2)}"


                        header_tag["class"] = "article"
                    elif re.search(r'^Part \d+\.',header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = re.search(r'^Part (?P<s_id>\d+)\.',header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2',class_='article').get('id')}p{chapter_id.zfill(2)}"
                        header_tag["class"] = "part"
                    elif SUBCHAPTER_pattern.search(header_tag.text.strip()) or \
                            SUBCHAPTER_pattern1.search(header_tag.text.strip()):
                        if header_tag.b:
                            header_tag.name = "h2"
                            if SUBCHAPTER_pattern.search(header_tag.text.strip()):
                                chapter_id = SUBCHAPTER_pattern.search(header_tag.text.strip()).group('ar_id')
                            elif SUBCHAPTER_pattern1.search(header_tag.text.strip()):
                                chapter_id = SUBCHAPTER_pattern1.search(header_tag.text.strip()).group('ar_id')

                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2',class_='article').get('id')}s{chapter_id.zfill(2)}"
                            header_tag["class"] = "sub"
                    if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[IVX]+)\.', header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous({'h4','h3'}).get('id')}-{tag_text}"
                        header_tag['class'] = 'casehead'
                        alpha ='A'
                    elif alpha:
                        if re.search(fr'^{alpha}\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[A-Z])\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casehead').get('id')}-{tag_text}"
                            header_tag['class'] = 'casesub'
                            alpha = chr(ord(alpha) + 1)
                        elif re.search(r'^[0-9]\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[0-9])\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag['id'] = f"{header_tag.find_previous('h5', class_='casesub').get('id')}-{tag_text}"
                    self.a_nav_count = 0
                    self.s_nav_count = 0

                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if section_pattern.search(header_tag.text.strip()):
                        self.head4_count = 1
                        header_tag.name = "h3"
                        section_id = section_pattern.search(header_tag.text.strip()).group('sec_id')
                        curr_head_id = f"{header_tag.find_previous({'h2','h1'}).get('id')}s{section_id.zfill(2)}"

                        if curr_head_id in cur_head_list:
                            header_tag['id'] = f"{header_tag.find_previous({'h2','h1'}).get('id')}s{section_id.zfill(2)}.{self.head3_count}"
                            self.head3_count += 1
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"

                        cur_head_list.append(curr_head_id)
                        header_tag["class"] = "section"


                elif header_tag.get("class") == [self.class_regex["head4"]] or \
                        header_tag.get("class") == [self.class_regex["head"]]:

                    if header_tag.text.strip() in head4_list:
                        header_tag.name = "h4"
                        subsection_id = header_tag.text.strip().lower()
                        subsection_id = re.sub('[\s\W]','',subsection_id)
                        curr_tag_id = f"{header_tag.find_previous({'h3','h2','h1'}).get('id')}-{subsection_id}"

                        if curr_tag_id in cur_id_list:
                            header_tag['id'] = f"{header_tag.find_previous({'h3','h2','h1'}).get('id')}-{subsection_id}.{self.head4_count}"
                            self.head4_count += 1
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{subsection_id}"

                        cur_id_list.append(header_tag['id'])

                    elif article_pattern.search(header_tag.text.strip()):
                        self.head4_count = 1
                        header_tag.name = "h3"
                        chapter_id = article_pattern.search(header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3',class_='section').get('id')}a{chapter_id.zfill(2)}"
                        header_tag["class"] = "article"

                    elif section_pattern1.search(header_tag.text.strip()) or section_pattern2.search(header_tag.text.strip()):
                        self.head4_count = 1
                        header_tag.name = "h3"

                        if section_pattern1.search(header_tag.text.strip()):
                            chapter_id = section_pattern1.search(header_tag.text.strip()).group('s_id')
                            header_tag[
                                    'id'] = f"{header_tag.find_previous('h3', class_='section').get('id')}s{chapter_id.zfill(2)}"

                        elif section_pattern2.search(header_tag.text.strip()):
                            chapter_id = section_pattern2.search(header_tag.text.strip()).group('s_id')
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h3', class_='article').get('id')}s{chapter_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if chapter_pattern.search(header_tag.text.strip()) or \
                            article_pattern1.search(header_tag.text.strip()) or \
                            section_pattern.search(header_tag.text.strip()) or \
                            SUBCHAPTER_pattern.search(header_tag.text.strip()) or \
                            SUBCHAPTER_pattern1.search(header_tag.text.strip()) or \
                            part_pattern.search(header_tag.text.strip()) :

                        header_tag.name = "li"
                        if header_tag.find_previous().name == "li":
                            ul_tag.append(header_tag)
                        else:
                            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            header_tag.wrap(ul_tag)

                            if chapter_pattern.search(ul_tag.text.strip()):
                                ul_tag.find_previous("nav").append(ul_tag)
                            else:
                                nav_tag = self.soup.new_tag("nav")
                                ul_tag.wrap(nav_tag)

        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)

        print('tags replaced')

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num,cnav):
        nav_list = []
        nav_link = self.soup.new_tag('a')
        nav_link.append(list_item.text)

        if re.search('constitution', self.html_file_name):
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
                list_item["id"] = f"{prev_id}{sub_tag}{chap_num}-{cnav}"
            else:
                nav_link["href"] = f"#{self.title_id}{sub_tag}{chap_num}"
                list_item["id"] = f"#{self.title_id}{sub_tag}{chap_num}-{cnav}"
        else:
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
                list_item["id"] = f"{prev_id}{sub_tag}{chap_num}-{cnav}"
            else:
                if sec_num:
                    nav_link["href"] = f"#t{self.title_id.zfill(2)}c{chap_num}s{sec_num}"
                    list_item["id"] = f"t{self.title_id.zfill(2)}c{chap_num}s{sec_num}-{cnav}"
                else:
                    nav_link["href"] = f"#t{self.title_id.zfill(2)}{sub_tag}{chap_num}"
                    list_item["id"] = f"t{self.title_id.zfill(2)}{sub_tag}{chap_num}-{cnav}"

        nav_list.append(nav_link)
        list_item.contents = nav_list


    def create_chapter_section_nav(self):
        count = 0
        chapter_pattern = re.compile(r'^(Chapter)\s(?P<chap_id>\d+([A-Z])*)')
        section_pattern = re.compile(r'^§*\s*(?P<sec_id>\d+(\.\d+)*-\d+(\.[A-Z]+)*-\d+(\.\d+)*)')
        subchapter_pattern = re.compile(r'(?P<s_id>[A-Z])\.')
        article_pattern1 = re.compile(r'^(Article|Revised Article)\s(?P<s_id>\d+([A-Z])*(\.[A-Z])*)')
        subchapter_pattern1 = re.compile(r'^Division (?P<s_id>\d+)\. ')
        part_pattern = re.compile(r'^Part\s*(?P<p_id>\d+([A-Z])*)')

        for list_item in self.soup.find_all():
            if list_item.name == "li":
                if re.search('constitution', self.html_file_name):
                    if re.search(r'^Article \d+\.', list_item.text.strip()):
                        chap_num = re.search(r'^Article (?P<chap>\d+)\. ', list_item.text.strip()).group(
                                "chap").zfill(2)
                        sub_tag = "a"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^§ \d+\.', list_item.text.strip()):
                        chap_num = re.search(r'^§ (?P<chap>\d+)\. ', list_item.text.strip()).group(
                                "chap").zfill(2)
                        sub_tag = "s"
                        prev_id = list_item.find_previous('h2').get("id")
                        self.a_nav_count += 1
                        cnav = f'snav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^AMENDMENTS TO THE CONSTITUTION', list_item.text.strip()):
                        chap_num = re.sub(r'[\s\W]+','', list_item.text.strip()).lower()
                        sub_tag = "a"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^Section \d+', list_item.text.strip()):
                        chap_num = re.search(r'^Section (?P<chap>\d+)', list_item.text.strip()).group(
                                "chap").zfill(2)
                        sub_tag = "s"
                        if re.match(r'^Article', list_item.find_previous('h2').text.strip()):
                            prev_id = list_item.find_previous('h2').get("id")
                        else:
                            prev_id = list_item.find_previous('h3').get("id")
                        self.a_nav_count += 1
                        cnav = f'snav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^Amendment \d+', list_item.text.strip()):
                        chap_num = re.search(r'^Amendment (?P<chap>\d+)', list_item.text.strip()).group(
                                "chap").zfill(2)
                        sub_tag = "am"
                        prev_id = list_item.find_previous('h2').get("id")
                        self.a_nav_count += 1
                        cnav = f'amnav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                else:
                    if chapter_pattern.search(list_item.text.strip()):
                        chap_id = chapter_pattern.search(list_item.text.strip()).group('chap_id')
                        sub_tag = "c"
                        prev_id = list_item.find_previous('h1').get("id")
                        self.c_nav_count += 1
                        cnav = f'cnav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None,cnav)
                    elif article_pattern1.search(list_item.text.strip()):
                        chap_id = article_pattern1.search(list_item.text.strip()).group('s_id')
                        sub_tag = "a"
                        prev_id = list_item.find_previous({'h2','h1'}).get("id")
                        self.a_nav_count += 1
                        cnav = f'anav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None,cnav)
                    elif section_pattern.search(list_item.text.strip()):
                        chap_id = section_pattern.search(list_item.text.strip()).group('sec_id')
                        sub_tag = "s"
                        prev_id = list_item.find_previous('h2').get("id")
                        self.s_nav_count += 1
                        cnav = f'snav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None,cnav)
                    elif subchapter_pattern.search(list_item.text.strip()) or \
                            subchapter_pattern1.search(list_item.text.strip()):
                        if subchapter_pattern.search(list_item.text.strip()):
                            chap_id = subchapter_pattern.search(list_item.text.strip()).group('s_id')
                        elif subchapter_pattern1.search(list_item.text.strip()):
                            chap_id = subchapter_pattern1.search(list_item.text.strip()).group('s_id')
                        sub_tag = "s"
                        prev_id = list_item.find_previous('h2',class_='article').get("id")
                        self.s_nav_count += 1
                        cnav = f'pnav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None,cnav)

                    elif part_pattern.search(list_item.text.strip()):
                        chap_id = part_pattern.search(list_item.text.strip()).group('p_id')
                        sub_tag = "p"
                        prev_id = list_item.find_previous('h2',class_='article').get("id")
                        self.s_nav_count += 1
                        cnav = f'snav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None,cnav)

            elif list_item.name in ['h1','h2']:
                self.c_nav_count = 0
                self.a_nav_count = 0
                self.s_nav_count = 0


    def convert_paragraph_to_alphabetical_ol_tags(self):
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
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        cap_alpha_cur_tag = None
        main_sec_alpha1 = 'a'
        sec_alpha_cur_tag = None
        cap_alpha1 = 'A'
        cap_alpha2 = 'a'
        cap_alpha1_cur_tag = None
        ol_head_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5','p']):
            current_tag_text = p_tag.text.strip()
            if re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                if main_sec_alpha in ["h","k","u","w"]:
                    main_sec_alpha = chr(ord(main_sec_alpha) + 2)
                else:
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(i\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>i)\)', current_tag_text)
                    prev_id1 = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)

            elif re.search(r'^\([ivxl]+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                roman_cur_tag = p_tag
                ol_head = 1
                cap_alpha = 'A'

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(roman_ol)
                        prev_id1 = sec_alpha_cur_tag.get("id")
                    else:
                        prev_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:

                    roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([ivxl]+\)', '', current_tag_text)

                if re.search(rf'^\([ivx]+\)\s*\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivx]+\)\s*\(A\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[ivx]+)\)\s*\((?P<pid>A)\)', current_tag_text)
                    cap_alpha_id = f'{roman_cur_tag.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag1.group("cid")}{cur_tag1.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = 'B'

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                ol_head = 1
                cap_alpha_cur_tag = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    roman_cur_tag.append(cap_alpha_ol)
                    cap_alpha_id = roman_cur_tag.get("id")
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)

                if cap_alpha in ["H","K","U","W"]:
                    cap_alpha = chr(ord(cap_alpha) + 2)
                elif cap_alpha =='Z':
                    cap_alpha ='A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

                if re.search(rf'^\([A-Z]\)\s*\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s*\(I\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_roman_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[A-Z])\)\s*\((?P<pid>I)\)', current_tag_text)
                    prev_rom_id = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("cid")}{cur_tag1.group("pid")}'
                    cap_roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_roman_ol)


            elif re.search(rf'^\({cap_alpha2}{cap_alpha2}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_ol.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<p_id>{cap_alpha2}{cap_alpha2})\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{sec_alpha_id}{p_tag_id}'
                p_tag.string = re.sub(rf'^\({cap_alpha2}{cap_alpha2}\)', '', current_tag_text)
                cap_alpha2 = chr(ord(cap_alpha2) + 1)


            elif re.search(r'^\([IVX]+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_roman_tag = p_tag

                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)

                    cap_alpha_cur_tag.append(cap_roman_ol)
                    prev_rom_id = cap_alpha_cur_tag.get("id")

                else:
                    cap_roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[IVX]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_rom_id}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)


            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    if cap_roman_tag:
                        num_id1 = cap_roman_tag.get('id')
                        cap_roman_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

            elif re.search(rf'^\([a-z]\)', current_tag_text) and p_tag.name == "p":
                if sec_alpha_cur_tag:
                    p_tag.name = "li"
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    sec_alpha_cur_tag.append(p_tag)
                    sec_id = re.search(rf'^\((?P<s_id>[a-z])\)',current_tag_text).group("s_id")
                    p_tag["id"] = f'{sec_alpha_id}{sec_id}.1'
                    sec_alpha_cur_tag = p_tag
                    p_tag.string = re.sub(rf'^\([a-z]\)', '', current_tag_text)

            elif re.search(rf'^{ol_head}\.', current_tag_text) and p_tag.name == "p" and p_tag.b:
                p_tag.name = "li"
                ol_head_tag = p_tag
                main_sec_alpha1 = 'a'

                if re.search(r'^1\.', current_tag_text):
                    head_ol = self.soup.new_tag("ol")
                    p_tag.wrap(head_ol)
                    if cap_alpha1_cur_tag:
                        cap_alpha1_cur_tag.append(head_ol)
                        ol_head_id = cap_alpha1_cur_tag.get('id')
                    else:
                        ol_head_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    head_ol.append(p_tag)

                p_tag["id"] = f'{ol_head_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1


            elif re.search(rf'^{cap_alpha1}\.', current_tag_text) and p_tag.name == "p" and p_tag.b:
                p_tag.name = "li"
                cap_alpha1_cur_tag = p_tag
                ol_head = 1

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha1_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha1_ol)
                    cap_alpha1_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha1_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha1_id}{cap_alpha1}'
                p_tag.string = re.sub(rf'^{cap_alpha1}\.', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)


            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag1 = p_tag

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)
                    if ol_head_tag:
                        ol_head_tag.append(sec_alpha_ol1)
                        sec_alpha_id1 = f"{ol_head_tag.get('id')}ol{ol_count}"
                    else:
                        sec_alpha_id1 = p_tag.find_previous("li").get('id')
                        p_tag.find_previous("li").append(sec_alpha_ol1)

                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

            if re.search(r'^CASE NOTES', current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                ol_head = 1
                cap_alpha = 'A'
                cap_alpha_cur_tag = None
                num_count = 1
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha2 = 'a'
                cap_roman_tag = None
                cap_alpha1_cur_tag = None
                ol_head_tag = None
        print('ol tags added')




    def wrap_div_tags(self):
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


    def clean_html_and_add_cite(self):

        title_01 = ['6', '12', '15', '16', '17', '21', '22', '26', '32', '40', '42']
        title_02 = ['1', '2', '3', '4', '6', '7', '9', '11', '14']
        title_03 = ['1', '2', '3', '5', '8', '9']
        title_04 = ['10']
        title_05 = ['2', '3', '4', '6', '9', '13']
        title_06 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        title_07 = ['3', '4', '5', '11', '12', '13', '16', '19', '22']
        title_08 = ['2', '7']
        title_09 = ['1', '2', '3', '4', '5', '6', '7', '8', '12', '13', '15', '19', '24']
        title_10 = ['2', '3', '4', '5']
        title_11 = ['2', '5', '6', '7', '17', '19', '20', '23', '31', '34', '45']
        title_12 = ['2', '4', '5', '7', '8', '9']
        title_13 = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        title_14 = ['1', '2', '3', '4', '6', '8', '12']
        title_15 = ['1', '2', '3', '4', '5', '6', '7', '9', '11']
        title_16 = ['1', '4', '5', '6', '10', '9', '12']
        title_17 = ['1', '4', '7', '10', '14', '16', '17', '18', '19', '20', '21', '23', '29', '30', '31']
        title_18 = ['1', '3', '4', '5', '6', '7', '8', '9', '10']
        title_19 = ['2', '5', '7', '8', '9', '10', '11', '12', '13']
        title_20 = ['1', '2', '4', '5', '6']
        title_21 = ['2', '3', '4', '6', '7', '9', '10', '13', '16', '17', '18', '20', '23']
        title_22 = ['4', '5', '20', '21', '22', '23', '24', '29']
        title_23 = ['2', '3', '4', '6', '1', '5']
        title_24 = ['3']
        title_25 = ['1', '10']
        title_26 = ['2', '3', '6', '8', '9', '12', '13', '15', '16', '18', '19', '20', '22', '23', '29', '35', '38',
                    '40', '43', '48', ]
        title_27 = ['3', '4', '14']
        title_28 = ['7', '11']
        title_29 = ['1', '3', '6', '7']
        title_30 = ['2', '3', '5', '7']

        title_31 = ['1', '2', '5', '7', '8', '9', '18', '19']
        title_32 = ['3']
        title_33 = ['1', '7', '16', '20', '21', '24', '26', '28', '30', '33', '36', '39']
        title_34 = ['1', '14', '19', '21', '26']
        title_35 = ['1', '2', '4', '5', '7', '8', '9', '10', '11', '13', '22', '25']
        title_36 = ['1', '2', '6', '7', '8', '10']
        title_37 = ['2', '3', '5', '7', '8', '9', '12', '15', '16']
        title_38 = []
        title_39 = ['1', '2', '3', '6', '14', '15', '16', '17']
        title_40 = ['1', '12', '13', '14']
        title_41 = ['2', '3', '4', '5', '6', '7', '9', '11','12','13']
        title_42 = ['1', '2', '4']


        reg_dict = {'wy_code': r'(\d+ Wyo\. LEXIS \d+)'}
        cite_p_tags = []
        for tag in self.soup.findAll(lambda tag: re.search(r"§*\s*\d+-\d+-\d+"
                                                           r"|\d+ Wyo\. LEXIS \d+",
                                                           tag.get_text()) and tag.name == 'p'
                                                 and tag not in cite_p_tags):
            cite_p_tags.append(tag)

            text = str(tag)
            for match in set(
                    x[0] for x in re.findall(r'\b(\d{1,2}-\d(\w+)?-\d+(\.\d+)?(\s*(\(\w+\))+)?)', tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                tag.clear()

                id_reg = re.search(r'(?P<title>\w+)-(?P<chap>\w+)-(?P<sec>\d+(\.\d+)?)', match.strip())
                title = id_reg.group("title").strip()
                section = re.sub(r'(\(\w+\))+', '', match).strip()
                target = "_self"
                title_id = f'title_{title.zfill(2)}'
                sec_id = id_reg.group("sec")
                ar_id = sec_id[:2]
                ar_id1 = sec_id[:1]

                if title.strip() != self.title:
                    if int(title.zfill(2)) < 43:
                        if id_reg.group("chap") in eval(title_id):
                            if len(id_reg.group("sec")) == 3:
                                a_id = f'gov.wy.code.title.{title.zfill(2)}.html#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}a{ar_id1.zfill(2)}s{section}'

                            else:
                                a_id = f'gov.wy.code.title.{title.zfill(2)}.html#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}a{ar_id}s{section}'
                        else:
                            a_id = f'gov.wy.code.title.{title.zfill(2)}.html#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'
                        target = "_blank"

                else:
                        if id_reg.group("chap") in eval(title_id):
                            if len(id_reg.group("sec")) == 3:
                                a_id = f'#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}a{ar_id1.zfill(2)}s{section}'
                            else:
                                a_id = f'#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}a{ar_id}s{section}'
                        else:
                            a_id = f'#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'

                if ol_reg := re.search(r'(\(\w+\))+', match.strip()):
                        ol_num = re.sub(r'\(|\)', '', ol_reg.group())
                        a_id = f'{a_id}ol1{ol_num}'


                text = re.sub(fr'\s{re.escape(match)}',
                                  f' <cite class="octn"><a href="{a_id}" target="{target}">{match}</a></cite>', inside_text,
                                  re.I)
                tag.append(text)

            for match in set(
                        x for x in re.findall(r'\d+ Wyo\. LEXIS \d+',
                                   tag.get_text())):

                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                tag.clear()
                text = re.sub(re.escape(match), f'<cite class="wy_code">{match}</cite>', inside_text, re.I)
                tag.append(text)


        main_tag = self.soup.new_tag('main')
        chap_nav = self.soup.find('nav')
        tag_to_wrap = chap_nav.find_next_sibling()
        while True:
            next_tag = tag_to_wrap.find_next_sibling()
            main_tag.append(tag_to_wrap)
            if not next_tag:
                chap_nav.insert_after(main_tag)
                break
            tag_to_wrap = next_tag

        print('added cites')

        clss = re.compile(r'p\d+')
        for all_tag in self.soup.findAll(class_=clss):
            del all_tag["class"]

        for tag in self.soup.findAll():
            if len(tag.contents) == 0:
                if tag.name == 'meta':
                    if tag.attrs.get('http-equiv') == 'Content-Style-Type':
                        tag.decompose()
                        continue
                    self.meta_tags.append(tag)
                elif tag.name == 'br':
                    if not tag.parent or tag in tag.parent.contents:
                        tag.decompose()
                continue

            if len(tag.get_text(strip=True)) == 0:
                tag.extract()



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

        with open(f"../../cic-code-wy/transforms/wy/ocwy/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str.replace('& ','&amp; '))



    def create_case_note_nav(self):
            cap_alpha = None

            for case_tag in self.soup.find_all("p", class_=[self.class_regex["head4"]]):
                if re.search(r'^[IVX]+\. ', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[IVX]+)\.', case_tag.text.strip()).group("cid").lower()
                    rom_id = f"{case_tag.find_previous({'h4','h3'}).get('id')}-{case_id}"
                    nav_link["href"] = f"#{case_tag.find_previous({'h4','h3'}).get('id')}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list
                    case_tag["class"] = "casenote"
                    cap_alpha = 'A'

                elif cap_alpha:
                    if re.search(fr'^{cap_alpha}\.', case_tag.text.strip()):
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(case_tag.text)
                        case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid").lower()
                        alpha_id = f"{rom_id}-{case_id}"
                        nav_link["href"] = f"#{rom_id}-{case_id}"

                        nav_list.append(nav_link)
                        case_tag.contents = nav_list
                        case_tag["class"] = "casenote"
                        cap_alpha = chr(ord(cap_alpha) + 1)

                    elif re.search(r'^[0-9]+\.', case_tag.text.strip()):
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(case_tag.text)
                        case_id = re.search(r'^(?P<cid>[0-9]+)\.', case_tag.text.strip()).group("cid").lower()
                        digit_id = f"{alpha_id}-{case_id}"
                        nav_link["href"] = f"#{alpha_id}-{case_id}"
                        nav_list.append(nav_link)
                        case_tag.contents = nav_list
                        case_tag["class"] = "casenote"



    def create_case_note_ul(self):
        for case_tag in self.soup.find_all(class_='casenote'):
            case_tag.name = "li"
            if re.search(r'^[IVX]+\. ', case_tag.a.text.strip()):
                rom_tag = case_tag
                if re.search(r'^I\.', case_tag.a.text.strip()):
                    rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(rom_ul)
                else:
                    rom_ul.append(case_tag)

            elif re.search(r'^[A-Z]\. ', case_tag.a.text.strip()):
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
        if re.search('constitution', self.html_file_name):
            self.class_regex = {'head1': r'^Constitution of the State of Wyoming|THE CONSTITUTION OF THE UNITED STATES OF AMERICA', 'ul': r'^(PREAMBLE|Preamble)','head2':'Article \d\.',
                                  'head4': '^History\.', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$','head':'^Section added\.',
                                  'head3': r'^§ \d|^sec\.|^Section \d',}

            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_chapter_section_nav()
            self.convert_paragraph_to_alphabetical_ol_tags()
            self.create_case_note_nav()
            self.create_case_note_ul()
            self.wrap_div_tags()

        else:
            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_chapter_section_nav()
            self.convert_paragraph_to_alphabetical_ol_tags()
            self.create_case_note_nav()
            self.create_case_note_ul()
            self.wrap_div_tags()

        self.clean_html_and_add_cite()
        self.write_soup_to_file()
        print(f'finished {self.html_file_name}')
        print(datetime.now() - start_time)

