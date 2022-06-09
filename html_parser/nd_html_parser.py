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
import os
import os.path


class NDParseHtml(ParserBase):

    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.previous = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.class_regex = {'head1': r'TITLE \d+', 'ul': r'^CHAPTER \d+(\.\d+)*-\d+',
                            'head2': r'^CHAPTER \d+(\.\d+)*-\d+',
                            'head4': '^Source:',
                            'head3': '^\d+(\.\d+)*-\d+-\d+\.(\d+\.)*',
                            'junk1': '^Annotations$', 'NTD': '^Notes to Decisions'}

        self.watermark_text = """Release {0} of the Official Code of North Dakota Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
        """
        self.meta_tags = []
        self.tag_to_unwrap = []
        self.head4_list = ['Derivation:', 'Notes to Decisions', 'Cross-References\.', 'Law Reviews\.',
                           'DECISIONS UNDER PRIOR LAW', 'Source:', 'Decisions under Prior Law',
                           'DECISIONS UNDER PRIOR PROVISIONS']
        self.c_nav_count = 0
        self.a_nav_count = 0
        self.s_nav_count = 0
        self.count = 1
        self.head4count = 1
        self.start_parse()

    def create_page_soup(self):
        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """
        with open(f'../transforms/nd/ocnd/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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

        if title := re.search(r'TITLE\s(?P<title>\d+(\.\d+)*)',
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

    def replace_tags(self):
        watermark_p = None
        title_tag = None
        header4_tag = None
        note_to_decision_list = []
        cur_head_list = []
        chap_id_list = []
        note_to_decision_id_list = []
        chap_count = 1
        cur_id_list = []
        art_ids_list = []
        cap_alpha = 'A'
        cap_roman = "I"
        alpha = None
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        head4_list = ['Revision of title. —', 'Cross references. —', 'Law reviews. —', 'Editor\'s notes. —',
                      'History.', 'Effective dates. —']

        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if re.search('constitution\.nd', self.html_file_name):
                    self.title_id = 'constitution-nd'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id = 'constitution-us'

                Article_pattern = re.compile(r'^ARTICLE\s(?P<chap_id>\d+([IVX]+)*) ')

                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^CONSTITUTION OF NORTH DAKOTA|^CONSTITUTION OF THE UNITED STATES OF AMERICA',
                                 header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.wrap(self.soup.new_tag("nav"))
                        header_tag['id'] = self.title_id
                        watermark_p = self.soup.new_tag('p', Class='transformation')
                        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                                        datetime.now().date())
                        self.soup.find("nav").insert(0, watermark_p)

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE [IVX]+', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = f"{header_tag.find_previous('h1').get('id')}a{re.search(r'^ARTICLE (?P<ar_id>[IVX]+)', header_tag.text.strip()).group('ar_id').zfill(2)}"

                        if article_id in art_ids_list:
                            header_tag[
                                'id'] = f"{article_id.zfill(2)}.1"
                        else:
                            header_tag[
                                'id'] = f"{article_id.zfill(2)}"

                        art_ids_list.append(article_id)

                    elif re.search(r'^ARTICLE\s\d+([A-Z])*', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^ARTICLE\s(?P<s_id>\d+([A-Z])*)', header_tag.text.strip()).group('s_id')

                        article_id = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}a{sec_id.zfill(2)}"

                        if article_id in art_ids_list:
                            header_tag[
                                'id'] = f"{article_id.zfill(2)}.1"
                        else:
                            header_tag[
                                'id'] = f"{article_id.zfill(2)}"

                        art_ids_list.append(article_id)
                        header4_tag = None
                        self.count1 = 1
                        header_tag['class'] = "article"

                    elif re.search(r'^SCHEDULE|^PREAMBLE|^TRANSITION SCHEDULE|^Preamble|^ARTICLES OF AMENDMENT',
                                   header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.sub(r'[\s\W]+', '', header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}-{article_id.zfill(2)}"

                    elif re.search(r'^Section \d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^Section\s(?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                        header4_tag = None
                        self.count1 = 1

                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if re.search(r'^Section\s\d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^Section\s(?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                        header4_tag = None
                        self.count1 = 1

                    elif re.search(r'^§\s\d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^§\s(?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3', class_='article').get('id')}s{sec_id.zfill(2)}"
                        header4_tag = None
                        self.count1 = 1

                    else:
                        head3_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                        header_tag.name = "h3"
                        header_tag[
                            'id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}-{head3_text}"
                        header4_tag = None
                        self.count1 = 1

                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^[A-Za-z“]+|^—|^[IVX]+\.', header_tag.text.strip()) \
                            and header4_tag \
                            and re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR PROVISIONS',
                                          header_tag.find_previous("h4").text.strip()) \
                            and not re.search(r'^Analysis', header_tag.text.strip()):
                        header_tag.name = "li"
                        header_tag['class'] = "note"
                        note_to_decision_list.append(header_tag.text.strip())

                    elif re.search(r'^Source:', header_tag.text.strip()) and header_tag.b:
                        new_tag = self.soup.new_tag("h4")
                        NTD_rom_head_tag = None
                        NTD_head_id = None
                        new_tag.string = header_tag.b.text.strip()
                        curr_head4_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source"

                        if curr_head4_id in cur_head_list:
                            new_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source.{self.count1}"
                            self.count1 += 1
                        else:
                            new_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source"

                        cur_head_list.append(curr_head4_id)

                        header_tag.insert_before(new_tag)
                        header_tag.b.clear()

                elif header_tag.get("class") == [self.class_regex["NTD"]]:
                    if header_tag.text.strip() in self.head4_list:
                        header_tag.name = "h4"
                        NTD_rom_head_tag = None
                        NTD_head_id = None
                        h4_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                        curr_tag_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"
                        if curr_tag_id in cur_id_list:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}.{self.head4count}"
                            self.head4count += 1
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"

                        cur_id_list.append(header_tag['id'])
                        header4_tag = header_tag

                    elif header_tag.text.strip() in note_to_decision_list:
                        if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            NTD_rom_head_tag = header_tag
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                            NTD_rom_head_id = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            if NTD_rom_head_id in note_to_decision_id_list:
                                header_tag['id'] = f"{NTD_rom_head_id}.1"
                            else:
                                header_tag['id'] = f"{NTD_rom_head_id}"
                            note_to_decision_id_list.append(NTD_rom_head_id)

                        elif re.search(r'^—\s*—', header_tag.text.strip()):
                            header_tag.name = "h5"
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                            NTD_inner_head_id = f"{NTD_inr_head_id}-{NTD_text}"

                            if NTD_inner_head_id in note_to_decision_id_list:
                                header_tag['id'] = f"{NTD_inr_head_id}-{NTD_text}.1"
                            else:
                                header_tag['id'] = f"{NTD_inr_head_id}-{NTD_text}"

                            note_to_decision_id_list.append(NTD_inner_head_id)

                        elif re.search(r'^—', header_tag.text.strip()):
                            header_tag.name = "h5"
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                            NTD_inr_head_id = f"{NTD_head_id}-{NTD_text}"

                            if NTD_head_id:
                                if NTD_inr_head_id in note_to_decision_id_list:
                                    header_tag['id'] = f"{NTD_head_id}-{NTD_text}.1"
                                else:
                                    header_tag['id'] = f"{NTD_head_id}-{NTD_text}"

                            else:
                                header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            note_to_decision_id_list.append(NTD_inr_head_id)
                            NTD_inr_head_id = header_tag['id']

                        else:
                            header_tag.name = "h5"
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()

                            if NTD_rom_head_tag:
                                NTD_head_id = f"{NTD_rom_head_id}-{NTD_text}"
                            else:
                                NTD_head_id = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            if NTD_head_id in note_to_decision_id_list:
                                header_tag['id'] = f"{NTD_head_id}.1"
                            else:
                                header_tag['id'] = f"{NTD_head_id}"

                            note_to_decision_id_list.append(NTD_head_id)

                elif header_tag.get("class") == [self.class_regex["ul"]]:
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


            # titlefiles
            else:
                title_pattern = re.compile(r'^TITLE\s(?P<title_id>\d+(\.\d+)*)')
                chapter_pattern = re.compile(r'^CHAPTER\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)')
                section_pattern = re.compile(r'^(?P<sec_id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)\.')
                article_pattern = re.compile(r'^Article (?P<aid>[IVX]+)')
                part_pattern = re.compile(r'^Part (?P<pid>\d+)')
                part_rom_pattern = re.compile(r'^Part (?P<pid>[IVX]+)')

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
                        chap_count = 1

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if chapter_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = chapter_pattern.search(header_tag.text.strip()).group('chapid')
                        if header_tag.find_previous('h2', class_="articleh2"):
                            chap_id1 = f"{header_tag.find_previous('h2', class_='articleh2').get('id')}c{chapter_id.zfill(2)}"
                            if chap_id1 in chap_id_list:
                                header_tag[
                                    'id'] = f"{header_tag.find_previous('h2', class_='articleh2').get('id')}c{chapter_id.zfill(2)}.{chap_count}"
                                chap_count += 1
                            else:
                                header_tag[
                                    'id'] = f"{header_tag.find_previous('h2', class_='articleh2').get('id')}c{chapter_id.zfill(2)}"
                            chap_id_list.append(chap_id1)
                        else:
                            chap_id2 = f"{header_tag.find_previous('h1').get('id')}c{chapter_id.zfill(2)}"
                            if chap_id2 in chap_id_list:
                                header_tag[
                                    'id'] = f"{header_tag.find_previous('h1').get('id')}c{chapter_id.zfill(2)}.{chap_count}"
                                chap_count += 1
                            else:
                                header_tag['id'] = f"{header_tag.find_previous('h1').get('id')}c{chapter_id.zfill(2)}"
                            chap_id_list.append(chap_id2)
                        header_tag["class"] = "chaph2"

                        chap_count = 1

                    elif article_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = article_pattern.search(header_tag.text.strip()).group('aid')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{chapter_id.zfill(2)}"
                        header_tag["class"] = "articleh2"

                    elif part_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = part_pattern.search(header_tag.text.strip()).group('pid')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2', class_='chaph2').get('id')}p{chapter_id.zfill(2)}"
                        header_tag["class"] = "parth2"

                    elif part_rom_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = part_rom_pattern.search(header_tag.text.strip()).group('pid')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}p{chapter_id.zfill(2)}"
                        header_tag["class"] = "parth2"

                    self.count = 1

                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if section_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        section_id = section_pattern.search(header_tag.text.strip()).group('sec_id')
                        curr_head_id = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"

                        if curr_head_id in cur_head_list:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}.{self.count:02}"
                            self.count += 1
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"

                        cur_head_list.append(curr_head_id)
                        header_tag["class"] = "section"
                        self.head4count = 1
                        header4_tag = None
                        self.count1 = 1

                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^[A-Za-z“"]+|^—', header_tag.text.strip()) \
                            and header4_tag \
                            and not re.search(r'^Analysis', header_tag.text.strip()) \
                            and re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR LAW',
                                          header_tag.find_previous("h4").text.strip(), re.I):
                        header_tag.name = "li"
                        header_tag['class'] = "note"
                        note_to_decision_list.append(header_tag.text.strip())

                    elif re.search(r'^Source:', header_tag.text.strip()) and header_tag.b:
                        new_tag = self.soup.new_tag("h4")
                        new_tag.string = header_tag.b.text.strip()
                        curr_head4_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source"

                        if curr_head4_id in cur_head_list:
                            new_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source.{self.count1}"
                            self.count1 += 1
                        else:
                            new_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-Source"

                        cur_head_list.append(curr_head4_id)

                        header_tag.insert_before(new_tag)
                        header_tag.b.clear()

                elif header_tag.get("class") == [self.class_regex["NTD"]]:
                    if header_tag.text.strip() in self.head4_list:
                        header_tag.name = "h4"
                        h4_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                        curr_tag_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"
                        if curr_tag_id in cur_id_list:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}.{self.head4count}"
                            self.head4count += 1
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"

                        cur_id_list.append(header_tag['id'])
                        header4_tag = header_tag
                        NTD_head_id = None

                    elif header_tag.text.strip() in note_to_decision_list:
                        if re.search(r'^—', header_tag.text.strip()):
                            header_tag.name = "h5"
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                            NTD_inr_head_id = f"{NTD_head_id}-{NTD_text}"

                            if NTD_head_id:
                                if NTD_inr_head_id in note_to_decision_id_list:
                                    header_tag['id'] = f"{NTD_head_id}-{NTD_text}.1"
                                else:
                                    header_tag['id'] = f"{NTD_head_id}-{NTD_text}"

                            else:
                                header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            note_to_decision_id_list.append(NTD_inr_head_id)

                        else:
                            header_tag.name = "h5"
                            NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                            NTD_head_id = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            if NTD_head_id in note_to_decision_id_list:
                                header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}.1"
                            else:
                                header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                            note_to_decision_id_list.append(NTD_head_id)

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if chapter_pattern.search(header_tag.text.strip()) or \
                            section_pattern.search(header_tag.text.strip()) or \
                            article_pattern.search(header_tag.text.strip()) or \
                            part_pattern.search(header_tag.text.strip()) or \
                            part_rom_pattern.search(header_tag.text.strip()):
                        header_tag.name = "li"

                        if header_tag.find_previous().name == "li":
                            header_tag.find_previous("nav").append(header_tag)

                        else:
                            if header_tag.find_previous("h2"):
                                nav_tag = self.soup.new_tag("nav")
                                header_tag.wrap(nav_tag)
                            else:
                                header_tag.find_previous("nav").append(header_tag)

                        if header_tag.find_previous().name == "li":
                            ul_tag.append(header_tag)

                        else:
                            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            header_tag.wrap(ul_tag)

        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        self.meta_tags.append(stylesheet_link_tag)

        print('tags replaced')

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num, cnav):
        nav_list = []
        nav_href_list = []
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
        section_pattern = re.compile(r'^(?P<sec_id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)\.')
        chapter_pattern = re.compile(r'^CHAPTER\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)')
        article_pattern = re.compile(r'^Article (?P<aid>[IVX]+)')
        part_pattern = re.compile(r'^Part (?P<pid>\d+)')
        part_rom_pattern = re.compile(r'^Part (?P<pid>[IVX]+)')

        for list_item in self.soup.find_all():
            if list_item.name == "li" and list_item.get("class") == [self.class_regex['ul']]:
                if re.search('constitution', self.html_file_name):
                    if re.search(r'^ARTICLE\s[IVX]+', list_item.text.strip()):
                        chap_num = re.search(r'^ARTICLE\s(?P<chap>[IVX]+)', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "a"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^PREAMBLE|^TRANSITION SCHEDULE|^SCHEDULE|^Preamble|^ARTICLES OF AMENDMENT',
                                   list_item.text.strip()):
                        article_id = re.sub(r'[\s\W]+', '', list_item.text.strip()).lower()
                        sub_tag = "-"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, article_id, sub_tag, prev_id, None, cnav)

                    elif re.search(r'^(Section|§)\s\d+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(Section|§)\s(?P<chap>\d+)\.', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "s"
                        prev_id = list_item.find_previous({'h3', 'h2'}).get("id")
                        self.a_nav_count += 1
                        cnav = f'snav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^ARTICLE\s\d+([A-Z])*', list_item.text.strip()):
                        chap_num = re.search(r'^ARTICLE\s(?P<chap>\d+([A-Z])*)', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "a"
                        prev_id = list_item.find_previous({'h2', 'h1'}).get("id")
                        self.a_nav_count += 1
                        cnav = f'snav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^Section \d+|to 25\. 1 to 25\.', list_item.text.strip()):
                        chap_num = re.sub(r'[\W\s]+', '', list_item.text.strip())
                        sub_tag = "-"
                        prev_id = list_item.find_previous('h2').get("id")
                        self.a_nav_count += 1
                        cnav = f'snav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)
                else:
                    if section_pattern.search(list_item.text.strip()):
                        chap_id = section_pattern.search(list_item.text.strip()).group('sec_id')
                        sub_tag = "s"
                        prev_id = list_item.find_previous({'h2', 'h1'}).get("id")
                        self.s_nav_count += 1
                        cnav = f'snav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None, cnav)

                    elif chapter_pattern.search(list_item.text.strip()):
                        chap_id = chapter_pattern.search(list_item.text.strip()).group('chapid')
                        sub_tag = "c"

                        if list_item.find_previous('h2', class_="articleh2"):
                            prev_id = list_item.find_previous('h2', class_="articleh2").get("id")
                        else:
                            prev_id = list_item.find_previous('h1').get("id")
                        self.s_nav_count += 1
                        cnav = f'cnav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None, cnav)

                    elif article_pattern.search(list_item.text.strip()):
                        chap_id = article_pattern.search(list_item.text.strip()).group('aid')
                        sub_tag = "a"
                        prev_id = list_item.find_previous('h1').get("id")
                        self.a_nav_count += 1
                        cnav = f'cnav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None, cnav)

                    elif part_pattern.search(list_item.text.strip()):
                        part_id = part_pattern.search(list_item.text.strip()).group('pid')
                        sub_tag = "p"
                        prev_id = list_item.find_previous('h2', class_='chaph2').get("id")
                        self.a_nav_count += 1
                        cnav = f'pnav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, part_id.zfill(2), sub_tag, prev_id, None, cnav)

                    elif part_rom_pattern.search(list_item.text.strip()):
                        part_id = part_rom_pattern.search(list_item.text.strip()).group('pid')
                        sub_tag = "p"
                        prev_id = list_item.find_previous('h1').get("id")
                        self.a_nav_count += 1
                        cnav = f'pnav{self.a_nav_count:02}'
                        self.set_chapter_section_nav(list_item, part_id.zfill(2), sub_tag, prev_id, None, cnav)

            elif list_item.name in ['h1', 'h2']:
                self.c_nav_count = 0
                self.s_nav_count = 0
                self.a_nav_count = 0

    def convert_paragraph_to_alphabetical_ol_tags_con(self):
        main_sec_alpha = 'a'
        num_count = 1
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        num_cur_tag = None
        num_cur_tag1 = None
        sec_alpha_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha = "a"

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    ol_count += 1
                else:
                    num_ol.append(p_tag)

                p_tag["id"] = f'{num_id}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

                if re.search(r'^\([0-9]+\)\s*\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*\(a\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*\((?P<pid>a)\)', current_tag_text)

                    sec_alpha_id = f'{num_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag1.group("pid")}'
                    sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = "b"

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_cur_tag.get('id')
                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    ol_count += 1
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

            elif re.search(rf'^\([a-z]\d+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                sec_alpha_ol.append(p_tag)
                li_id = re.search(rf'^\((?P<id>[a-z]\d+)\)', current_tag_text).group("id")
                p_tag["id"] = f'{sec_alpha_id}-{li_id}'
                p_tag.string = re.sub(rf'^\({li_id}\)', '', current_tag_text)

            elif re.search(rf'^\(\d+[a-z]\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                num_ol.append(p_tag)
                li_id = re.search(rf'^\((?P<id>\d+[a-z])\)', current_tag_text).group("id")
                p_tag["id"] = f'{num_id}-{li_id}'
                p_tag.string = re.sub(rf'^\({li_id}\)', '', current_tag_text)

            if re.search(r'^CASE NOTES|^"Sec\. \d+\.', current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                ol_count = 1
                num_count = 1
                num_cur_tag = None
                main_sec_alpha = 'a'
                num_cur_tag1 = None

        print('ol tags added')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        inner_sec_alpha = 'a'
        ol_head = 1
        num_count = 1
        inner_num_count = 1
        ol_count = 1
        main_sec_alpha = 'a'
        sec_alpha = 'a'
        sec_alpha_cur_tag = None
        inr_sec_alpha_cur_tag = None
        num_cur_tag = None
        inr_num_cur_tag = None
        ol_head_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha = 'a'
                inr_sec_alpha_cur_tag = None
                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_cur_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    ol_count += 1
                else:
                    num_ol.append(p_tag)
                p_tag["id"] = f'{num_cur_id}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count = num_count + 1

                if re.search(rf'^\d+\.\s*a\.', current_tag_text):
                    p_tag.name = "li"
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\d+\.\s*a\.', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    sec_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = "b"
                    inner_num_count = 1

            elif re.search(rf'^{main_sec_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                inner_num_count = 1
                inr_sec_alpha_cur_tag = None
                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    num_cur_tag.append(sec_alpha_ol)
                    sec_alpha_id = num_cur_tag.get('id')
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^{main_sec_alpha}\.', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\D+\.\s\(1\)', current_tag_text):
                    p_tag.name = "li"
                    inr_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\D+\.\s\(1\)', '', current_tag_text)
                    inr_num_cur_tag = li_tag
                    inr_num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    inr_num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_num_ol)
                    inner_num_count = 2

            elif re.search(rf'^{sec_alpha}{sec_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                inner_num_count = 1
                inr_sec_alpha_cur_tag = None
                sec_alpha_ol.append(p_tag)
                sec_alpha_id = num_cur_tag.get('id')
                p_tag["id"] = f'{sec_alpha_id}{sec_alpha}{sec_alpha}'
                p_tag.string = re.sub(rf'^{sec_alpha}{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

            elif re.search(rf'^\({inner_num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_num_cur_tag = p_tag
                inner_sec_alpha = 'a'
                if re.search(r'^\(1\)', current_tag_text):
                    inr_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inr_num_ol)
                    if inr_sec_alpha_cur_tag:
                        inr_sec_alpha_cur_tag.append(inr_num_ol)
                        inr_num_id = inr_sec_alpha_cur_tag.get('id')
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(inr_num_ol)
                        inr_num_id = sec_alpha_cur_tag.get('id')
                    else:
                        inr_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inr_num_ol.append(p_tag)
                p_tag["id"] = f'{inr_num_id}{inner_num_count}'
                p_tag.string = re.sub(rf'^\({inner_num_count}\)', '', current_tag_text)
                inner_num_count = inner_num_count + 1

                if re.search(rf'^\(\d+\)\s*\(a\)', current_tag_text):
                    p_tag.name = "li"
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\(a\)', '', current_tag_text)
                    inr_sec_alpha_cur_tag = li_tag
                    inr_sec_alpha_id = f'{inr_num_cur_tag.get("id")}'
                    li_tag["id"] = f'{inr_num_cur_tag.get("id")}a'
                    inr_sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_sec_alpha_ol)
                    inner_sec_alpha = 'b'
                    ol_head = 1

            elif re.search(rf'^\({inner_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_sec_alpha_cur_tag = p_tag
                ol_head = 1
                if re.search(r'^\(a\)', current_tag_text):
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inr_sec_alpha_ol)
                    if inr_num_cur_tag:
                        inr_num_cur_tag.append(inr_sec_alpha_ol)
                        inr_sec_alpha_id = inr_num_cur_tag.get('id')
                    else:
                        inr_sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inr_sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inr_sec_alpha_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}\)', '', current_tag_text)
                inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

                if re.search(rf'^\(\D\)\s*\[1\]', current_tag_text):
                    p_tag.name = "li"
                    inr_head_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\D\)\s*\[1\]', '', current_tag_text)
                    ol_head_cur_tag = li_tag
                    ol_head_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    inr_head_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_head_ol)
                    ol_head = 2

            elif re.search(rf'^\[{ol_head}\]', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                ol_head_cur_tag = p_tag
                if re.search(r'^\[1\]', current_tag_text):
                    inr_head_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inr_head_ol)
                    inr_sec_alpha_cur_tag.append(inr_head_ol)
                    ol_head_id = inr_sec_alpha_cur_tag.get('id')
                else:
                    inr_head_ol.append(p_tag)

                p_tag["id"] = f'{ol_head_id}{ol_head}'
                p_tag.string = re.sub(rf'^\[{ol_head}\]', '', current_tag_text)
                ol_head = ol_head + 1

            if p_tag.name in ['h3', 'h4', 'h5']:
                inner_sec_alpha = 'a'
                ol_head = 1
                num_count = 1
                inner_num_count = 1
                ol_count = 1
                main_sec_alpha = 'a'
                sec_alpha_cur_tag = None
                inr_sec_alpha_cur_tag = None
                num_cur_tag = None
                inr_num_cur_tag = None
                ol_head_cur_tag = None

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
                            if tag_to_wrap:
                                next_tag = tag_to_wrap.find_next_sibling()
                            else:
                                break
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

    def clean_html_and_add_cite(self):

        cite_p_tags = []
        for tag in self.soup.findAll(
                lambda tag: re.search(r"\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*\."
                                      r"|Chapter\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)"
                                      r"|N\.D\. LEXIS \d+",
                                      tag.get_text()) and tag.name == 'p'
                            and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            text = str(tag)

            for match in set(
                    x[0] for x in re.findall(r"(\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*"
                                             r"|Chapter\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*))",
                                             tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>|<p.+>', '', text, re.DOTALL)

                if re.search(r'Chapter\s\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*', match.strip()):
                    id_reg = re.search(r'Chapter\s(?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*([A-Z])*)',
                                       match.strip())
                else:
                    id_reg = re.search(
                        r'(?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*-\d+(\.\d+)*)',
                        match.strip())

                title = id_reg.group("title").strip()
                title_id = f'{title.zfill(2)}'

                if os.path.isfile(
                        f"../../code-nd/transforms/nd/ocnd/r{self.release_number}/gov.nd.code.title.{title_id}.html"):
                    with open(
                            f"../../code-nd/transforms/nd/ocnd/r{self.release_number}/gov.nd.code.title.{title_id}.html",
                            'r') as firstfile:

                        for line in firstfile:

                            if re.search(rf'id=".+(s|c){id_reg.group("cite")}">$', line.strip()):
                                tag.clear()
                                head_id = re.search(rf'id="(?P<h_id>.+(s|c){id_reg.group("cite")})">$', line.strip())

                                if title_id == self.title_id:
                                    target = "_self"
                                    a_id = f'#{head_id.group("h_id")}'
                                else:
                                    target = "_blank"
                                    a_id = f'gov.nd.stat.title.{title_id}.html#{head_id.group("h_id")}'

                                text = re.sub(fr'\s{re.escape(match)}',
                                              f' <cite class="ocnd"><a href="{a_id}" target="{target}">{match}</a></cite>',
                                              inside_text,
                                              re.I)
                                tag.append(text)

            for match in set(
                    x for x in re.findall(r'N\.D\. LEXIS \d+',
                                          tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                tag.clear()
                text = re.sub(re.escape(match), f'<cite class="nd_code">{match}</cite>', inside_text, re.I)
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

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

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
        with open(f"../../code-nd/transforms/nd/ocnd/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str.replace('& ', '&amp; '))

    def create_Notes_to_Decisions(self):
        note_to_dec_ids: list = []
        NTD_id1 = None
        NTD_id = None

        for NTD_tag in self.soup.find_all():
            if NTD_tag.name == "h4" and re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR LAW',
                                                  NTD_tag.text.strip(), re.I):
                NTD_id1 = None
                NTD_id = None

            elif NTD_tag.name == "li" and NTD_tag.get('class') == 'note':
                if re.search(r'^[IVX]+\.', NTD_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text1 = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()
                    NTD_id1 = f"{NTD_tag.find_previous('h4').get('id')}-{NTD_text1}"
                    nav_link_href = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}"

                    if nav_link_href in note_to_dec_ids:
                        nav_link["href"] = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}.1"
                    else:
                        nav_link["href"] = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}"

                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                elif re.search(r'^—', NTD_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()
                    nav_link_href = f"#{NTD_id}-{NTD_text}"

                    if NTD_id:
                        if nav_link_href in note_to_dec_ids:
                            nav_link["href"] = f"#{NTD_id}-{NTD_text}.1"
                        else:
                            nav_link["href"] = f"#{NTD_id}-{NTD_text}"

                    else:
                        nav_link["href"] = f"#{NTD_tag.find_previous('h4').get('id')}-{NTD_text}"
                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                else:
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()

                    if NTD_id1:
                        NTD_id = f"{NTD_id1}-{NTD_text}"
                    else:
                        NTD_id = f"{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text}"

                    if NTD_id in note_to_dec_ids:
                        nav_link["href"] = f"#{NTD_id}.1"
                    else:
                        nav_link["href"] = f"#{NTD_id}"

                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                note_to_dec_ids.append(NTD_id)

    def create_Notes_to_Decisions_ul(self):
        note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_head_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_inner_ul1 = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_head_tag = None
        note_to_dec_inr_tag = None
        note_to_dec_tag = None

        for NTD_tag in self.soup.find_all("li", class_='note'):

            if re.search(r'^[IVX]+\.', NTD_tag.a.text.strip()):
                note_to_dec_head_tag = NTD_tag
                if re.search(r'I\.', NTD_tag.a.text.strip()):
                    note_to_dec_head_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    NTD_tag.wrap(note_to_dec_head_ul)
                else:
                    note_to_dec_head_ul.append(NTD_tag)

            elif re.search(r'^—\s*—', NTD_tag.a.text.strip()):
                if re.search(r'^—\s*—', NTD_tag.find_previous().text.strip()):
                    note_to_dec_inner_ul1.append(NTD_tag)
                else:
                    note_to_dec_inner_ul1 = self.soup.new_tag("ul", **{"class": "leaders"})
                    NTD_tag.wrap(note_to_dec_inner_ul1)
                    note_to_dec_inr_tag.append(note_to_dec_inner_ul1)

            elif re.search(r'^—', NTD_tag.a.text.strip()):
                note_to_dec_inr_tag = NTD_tag
                if re.search(r'^—', NTD_tag.find_previous().text.strip()):
                    note_to_dec_inner_ul.append(NTD_tag)
                elif NTD_tag.find_previous("p"):
                    if re.search(r'^Analysis', NTD_tag.find_previous("p").text.strip()):
                        note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_inner_ul)
                else:
                    note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    NTD_tag.wrap(note_to_dec_inner_ul)
                    note_to_dec_tag.append(note_to_dec_inner_ul)

            else:
                note_to_dec_tag = NTD_tag
                if re.search(r'^Notes to Decisions|^Analysis|^DECISIONS UNDER PRIOR LAW',
                             NTD_tag.find_previous().text.strip(), re.I):
                    note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    NTD_tag.wrap(note_to_dec_ul)

                    if note_to_dec_head_tag:
                        note_to_dec_head_tag.append(note_to_dec_ul)

                else:
                    if NTD_tag.find_previous("p"):
                        if re.search(r'^Analysis', NTD_tag.find_previous("p").text.strip()):
                            note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            NTD_tag.wrap(note_to_dec_ul)
                    else:
                        note_to_dec_ul.append(NTD_tag)

    def create_Notes_to_Decisions_ul_con(self):
        note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_head_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_inner_ul1 = self.soup.new_tag("ul", **{"class": "leaders"})
        note_to_dec_head_tag = None
        note_to_dec_inr_tag = None
        note_to_dec_tag = None

        for NTD_tag in self.soup.find_all():
            if NTD_tag.name == "h4" and re.search(r'^Notes to Decisions|'
                                                  r'^DECISIONS UNDER PRIOR LAW|'
                                                  r'^DECISIONS UNDER PRIOR PROVISIONS',
                                                  NTD_tag.text.strip(), re.I):
                note_to_dec_head_tag = None

            elif NTD_tag.name == "li" and NTD_tag.get('class') == 'note':
                if re.search(r'^[IVX]+\.', NTD_tag.a.text.strip()):

                    note_to_dec_head_tag = NTD_tag
                    if re.search(r'^I\.', NTD_tag.a.text.strip()):
                        note_to_dec_head_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_head_ul)
                    else:
                        note_to_dec_head_ul.append(NTD_tag)

                elif re.search(r'^—\s*—', NTD_tag.a.text.strip()):
                    if re.search(r'^—\s*—', NTD_tag.find_previous().text.strip()):
                        note_to_dec_inner_ul1.append(NTD_tag)
                    else:
                        note_to_dec_inner_ul1 = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_inner_ul1)
                        note_to_dec_inr_tag.append(note_to_dec_inner_ul1)

                elif re.search(r'^—', NTD_tag.a.text.strip()):
                    note_to_dec_inr_tag = NTD_tag
                    if re.search(r'^—', NTD_tag.find_previous().text.strip()):
                        note_to_dec_inner_ul.append(NTD_tag)
                    elif NTD_tag.find_previous("p"):
                        if re.search(r'^Analysis', NTD_tag.find_previous("p").text.strip()):
                            note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            NTD_tag.wrap(note_to_dec_inner_ul)
                    else:
                        note_to_dec_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_inner_ul)
                        note_to_dec_tag.append(note_to_dec_inner_ul)

                else:
                    note_to_dec_tag = NTD_tag
                    if re.search(r'^[IVX]+\.',NTD_tag.find_previous().text.strip(), re.I):
                        note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_ul)
                        note_to_dec_head_tag.append(note_to_dec_ul)
                    elif re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR PROVISIONS',NTD_tag.find_previous().text.strip(), re.I):
                        note_to_dec_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        NTD_tag.wrap(note_to_dec_ul)
                    else:
                        note_to_dec_ul.append(NTD_tag)

    def create_Notes_to_Decisions_con(self):
        note_to_dec_ids: list = []
        NTD_id1 = None

        for NTD_tag in self.soup.find_all():
            if NTD_tag.name == "h4" and re.search(r'^Notes to Decisions|'
                                                  r'^DECISIONS UNDER PRIOR LAW|'
                                                  r'^DECISIONS UNDER PRIOR PROVISIONS',
                                                  NTD_tag.text.strip(), re.I):
                NTD_id1 = None
                NTD_id = None

            elif NTD_tag.name == "li" and NTD_tag.get('class') == 'note':
                if re.search(r'^[IVX]+\.', NTD_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text1 = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()
                    NTD_id1 = f"{NTD_tag.find_previous('h4').get('id')}-{NTD_text1}"
                    nav_link_href = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}"

                    if nav_link_href in note_to_dec_ids:
                        nav_link["href"] = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}.1"
                    else:
                        nav_link["href"] = f"#{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text1}"
                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                elif re.search(r'^—\s*—', NTD_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()
                    nav_link["href"] = f"{NTD_inr_id}-{NTD_text}"
                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                elif re.search(r'^—', NTD_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()
                    nav_link_href = f"#{NTD_id}-{NTD_text}"

                    if NTD_id:
                        if nav_link_href in note_to_dec_ids:
                            nav_link["href"] = f"#{NTD_id}-{NTD_text}.1"
                        else:
                            nav_link["href"] = f"#{NTD_id}-{NTD_text}"
                    else:
                        nav_link["href"] = f"#{NTD_tag.find_previous('h4').get('id')}-{NTD_text}"

                    NTD_inr_id = nav_link["href"]
                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                else:
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(NTD_tag.text)
                    NTD_text = re.sub(r'\W+', '', NTD_tag.text.strip()).lower()

                    if NTD_id1:
                        NTD_id = f"{NTD_id1}-{NTD_text}"
                    else:
                        NTD_id = f"{NTD_tag.find_previous({'h4', 'h3'}).get('id')}-{NTD_text}"
                    if NTD_id in note_to_dec_ids:
                        nav_link["href"] = f"#{NTD_id}.1"
                    else:
                        nav_link["href"] = f"#{NTD_id}"

                    nav_list.append(nav_link)
                    NTD_tag.contents = nav_list

                note_to_dec_ids.append(NTD_id)

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
            self.class_regex = {'head1': r'^CONSTITUTION OF NORTH DAKOTA|CONSTITUTION OF THE UNITED STATES OF AMERICA',
                                'ul': r'^PREAMBLE|^§ \d\.', 'head2': '^ARTICLE (I|1)',
                                'head4': '^Source:', 'junk1': '^Text$',
                                'head3': r'^Section \d\.|^§ \d\.', 'NTD': '^Notes to Decisions'}
            self.generate_class_name()
            self.remove_junk()
            self.replace_tags()
            self.create_chapter_section_nav()
            self.convert_paragraph_to_alphabetical_ol_tags()
            self.create_Notes_to_Decisions_con()
            self.create_Notes_to_Decisions_ul_con()
        else:
            self.generate_class_name()
            self.remove_junk()
            self.replace_tags()
            self.create_chapter_section_nav()
            self.convert_paragraph_to_alphabetical_ol_tags()
            self.create_Notes_to_Decisions()
            self.create_Notes_to_Decisions_ul()

        self.wrap_div_tags()
        self.clean_html_and_add_cite()
        self.write_soup_to_file()
        print(f'finished {self.html_file_name}')
        print(datetime.now() - start_time)
