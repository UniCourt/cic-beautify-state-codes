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



class ARParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.previous = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.tag_type_dict = {'head1': r'TITLE \d', 'ul': r'^Subchapter 1 —',
                              'head4': 'Research References',
                              'ol_p': r'^\([a-z]\)', 'junk1': '^Annotations$', 'normalp': '^Publisher\'s Notes',
                              }
        self.watermark_text = """Release {0} of the Official Code of Arkansas Annotated released {1}. 
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
        with open(f'../transforms/ar/ocar/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
            class_tag = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(
                    rf'{value}', tag.get_text().strip(), re.I))
            if class_tag:
                self.tag_type_dict[key] = class_tag['class'][0]

                if re.search('junk', key):
                    self.junk_tag_class.append(class_tag['class'][0])

        if not re.search('constitution', self.html_file_name):
            h3_class = self.soup.find(lambda tag: tag.name == 'p' and re.search(
                rf'^\d+-\d+-\d+', tag.get_text().strip(), re.I) and tag.get('class')[0] != self.tag_type_dict['ul'])[
                'class'][
                0]
            self.tag_type_dict['head3'] = h3_class
            # self.tag_type_dict['head3'] = "p7"

            h2_class = self.soup.find(lambda tag: tag.name == 'p' and re.search(
                rf'^CHAPTER \d', tag.get_text().strip(), re.I) and tag.get('class')[0] != self.tag_type_dict['ul'])[
                'class'][
                0]
            self.tag_type_dict['head2'] = h2_class
        else:
            h2_class = self.soup.find(lambda tag: tag.name == 'p' and re.search(
                rf'^Article \d', tag.get_text().strip(), re.I) and tag.get('class')[0] != self.tag_type_dict['ul'])[
                'class'][
                0]
            self.tag_type_dict['head2'] = h2_class
            h3_class = self.soup.find(lambda tag: tag.name == 'p' and re.search(
                r'^§ \d', tag.get_text().strip(), re.I) and tag.get('class')[0] != self.tag_type_dict['ul'])[
                'class'][
                0]
            self.tag_type_dict['head3'] = h3_class

        if ol_p_2_tag := self.soup.find(lambda tag: tag.name == 'p' and re.search(
                r'^Maximum Name of Fund', tag.get_text().strip(), re.I)
                                                                  and tag.get('class')[0] not in self.tag_type_dict.values()):
            self.tag_type_dict['ol_p'] = [self.tag_type_dict['ol_p'], ol_p_2_tag['class'][0]]

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
            if junk_tag.name and junk_tag.get('class')[0] == 'Apple-converted-space':
                junk_tag.string = ' '
                junk_tag.unwrap()
            else:
                junk_tag.decompose()
        if title := re.search(r'title\s(?P<title>\d+)',
                              self.soup.find('p', class_=self.tag_type_dict['head1']).get_text(), re.I):

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
        tag_dict = {self.tag_type_dict['head1']: "h1", self.tag_type_dict['head2']: "h2",
                    self.tag_type_dict.get('part', ''): "h4",
                    self.tag_type_dict['head3']: "h3", self.tag_type_dict['head4']: "h4",
                    self.tag_type_dict['ul']: "li",
                    }
        for key, value in tag_dict.items():
            ul = self.soup.new_tag("ul", Class="leaders")
            while True:



                p_tag = self.soup.find('p', {"class": key})



                if not p_tag or p_tag.has_attr('Class') and p_tag['Class'] == 'transformation':
                    break
                p_tag.name = value

                if key == self.tag_type_dict['ul']:
                    if p_tag.findPrevious().name != 'li':
                        p_tag.wrap(ul)
                    elif p_tag.findPrevious().name == 'li':
                        ul.append(p_tag)
                    if p_tag.findNext().has_attr('class') and \
                            p_tag.findNext()['class'][0] != self.tag_type_dict['ul']:
                        new_nav = self.soup.new_tag('nav')
                        if re.search(r'sec\.|chap\.|Art\.', ul.contents[0].get_text(), re.I):
                            ul.contents[0].name = 'p'
                            ul.contents[0]['class'] = 'navheader'
                            new_nav.append(ul.contents[0])
                        ul.wrap(new_nav)
                        ul = self.soup.new_tag("ul", Class="leaders")


                if value in ['h2', 'h3']:
                    if chap_section_regex := re.search(
                            r'^(?P<title>\d+)-(?P<chapter>\d+([a-z])?)-(?P<section>\d+(\.\d+)?)'
                            r'|(chapter|article|part|subpart)\s(?P<chap>\d+([a-z])?)',
                            p_tag.get_text().strip(), re.I):
                        if chapter := chap_section_regex.group('chap'):
                            if re.search('^article', p_tag.get_text().strip(), re.I) and \
                                    (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h2'
                                                                               and not re.search('^part',
                                                                                                 tag.get_text(),
                                                                                                 re.I))):
                                if re.search(r'chapter \d', chap_id.get_text(), re.I):
                                    p_tag['id'] = f'{chap_id["id"]}a{chapter.zfill(2)}'
                                else:
                                    cleansed_chap = re.sub(r'\d+$', '', chap_id["id"])
                                    p_tag['id'] = f'{cleansed_chap}{chapter.zfill(2)}'
                                p_tag['class'] = 'articleh2'
                            elif re.search('^part', p_tag.get_text().strip(), re.I) and \
                                    (chap_id := p_tag.findPrevious('h2')):
                                if re.search(r'(chapter|article) \d', chap_id.get_text(), re.I):
                                    p_tag['id'] = f'{chap_id["id"]}p{chapter.zfill(2)}'
                                else:
                                    cleansed_chap = re.sub(r'\d+$', '', chap_id["id"])
                                    p_tag['id'] = f'{cleansed_chap}{chapter.zfill(2)}'
                                p_tag['class'] = 'parth2'
                            elif re.search('^subchapter', p_tag.get_text().strip(), re.I) and \
                                    (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h2' and re.search('^Chapter', tag.get_text()))):
                                p_tag.name = 'h3'
                                p_tag['id'] = f'{chap_id["id"]}sc{chapter.zfill(2)}'
                                p_tag['class'] = 'subchapterh3'

                            elif re.search('^Subpart', p_tag.get_text().strip(), re.I) and \
                                    (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h2' and re.search('^Part', tag.get_text()))):
                                p_tag.name = 'h3'
                                p_tag['id'] = f'{chap_id["id"]}sp{chapter.zfill(2)}'
                                p_tag['class'] = 'subparth3'

                            else:
                                p_tag['id'] = f't{self.title.zfill(2)}c{chapter.zfill(2)}'
                        else:
                            chapter = chap_section_regex.group("chapter")
                            section = f'{self.title}-{chapter}-{chap_section_regex.group("section")}'
                            p_tag[
                                'id'] = f't{self.title.zfill(2)}c{chapter.zfill(2)}s{section}'
                        if previous_sibling_tag := p_tag.find_previous(
                                lambda tag: tag.name == 'h3' and re.search(p_tag['id'], tag.get('id', ''))):
                            if pervious_tag_id_num_match := re.search(rf'{p_tag["id"]}(\.\d)?\.(?P<count>\d+)',
                                                                      previous_sibling_tag['id'], re.I):
                                p_tag['id'] = f"{p_tag['id']}.{int(pervious_tag_id_num_match.group('count')) + 1}"
                            else:
                                p_tag['id'] = f"{p_tag['id']}.1"
                    elif section_match := re.search(r'^(?P<sec>\w+)\.', p_tag.get_text()):
                        p_tag.name = 'h3'
                        chap_tag = p_tag.find_previous(lambda tag: tag.name == 'h2'
                                                                   and re.search(r'chapter \w+', tag.get_text(), re.I))
                        chap_id = re.search(r'chapter (?P<chap_id>\w+)', chap_tag.get_text(), re.I).group('chap_id')
                        section_id = f'{self.title.zfill(2)}-{chap_id.zfill(2)}-{section_match.group("sec")}'
                        p_tag['id'] = f'{chap_tag["id"]}s{section_id}'
                    else:
                        if re.search(r'^Section [IVX]+',p_tag.get_text()):
                            p_tag.name = 'h5'
                            sec_id =re.search(r'^Section (?P<s_id>[IVX]+)',p_tag.get_text()).group("s_id")
                            p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}s{sec_id}'
                        else:
                            p_tag.name = 'h5'

                elif value == 'h4':
                    chap_tag = p_tag.find_previous('h2')
                    if self.headers_class_dict.get(p_tag.get_text()):
                        p_tag['class'] = self.headers_class_dict.get(p_tag.get_text())
                    p_tag['id'] = re.sub(r'\s+|\'', '', f't{self.title.zfill(2)}-{p_tag.get_text()}')
                    part_tag = p_tag.find_previous(
                        lambda tag: re.search(r'h\d', tag.name) and tag.name != 'h5' and tag.has_attr('class')
                                    and tag['class'] not in self.headers_class_dict.values())

                    if re.search(r'^\d', p_tag.get_text()):
                        chap_id = p_tag.find_previous_sibling(lambda tag: re.search('^[a-zA-Z]', tag.get_text())
                                                                          and tag.name != 'h5' and re.search(r'h\d',
                                                                                                             tag.name))

                    elif part_tag and part_tag.has_attr('class') and part_tag['class'] == 'part_header':
                        chap_id = part_tag

                    elif not p_tag.has_attr('class') or p_tag['class'] not in self.headers_class_dict.values():
                        chap_id = p_tag.find_previous(lambda tag: tag.name in ['h2', 'h3'] or tag.has_attr('class') and
                                                                  tag['class'] in self.headers_class_dict.values())
                    else:
                        chap_id = p_tag.find_previous(lambda tag: tag.name in ['h2', 'h3'])
                    if chap_id and chap_id.has_attr('id'):
                        id_text = re.sub(r'\s|"|\'', '', p_tag.get_text())
                        p_tag['id'] = f'{chap_id["id"]}-{id_text}'

                    if self.tag_type_dict.get('part') and key == self.tag_type_dict['part']:
                        part_num = re.search(r'^part\s(?P<num>\w+(\.\w+)?)', p_tag.get_text().strip(), re.I).group(
                            'num')
                        p_tag['class'] = 'part_header'
                        p_tag['id'] = f'{chap_tag["id"]}p{part_num.zfill(2)}'
                    if p_tag.get('class') in self.headers_class_dict.values():
                        previous_id_num = 0
                        if previous_h4 := p_tag.findPrevious(
                                lambda tag: tag.name == 'h4' and re.search(f"{p_tag['id']}\d+$", tag['id'], re.I)):
                            previous_id_num = int(re.search(r'\d+$', previous_h4['id'], re.I).group())
                        p_tag['id'] = f'{p_tag["id"]}{str(previous_id_num + 1).zfill(2)}'

                elif value == 'h5':
                    if re.search(r'\w+', p_tag.get_text()):
                        break_span = self.soup.new_tag('span', Class='headbreak')
                        article_title = p_tag.findNext(
                            lambda tag: tag.name == 'p' and re.search(r'\w+', tag.get_text()))
                        article_title.string = re.sub(r'^\W+', '', article_title.get_text())
                        p_tag.contents.append(article_title.string)
                        p_tag.contents.insert(1, break_span)
                        article_title.decompose()
                    else:
                        p_tag.decompose()
                elif value == 'h1':
                    if re.search(r'title \d', p_tag.get_text(), re.I):
                        watermark_p = self.soup.new_tag('p', Class='transformation')
                        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                                        datetime.now().date())
                        p_tag.insert_before(watermark_p)
                        title_tag = p_tag
                    else:
                        p_tag.name = 'h5'
                if (st_reg := re.search(r'^Subtitle (?P<stnum>\d+)', p_tag.get_text())) and p_tag.name == 'h5':
                    p_tag['class'] = 'subtitleh2'
                    p_tag.name = 'h2'
                    p_tag['id'] = f't{self.title.zfill(2)}st{st_reg.group("stnum").zfill(2)}'




        for p_tag in self.soup.find_all(class_=self.tag_type_dict['ol_p']):
            if re.search('^(Article|ARTICLE) [IVX]+', p_tag.get_text().strip(), re.I) and \
                    (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h3'
                                                               and  re.search('^\d+-\d+([a-z])?-\d+(\.\d+)?',
                                                                                 tag.get_text(),
                                                                               re.I))):

                p_tag.name = "h4"
                art_id = re.search('^(Article|ARTICLE) (?P<a_id>[IVX]+)', p_tag.get_text().strip(), re.I).group("a_id")
                p_tag['id'] = f'{chap_id["id"]}a{art_id}'
            elif re.search('^Section [A-Z]\.', p_tag.get_text().strip(), re.I) and \
                    (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h4'
                                                               and  re.search('^(Article|ARTICLE) (?P<a_id>[IVX]+)',
                                                                                 tag.get_text(),
                                                                               re.I))):

                p_tag.name = "h4"
                art_id = re.search('^Section (?P<a_id>[A-Z])\.', p_tag.get_text().strip(), re.I).group("a_id")
                p_tag['id'] = f'{chap_id["id"]}a{art_id}'

            # elif re.search('^SECTION \d+\.', p_tag.get_text().strip(), re.I) and \
            #         (chap_id := p_tag.findPrevious(lambda tag: tag.name == 'h3'
            #                                                    and  re.search('^\d+\.',
            #                                                                      tag.get_text(),
            #                                                                    re.I))):
            #
            #     print(p_tag)
            #
            #     p_tag.name = "h5"
            #     art_id = re.search('^SECTION (?P<a_id>\d+)\.', p_tag.get_text().strip(), re.I).group("a_id")
            #     p_tag['id'] = f'{chap_id["id"]}sec{art_id}'




        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        if watermark_p:
            chap_nav = self.soup.find('nav')
            chap_nav.insert(0, watermark_p)
            chap_nav.insert(1, title_tag)
        print('tags replaced')

    def convert_paragraph_to_alphabetical_ol_tags1(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        inner_sec_alpha = 'a'
        cap_alpha = 'A'
        inner_cap_alpha = 'A'
        num_count = 1
        inner_numcount = 1
        inner_num_count = 1
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        cap_alpha_cur_tag = None
        roman_cur_tag = None
        sec_alpha_cur_tag = None
        inner_sec_alpha_cur_tag = None
        num_cur_tag = None
        inner_alpha = 'a'
        roman_cur_tag1 = None
        rom = 0
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha1 = 'A'
        cap_alpha2 = 'a'
        n_tag = None
        cap_alpha1_cur_tag = None
        sec_alpha_cur_tag1 = None
        ol_head_tag = None
        small_roman = 'i'
        small_roman1 = 'i'
        innernum_cur_tag = None
        section_tag = None
        inner_num_cur_tag = None



        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):

            current_tag_text = p_tag.text.strip()

            if re.search(r'SECTION \d+\.', current_tag_text):
                section_tag = p_tag
            elif p_tag.name in ['h3', 'h4', 'h5']:
                section_tag = None




            if re.search(rf'^\({inner_numcount}\)', current_tag_text) \
                    and p_tag.name == "p" and inner_sec_alpha_cur_tag:

                p_tag.name = "li"
                innernum_cur_tag = p_tag
                inner_cap_alpha = "A"


                if re.search(r'^\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if inner_sec_alpha_cur_tag:
                        inner_num_id = inner_sec_alpha_cur_tag.get('id')
                        inner_sec_alpha_cur_tag.append(inner_num_ol)

                else:
                    inner_num_ol.append(p_tag)


                p_tag["id"] = f'{inner_num_id}{inner_numcount}'
                p_tag.string = re.sub(rf'^\({inner_numcount}\)', '', current_tag_text)
                inner_numcount += 1

                if re.search(rf'^\([0-9]+\)\s*\(A\)', current_tag_text):
                    inner_cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*\(A\)', '', current_tag_text)
                    inner_cap_alpha_cur_tag1 = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*\((?P<pid>A)\)', current_tag_text)
                    inner_cap_alpha_id1 = f'{innernum_cur_tag.get("id")}'
                    li_tag["id"] = f'{innernum_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    inner_cap_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_cap_alpha_ol1)
                    inner_cap_alpha = "B"






            elif re.search(rf'^\({inner_sec_alpha}\)', current_tag_text) \
                    and p_tag.name == "p" and (roman_cur_tag or roman_cur_tag1 ) :

                p_tag.name = "li"
                inner_sec_alpha_cur_tag = p_tag
                inner_numcount = 1
                innernum_cur_tag = None


                if re.search(r'^\(a\)', current_tag_text):
                    inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inner_sec_alpha_ol)

                    if roman_cur_tag1:
                        roman_cur_tag1.append(inner_sec_alpha_ol)
                        inner_sec_alpha_id = f"{roman_cur_tag1.get('id')}"


                    else:
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha_id = f"{roman_cur_tag.get('id')}"

                else:
                    inner_sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inner_sec_alpha_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}\)', '', current_tag_text)
                inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)


                if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)

                    num_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                    inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    inner_num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_num_ol)
                    inner_numcount = 2
                    inner_cap_alpha = 'B'



            # elif re.search(rf'^\({small_roman}\)', current_tag_text) and p_tag.name == "p" \
            #             and num_cur_tag and cap_alpha_cur_tag and main_sec_alpha not in ['i','v','x'] :
            elif re.search(rf'^\({small_roman}\)', current_tag_text):
                p_tag.name = "li"
                roman_cur_tag = p_tag
                inner_sec_alpha = 'a'
                inner_sec_alpha_cur_tag = None

                if re.search(r'^\(i\)', current_tag_text):
                    if re.search(r'^\(ii\)|^\([a-b]\)|^\(1\)|^\(A\)',p_tag.find_next_sibling("p").text.strip()):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        p_tag.wrap(roman_ol)

                        if cap_alpha_cur_tag:
                            cap_alpha_cur_tag.append(roman_ol)
                            prev_id1 = cap_alpha_cur_tag.get("id")
                        elif num_cur_tag:
                            num_cur_tag.append(roman_ol)
                            prev_id1 = num_cur_tag.get("id")
                        elif sec_alpha_cur_tag:
                            sec_alpha_cur_tag.append(roman_ol)
                            prev_id1 = sec_alpha_cur_tag.get("id")

                        rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                        p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                        p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                        small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                    else:
                        p_tag.name = "li"
                        sec_alpha_cur_tag = p_tag
                        cap_alpha_cur_tag = None
                        num_cur_tag = None
                        roman_cur_tag = None
                        num_count = 1

                        sec_alpha_ol.append(p_tag)
                        # sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                        p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                        if main_sec_alpha == 'z':
                            main_sec_alpha = 'a'
                        else:
                            main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                        ol_count += 1

                        if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                            num_ol = self.soup.new_tag("ol")
                            li_tag = self.soup.new_tag("li")
                            li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)

                            num_cur_tag = li_tag
                            cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                            num_id = f'{sec_alpha_cur_tag.get("id")}'
                            li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                            num_ol.append(li_tag)
                            p_tag.string = ""
                            p_tag.append(num_ol)
                            num_count = 2
                            cap_alpha = "A"

                            if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)', current_tag_text):
                                cap_alpha_ol = self.soup.new_tag("ol", type="A")
                                inner_li_tag = self.soup.new_tag("li")
                                cap_alpha_cur_tag = inner_li_tag
                                inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)', '', current_tag_text)
                                cur_tag = re.search(r'^\((?P<cid>[a-z])\)(\s)?\((?P<pid>1)\)\s?\((?P<nid>A)\)',
                                                    current_tag_text)
                                cap_alpha_id = f'{num_cur_tag.get("id")}'
                                inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                                cap_alpha_ol.append(inner_li_tag)
                                num_cur_tag.string = ""
                                num_cur_tag.append(cap_alpha_ol)
                                cap_alpha = "B"

                                if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', current_tag_text):
                                    roman_ol = self.soup.new_tag("ol", type="i")
                                    inner_li_tag = self.soup.new_tag("li")
                                    roman_cur_tag = inner_li_tag
                                    inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', '',
                                                                 current_tag_text)
                                    prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                                    inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                                    roman_ol.append(inner_li_tag)
                                    cap_alpha_cur_tag.string = ""
                                    cap_alpha_cur_tag.append(roman_ol)
                                    small_roman = "ii"

                        if re.search(rf'^\([a-z]+\)\s*\(i\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="i")
                            li_tag = self.soup.new_tag("li")
                            li_tag.string = re.sub(r'^\([a-z]+\)\s*\(i\)', '', current_tag_text)
                            roman_cur_tag = li_tag
                            cur_tag1 = re.search(r'^\((?P<cid>[a-z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                            prev_id1 = f'{sec_alpha_cur_tag.get("id")}'
                            li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                            roman_ol.append(li_tag)
                            p_tag.string = ""
                            p_tag.append(roman_ol)
                            small_roman = "ii"



                else:
                        roman_ol.append(p_tag)

                        rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                        p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                        p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)

                        small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()


                if re.search(rf'^\([ivx]+\)\s*\(a\)', current_tag_text):
                    inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivxl]+\)\s*\(a\)', '', current_tag_text)
                    inner_sec_alpha_cur_tag = li_tag

                    inner_sec_alpha_id = f'{roman_cur_tag.get("id")}'
                    li_tag["id"] = f'{roman_cur_tag.get("id")}a'

                    inner_sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_sec_alpha_ol)
                    inner_sec_alpha = 'b'

                if re.search(rf'^\([ivx]+\)\s*\(a\)\s*\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivxl]+\)\s*\(a\)\s*\(1\)', '', current_tag_text)
                    innernum_cur_tag = li_tag

                    inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}1'
                    inner_num_ol.append(li_tag)
                    inner_sec_alpha_cur_tag.string = ""
                    inner_sec_alpha_cur_tag.append(inner_num_ol)

                    inner_numcount = 2

            elif re.search(rf'^\({inner_cap_alpha}\)', current_tag_text) and innernum_cur_tag:
                p_tag.name = "li"
                inner_cap_alpha_cur_tag1 = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    inner_cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inner_cap_alpha_ol1)
                    innernum_cur_tag.append(inner_cap_alpha_ol1)
                    inner_cap_alpha_id1 = f"{innernum_cur_tag.get('id')}"

                else:
                    inner_cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{inner_cap_alpha_id1}{inner_cap_alpha}'
                p_tag.string = re.sub(rf'^\({inner_cap_alpha}\)', '', current_tag_text)
                if inner_cap_alpha == "Z":
                    inner_cap_alpha ='A'
                else:
                    inner_cap_alpha = chr(ord(inner_cap_alpha) + 1)

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p" :
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                cap_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None
                roman_cur_tag = None
                num_count = 1
                # inner_num_count = 1

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)

                    if num_cur_tag:
                        num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = f"{num_cur_tag.get('id')}"

                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"

                    elif inner_num_cur_tag:
                        inner_num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = f"{inner_num_cur_tag.get('id')}"

                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"


                else:
                    sec_alpha_ol.append(p_tag)



                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                if main_sec_alpha =='z':
                    main_sec_alpha = 'a'
                else:
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                ol_count += 1
                num_cur_tag = None

                if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)

                    num_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                    num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(num_ol)
                    num_count = 2
                    cap_alpha = "A"

                    if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        cap_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)\s*\((?P<nid>A)\)', current_tag_text)
                        cap_alpha_id = f'{num_cur_tag.get("id")}'

                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                        cap_alpha_ol.append(inner_li_tag)
                        num_cur_tag.string = ""
                        num_cur_tag.append(cap_alpha_ol)
                        cap_alpha = "B"
                        small_roman = 'i'

                        if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="i")
                            inner_li_tag = self.soup.new_tag("li")
                            roman_cur_tag = inner_li_tag
                            inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', '', current_tag_text)
                            prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                            inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                            roman_ol.append(inner_li_tag)
                            cap_alpha_cur_tag.string = ""
                            cap_alpha_cur_tag.append(roman_ol)
                            small_roman = "ii"

                if re.search(rf'^\([a-z]+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]+\)\s*\(i\)', '', current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                    prev_id1 = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"



            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = "A"
                small_roman = 'i'
                roman_cur_tag = None
                cap_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    if sec_alpha_cur_tag:
                        num_id = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol)

                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")

                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"

                    else:
                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    num_ol.append(p_tag)

                p_tag["id"] = f'{num_id}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1


                if re.search(rf'^\([0-9]+\)\s*\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag

                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*\((?P<pid>A)\)', current_tag_text)
                    cap_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"
                    small_roman = 'i'

                    if re.search(rf'^\([0-9]+\)\s*\(A\)\s*\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        roman_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([0-9]+\)\s*\(A\)\s*\(i\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[0-9]+)\)(\s)?\((?P<pid>A)\)\s?\((?P<nid>i)\)', current_tag_text)
                        prev_id1 = f'{num_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}{cur_tag.group("nid")}'
                        roman_ol.append(inner_li_tag)
                        cap_alpha_cur_tag.string = ""
                        cap_alpha_cur_tag.append(roman_ol)
                        small_roman = "ii"

                    if re.search(rf'^\([0-9]+\)\s*\(A\)\s*\(i\)\s*\(a\)', current_tag_text):
                        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_sec_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([0-9]+\)\s*\(A\)\s*\(i\)\s*\(a\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[0-9]+)\)(\s)?\((?P<pid>A)\)\s?\((?P<nid>i)\)\s*\((?P<id>a)\)', current_tag_text)
                        inner_sec_alpha_id = f'{roman_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag.group("id")}'
                        inner_sec_alpha_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha = "b"


            elif re.search(r'^\([A-Z]\)\([A-Z]\)(\([A-Z]\))*', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_ol.append(p_tag)

                p_tag_id = re.search(rf'^\((?P<cap>[A-Z])\)\((?P<cap1>[A-Z])\)(\((?P<cap2>[A-Z])\))*',
                                     current_tag_text)
                if p_tag_id.group("cap2"):
                    p_tag[
                        "id"] = f'{cap_alpha_id}{p_tag_id.group("cap")}{p_tag_id.group("cap1")}{p_tag_id.group("cap2")}'
                    p_tag.string = re.sub(rf'^\([A-Z]\)\([A-Z]\)', '', current_tag_text)
                elif p_tag_id.group("cap1"):
                    p_tag["id"] = f'{cap_alpha_id}{p_tag_id.group("cap")}{p_tag_id.group("cap1")}'
                    p_tag.string = re.sub(rf'^\([A-z]\)\([A-Z]\)(\([A-Z]\))', '', current_tag_text)



            elif re.search(rf'^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                inner_sec_alpha = 'a'
                inner_sec_alpha_cur_tag = None

                roman_cur_tag = None
                small_roman = 'i'

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    if num_cur_tag:
                        num_cur_tag.append(cap_alpha_ol)
                        cap_alpha_id = num_cur_tag.get("id")
                    else:
                        cap_alpha_id = p_tag.find_previous("li").get("id")
                        p_tag.find_previous("li").append(cap_alpha_ol)
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                if cap_alpha == "Z":
                    cap_alpha ='A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)



                if re.search(rf'^\([A-Z]+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)', '', current_tag_text)

                    roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[A-Z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"


                    if re.search(rf'^\([A-Z]+\)\s*\(i\)\s*\(a\)', current_tag_text):
                        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_sec_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)\s*\(a\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[A-Z]+)\)(\s)?\((?P<pid>i)\)\s?\((?P<nid>a)\)',
                                            current_tag_text)
                        inner_sec_alpha_id = f'{cap_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}{cur_tag.group("nid")}'
                        inner_sec_alpha_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha = 'b'

                    if re.search(rf'^\([A-Z]+\)\s*\(i\)\s*\(a\)\s*\(1\)', current_tag_text):
                        inner_num_ol = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        innernum_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)\s*\(a\)\s*\(1\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[A-Z]+)\)(\s)?\((?P<pid>i)\)\s?\((?P<nid>a)\)',
                                            current_tag_text)
                        inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}1'
                        inner_num_ol.append(inner_li_tag)
                        inner_sec_alpha_cur_tag.string = ""
                        inner_sec_alpha_cur_tag.append(inner_num_ol)
                        inner_numcount = 2



            elif re.search(rf'^{inner_cap_alpha}\. ', current_tag_text) :
                p_tag.name = "li"
                inner_cap_alpha_cur_tag = p_tag
                inner_num_count = 1


                if re.search(r'^A\.', current_tag_text):
                    inner_cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inner_cap_alpha_ol)

                    if section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")
                        inner_cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"

                    else:
                        inner_cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    inner_cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inner_cap_alpha_id}{inner_cap_alpha}'
                p_tag.string = re.sub(rf'^{inner_cap_alpha}\.', '', current_tag_text)
                if inner_cap_alpha == "Z":
                    inner_cap_alpha ='A'
                else:
                    inner_cap_alpha = chr(ord(inner_cap_alpha) + 1)




            elif re.search(rf'^{inner_num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_num_cur_tag = p_tag
                inner_alpha = "a"
                small_roman = 'i'
                # main_sec_alpha = 'a'

                if re.search(r'^1\.', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if inner_cap_alpha_cur_tag:
                        inner_cap_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = inner_cap_alpha_cur_tag.get('id')
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = cap_alpha_cur_tag.get('id')
                    elif inner_alpha_cur_tag:
                        inner_alpha_cur_tag.append(inner_num_ol)
                        num_id1 =inner_alpha_cur_tag.get('id')
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = sec_alpha_cur_tag.get('id')


                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group("sid")
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"

                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"


                else:
                    inner_num_ol.append(p_tag)

                p_tag["id"] = f'{num_id1}{inner_num_count}'
                p_tag.string = re.sub(rf'^{inner_num_count}\.', '', current_tag_text)
                inner_num_count += 1


            elif re.search(rf'^{inner_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_alpha_cur_tag = p_tag
                small_roman1 = "i"


                if re.search(r'^a\.', current_tag_text):
                    inner_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inner_alpha_ol)
                    inner_num_cur_tag.append(inner_alpha_ol)
                    inner_alpha_id = f"{inner_num_cur_tag.get('id')}"

                else:
                    inner_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inner_alpha_id}{inner_alpha}'
                p_tag.string = re.sub(rf'^{inner_alpha}\.', '', current_tag_text)
                inner_alpha = chr(ord(inner_alpha) + 1)

            elif re.search(rf'^{small_roman1}\. ', current_tag_text) and p_tag.name == "p" :
                p_tag.name = "li"
                roman_cur_tag1 = p_tag
                inner_sec_alpha = 'a'

                if re.search(r'^i\.', current_tag_text):
                    roman_ol1 = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)

                    if inner_alpha_cur_tag:
                        inner_alpha_cur_tag.append(roman_ol1)
                        prev_id1 = inner_alpha_cur_tag.get("id")
                    else:
                        inner_num_cur_tag.append(roman_ol1)
                        prev_id1 = inner_num_cur_tag.get("id")
                else:
                        roman_ol1.append(p_tag)

                rom_head = re.search(r'^(?P<rom>[ivxl]+)\.', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(rf'^{small_roman1}\.', '', current_tag_text)

                small_roman1 = roman.toRoman(roman.fromRoman(small_roman1.upper()) + 1).lower()


            elif re.search(rf'^\({main_sec_alpha}{main_sec_alpha}\)',current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                cap_alpha_cur_tag = None
                num_cur_tag = None
                roman_cur_tag = None
                num_count = 1

                sec_alpha_ol.append(p_tag)
                p_tag.string = re.sub(rf'^\({main_sec_alpha}{main_sec_alpha}\)', '', current_tag_text)
                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}{main_sec_alpha}'
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)



            if p_tag.name in ['h3', 'h4', 'h5'] or re.search(r'SECTION \d+\.',current_tag_text):
                cap_alpha = 'A'
                cap_alpha_cur_tag = None
                num_count = 1
                ol_count = 1
                inner_numcount = 1
                inner_num_count = 1
                main_sec_alpha = 'a'
                inner_sec_alpha = 'a'
                inner_alpha ='a'
                inner_cap_alpha = 'A'
                inner_alpha_cur_tag =  None
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None
                inner_cap_alpha_cur_tag = None
                innernum_cur_tag = None
                inner_num_cur_tag = None
                num_cur_tag = None
                cap_alpha1 = "A"
                n_tag = None
                cap_alpha2 = 'a'
                cap_roman_tag = None
                cap_alpha1_cur_tag = None
                sec_alpha_cur_tag1 = None
                ol_head_tag = None
                roman_cur_tag = None
                roman_cur_tag1 = None

        print('ol tags added')















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
        ol_count = 0
        sub_ol_id = None
        sec_sub_ol = None
        sec_sub_li = None
        sub_alpha_ol = None
        prev_chap_id = None
        p_tag = self.soup.find('p', {'class': self.tag_type_dict['ol_p']})
        while p_tag:

            set_p_tag = True
            if not re.search(r'\w+', p_tag.get_text()):
                continue
            if chap_id := p_tag.findPrevious(lambda tag: tag.name in ['h2', 'h3']):
                sec_id = chap_id["id"]
                if sec_id != prev_chap_id:
                    ol_count = 0
                prev_chap_id = sec_id
                set_string = True
                data_str = p_tag.get_text()
                p_tag.string = data_str
                if re.search(rf'^\({main_sec_alpha}\)', data_str):
                    cap_alpha = 'A'
                    sec_sub_ol = None
                    p_tag.name = 'li'
                    previous_alpha_li = p_tag
                    if main_sec_alpha == 'a':
                        ol_count += 1
                        p_tag.wrap(alpha_ol)
                    else:
                        alpha_ol.append(p_tag)
                    num_ol = self.soup.new_tag("ol")
                    previous_num_li = None
                    previous_inner_li = None
                    ol_head = 1
                    small_roman = 'i'
                    alpha_li_id = f'{sec_id}ol{ol_count}{main_sec_alpha}'
                    p_tag['id'] = alpha_li_id
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                    if re.search(r'^\(\w\)\s?\(\d\)', data_str):
                        li_num = re.search(r'^\(\w\)\s?\((?P<num>\d)\)', data_str).group('num')
                        p_tag.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
                        new_li = self.soup.new_tag('p')
                        new_li.string = re.sub(r'^\(\w\)\s?\(\d\)', '', data_str)
                        p_tag.string.replace_with(new_li)
                        new_li.wrap(num_ol)
                        new_li.name = 'li'
                        previous_num_li = new_li
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        set_string = False
                        ol_head += 1
                        num_li_id = f'{alpha_li_id}{li_num}'
                        new_li['id'] = num_li_id
                        if re.search(r'^\(\w\)\s?\(\d\)\s?\(\w\)', data_str):
                            li_alpha = re.search(r'^\(\w\)\s?\(\d\)\s?\((?P<alpha>\w)\)', data_str).group('alpha')
                            new_li = self.soup.new_tag('p')
                            new_li.string = re.sub(r'^\(\w+\)\s?\(\d\)\s?\(\w\)', '', data_str)
                            previous_num_li.string.replace_with(new_li)
                            new_li.wrap(cap_alpha_ol)
                            new_li.name = 'li'
                            previous_inner_li = new_li
                            inner_ol = self.soup.new_tag("ol", type="i")
                            new_li['id'] = f'{num_li_id}{li_alpha}'
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            else:
                                cap_alpha = chr(ord(cap_alpha) + 1)
                elif re.search(r'^\(\w+(\.\d)?\)', p_tag.text.strip()):
                    if re.search(r'^\(\d+\.\d\)', p_tag.text.strip()):
                        if previous_num_li:
                            previous_num_li.append(p_tag)
                        continue

                    if re.search(rf'^\({ol_head}\)', p_tag.text.strip()):
                        cap_alpha = "A"
                        small_roman = 'i'
                        incr_ol_count = False
                        if previous_alpha_li:
                            previous_alpha_li.append(p_tag)
                        previous_num_li = p_tag
                        p_tag.name = "li"
                        if ol_head == 1:
                            incr_ol_count = True
                            p_tag.wrap(num_ol)
                        else:
                            num_ol.append(p_tag)
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        previous_inner_li = None
                        if alpha_li_id:
                            num_li_id = f'{alpha_li_id}{ol_head}'
                        else:
                            if incr_ol_count:
                                ol_count += 1
                            num_li_id = f'{sec_id}ol{ol_count}{ol_head}'
                        p_tag['id'] = num_li_id
                        ol_head += 1
                        if re.search(r'^\(\d+\)\s?\(\w+\)', p_tag.text.strip()):
                            small_roman = 'i'
                            li_alpha = re.search(r'^\(\d+\)\s?\((?P<alpha>\w+)\)', p_tag.text.strip()).group('alpha')
                            new_li = self.soup.new_tag('p')
                            new_li.string = re.sub(r'^\(\d+\)\s?\(\w+\)', '', p_tag.text.strip())
                            p_tag.string.replace_with(new_li)
                            new_li.wrap(cap_alpha_ol)
                            new_li.name = 'li'
                            previous_inner_li = new_li
                            set_string = False
                            inner_ol = self.soup.new_tag("ol", type="i")
                            cap_alpha_li_id = f'{num_li_id}{li_alpha}'
                            new_li['id'] = f'{num_li_id}{li_alpha}'
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            else:
                                cap_alpha = chr(ord(cap_alpha) + 1)
                            if re.search(r'^\(\d+\)\s?\([A-Z]\)\s?\(\w+\)', data_str):
                                li_roman = re.search(r'^\(\d+\)\s?\([A-Z]\)\s?\((?P<roman>\w+)\)', data_str).group('roman')
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\(\d+\)\s?\([A-Z]\)\s?\(\w+\)', '', data_str)
                                p_tag.string.replace_with(new_li)
                                new_li.wrap(inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                new_li['id'] = small_roman_id
                                previous_roman_li = new_li
                    elif re.search(r'^\(\d+\)', p_tag.text.strip()) and sec_sub_ol:
                        digit = re.search(r'^\((?P<sec_digit>\d+)\)', data_str).group('sec_digit')
                        sec_sub_li = self.soup.new_tag('li')
                        sec_sub_li.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
                        sec_sub_li['id'] = f"{sub_ol_id}{digit}"
                        sec_sub_ol.append(sec_sub_li)
                        sub_alpha_ol = self.soup.new_tag('ol', type='A')
                        sec_sub_li.append(sub_alpha_ol)
                        p_tag.decompose()
                        continue
                    elif previous_num_li:
                        if cap_alpha_match := re.search(fr'^\({cap_alpha}+\)|(^\([A-Z]+(\.\d+)?\))', p_tag.text.strip()):
                            small_roman = 'i'
                            li_alpha = re.search(r'^\((?P<alpha>\w+(\.\d+)?)\)', data_str).group('alpha')
                            previous_num_li.append(p_tag)
                            p_tag.name = 'li'
                            previous_roman_li = None
                            if sec_sub_ol:
                                p_tag['id'] = f'{sec_sub_li["id"]}{li_alpha}'
                                if re.search(r'\d+', cap_alpha_match.group(0)):
                                    p_tag.name = 'p'
                                    previous_inner_li.apend(p_tag)
                                else:
                                    sub_alpha_ol.append(p_tag)
                            else:
                                if re.search(r'\d+', cap_alpha_match.group(0)):
                                    p_tag.name = 'p'
                                    previous_inner_li.insert(len(previous_inner_li.contents), p_tag)
                                else:
                                    p_tag.wrap(cap_alpha_ol)
                                    previous_inner_li = p_tag
                                inner_ol = self.soup.new_tag("ol", type="i")
                                cap_alpha_li_id = f'{num_li_id}{li_alpha}'
                                p_tag['id'] = cap_alpha_li_id
                            if re.search(r'^\([A-Z]\)\s?\(\w+\)', p_tag.text.strip()):
                                li_roman = re.search(r'^\([A-Z]\)\s?\((?P<roman>\w+)\)', data_str).group('roman')
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\([A-Z]\)\s?\(\w+\)', '', p_tag.text.strip())
                                p_tag.string.replace_with(new_li)
                                new_li.wrap(inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                p_tag['id'] = small_roman_id
                                previous_roman_li = new_li
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            elif not re.search(r'\d+', cap_alpha_match.group(0)):
                                cap_alpha = chr(ord(cap_alpha) + 1)
                        elif previous_inner_li:
                            if alpha_match := re.search(r'^\((?P<alpha>[a-z])+\)', p_tag.text.strip()):
                                li_roman = alpha_match.group('alpha')
                                if li_roman.upper() == roman.toRoman(roman.fromRoman(small_roman.upper()) + 1):
                                    small_roman = li_roman
                                    previous_inner_li.append(p_tag)
                                    p_tag.name = 'li'
                                    p_tag.wrap(inner_ol)
                                    roman_ol = self.soup.new_tag("ol", type="I")
                                    small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                    p_tag['id'] = small_roman_id
                                    previous_roman_li = p_tag
                                    small_letter_inner_ol = self.soup.new_tag("ol", type="a")
                                elif previous_roman_li:
                                    small_letter_inner_ol.append(p_tag)
                                    p_tag.name = 'li'
                                    p_tag.wrap(previous_roman_li)
                                    p_tag['id'] = f'{small_roman_id}{li_roman}'
                            elif sub_sec_match := re.search(r'^\(\w\.\d\)\s?\((?P<sec_digit>\d+)\)', p_tag.text.strip()):
                                digit_match = re.search(r'^\(\w\.(?P<digit>\d+)\)\s?\((?P<sec_digit>\d+)\)',
                                                        p_tag.text.strip())
                                sub_ol = self.soup.new_tag('ol', Class="sub_ol")
                                sub_ol_id = f"{cap_alpha_li_id}.{digit_match.group('digit')}"
                                sub_li = self.soup.new_tag('li')
                                sub_li.string = sub_sec_match.group()
                                sub_li['id'] = sub_ol_id
                                sub_ol.append(sub_li)
                                sec_sub_ol = self.soup.new_tag('ol')
                                sub_li.append(sec_sub_ol)
                                sec_sub_li = self.soup.new_tag('li')
                                sec_sub_li.string = re.sub(r'^\(\w\.\d+\)\s?\(\d+\)', '', data_str)
                                sec_sub_li['id'] = f"{sub_ol_id}{digit_match.group('sec_digit')}"
                                sec_sub_ol.append(sec_sub_li)
                                sub_alpha_ol = self.soup.new_tag('ol', type='A')
                                sec_sub_li.append(sub_alpha_ol)
                                previous_alpha_li.insert(len(previous_alpha_li.contents), sub_ol)
                                p_tag.decompose()
                            elif previous_roman_li:
                                if re.search(r'^\([A-Z]+\)', p_tag.text.strip()):
                                    li_roman = re.search(r'^\((?P<roman>\w+)\)', data_str).group('roman')
                                    previous_roman_li.append(p_tag)
                                    p_tag.name = 'li'
                                    p_tag.wrap(roman_ol)
                                    p_tag['id'] = f'{small_roman_id}{li_roman}'
                            else:
                                previous_inner_li.insert(len(previous_num_li.contents), p_tag)

                elif re.search(r'^History\.', p_tag.get_text(), re.I) or \
                        re.search(r'^\d+-\d+-\d+', p_tag.find_previous_sibling().get_text()):
                    p_tag = p_tag.find_next_sibling(lambda tag: tag.name == 'p' and
                                                                tag.get('class')[0] in self.tag_type_dict['ol_p'])
                    set_p_tag = False
                    ol_head = 1
                    main_sec_alpha = 'a'
                    cap_alpha = "A"
                    small_roman = 'i'
                    previous_alpha_li = None
                    previous_num_li = None
                    previous_inner_li = None
                    alpha_li_id = None
                    previous_roman_li = None
                    sec_sub_ol = None
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    num_ol = self.soup.new_tag("ol")

                else:
                    if previous_inner_li:
                        previous_inner_li.append(p_tag)
                    elif previous_num_li:
                        previous_num_li.append(p_tag)
                    elif previous_alpha_li:
                        previous_alpha_li.append(p_tag)
                if set_string:
                    p_tag.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
            if set_p_tag:
                p_tag = p_tag.find_next_sibling(lambda tag: tag.name == 'p' and re.search('.+', tag.get_text()))
        print('ol tags added')




    def create_case_notes_nav_tag(self):
        """
            - match and find analysis navigation tag
            - split the contents of tag by line break
            - convert each line to a li
            - create new nav tag and ul tag
            - append each created li to new ul tag
        """
        for case_notes_tag in self.soup.findAll(lambda tag: tag.name == 'h4'
                                                            and re.search('Case Notes', tag.get_text().strip())):

            if not case_notes_tag.find_next_sibling().b:
                case_notes_nav = case_notes_tag.find_next_sibling()
                nav_tag = self.soup.new_tag('nav')
                new_ul = self.soup.new_tag("ul", Class="leaders")
                ul = self.soup.new_tag("ul", Class="leaders")
                previous_li = None
                for headers_text in [s for s in case_notes_nav.get_text().splitlines() if s]:
                    new_li = self.soup.new_tag('li')
                    if header := case_notes_nav.find_next_sibling(lambda tag:
                                                              re.search(rf'^{headers_text.strip()}$', tag.get_text().strip())
                                                              and tag.name == 'h4'):
                        if previous_li and re.search(r'^—|^-', headers_text.strip()):
                            ul.insert(len(ul), new_li)
                            previous_li.append(ul)
                            header_id = re.sub(r'[\s—-]+', '', f'{previous_li.a.attrs.get("href")}{headers_text.strip()}')
                        else:
                            header_id = re.sub(r'[\s—-]+', '', f'#{case_notes_tag.get("id")}{headers_text.strip()}')
                            new_ul.insert(len(new_ul), new_li)
                            previous_li = new_li
                            ul = self.soup.new_tag("ul", Class="leaders")
                        new_a = self.soup.new_tag('a', href=header_id)
                        new_a.string = headers_text
                        new_li.append(new_a)
                        header['id'] = header_id.strip('#')
                nav_tag.append(new_ul)
                case_notes_nav.replace_with(nav_tag)



        print('created analysis tag')



    def remove_or_replace_class_names(self):
        """
            - create dictionary with h4 tags values as key
              with appropriate class name and number of occurance as list of values
            - for each tag in html
            - if tag name is "b" replace it with new span tag with calss name "headbreak"
            - if tag doesnt have any contents and tag name is meta or br delete it
            - if tag only contains § and nothing, unwrap the tag
            - if tag doesnt contain any alpha numeric characters delete the tag
            - if tags value is present in 'notes_headers_dict' change tags name and add class name and id accordingly
        """
        notes_headers_dict = {'Code Commission notes.': ['ccnotes', 0],
                              "Editor's notes.": ['ednotes', 0],
                              'Cross references.': ['crnotes', 0],
                              'Law reviews.': ['lrnotes', 0]}
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
                elif tag.name == 'br':
                    if not tag.parent or tag in tag.parent.contents:
                        tag.decompose()
                continue
            elif re.search(r'^§+$', tag.get_text()):
                tag.unwrap()
                del tag["class"]
                continue
            elif not re.search(r'\w+', tag.get_text()):
                tag.decompose()
                continue

            elif tag.b and tag.b.get_text() in notes_headers_dict.keys() and tag.name != 'b':
                notes_headers_dict[tag.b.get_text().strip()][1] += 1
                class_name = notes_headers_dict[tag.b.get_text().strip()][0]
                notes_id = f't{self.title.zfill(2)}-{class_name}{str(notes_headers_dict[tag.b.get_text().strip()][1]).zfill(2)}'
                chap_id = tag.findPrevious(lambda x: re.search(r'h\d', x.name) and x.name != 'h5')
                if chap_id and chap_id.has_attr('id'):
                    notes_id = f'{chap_id["id"]}-{class_name}{str(notes_headers_dict[tag.b.get_text().strip()][1]).zfill(2)}'
                head = self.soup.new_tag('h5', Class=f'{class_name} lalign')
                head.append(tag.b)
                head['id'] = notes_id
                tag.insert_before(head)
            elif re.search(r'p\d|s\d', str(tag.get('class')), re.I):
                del tag["class"]
            if tag.name == 'p':
                if len(tag.contents) >= 3:
                    if isinstance(tag.contents[-1], element.NavigableString) and not re.search(r'\w', tag.contents[-1]):
                        tag.contents.pop()
                    if tag.contents[-1].name == 'br':
                        tag.contents.pop()

                if tag.b and re.search(r'.+/b>[^\w]+\s?-', str(tag), re.I):
                    if re.search(r'Sodomy statute not changed', tag.b.get_text(), re.I):
                        catch_line_span = self.soup.new_tag('span', Class='catchline boldspan')
                        tag.b.insert_before(catch_line_span)
                        catch_line_span.append(tag.b)
                    else:
                        new_h5 = self.soup.new_tag('h5')
                        new_h5.append(tag.b)
                        new_h5['class'] = 'lalign'
                        tag.insert_before(new_h5)
                # if section_header_match := re.search(r'^\d+-\d+-\d+', tag.get_text().strip(), re.I):
                #     tag.name = 'h3'
                #     chap_tag = tag.find_previous(lambda tag: tag.name == 'h2')
                #     tag['id'] = f'{chap_tag["id"]}{section_header_match.group()}'
                #     if previous_sibling_tag := tag.find_previous(lambda tag: tag.name == 'h3' and
                #                                                              re.search(tag['id'], tag.get('id', ''))):
                #         if pervious_tag_id_num_match := \
                #                 re.search(rf'{tag["id"]}(\.\d)?\.(?P<count>\d+)',
                #                           previous_sibling_tag['id'], re.I):
                #             tag['id'] = f"{tag['id']}.{int(pervious_tag_id_num_match.group('count')) + 1}"
                #         else:
                #             tag['id'] = f"{tag['id']}.1"
            if tag.name in ['h3', 'h2']:
                for value in notes_headers_dict.values():
                    value[1] = 0
            if tag.name == 'b':
                self.tag_to_unwrap.append(tag)
        print('removed class names')

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

    def add_anchor_tags(self):
        """
            - for each nav tag in html
            - using the text of the tag build an id and a reference to a tag
            - ie. 1-2-3 here 1 is title 2 is chapter number and 3 is section number
            - add a property called 'aria-describedby' with value same as previously built reference link
        """
        self.soup = BeautifulSoup(self.soup.prettify(formatter=None), features='lxml')
        for ul in self.soup.findAll('nav'):
            id_num = 0
            li_num = 0
            # chap_header_tag = self.soup.find(
            #     lambda tag: tag.name == 'h2' and re.search(rf'chapter|article', tag.get_text()
            #                                                .strip(), re.I))
            # chap_match = re.search(r'(chapter|article)\s(?P<num>\w+)(?P<name>.+)', chap_header_tag.get_text(),
            #                        re.DOTALL | re.I)
            # chap_reg = fr'{chap_match.group("num")}\.?\s{chap_match.group("name").strip()}'
            if re.search(r'^Subtitle \d', ul.li.get_text().strip()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if st_num_reg := re.search(r'^Subtitle\s(?P<st_num>\d+)', li.get_text().strip()):
                        header_id = f'#t{self.title.zfill(2)}st{st_num_reg.group("st_num").zfill(2)}'
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-cnav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            if re.search('^Chapter', ul.li.get_text().strip()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if chap_no := re.search(r'^Chapter\s(?P<chap_num>\d+([a-z])?)', li.get_text().strip()):
                        header_id = f'#t{self.title.zfill(2)}c{chap_no.group("chap_num").zfill(2)}'
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-cnav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            if re.search('^Subchapter \d', ul.get_text().strip()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if chap_no := re.search(r'^Subchapter\s(?P<sub_chap_num>\d+)', li.get_text().strip()):
                        previous_head = ul.find_previous(lambda tag: tag.name == 'h2' and re.search('^Chapter', tag.get_text().strip()))
                        header_id = f'#{previous_head["id"]}sc{chap_no.group("sub_chap_num").zfill(2)}'
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-cnav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            if re.search('^Subpart \d', ul.get_text().strip()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if chap_no := re.search(r'^Subpart\s(?P<sub_chap_num>\d+)', li.get_text().strip()):
                        previous_head = ul.find_previous(lambda tag: tag.name == 'h2' and re.search('^Part', tag.get_text().strip()))
                        header_id = f'#{previous_head["id"]}sp{chap_no.group("sub_chap_num").zfill(2)}'
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-cnav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            if re.search('^\d+\.', ul.get_text().strip()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if chap_no := re.search(r'(?P<sub_chap_num>\d+)\.', li.get_text().strip()):
                        previous_head = ul.find_previous(lambda tag: tag.name == 'h2' and re.search('^Chapter', tag.get_text().strip()))
                        pvr_id = re.search(r't(?P<tid>\d+)c(?P<cid>\d+)',previous_head["id"])
                        header_id = f'#{previous_head["id"]}s{pvr_id.group("tid")}-{pvr_id.group("cid")}-{chap_no.group("sub_chap_num")}'
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-cnav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)

            elif re.search(r'Sec|^\d+-\w+-\d+(\.\d+)?', ul.find().get_text().strip()):
                for li in ul.findAll('li'):
                    if sec_id_reg := re.search(r'^(?P<sec>\d{1,2}-\d(\w+)?-\d+(\.\d+)?)', li.get_text().strip()):
                        sec_id = sec_id_reg.group('sec')
                    else:
                        sec_id = re.search(r'^(?P<sec>.+)\.?(\s|$)', li.get_text().strip()).group('sec')
                    if chap_no_match := re.search(r'\d+-(?P<chap>\d+([a-z])?)-\d+', sec_id, re.I):
                        li_num += 1
                        chap_no = chap_no_match.group('chap')
                        header_id = f'#t{self.title.zfill(2)}c{chap_no.zfill(2)}s{sec_id}'
                        if li.find_previous_sibling(lambda tag: tag.name == 'li' and
                                                                re.search(header_id, str(tag.a.attrs.get('href')))):
                            id_num += 1
                            header_id = f"{header_id}.1"
                        elif ul.find_previous('nav').find(lambda tag: tag.name == 'a' and
                                                                      re.search(header_id, str(tag.attrs.get('href')))):
                            id_num += 1
                            header_id = f"{header_id}.1"
                        anchor = self.soup.new_tag('a', href=header_id)
                        cleansed_header_id = header_id.strip("#")
                        anchor.attrs['aria-describedby'] = cleansed_header_id
                        li['id'] = f'{cleansed_header_id}-snav{str(li_num).zfill(2)}'
                        anchor.string = li.text
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            elif ul.p and re.search('ANALYSIS', ul.p.get_text()):
                for li in ul.findAll('li'):
                    li_num += 1
                    sec_id = li.findPrevious(lambda tag: tag.name in ['h3', 'h2'] or
                                                         tag.has_attr('class') and
                                                         tag['class'][0] in self.headers_class_dict.values())['id']
                    id_text = re.sub(r'\s|"|\'', '', li.get_text())
                    header_id = f'#{sec_id}-{id_text}'
                    anchor = self.soup.new_tag('a', href=header_id)
                    cleansed_header_id = header_id.strip("#")
                    anchor.attrs['aria-describedby'] = cleansed_header_id
                    li['id'] = f'{cleansed_header_id}-anav{str(li_num).zfill(2)}'
                    anchor.string = li.text
                    if li.string:
                        li.string.replace_with(anchor)
                    else:
                        li.contents = []
                        li.append(anchor)
        print('added anchor tags')

    def clean_html_and_add_cite(self):
        reg_dict = {'ga_court': r'(\d+ (Ga\.) \d+)',
                    'ga_app_court': r'(\d+ Ga\.( App\.) \d+)',
                    'app_court': r'(\d+ S\.E\.(2d)? \d+)',
                    'us_code': r'(\d+ U\.S\.(C\. §)? \d+(\(\w\))?)',
                    's_court': r'(\d+ S\. (Ct\.) \d+)',
                    'l_ed': r'(\d+ L\. (Ed\.) \d+)',
                    'lra': r'(\d+ L\.R\.(A\.)? \d+)',
                    'am_st_r': r'(\d+ Am\. St\.( R\.)? \d+)',
                    'alr': r'(\d+ A\.L\.R\.(2d)? \d+)'}
        cite_p_tags = []
        for tag in self.tag_to_unwrap:
            tag.unwrap()

        for tag in self.soup.findAll(lambda tag: re.search(r"§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                                           r"|\d+ Ga.( App.)? \d+"
                                                           r"|\d+ S.E.(2d)? \d+"
                                                           r"|\d+ U.S.C. § \d+(\(\w\))?"
                                                           r"|\d+ S\. (Ct\.) \d+"
                                                           r"|\d+ L\. (Ed\.) \d+"
                                                           r"|\d+ L\.R\.(A\.)? \d+"
                                                           r"|\d+ Am\. St\.( R\.)? \d+"
                                                           r"|\d+ A\.L\.(R\.)? \d+",
                                                           tag.get_text()) and tag.name == 'p'
                                                 and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            text = str(tag)
            for match in set(
                    x[0] for x in re.findall(r'\b(\d{1,2}-\d(\w+)?-\d+(\.\d+)?(\s?(\(\w+\))+)?)', tag.get_text())):
                inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                tag.clear()
                id_reg = re.search(r'(?P<title>\w+)-(?P<chap>\w+)-(?P<sec>\d+(\.\d+)?)', match.strip())
                title = id_reg.group("title").strip()
                section = re.sub(r'(\(\w+\))+', '', match).strip()
                target = "_self"
                if title.strip() != self.title:
                    a_id = f'gov.ar.code.title.{title.zfill(2)}.html#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'
                    target = "_blank"
                else:
                    a_id = f'#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'
                if ol_reg := re.search(r'(\(\w+\))+', match.strip()):
                    ol_num = re.sub(r'\(|\)', '', ol_reg.group())
                    a_id = f'{a_id}ol1{ol_num}'
                text = re.sub(fr'\s{re.escape(match)}',
                              f' <cite class="ocar"><a href="{a_id}" target="{target}">{match}</a></cite>', inside_text,
                              re.I)
                tag.append(text)

            for key, value in reg_dict.items():
                for match in set(x[0] for x in re.findall(value, tag.get_text(), re.I)):
                    inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
                    tag.clear()
                    text = re.sub(re.escape(match),
                                  f'<cite class="{key}">{match}</cite>',
                                  inside_text, re.I)
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
        # html5validate.validate(soup_str)
        with open(f"../transforms/ar/ocar/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    def replace_tag_names_constitution(self):
        """
            - create dictionary with class names as keys with associated tag name as its value
            - find all the tags in html with specified class names from dict
              and replace tag with associated tag name (p1 -> h1)
            - based on tag name find or build id for that tag
            - create watermark tag and append it with h1 to first nav tag
        """
        tag_dict = {"h2": self.tag_type_dict['head2'],
                    "h3": self.tag_type_dict['head3'],
                    "h4": self.tag_type_dict['head4'], "li": self.tag_type_dict['ul']}

        for key, value in tag_dict.items():
            amendment_num = 0
            ul = self.soup.new_tag("ul", Class="leaders")
            while True:
                p_tag = self.soup.find('p', {"class": value})
                if not p_tag:
                    break
                p_tag.name = key

                if value == self.tag_type_dict['ul']:
                    if p_tag.findPrevious().name != 'li':
                        p_tag.wrap(ul)
                    elif p_tag.findPrevious().name == 'li':
                        ul.append(p_tag)
                    if p_tag.findNext().has_attr('class') and \
                            p_tag.findNext()['class'][0] != self.tag_type_dict['ul']:
                        new_nav = self.soup.new_tag('nav')
                        ul.wrap(new_nav)
                        ul = self.soup.new_tag("ul", Class="leaders")
                if key == 'h2':
                    if chap_section_regex := re.search(r'^(ARTICLE|AMEND(MENT)?(\.)?)\s(?P<chap>\w+)',
                                                       p_tag.get_text().strip(), re.I):
                        if re.search('^AMEND', p_tag.get_text().strip(), re.I):
                            p_tag['id'] = f"{self.title}-am{chap_section_regex.group('chap').zfill(2)}"
                        else:
                            p_tag['id'] = f"{self.title}-a{chap_section_regex.group('chap').zfill(2)}"
                    elif re.search('amendments', p_tag.get_text().strip(), re.I):
                        amendment_num += 1
                        p_tag['id'] = f"{self.title}-amendment{str(amendment_num).zfill(2)}"
                elif key == 'h3':
                    if chap_section_regex := re.search(r'^§\s(?P<sec>\w+(-\w+)?)\.',
                                                       p_tag.get_text().strip(), re.I):
                        if re.search('paragraph', p_tag.get_text().strip(), re.I):
                            p_tag['class'] = 'paragraph_head'
                            parent = p_tag.find_previous_sibling(lambda tag: tag.name in 'h3'
                                                                             and not re.search('paragraph',
                                                                                               tag.get_text().strip()
                                                                                               , re.I))
                            p_tag['id'] = f"{parent['id']}p{chap_section_regex.group('sec').zfill(2)}"
                        else:
                            parent = p_tag.find_previous_sibling(lambda tag: tag.name == 'h2' and tag.get('id'))
                            p_tag['id'] = f"{parent['id']}s{chap_section_regex.group('sec').zfill(2)}"
                    elif amendment_num_reg := re.search(r'Amend\s\.(?P<amend>\w+)',
                                                        p_tag.get_text().strip(), re.I):
                        p_tag['class'] = 'amendment_head'
                        parent = p_tag.find_previous_sibling(lambda tag: tag.name in 'h2'
                                                                         and re.search('^Amend',
                                                                                       tag.get_text().strip(), re.I))
                        p_tag['id'] = f"{parent['id']}am{amendment_num_reg.group('amend')}"
                elif key == 'h4':
                    if self.headers_class_dict.get(p_tag.get_text()):
                        p_tag['class'] = self.headers_class_dict.get(p_tag.get_text())
                    p_tag['id'] = re.sub(r'\s+|\'', '', f'{self.title.zfill(2)}-{p_tag.get_text()}')
                    if re.search(r'^\d', p_tag.get_text()):
                        chap_id = p_tag.find_previous_sibling(lambda tag: re.search('^[a-zA-Z]', tag.get_text())
                                                                          and tag.name != 'h5' and re.search(r'h\d',
                                                                                                             tag.name))
                    elif not p_tag.has_attr('class') or p_tag['class'] not in self.headers_class_dict.values():
                        chap_id = p_tag.find_previous(lambda tag: tag.name in ['h2', 'h3'] or tag.has_attr('class') and
                                                                  tag['class'] in self.headers_class_dict.values())
                    else:
                        chap_id = p_tag.findPrevious(lambda tag: tag.name != 'h4' and re.search(r'h\d', tag.name))
                    if chap_id and chap_id.has_attr('id'):
                        id_text = re.sub(r'\s|"|\'', '', p_tag.get_text())
                        p_tag['id'] = f'{chap_id["id"]}-{id_text}'
                    if p_tag.find_previous(lambda tag: p_tag['id'] == tag.get('id', '')):
                        p_tag['id'] = f"{p_tag['id']}.1"
                if not re.search(r'\w+', p_tag.get_text()):
                    p_tag.decompose()

        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        h1_tag = self.soup.find(lambda tag: re.search('^Constitution', tag.get_text(), re.I))
        h1_tag.name = 'h1'
        watermark_p = self.soup.new_tag('p', Class='transformation')
        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                        datetime.now().date())
        h1_tag.insert_before(watermark_p)
        title_tag = h1_tag
        chap_nav = self.soup.find('nav')
        chap_nav.insert(0, watermark_p)
        chap_nav.insert(1, title_tag)
        for tag in self.soup.findAll('span'):
            tag.unwrap()

    def add_anchor_constitution(self):
        for nav in self.soup.findAll('nav'):
            new_p = self.soup.new_tag('p')
            # if not re.search(r'^§ \d|^AMEND', nav.get_text(), re.I):
            #     print(nav)
            #     new_p.string = nav.find('li').get_text()
            #     if nav.h1:
            #         nav.h1.insert_after(new_p)
            #     else:
            #         nav.insert(0, new_p)
            #     nav.find('li').decompose()



            if re.search('preamble', new_p.get_text(), re.I):
                amendment_num = 0
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^Article (\d+)', li.get_text()):
                        article_num = roman_match.group(1)
                        header_id = f'{self.title}-a{article_num.zfill(2)}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.get_text()
                        anchor.attrs['aria-describedby'] = header_id
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
                    elif re.search('AMENDMENT|APPENDIX', li.get_text(), re.I):
                        amendment_num += 1
                        header_id = f'{self.title}-amendment{str(amendment_num).zfill(2)}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.get_text()
                        anchor.attrs['aria-describedby'] = header_id
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            elif re.search(r'§ \d+\.', nav.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^§ (\d+)\.', li.get_text()):
                        section_num = roman_match.group(1)
                        parent = nav.find_previous_sibling(lambda tag: tag.name == 'h2' and tag.get('id'))
                        header_id = f'{parent["id"]}s{section_num.zfill(2)}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.get_text()
                        anchor.attrs['aria-describedby'] = header_id
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            # elif re.search('paragraph', new_p.get_text(), re.I):
            #     for li in nav.ul.findAll('li'):
            #         if roman_match := re.search(r'^(\S+)\.', li.get_text()):
            #             paragraph_num = roman_match.group(1)
            #             parent = nav.find_previous_sibling(lambda tag: tag.name in ['h2', 'h3'] and
            #                                                            re.search('^article|^section', tag.get_text(),
            #                                                                      re.I))
            #             header_id = f'{parent["id"]}p{paragraph_num}'
            #             anchor = self.soup.new_tag('a', href=f'#{header_id}')
            #             anchor.string = li.string
            #             anchor.attrs['aria-describedby'] = header_id
            #             li.string.replace_with(anchor)
            elif re.search(r'^amend(ment)?(\.)?', nav.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^AMEND(MENT)?(\.)? (?P<amnum>\d+)', li.get_text()):
                        article_num = roman_match.group('amnum')
                        header_id = f'{self.title}-am{article_num.zfill(2)}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.get_text()
                        anchor.attrs['aria-describedby'] = header_id
                        if li.string:
                            li.string.replace_with(anchor)
                        else:
                            li.contents = []
                            li.append(anchor)
            # elif re.search('^analysis', nav.get_text(), re.I):
            #     for li in nav.ul.findAll('li'):
            #         parent = nav.find_previous_sibling(lambda tag: tag.name in ['h3', 'h2'] or
            #                                                        tag.has_attr('class') and
            #                                                        tag['class'] in self.headers_class_dict.values())
            #         id_text = re.sub(r"\s+|\'", '', li.get_text())
            #         header_id = f'{parent["id"]}-{id_text}'
            #         anchor = self.soup.new_tag('a', href=f'#{header_id}')
            #         anchor.string = li.string
            #         anchor.attrs['aria-describedby'] = header_id
            #         li.string.replace_with(anchor)

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
            self.tag_type_dict = {'head1': r'^Constitution\s+Of\s+The', 'ul': r'^PREAMBLE',
                                  'head4': '^Case Notes', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$',
                                  'head3': r'^§ \d', 'normalp': '^Editor\'s note'}
            self.get_class_name()
            self.remove_junk()
            self.replace_tag_names_constitution()
            self.convert_paragraph_to_alphabetical_ol_tags1()
            self.create_case_notes_nav_tag()
            self.remove_or_replace_class_names()
            self.add_anchor_constitution()
            self.wrap_div_tags()
        else:
            self.get_class_name()
            self.remove_junk()
            self.replace_tags()
            self.convert_paragraph_to_alphabetical_ol_tags1()
            self.create_case_notes_nav_tag()
            self.remove_or_replace_class_names()
            self.add_anchor_tags()
            self.wrap_div_tags()
        self.clean_html_and_add_cite()
        self.write_soup_to_file()
        print(datetime.now() - start_time)


        #--input_file_name gov.ar.code.title.04.html