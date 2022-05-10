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


class GAParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.html_file_name = input_file_name
        self.soup = None
        self.title = None
        self.previous = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.tag_type_dict = {'head1': r'TITLE \d','ul': r'^Chap\.|^Art\.|^Sec\.|^CHAPTER \d|^Article 1', 'head2': r'^CHAPTER \d|^ARTICLE \d|^Article 1',
                              'head4': '^JUDICIAL DECISIONS|OPINIONS OF THE ATTORNEY GENERAL',
                              'ol_p': r'^\([a-z]\)', 'junk1': '^Annotations$', 'normalp': '^Editor\'s note',
                              'article': r'^Article \d$|^Part \d$'}
        self.watermark_text = """Release {0} of the Official Code of Georgia Annotated released {1}. 
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
        with open(f'../transforms/ga/ocga/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
            # class_tag = self.soup.find(
            #     lambda tag: tag.name == 'p' and re.search(
            #         rf'{value}', tag.get_text().strip(), re.I))

            class_tag = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.tag_type_dict.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.tag_type_dict.values() )

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

            if part_class := self.soup.find(lambda tag: tag.name == 'p' and re.search(
                    '^PART', tag.get_text().strip()) and tag.get('class')[0] != self.tag_type_dict['article']):
                if part_class['class'][0] not in self.tag_type_dict.values():
                    self.tag_type_dict['part'] = part_class['class'][0]

            if h3_class_1 := self.soup.find(lambda tag: tag.name == 'p' and re.search(
                    rf'^\d+-\d+-\d+\.', tag.get_text().strip(), re.I) and tag.get('class')[0]
                                                        not in self.tag_type_dict.values()):
                self.tag_type_dict['head3.1'] = h3_class_1['class'][0]

        # self.junk_tag_class.append(
        #     self.soup.find(lambda tag: tag.name == 'p' and tag.get_text().strip() == '')['class'][0])
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
        """
            - create dictionary with class names as keys with associated tag name as its value
            - find all the tags in html with specified class names from dict
              and replace tag with associated tag name (p1 -> h1)
            - based on tag name find or build id for that tag
            - create watermark tag and append it with h1 to first nav tag
        """
        watermark_p = None
        title_tag = None
        tag_dict = {self.tag_type_dict['head1']: "h1", self.tag_type_dict['head2']: "h2",
                    self.tag_type_dict.get('part', ''): "h4",
                    self.tag_type_dict['head3']: "h3", self.tag_type_dict['head4']: "h4",
                    self.tag_type_dict['ul']: "li", self.tag_type_dict['article']: "h5",
                    self.tag_type_dict.get('head3.1', ''): 'h3'
                    }


        for key, value in tag_dict.items():
            ul = self.soup.new_tag("ul", Class="leaders")
            while True:
                p_tag = self.soup.find('p', {"class": key})
                if not p_tag or p_tag.has_attr('Class') and p_tag['Class'] == 'transformation':
                    break
                p_tag.name = value

                if key == self.tag_type_dict['ul']:
                    if p_tag.findPrevious().name == 'li':
                        ul.append(p_tag)
                    elif p_tag.findPrevious().name != 'li':
                        p_tag.wrap(ul)


                    if p_tag.findNext().has_attr('class') and p_tag.findNext()['class'][0] != self.tag_type_dict['ul']:
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
                            r'|^(chapter|article|part)\s(?P<chap>\d+([a-z])?)',
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
                                    p_tag['id'] = f'{p_tag.find_previous("h2",class_="articleh2").get("id")}p{chapter.zfill(2)}'

                                else:
                                    cleansed_chap = re.sub(r'\d+$', '', chap_id["id"])
                                    # p_tag['id'] = f'{cleansed_chap}{chapter.zfill(2)}'
                                    p_tag[
                                        'id'] = f'{p_tag.find_previous("h2", class_="articleh2").get("id")}p{chapter.zfill(2)}'

                                p_tag['class'] = 'parth2'


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
                        """
                            title 34 has section_header with same class name as chapter header 
                            and there was no proper section annotation 
                            ex:CHAPTER 15
                                RESERVED
                             section : 2. Procedure to Elect Coverage, Reject Coverage or Revoke Exemption.
                        """
                        p_tag.name = 'h3'
                        chap_tag = p_tag.find_previous(lambda tag: tag.name == 'h2'
                                                                   and re.search(r'chapter \w+', tag.get_text(), re.I))
                        chap_id = re.search(r'chapter (?P<chap_id>\w+)', chap_tag.get_text(), re.I).group('chap_id')
                        section_id = f'{self.title.zfill(2)}-{chap_id.zfill(2)}-{section_match.group("sec")}'
                        p_tag['id'] = f'{chap_tag["id"]}s{section_id}'

                    elif re.search(r'^Subpart \d+[A-Z]*',p_tag.get_text().strip()):
                        sec_id = re.search(r'^Subpart (?P<sno>\d+[A-Z]*)',p_tag.get_text().strip()).group("sno")
                        p_tag['id'] = f'{p_tag.find_previous("h2",class_="parth2").get("id")}s{sec_id}'

                    else:
                        p_tag.name = 'h5'


                # elif value == 'h4':
                    # chap_tag = p_tag.find_previous('h2')
                    # if self.headers_class_dict.get(p_tag.get_text()):
                    #     p_tag['class'] = self.headers_class_dict.get(p_tag.get_text())
                    # p_tag['id'] = re.sub(r'\s+|\'', '', f't{self.title.zfill(2)}-{p_tag.get_text()}')
                    # part_tag = p_tag.find_previous(
                    #     lambda tag: re.search(r'h\d', tag.name) and tag.name != 'h5' and tag.has_attr('class')
                    #                 and tag['class'] not in self.headers_class_dict.values())
                    # if re.search(r'^\d', p_tag.get_text()):
                    #     chap_id = p_tag.find_previous_sibling(lambda tag: re.search('^[a-zA-Z]', tag.get_text())
                    #                                                       and tag.name != 'h5' and re.search(r'h\d',
                    #                                                                                          tag.name))
                    # elif part_tag and part_tag.has_attr('class') and part_tag['class'] == 'part_header':
                    #     chap_id = part_tag
                    # elif not p_tag.has_attr('class') or p_tag['class'] not in self.headers_class_dict.values():
                    #     chap_id = p_tag.find_previous(lambda tag: tag.name in ['h2', 'h3'] or tag.has_attr('class') and
                    #                                               tag['class'] in self.headers_class_dict.values())
                    # else:
                    #     chap_id = p_tag.find_previous(lambda tag: tag.name in ['h2', 'h3'])
                    # if chap_id and chap_id.has_attr('id'):
                    #     id_text = re.sub(r'\s|"|\'', '', p_tag.get_text())
                    #     p_tag['id'] = f'{chap_id["id"]}-{id_text}'
                    # if self.tag_type_dict.get('part') and key == self.tag_type_dict['part']:
                    #     part_num = re.search(r'^part\s(?P<num>\w+(\.\w+)?)', p_tag.get_text().strip(), re.I).group(
                    #         'num')
                    #     p_tag['class'] = 'part_header'
                    #     p_tag['id'] = f'{chap_tag["id"]}p{part_num.zfill(2)}'
                    # if p_tag.get('class') in self.headers_class_dict.values():
                    #     previous_id_num = 0
                    #     if previous_h4 := p_tag.findPrevious(
                    #             lambda tag: tag.name == 'h4' and re.search(f"{p_tag['id']}\d+$", tag['id'], re.I)):
                    #         previous_id_num = int(re.search(r'\d+$', previous_h4['id'], re.I).group())
                    #     p_tag['id'] = f'{p_tag["id"]}{str(previous_id_num + 1).zfill(2)}'




                elif value == 'h5':
                    if re.search(r'\w+', p_tag.get_text()):

                        # break_span = self.soup.new_tag('span', Class='headbreak')
                        break_span = self.soup.new_tag('br')
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

        cur_id_list = []
        for tag in self.soup.find_all("h4"):
            if re.search(r'\. —$', tag.get_text()) or tag.get_text().isupper():
                h4_text = re.sub(r'\s+','',tag.get_text()).lower()
                h4_id = f'{tag.find_previous({"h3","h2","h1"}).get("id")}-{h4_text}'
                if h4_id in cur_id_list:
                    tag["id"] = f'{h4_id}.1'
                else:
                    tag["id"] = f'{h4_id}'

                cur_id_list.append(tag["id"])

            else:
                tag.name = "p"




        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        if watermark_p:
            chap_nav = self.soup.find('nav')
            chap_nav.insert(0, watermark_p)
            chap_nav.insert(1, title_tag)



        print('tags replaced')

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
        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_ol = self.soup.new_tag("ol", type="i")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")
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
        for p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['ol_p']}):

            if not re.search('\w+', p_tag.get_text()):
                continue
            chap_id = p_tag.findPrevious(lambda tag: tag.name in ['h2', 'h3'])

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

            elif re.search(r'^\([IVX]+\)', p_tag.text.strip()) and cap_alpha not in ['I','V','X']:
                p_tag.name = "li"

                if re.search(r'^\(I\)', p_tag.text.strip()):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    prev_rom_id = p_tag.find_previous("li").get("id")
                    p_tag.find_previous("li").append(cap_roman_ol)
                else:
                    print(p_tag)
                    cap_roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[IVX]+)\)', p_tag.text.strip())
                p_tag["id"] = f'{prev_rom_id}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([IVX]+\)', '', p_tag.text.strip())

            elif re.search(r'^\(\w+(\.\d)?\)', p_tag.text.strip()):
                if re.search(r'^\(\d+\.\d\)', p_tag.text.strip()):
                    if previous_num_li:
                        previous_num_li.append(p_tag)
                    continue

                if re.search(rf'^\({ol_head}\)', p_tag.text.strip()):
                    cap_alpha = "A"
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
                        if re.search(r'^\([a-z]+\)', p_tag.text.strip()):
                            li_roman = re.search(r'^\((?P<roman>\w+)\)', data_str).group('roman')
                            previous_inner_li.append(p_tag)
                            p_tag.name = 'li'
                            p_tag.wrap(inner_ol)
                            roman_ol = self.soup.new_tag("ol", type="I")
                            small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                            p_tag['id'] = small_roman_id
                            previous_roman_li = p_tag
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

            elif re.search(r'^\([^\)]{6,}\)', p_tag.get_text(), re.I) or \
                    re.search(r'^\d+-\d+-\d+', p_tag.find_previous_sibling().get_text()) or \
                    re.search(r'Section \d+\.\s', p_tag.get_text()):
                ol_head = 1
                main_sec_alpha = 'a'
                cap_alpha = "A"
                previous_alpha_li = None
                previous_num_li = None
                previous_inner_li = None
                alpha_li_id = None
                previous_roman_li = None
                sec_sub_ol = None
                alpha_ol = self.soup.new_tag("ol", type="a")
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
        print('ol tags added')

    def convert_to_numeric_ol_tags(self):
        new_ol_tag_for_p = self.soup.new_tag('ol')
        new_tag = None
        for ol_p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['normalp']}):
            if re.search("^Editor's notes", ol_p_tag.get_text()) and not ol_p_tag.findNext('p').b and \
                    re.search(".+\(1\)", ol_p_tag.findNext('p').get_text().strip('"')):
                new_tag = self.soup.new_tag('li', Class=self.tag_type_dict['normalp'])
                new_string = re.search('\"\(1\)(?P<data>.+)', ol_p_tag.findNext('p').get_text(), re.DOTALL).group(
                    'data')
                new_tag.string = new_string
                ol_p_tag.findNext('p').string = re.sub(rf'\"\(1\)\s?{new_string}', '',
                                                       ol_p_tag.findNext('p').get_text())
            if re.search(r'^\(\d+\)', ol_p_tag.text.strip().strip('"')):
                if ol_p_tag.findPrevious().name != 'li':
                    if not re.search(r'^\(1\)', ol_p_tag.text.strip().strip('"')) and not new_tag:
                        continue
                    elif new_tag:
                        ol_p_tag.insert_before(new_tag)
                        new_tag.wrap(new_ol_tag_for_p)
                    ol_p_tag.wrap(new_ol_tag_for_p)
                elif ol_p_tag.findPrevious().name == 'li':
                    new_ol_tag_for_p.append(ol_p_tag)
                ol_p_tag.name = 'li'
                ol_p_tag.string = re.sub(r'^\"\(\d+\)', '', ol_p_tag.text)
            if ol_p_tag.findNext('p') and ol_p_tag.findNext('p').b:
                new_tag = None
                new_ol_tag_for_p = self.soup.new_tag('ol')
        print('converted numeric ol')

    def create_analysis_nav_tag(self):
        """
            - match and find analysis navigation tag
            - split the contents of tag by line break
            - convert each line to a li
            - create new nav tag and ul tag
            - append each created li to new ul tag
        """
        for analysis_p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['normalp']}):
            if re.search(r'^Editor\'s notes.+ANALYSIS', analysis_p_tag.get_text(), re.DOTALL):
                parent_id = analysis_p_tag.find_previous(lambda tag: tag.name in ['h2', 'h2', 'h3'])['id']
                editors_tag = self.soup.new_tag('p')
                editors_header = self.soup.new_tag('h5', Class='ednotes lalign')
                editors_header.string = "Editor's notes."
                editors_header['id'] = f'{parent_id}-ednotes01'
                editors_text = re.search(r'^Editor\'s notes\.(?P<text>.+)ANALYSIS',
                                         analysis_p_tag.get_text(), re.DOTALL).group('text')
                editors_tag.string = editors_text
                analysis_p_tag.insert_before(editors_header)
                editors_header.insert_after(editors_tag)
            if re.search('<b>ANALYSIS', str(analysis_p_tag)):
                p_tag = self.soup.new_tag('p')
                p_tag.string = 'ANALYSIS'
                p_tag['class'] = 'analysis_nav_header'
                nav_tag = self.soup.new_tag('nav')
                nav_tag.append(p_tag)
                new_ul = self.soup.new_tag("ul", Class="leaders")
                ol = self.soup.new_tag("ol")
                previous_li = None
                for headers_text in analysis_p_tag.get_text().splitlines():
                    if not re.search('ANALYSIS|Editor\'s notes', headers_text.strip()) and headers_text.strip():
                        new_li = self.soup.new_tag('li')
                        new_li.string = headers_text
                        if previous_li and re.search(r'^\d', headers_text.strip()):
                            previous_li.append(new_li)
                            ol.insert(len(ol), new_li)
                        else:
                            new_ul.insert(len(new_ul), new_li)
                            previous_li = new_li
                            ol = self.soup.new_tag("ol")
                nav_tag.append(new_ul)
                analysis_p_tag.replace_with(nav_tag)
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
                if section_header_match := re.search(r'^\d+-\d+-\d+', tag.get_text().strip(), re.I):
                    tag.name = 'h3'
                    chap_tag = tag.find_previous(lambda tag: tag.name == 'h2')
                    tag['id'] = f'{chap_tag["id"]}{section_header_match.group()}'
                    if previous_sibling_tag := tag.find_previous(lambda tag: tag.name == 'h3' and
                                                                             re.search(tag['id'], tag.get('id', ''))):
                        if pervious_tag_id_num_match := \
                                re.search(rf'{tag["id"]}(\.\d)?\.(?P<count>\d+)',
                                          previous_sibling_tag['id'], re.I):
                            tag['id'] = f"{tag['id']}.{int(pervious_tag_id_num_match.group('count')) + 1}"
                        else:
                            tag['id'] = f"{tag['id']}.1"
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
            chap_header_tag = self.soup.find(
                lambda tag: tag.name == 'h2' and re.search(rf'chapter|article', tag.get_text()
                                                           .strip(), re.I))
            chap_match = re.search(r'(chapter|article)\s(?P<num>\w+)(?P<name>.+)', chap_header_tag.get_text(),
                                   re.DOTALL | re.I)
            chap_reg = fr'{chap_match.group("num")}\.?\s{chap_match.group("name").strip()}'
            if re.search(chap_reg, ul.get_text(), re.I) or ul.p and re.search('Chap|Art', ul.p.get_text()):
                for li in ul.findAll('li'):
                    li_num += 1
                    if re.search('^\d+\w?', li.get_text().strip()):
                        chap_no = re.search('^\d+\w?', li.get_text().strip()).group()
                        header_id = f'#t{self.title.zfill(2)}c{chap_no.zfill(2)}'
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

        for li in self.soup.find_all("li"):
            if re.search(r'^\d+\w?\.?\s', li.text.strip()):
                first_nav = self.soup.find("ul")
                if not li.has_attr('id'):
                    chap_no = re.search('^\d+\w?', li.get_text().strip()).group()
                    header_id = f'#t{self.title.zfill(2)}c{chap_no.zfill(2)}'
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


            elif re.search(r'^CHAPTER \d+[A-Z]*', li.text.strip()):
                chap_no = re.search('^CHAPTER (?P<cno>\d+[A-Z]*)', li.get_text().strip()).group('cno')
                header_id = f'#t{self.title.zfill(2)}c{chap_no.zfill(2)}'
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


            elif re.search(r'^Subpart \d+[A-Z]*', li.text.strip()):
                chap_no = re.search('^Subpart (?P<cno>\d+[A-Z]*)', li.get_text().strip()).group('cno')
                header_id = f'#{li.find_previous("h2",class_="parth2").get("id")}s{chap_no}'
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
            elif re.search(r'^PART \d+[A-Z]*', li.text.strip()):
                chap_no = re.search('^PART (?P<cno>\d+[A-Z]*)', li.get_text().strip()).group('cno')
                header_id = f'#{li.find_previous("h2").get("id")}p{chap_no.zfill(2)}'
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

        print('added anchor tags')




    def clean_html_and_add_cite(self):
        """
            - find all the tags in html which matches the pattern of section id(1-1-1)
            - check if the section ids target present in same html
            - if not build a link with proper path for that html using matched text
            - add an anchor tag with reference to that html
            - build a dict with all possible cite tags which are non GA code cites and its patterns
            - find all the tags which matches the pattern
            - replace each tag with new cite tag with same text
        """
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
                    a_id = f'gov.ga.ocga.title.{title.zfill(2)}.html#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'
                    target = "_blank"
                else:
                    a_id = f'#t{title.zfill(2)}c{id_reg.group("chap").zfill(2)}s{section}'
                if ol_reg := re.search(r'(\(\w+\))+', match.strip()):
                    ol_num = re.sub(r'\(|\)', '', ol_reg.group())
                    a_id = f'{a_id}ol1{ol_num}'
                text = re.sub(fr'\s{re.escape(match)}',
                              f'<cite class="ocga"><a href="{a_id}" target="{target}">{match}</a></cite>', inside_text,
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
        with open(f"../../cic-code-ga/transforms/ga/ocga/r{self.release_number}/{self.html_file_name}", "w") as file:
            # file.write(soup_str)
            file.write(soup_str.replace('<br/>', '<br />'))

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
                    if chap_section_regex := re.search(r'^(ARTICLE|section)\s(?P<chap>\w+)\.',
                                                       p_tag.get_text().strip(), re.I):
                        if re.search('^section', p_tag.get_text().strip(), re.I):
                            p_tag.name = 'h3'
                            parent = p_tag.find_previous_sibling(lambda tag: tag.name == 'h2')
                            p_tag['id'] = f"{parent['id']}s{chap_section_regex.group('chap')}"
                        else:
                            p_tag['id'] = f"{self.title}-a{chap_section_regex.group('chap')}"
                    elif re.search('amendments', p_tag.get_text().strip(), re.I):
                        amendment_num += 1
                        p_tag['id'] = f"{self.title}-amendment{str(amendment_num).zfill(2)}"
                elif key == 'h3':
                    if chap_section_regex := re.search(r'(Paragraph|Section)\s(?P<sec>\w+(-\w+)?)\.',
                                                       p_tag.get_text().strip(), re.I):
                        if re.search('paragraph', p_tag.get_text().strip(), re.I):
                            p_tag['class'] = 'paragraph_head'
                            parent = p_tag.find_previous_sibling(lambda tag: tag.name in 'h3'
                                                                             and not re.search('paragraph',
                                                                                               tag.get_text().strip()
                                                                                               , re.I))
                            p_tag['id'] = f"{parent['id']}p{chap_section_regex.group('sec')}"
                        else:
                            parent = p_tag.find_previous_sibling(lambda tag: tag.name == 'h2')
                            p_tag['id'] = f"{parent['id']}s{chap_section_regex.group('sec')}"
                    elif amendment_num_reg := re.search(r'Amendment\s(?P<amend>\w+)]',
                                                        p_tag.get_text().strip(), re.I):
                        p_tag['class'] = 'amendment_head'
                        parent = p_tag.find_previous_sibling(lambda tag: tag.name in 'h2'
                                                                         and re.search('^Amendments',
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
        h1_tag = self.soup.find(lambda tag: re.search('^CONSTITUTION OF THE', tag.get_text()))
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
            if not re.search('^analysis', nav.get_text(), re.I):
                new_p.string = nav.find('li').get_text()
                if nav.h1:
                    nav.h1.insert_after(new_p)
                else:
                    nav.insert(0, new_p)
                nav.find('li').decompose()
            if re.search('article', new_p.get_text(), re.I):
                amendment_num = 0
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^(\S+)\.', li.get_text()):
                        article_num = roman_match.group(1)
                        header_id = f'{self.title}-a{article_num}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.string
                        anchor.attrs['aria-describedby'] = header_id
                        li.string.replace_with(anchor)
                    elif re.search('AMENDMENT|APPENDIX', li.get_text(), re.I):
                        amendment_num += 1
                        header_id = f'{self.title}-amendment{str(amendment_num).zfill(2)}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.string
                        anchor.attrs['aria-describedby'] = header_id
                        li.string.replace_with(anchor)
            elif re.search(r'section|sec\.', new_p.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^(\S+)\.', li.get_text()):
                        section_num = roman_match.group(1)
                        parent = nav.find_previous_sibling(lambda tag: tag.name == 'h2')
                        header_id = f'{parent["id"]}s{section_num}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.string
                        anchor.attrs['aria-describedby'] = header_id
                        li.string.replace_with(anchor)
            elif re.search('paragraph', new_p.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^(\S+)\.', li.get_text()):
                        paragraph_num = roman_match.group(1)
                        parent = nav.find_previous_sibling(lambda tag: tag.name in ['h2', 'h3'] and
                                                                       re.search('^article|^section', tag.get_text(),
                                                                                 re.I))
                        header_id = f'{parent["id"]}p{paragraph_num}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.string
                        anchor.attrs['aria-describedby'] = header_id
                        li.string.replace_with(anchor)
            elif re.search(r'amend\.', new_p.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    if roman_match := re.search(r'^(\S+)\.', li.get_text()):
                        paragraph_num = roman_match.group(1)
                        parent = nav.find_previous_sibling(lambda tag: tag.name == 'h2' and
                                                                       re.search('^amendments', tag.get_text(), re.I))
                        header_id = f'{parent["id"]}am{paragraph_num}'
                        anchor = self.soup.new_tag('a', href=f'#{header_id}')
                        anchor.string = li.string
                        anchor.attrs['aria-describedby'] = header_id
                        li.string.replace_with(anchor)
            elif re.search('^analysis', nav.get_text(), re.I):
                for li in nav.ul.findAll('li'):
                    parent = nav.find_previous_sibling(lambda tag: tag.name in ['h3', 'h2'] or
                                                                   tag.has_attr('class') and
                                                                   tag['class'] in self.headers_class_dict.values())
                    id_text = re.sub(r"\s+|\'", '', li.get_text())
                    header_id = f'{parent["id"]}-{id_text}'
                    anchor = self.soup.new_tag('a', href=f'#{header_id}')
                    anchor.string = li.string
                    anchor.attrs['aria-describedby'] = header_id
                    li.string.replace_with(anchor)

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
            self.tag_type_dict = {'head1': r'^CONSTITUTION OF THE ', 'head2': r'^ARTICLE I', 'ul': r'^PREAMBLE',
                                  'head4': '^JUDICIAL DECISIONS', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$',
                                  'head3': r'^SECTION 1\.|^Paragraph I\.', 'normalp': '^Editor\'s note'}
            self.get_class_name()
            self.remove_junk()
            self.replace_tag_names_constitution()
            self.create_analysis_nav_tag()
            self.remove_or_replace_class_names()
            self.add_anchor_constitution()
            self.wrap_div_tags()
        else:

            self.get_class_name()
            self.remove_junk()
            self.replace_tags()
            self.convert_paragraph_to_alphabetical_ol_tags()
            # self.convert_to_numeric_ol_tags()
            self.create_analysis_nav_tag()
            self.remove_or_replace_class_names()
            self.wrap_div_tags()
            self.add_anchor_tags()
            # except Exception:
            #     pass
        self.clean_html_and_add_cite()
        self.write_soup_to_file()
        print(datetime.now() - start_time)
