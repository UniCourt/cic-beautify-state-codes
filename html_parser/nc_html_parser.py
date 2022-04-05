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
import os
import os.path


class NCParseHtml(ParserBase):

    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.previous = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.class_regex = {'head1': r'Chapter \d+', 'ul': r'^Article|^1\.|^(?P<sec_id>\d+([A-Z])*-\d+(\.\d+)*)',
                            'head2': r'^ARTICLE \d+\.',
                            'head4': '^CASE NOTES|^OFFICIAL COMMENT',
                            'head3': '^§* \d+([A-Z])*-\d+(-\d+)*(\.|,| through)', 'ol_p': r'^\(\d\)|^I\.',
                            'junk1': '^Annotations$', 'nav': '^Subchapter I\.|^——————————'}

        self.watermark_text = """Release {0} of the Official Code of North Carolina Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
        """
        self.meta_tags = []
        self.tag_to_unwrap = []
        self.headers_class_dict = {'JUDICIAL DECISIONS': 'jdecisions',
                                   'OPINIONS OF THE ATTORNEY GENERAL': 'opinionofag',
                                   'RESEARCH REFERENCES': 'rreferences'}
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
        with open(f'../transforms/nc/ocnc/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
         re.search('^Annotations|^Text|^Statute text', text_junk.text.strip())]

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["nav"]) if
         re.search('^——————————', text_junk.text.strip())]

        if title := re.search(r'Chapter\s(?P<title>\d+)',
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

    def recreate_tag(self):

        for p_tag in self.soup.find_all(class_=self.class_regex['ol_p']):
            if re.search(r'^I\.', p_tag.text.strip()) and p_tag.br:
                p_tag_text = p_tag.text.strip()
                p_tag.clear()
                rept_tag = re.split('\n', p_tag_text)
                for tag_text in rept_tag:
                    new_tag = self.soup.new_tag("p")
                    new_tag.string = tag_text
                    p_tag.append(new_tag)
                    new_tag["class"] = "casenote"
                p_tag.unwrap()

    def replace_tags(self):
        watermark_p = None
        title_tag = None
        cur_head_list = []
        cur_id_list = []
        cap_alpha = 'A'
        cap_roman = "I"
        alpha = None
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        head4_list = ['Revision of title. —', 'Cross references. —', 'Law reviews. —', 'Editor\'s notes. —',
                      'History.', 'Effective dates. —']

        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):

                if re.search('constitution\.nc', self.html_file_name):
                    self.title_id = 'constitution-wy'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id = 'constitution-us'

                Article_pattern = re.compile(r'^Article\s(?P<chap_id>\d+([A-Z])*) ')

                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^Constitution of North Carolina|^Constitution of the United States',
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
                        article_id = re.search(r'^ARTICLE (?P<ar_id>[IVX]+)', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"




                    elif re.search(r'^§ \d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^§ (?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"

                    if re.search(r'^AMENDMENTS|^Preamble', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.sub(r'[\s\W]+', '', header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"
                        header_tag['class'] = "amend"



                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if re.search(r'^§ \d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^§ (?P<s_id>\d+)\.', header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                    elif re.search(r'^(Section|Sec\.) \d+', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^(Section|Sec\.) (?P<s_id>\d+)', header_tag.text.strip()).group('s_id')
                        if re.match(r'^ARTICLE', header_tag.find_previous('h2').text.strip()):
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h3', class_='amend').get('id')}s{sec_id.zfill(2)}"

                    elif re.search(r'^Amendment \d+', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^Amendment (?P<s_id>\d+)', header_tag.text.strip()).group('s_id')

                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2', class_='amend').get('id')}s{sec_id.zfill(2)}"


                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^CASE NOTES|^OFFICIAL COMMENT|^COMMENT', header_tag.text.strip()):
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
                        cap_roman = "I"

                    elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                        header_tag.name = "h5"

                        h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_rom_id = f"{header_tag.find_previous('h4').get('id')}-{h5_rom_text}"
                        header_tag['id'] = h5_rom_id
                        cap_alpha = 'A'
                        cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                    elif re.search(fr'^{cap_alpha}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                        header_tag['id'] = h5_alpha_id
                        cap_alpha = chr(ord(cap_alpha) + 1)

                    elif re.search(r'^\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', header_tag.text.strip()).group("h5_id")
                        h5_num_id = f"{h5_alpha_id}-{h5_num_text}"
                        header_tag['id'] = h5_num_id




                elif header_tag.get("class") == [self.class_regex["ul"]] and not re.search('^(Article|Sec\.)',
                                                                                           header_tag.text.strip()):
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
                title_pattern = re.compile(r'^(Chapter)\s(?P<title_id>\d+([A-Z])*)')
                subchapter_pattern = re.compile(r'^Subchapter (?P<s_id>[IVX]+([A-Z])*)\.')
                section_pattern = re.compile(
                    r'^§+\s*(?P<sec_id>\d+([A-Z])*-\d+([A-Z])*(\.\d+[A-Z]*)*(-\d+)*)[:., through]')
                chap_ul_pattern = re.compile(r'^(?P<s_id>[0-9]*[A-Z]*(\.\d+)*)([:.,]| through| to)')
                sec_ul_pattern = re.compile(r'^(?P<sec_id>\d+([A-Z])*-\d+([A-Z])*(\.\d+)*(-\d+)*)[., through]')
                SUBCHAPTER_pattern = re.compile(r'^SUBCHAPTER (?P<s_id>[IVX]+([A-Z])*)\.')
                article_pattern = re.compile(r'^ARTICLE (?P<a_id>\d+([A-Z])*)(\.| to)')
                section_rule_pattern = re.compile(r'^Rule(s)*\s(?P<r_id>\d+(\.\d+)*)[:., through]')
                sub_article_pattern = re.compile(r'^(ARTICLE|Article) (?P<s_id>([IVX]+([A-Z])*)*(\d+)*)')

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


                elif header_tag.get("class") == [self.class_regex["head2"]]:

                    if SUBCHAPTER_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        subchapter_id = SUBCHAPTER_pattern.search(header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}s{subchapter_id.zfill(2)}"
                        header_tag["class"] = "subchap"

                    elif article_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = article_pattern.search(header_tag.text.strip()).group('a_id')

                        if header_tag.find_previous('h2', class_='subchap'):
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2', class_='subchap').get('id')}a{chapter_id.zfill(2)}"
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h1').get('id')}a{chapter_id.zfill(2)}"

                        header_tag["class"] = "article"
                        self.count = 1


                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if section_pattern.search(header_tag.text.strip()):

                        header_tag.name = "h3"
                        section_id = section_pattern.search(header_tag.text.strip()).group('sec_id')

                        curr_head_id = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"

                        if curr_head_id in cur_head_list:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}.{self.count}"
                            self.count += 1
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"

                        cur_head_list.append(curr_head_id)
                        header_tag["class"] = "section"
                        self.head4count = 1

                    elif section_rule_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        rule_sec = section_rule_pattern.search(header_tag.text.strip()).group("r_id")
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2', class_='article').get('id')}r{rule_sec.zfill(2)}"
                        header_tag["class"] = "rulesec"





                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^CASE NOTES|^OFFICIAL COMMENT|^COMMENT', header_tag.text.strip()):
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
                        cap_roman = "I"


                    elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):

                        header_tag.name = "h5"

                        h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_rom_id = f"{header_tag.find_previous('h4').get('id')}-{h5_rom_text}"
                        header_tag['id'] = h5_rom_id
                        cap_alpha = 'A'
                        cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                    elif re.search(fr'^{cap_alpha}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                        header_tag['id'] = h5_alpha_id
                        cap_alpha = chr(ord(cap_alpha) + 1)

                    elif re.search(r'^\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', header_tag.text.strip()).group("h5_id")
                        h5_num_id = f"{h5_alpha_id}-{h5_num_text}"
                        header_tag['id'] = h5_num_id


                elif header_tag.get("class") == [self.class_regex["nav"]]:
                    if subchapter_pattern.search(header_tag.text.strip()):
                        header_tag["class"] = "nav"
                        # header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}s{subchapter_pattern.search(header_tag.text.strip()).group('s_id').zfill(2)}"
                        header_tag.find_previous("nav").append(header_tag)

                    elif sub_article_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h4"
                        chapter_id = sub_article_pattern.search(header_tag.text.strip()).group('s_id')

                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3').get('id')}a{chapter_id.zfill(2)}"

                        header_tag["class"] = "subar"

                elif header_tag.get("class") == [self.class_regex["ol_p"]]:
                    if sub_article_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h4"
                        chapter_id = sub_article_pattern.search(header_tag.text.strip()).group('s_id')

                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3').get('id')}a{chapter_id.zfill(2)}"

                        header_tag["class"] = "subar"

                elif header_tag.get("class") == [self.class_regex["ul"]]:

                    if chap_ul_pattern.search(header_tag.text.strip()) or \
                            sec_ul_pattern.search(header_tag.text.strip()):
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


                    elif re.search(r'^Article|^Sec\.', header_tag.text.strip()) and not header_tag.find_previous("h2"):
                        header_tag.find_previous("nav").append(header_tag)

        for h3_tag in self.soup.find_all("h3"):
            if h3_tag.find_next_sibling():
                if h3_tag.find_next_sibling().name != "p":
                    h3_tag.name = "p"

        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)

        print('tags replaced')

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num, cnav):
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

        section_pattern = re.compile(r'^(?P<sec_id>\d+([A-Z])*-\d+([A-Z])*(\.\d+[A-Z]*)*(-\d+)*)[., through]')
        ul_pattern = re.compile(r'^(?P<s_id>[0-9]*[A-Z]*(\.\d+)*)[:., through]')
        subchapter_pattern = re.compile(r'^Subchapter (?P<s_id>[IVX]+([A-Z])*)\.')

        for list_item in self.soup.find_all():
            if list_item.name == "li":
                if re.search('constitution', self.html_file_name):
                    if re.search(r'^[IVX]+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<chap>[IVX]+)\. ', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "a"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_num.zfill(2), sub_tag, prev_id, None, cnav)

                    elif re.search(r'^Preamble|^AMENDMENTS', list_item.text.strip()):
                        article_id = re.sub(r'[\s\W]+', '', list_item.text.strip()).lower()
                        sub_tag = "a"
                        prev_id = None
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_nav(list_item, article_id, sub_tag, prev_id, None, cnav)


                    elif re.search(r'^\d+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<chap>\d+)\. ', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "s"
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
                    elif ul_pattern.search(list_item.text.strip()):
                        chap_id = ul_pattern.search(list_item.text.strip()).group('s_id')
                        sub_tag = "a"

                        if list_item.find_previous('p', class_="nav"):
                            prev_id = f"t{self.title_id}s{subchapter_pattern.search(list_item.find_previous('p', class_='nav').text.strip()).group('s_id').zfill(2)}"
                        elif list_item.find_previous('h2', class_="article"):
                            prev_id = list_item.find_previous('h2', class_="article").get("id")
                            sub_tag = "r"
                        else:
                            prev_id = list_item.find_previous('h1').get("id")
                        self.s_nav_count += 1
                        cnav = f'snav{self.s_nav_count:02}'
                        self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None, cnav)



            elif list_item.name in ['h1', 'h2']:
                self.c_nav_count = 0
                self.a_nav_count = 0
                self.s_nav_count = 0

    def convert_paragraph_to_alphabetical_ol_tags_constition(self):

        main_sec_alpha = 'a'
        num_count = 1
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        num_cur_tag = None
        num_cur_tag1 = None

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
        main_sec_alpha = 'a'
        ol_head = 1
        num_count = 1
        ol_count = 1
        main_sec_alpha1 = 'a'
        sec_alpha_cur_tag = None
        num_cur_tag1 = None
        cap_alpha1 = 'A'
        cap_alpha1_cur_tag = None
        sec_alpha_cur_tag1 = None
        ol_head_tag = None
        cap_roman = "I"
        small_roman = "i"
        roman_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):

            current_tag_text = p_tag.text.strip()

            if re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)

                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    ol_count += 1

                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    num_cur_tag1 = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)

                    num_id1 = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    num_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(num_ol1)
                    num_count = 2

            elif re.search(rf'^\([a-z]\d+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1
                sec_alpha_ol.append(p_tag)

                li_id = re.search(rf'^\((?P<id>[a-z]\d+)\)', current_tag_text).group("id")

                p_tag["id"] = f'{sec_alpha_id}-{li_id}'
                p_tag.string = re.sub(rf'^\({li_id}\)', '', current_tag_text)


            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                main_sec_alpha1 = 'a'
                small_roman = "i"

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        ol_count += 1
                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

                if re.search(r'^\([0-9]+\)\s*a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*a\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    sec_alpha_cur_tag1 = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*(?P<pid>a)\.', current_tag_text)

                    sec_alpha_id1 = f'{num_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag1.group("pid")}'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol1)
                    main_sec_alpha1 = "b"

                if re.search(r'^\([0-9]+\)\s*\(a\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*\(a\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*\((?P<pid>a)\)', current_tag_text)

                    alpha_id = f'{num_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag1.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(alpha_ol)
                    sec_alpha = "b"



            elif re.search(r'^\(\d+[a-z]\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                main_sec_alpha1 = 'a'
                num_ol1.append(p_tag)

                p_tag_text = re.search(rf'^\((?P<id>\d+[a-z])\)', current_tag_text).group("id")
                p_tag["id"] = f'{num_id1}-{p_tag_text}'
                p_tag.string = re.sub(rf'^\({p_tag_text}\)', '', current_tag_text)

                if re.search(rf'^\(\d+[a-z]\)\s*a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+[a-z]\)\s*a\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    sec_alpha_cur_tag1 = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>\d+[a-z])\)\s*(?P<pid>a)\.', current_tag_text)

                    sec_alpha_id1 = f'{num_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag1.group("pid")}'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol1)
                    main_sec_alpha1 = "b"



            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag1 = p_tag
                small_roman = "i"
                cap_alpha1_cur_tag = None

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)
                    if num_cur_tag1:
                        num_cur_tag1.append(sec_alpha_ol1)
                        sec_alpha_id1 = num_cur_tag1.get('id')
                    else:
                        sec_alpha_id1 = p_tag.find_previous("li").get('id')
                        p_tag.find_previous("li").append(sec_alpha_ol1)

                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

                ol_head = 1

                if re.search(rf'^[a-z]\.\s*1\.', current_tag_text):
                    head_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[a-z]\.\s*1\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    ol_head_tag = li_tag
                    cur_tag1 = re.search(r'^(?P<cid>[a-z])\.\s*(?P<pid>1)\.', current_tag_text)

                    ol_head_id = f'{sec_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag1.get("id")}{cur_tag1.group("pid")}'
                    head_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(head_ol)
                    ol_head = 2


            elif re.search(rf'^{ol_head}\.', current_tag_text) and p_tag.get("class") != "casenote" and not p_tag.b:
                p_tag.name = "li"
                ol_head_tag = p_tag
                cap_roman = "I"
                small_roman = "i"

                if re.search(r'^1\.', current_tag_text):
                    head_ol = self.soup.new_tag("ol")
                    p_tag.wrap(head_ol)

                    if cap_alpha1_cur_tag:
                        cap_alpha1_cur_tag.append(head_ol)
                        ol_head_id = cap_alpha1_cur_tag.get('id')
                    elif sec_alpha_cur_tag1:
                        sec_alpha_cur_tag1.append(head_ol)
                        ol_head_id = sec_alpha_cur_tag1.get('id')
                    else:
                        ol_head_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        ol_count += 1
                else:
                    head_ol.append(p_tag)

                p_tag["id"] = f'{ol_head_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1




            elif re.search(rf'^{cap_roman}\.', current_tag_text) \
                    and p_tag.get("class") != "casenote" and not p_tag.b and ol_head_tag:

                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^I\.', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(roman_ol)
                    ol_head_tag.append(roman_ol)
                    prev_id1 = ol_head_tag.get("id")

                else:
                    roman_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}{cap_roman}'
                p_tag.string = re.sub(rf'^{cap_roman}\.', '', current_tag_text)
                cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)



            elif re.search(rf'^\({small_roman}\)', current_tag_text) and p_tag.name == "p" \
                    and (sec_alpha_cur_tag1 or ol_head_tag or num_cur_tag1):
                p_tag.name = "li"
                roman_cur_tag = p_tag



                if re.search(r'^\(i\)', current_tag_text):
                    smallroman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(smallroman_ol)


                    prev_id1 = p_tag.find_previous("li").get('id')
                    p_tag.find_previous("li").append(smallroman_ol)


                else:
                    smallroman_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}{small_roman}'
                p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()



            elif re.search(rf'^{cap_alpha1}\.', current_tag_text) \
                    and p_tag.get("class") != "casenote" and not p_tag.b:
                p_tag.name = "li"
                cap_alpha1_cur_tag = p_tag
                ol_head = 1

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha1_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha1_ol)

                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(cap_alpha1_ol)
                        cap_alpha1_id = sec_alpha_cur_tag.get("id")
                    elif roman_cur_tag:
                        roman_cur_tag.append(cap_alpha1_ol)
                        cap_alpha1_id = roman_cur_tag.get("id")
                    else:
                        cap_alpha1_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        ol_count += 1
                else:
                    cap_alpha1_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha1_id}{cap_alpha1}'
                p_tag.string = re.sub(rf'^{cap_alpha1}\.', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)


            elif re.search(r'^\([a-z]\)', current_tag_text) and p_tag.name == "p":

                if sec_alpha_cur_tag:
                    p_tag.name = "li"
                    num_count = 1
                    sec_alpha_cur_tag = p_tag

                    if re.search(r'^\(a\)', current_tag_text):
                        sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(sec_alpha_ol)

                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        ol_count += 1

                    else:
                        sec_alpha_ol.append(p_tag)

                    sec_id = re.search(rf'^\((?P<s_id>[a-z])\)', current_tag_text).group("s_id")
                    p_tag["id"] = f'{sec_alpha_id}{sec_id}'

                    p_tag.string = re.sub(rf'^\([a-z]\)', '', current_tag_text)

            if re.search(r'^CASE NOTES|^"Sec\. \d+\.', current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                ol_head = 1
                ol_count = 1
                num_count = 1
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha1_cur_tag = None
                sec_alpha_cur_tag1 = None
                ol_head_tag = None
                cap_roman = "I"
                small_roman = "i"

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
                lambda tag: re.search(r"G\.S\.\s\d+[A-Z]*-\d+(\.\d+)*(\([a-z0-9]+\))*|Chapter \d+[A-Z]*|"
                                      r"\d+ N\.C\. \d+|"
                                      r"\d+ N\.C\. App\.",
                                      tag.get_text()) and tag.name == 'p'
                            and tag not in cite_p_tags):
            cite_p_tags.append(tag)

            text = str(tag)
            for match in set(
                    x[0] for x in re.findall(r'(G\.S\.\s\d+[A-Z]*-\d+(\.\d+)*(-\d+)*(\([a-z]*[0-9]*\)(\([0-9]\))*)*'
                                             r'|Chapter \d+[A-Z]*)', tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>|<p.+>', '', text, re.DOTALL)

                if re.search(r'Chapter \d+[A-Z]*', match.strip()):
                    id_reg = re.search(r'Chapter (?P<title>\d+[A-Z]*)', match.strip())
                else:
                    id_reg = re.search(
                        r'G\.S\.\s*(?P<cite>(?P<title>\d+[A-Z]*)-(?P<sec>\d+(\.\d+)*)(-\d+)*)(?P<ol>\([a-z]*\)(\([0-9]+\))*(\([a-z]\))*)*',
                        match.strip())

                title = id_reg.group("title").strip()
                title_id = f'{title.zfill(2)}'

                if re.search(r'^\d{3}[A-Z]*', title_id):
                    title_id1 = f'{title_id}'
                elif re.search(r'^\d{2}[A-Z]*', title_id):
                    title_id1 = f'0{title_id}'
                else:
                    title_id1 = f'00{title_id}'

                if re.search(r'Chapter \d+[A-Z]*', match.strip()):
                    tag.clear()
                    target = "_blank"
                    a_id = f'gov.nc.stat.title.{title_id1}.html'
                    text = re.sub(fr'\s{re.escape(match)}',
                                  f' <cite class="octn"><a href="{a_id}" target="{target}">{match}</a></cite>',
                                  inside_text,
                                  re.I)
                    tag.append(text)

                else:

                    if os.path.isfile(
                            f"../../code-nc/transforms/nc/ocnc/r{self.release_number}/gov.nc.stat.title.{title_id1}.html"):
                        with open(
                                f"../../code-nc/transforms/nc/ocnc/r{self.release_number}/gov.nc.stat.title.{title_id1}.html",
                                'r') as firstfile:

                            for line in firstfile:
                                if re.search(rf'id="\w+s{id_reg.group("cite")}">$', line.strip()):
                                    tag.clear()
                                    head_id = re.search(rf'id="(?P<h_id>\w+s{id_reg.group("cite")})">$', line.strip())

                                    if title_id == self.title_id:
                                        target = "_self"
                                        if id_reg.group("ol"):
                                            ol_id = re.sub(r'[() ]+', '', id_reg.group("ol"))

                                            if re.search(r'\([a-z][0-9]\)', id_reg.group("ol")):
                                                a_id = f'#{head_id.group("h_id")}ol1-{ol_id}'
                                            else:
                                                a_id = f'#{head_id.group("h_id")}ol1{ol_id}'

                                        else:
                                            a_id = f'#{head_id.group("h_id")}'
                                    else:
                                        target = "_blank"
                                        if id_reg.group("ol"):
                                            ol_id = re.sub(r'[() ]+', '', id_reg.group("ol"))
                                            a_id = f'gov.nc.stat.title.{title_id1}.html#{head_id.group("h_id")}ol1{ol_id}'
                                        else:
                                            a_id = f'gov.nc.stat.title.{title_id1}.html#{head_id.group("h_id")}'

                                    text = re.sub(fr'\s{re.escape(match)}',
                                                  f' <cite class="octn"><a href="{a_id}" target="{target}">{match}</a></cite>',
                                                  inside_text,
                                                  re.I)
                                    tag.append(text)

            for match in set(
                    x for x in re.findall(r'\d+ N\.C\. \d+|\d+ N\.C\. App\.',
                                          tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                tag.clear()
                text = re.sub(re.escape(match), f'<cite class="nc_code">{match}</cite>', inside_text, re.I)
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

        for tag in self.soup.find_all("p", class_="p2"):
            if tag.br:
                if len(tag.text) > 0:
                    tag.decompose()

        clss = re.compile(r'p\d+')
        for all_tag in self.soup.findAll(class_=clss):
            del all_tag["class"]

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
        with open(f"../../code-nc/transforms/nc/ocnc/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    def create_case_note_nav(self):
        cap_alpha = None

        for case_tag in self.soup.find_all("p", class_='casenote'):
            if re.search(r'^[IVX]+\. ', case_tag.text.strip()):
                if case_tag.find_next("p", class_='casenote') and cap_alpha == "I":
                    if re.search(r'^J\.', case_tag.find_next("p", class_='casenote').text.strip()):
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(case_tag.text)
                        case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid")
                        alpha_id = f"{rom_id}-{case_id}"
                        nav_link["href"] = f"#{rom_id}-{case_id}"
                        nav_link["class"] = "casenote"
                        nav_list.append(nav_link)
                        case_tag.contents = nav_list
                        case_tag["class"] = "casenote"
                        cap_alpha = chr(ord(cap_alpha) + 1)
                else:
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[IVX]+)\.', case_tag.text.strip()).group("cid")
                    rom_id = f"{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_link["href"] = f"#{case_tag.find_previous({'h4', 'h3'}).get('id')}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list
                    case_tag["class"] = "casenote"
                    cap_alpha = 'A'

            elif cap_alpha:
                if re.search(fr'^{cap_alpha}\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid")
                    alpha_id = f"{rom_id}-{case_id}"
                    nav_link["href"] = f"#{rom_id}-{case_id}"
                    nav_link["class"] = "casenote"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list
                    case_tag["class"] = "casenote"
                    cap_alpha = chr(ord(cap_alpha) + 1)

                elif re.search(r'^[0-9]+\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[0-9]+)\.', case_tag.text.strip()).group("cid")
                    digit_id = f"{alpha_id}-{case_id}"
                    nav_link["href"] = f"#{alpha_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list
                    case_tag["class"] = "casenote"

    def create_case_note_ul(self):
        cap_alpha = 'A'
        for case_tag in self.soup.find_all(class_='casenote'):
            case_tag.name = "li"

            if re.search(r'^[IVX]+\. ', case_tag.a.text.strip()):
                rom_tag = case_tag
                cap_alpha = 'A'
                if re.search(r'^I\.', case_tag.a.text.strip()):
                    if re.search(r'^J\.', case_tag.find_next(class_='casenote').a.text.strip()):
                        alpha_ul.append(case_tag)
                        cap_alpha = 'J'

                    else:
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                else:
                    rom_ul.append(case_tag)

            elif re.search(fr'^{cap_alpha}\.', case_tag.a.text.strip()):
                alpha_tag = case_tag
                if re.search(r'^A\.', case_tag.a.text.strip()):
                    alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(alpha_ul)
                    rom_tag.append(alpha_ul)
                else:
                    alpha_ul.append(case_tag)

                cap_alpha = chr(ord(cap_alpha) + 1)

            elif re.search(r'^[0-9]+\.', case_tag.a.text.strip()):
                digit_tag = case_tag
                if re.search(r'^1\.', case_tag.a.text.strip()):
                    digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(digit_ul)
                    alpha_tag.append(digit_ul)
                else:
                    digit_ul.append(case_tag)

    def create_case_note_nav1(self):
        cap_alpha = None
        cap_roman = "I"

        for case_tag in self.soup.find_all({"p", "h4"}):

            if case_tag.get("class") == "casenote" and case_tag.name == "p":
                if re.search(rf'^{cap_roman}\. ', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[IVX]+)\.', case_tag.text.strip()).group("cid")
                    rom_id = f"{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_link["href"] = f"#{case_tag.find_previous({'h4', 'h3'}).get('id')}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list
                    case_tag["class"] = "casenote"
                    cap_alpha = 'A'
                    cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                elif cap_alpha:
                    if re.search(fr'^{cap_alpha}\.', case_tag.text.strip()):
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(case_tag.text)
                        case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid")
                        alpha_id = f"{rom_id}-{case_id}"
                        nav_link["href"] = f"#{rom_id}-{case_id}"
                        nav_link["class"] = "casenote"
                        nav_list.append(nav_link)
                        case_tag.contents = nav_list
                        case_tag["class"] = "casenote"
                        cap_alpha = chr(ord(cap_alpha) + 1)

                    elif re.search(r'^[0-9]+\.', case_tag.text.strip()):
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(case_tag.text)
                        case_id = re.search(r'^(?P<cid>[0-9]+)\.', case_tag.text.strip()).group("cid")
                        digit_id = f"{alpha_id}-{case_id}"
                        nav_link["href"] = f"#{alpha_id}-{case_id}"
                        nav_list.append(nav_link)
                        case_tag.contents = nav_list
                        case_tag["class"] = "casenote"

            elif case_tag.name == "h4":
                cap_roman = "I"

    def create_case_note_ul1(self):
        cap_alpha = 'A'
        cap_roman = "I"
        for case_tag in self.soup.find_all({"p", "h4"}):
            if case_tag.get("class") == "casenote" and case_tag.name == "p":
                case_tag.name = "li"

                if re.search(rf'^{cap_roman}\. ', case_tag.a.text.strip()):
                    rom_tag = case_tag
                    cap_alpha = 'A'
                    if re.search(r'^I\.', case_tag.a.text.strip()):
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                    else:
                        rom_ul.append(case_tag)

                    cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                elif re.search(fr'^{cap_alpha}\.', case_tag.a.text.strip()):
                    alpha_tag = case_tag
                    if re.search(r'^A\.', case_tag.a.text.strip()):
                        alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(alpha_ul)
                        rom_tag.append(alpha_ul)
                    else:
                        alpha_ul.append(case_tag)

                    cap_alpha = chr(ord(cap_alpha) + 1)

                elif re.search(r'^[0-9]+\.', case_tag.a.text.strip()):
                    digit_tag = case_tag
                    if re.search(r'^1\.', case_tag.a.text.strip()):
                        digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(digit_ul)
                        alpha_tag.append(digit_ul)
                    else:
                        digit_ul.append(case_tag)

            elif case_tag.name == "h4":
                cap_roman = "I"

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
            self.class_regex = {'head1': r'^Constitution of North Carolina|Constitution of the United States',
                                'ul': r'^(Article|Preamble)', 'head2': '^ARTICLE I',
                                'head4': '^CASE NOTES', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$',
                                'head': '^Section added\.',
                                'head3': r'^§ \d|^sec\.|^Section \d', 'nav': '^Subchapter I\.|^——————————'}

            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_chapter_section_nav()
            self.convert_paragraph_to_alphabetical_ol_tags_constition()
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
            self.create_case_note_nav1()
            self.create_case_note_ul1()
            self.wrap_div_tags()

        self.clean_html_and_add_cite()
        self.write_soup_to_file()
        print(f'finished {self.html_file_name}')
        print(datetime.now() - start_time)

