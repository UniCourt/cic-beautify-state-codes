"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the start_parse method is called by parser base
    - this method based on the file type(constitution files or title files) decides which methods to run
"""
import collections

from bs4 import BeautifulSoup, Doctype, element
import re
from datetime import datetime
from parser_base import ParserBase

class VTParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^\d+\.', 'head2': '^CHAPTER \d+\.', 'head1': '^TITLE|^The Constitution of the United States of America',
                            'head3': r'^§ \d+(-\d+)*\.','junk': '^Annotations','article':'——————————', 'ol': r'^\(A\)', 'head4': '^History', \
                            'analysishead':'^\d+\.', 'part':'^PART \d',}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name
        self.nd_list = []
        self.navhead = None
        self.snav_count = 1
        self.cnav_count = 1

        self.watermark_text = """Release {0} of the Official Code of Vermont Annotated released {1}.
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
        This document is not subject to copyright and is in the public domain.
        """
        self.headers_class_dict = {'CASE NOTES': 'casenotes'}
        self.start_parse()

    def create_page_soup(self):
        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """

        with open(f'../transforms/vt/ocvt/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
            junk_tag.decompose()

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["article"]) if re.search('^——————————|^APPENDIX',text_junk.text.strip())]
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["ul"]) if
         re.search('^Executive Orders', text_junk.text.strip())]

        for text_junk in self.soup.find_all("p"):
            if len(text_junk.get_text(strip=True)) == 0 and not text_junk.get("class") == [self.class_regex["ul"]]:
                text_junk.decompose()


        if title := re.search(r'title\s(?P<title>\d+)',
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
        for p_tag in self.soup.find_all():
            if re.search('constitution', self.html_file_name):
                if p_tag.get("class") == [self.class_regex["Analysishead"]]:
                    if p_tag.br and re.search(r'^Analysis', p_tag.text.strip()):
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

            else:
                if p_tag.get("class") == [self.class_regex["article"]]:
                    if re.search(r'^SUBCHAPTER\s*\d+([A-Z])*\.', p_tag.text.strip()):
                       p_tag["class"] = "navhead"

                    if re.search(r'^PART\s*\d+([A-Z])*',p_tag.text.strip()):
                        p_tag["class"] = "navhead"

                if p_tag.get("class") == [self.class_regex["ol"]]:
                    if p_tag.br and re.search(r'^Analysis', p_tag.text.strip()):
                        p_tag_text = p_tag.text.strip()
                        p_tag.clear()
                        rept_tag = re.split('\n', p_tag_text)
                        for tag_text in rept_tag:
                            if re.search(r'Analysis',tag_text):
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

    def replace_tags(self):
        cur_id_list = []
        cur_head_list = []

        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if re.search('constitution\.vt', self.html_file_name):
                    self.title_id  = 'constitution-vt'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id  = 'constitution-us'

                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^Constitution of the United States|^CONSTITUTION OF THE STATE OF VERMONT',header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.wrap(self.soup.new_tag("nav"))
                        header_tag['id'] =  self.title_id

                    elif re.search(r'^ARTICLE [IVX]+\.*',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^ARTICLE (?P<ar_id>[IVX]+)\.*', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"

                    elif re.search(r'^AMENDMENT [IVX]+\.*',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^AMENDMENT (?P<ar_id>[IVX]+)\.*', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}am{article_id.zfill(2)}"
                        header_tag["class"] = "amendment"

                    elif re.search(r'^AMENDMENTS',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.sub(r'[\W]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id}"

                    elif re.search(r'^\[.+\]$',header_tag.text.strip()):
                        header_tag.name = "h3"
                        head_tag_text = re.sub(r'[\W\s]', '', header_tag.text.strip()).lower()
                        header_tag['id'] = f"{header_tag.find_previous('h2').get('id')}a{head_tag_text}"

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^CHAPTER [IVX]+',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^CHAPTER (?P<ar_id>[IVX]+)', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}c{article_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["analysis"]]:
                    if re.search(r'^\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        analysis_id = re.search(r'^(?P<a_id>\d+)\.', header_tag.text.strip()).group("a_id")
                        analysis_id1 = f"{header_tag.find_previous('h4').get('id')}-{analysis_id}"
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h4').get('id')}-{analysis_id}"

                    elif re.search(r'^\*\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        analysis_id = re.sub(r'[\W\d]','',header_tag.text.strip()).lower()
                        header_tag['id'] = f"{analysis_id1}-{analysis_id}"


                elif header_tag.get("class") == [self.class_regex["head3"]]:

                    if re.search(r'^§\s\d+\.\[.+\]', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.sub(r'[\W\s\d]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}a{sec_id.zfill(2)}"

                    elif re.search(r'^(Section|§) \d+(-[A-Z])*\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^(Section|§) (?P<sec_id>\d+(-[A-Z])*)\.', header_tag.text.strip()).group('sec_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"

                    elif re.search(r'^\[Amendment [IVX]+\]',header_tag.text.strip()):
                        header_tag.name = "h3"
                        amd_id =  re.search(r'^\[Amendment (?P<ar_id>[IVX]+)', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{amd_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["article"]]:
                    if re.search(r'^Section \d+\.', header_tag.text.strip()):
                        header_tag.name = "h4"
                        sec_id = re.search(r'^Section (?P<sec_id>\d+)\.', header_tag.text.strip()).group('sec_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3').get('id')}-sub{sec_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^ANNOTATIONS|^Annotations', header_tag.text.strip()):
                        header_tag.name = "h4"
                        sec_id = re.sub(r'[\W]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous({'h3','h2','h1'}).get('id')}-{sec_id}"

                elif header_tag.get("class") == [self.class_regex["ul"]] and not re.search('^PREAMBLE|^Section|^Article|^Amendment$|^Chapter',header_tag.text.strip()):
                    header_tag.name = "li"

            else:
                title_pattern = re.compile(r'^(TITLE)\s(?P<title_id>\d+)')
                Subchapter_pattern = re.compile(r'^Subchapter\s*(?P<s_id>\d+([A-Z])*)\.')
                chapter_pattern = re.compile(r'^(CHAPTER)\s(?P<chap_id>\d+([A-Z])*)\.')
                section_pattern = re.compile(r'^§*\s*(?P<sec_id>\d+([a-z]{0,2})*([A-Z])*(\.\d+)*(-\d+([a-z])*)*(\.\d+)*)\.*\s*')

                SUBCHAPTER_pattern = re.compile(r'^SUBCHAPTER\s*(?P<ar_id>\d+([A-Z])*)\.')
                analysis_pattern =  re.compile(r'^(?P<a_id>\d{0,2}(\.\d+)*)\.')
                analysis_pattern1 = re.compile(r'^\*\d+\.')
                part_pattern = re.compile(r'^PART\s*(?P<p_id>\d+([A-Z])*)')
                article_pattern = re.compile(r'ARTICLE (?P<s_id>\d+([A-Z])*)')
                article_pattern1 = re.compile(r'Article\s(?P<s_id>\d+([A-Z])*)')

                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if title_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag.wrap(self.soup.new_tag("nav"))
                        self.title_id = title_pattern.search(header_tag.text.strip()).group('title_id').zfill(2)
                        header_tag['id'] = f"t{self.title_id}"

                    elif  Subchapter_pattern.search(header_tag.text.strip()):
                        if not re.search(r'\[(RESERVED|Reserved)\]',header_tag.text.strip()) :
                            header_tag.name = "h2"

                        article_id = Subchapter_pattern.search(header_tag.text.strip()).group('s_id')
                        header_tag['id'] = f"{header_tag.find_previous('h2',class_='chapter').get('id')}sub{article_id.zfill(2)}"
                        self.snav_count = 1
                    elif article_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = article_pattern.search(header_tag.text.strip()).group('s_id')
                        header_tag['id'] = f"{header_tag.find_previous('h1').get('id')}c{article_id.zfill(2)}"

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if chapter_pattern.search(header_tag.text.strip()):
                        if not re.search(r'\[RESERVED FOR FUTURE USE\.\]|\[RESERVED\]',header_tag.text.strip()) :
                            header_tag.name = "h2"
                        chapter_id = chapter_pattern.search(header_tag.text.strip()).group('chap_id')

                        if header_tag.find_previous('h2', class_ ={'part','subtitle'}):
                            header_tag['id'] = f"{header_tag.find_previous('h2', class_={'part','subtitle'}).get('id')}c{chapter_id.zfill(2)}"
                        else:
                            header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"

                        header_tag["class"] = "chapter"
                        self.navhead = None
                        self.snav_count = 1

                    elif part_pattern.search(header_tag.text.strip()) :
                        header_tag.name = "h2"
                        part_id = part_pattern.search(header_tag.text.strip()).group('p_id')
                        header_tag['id'] = f"{header_tag.find_previous('h1').get('id')}p{part_id.zfill(2)}"
                        header_tag["class"] = "part"

                elif header_tag.get("class") == [self.class_regex["article"]]:

                    if article_pattern.search(header_tag.text.strip()) :
                        header_tag.name = "h2"
                        a_id = article_pattern.search(header_tag.text.strip()).group('s_id')
                        header_tag['id'] = f"{header_tag.find_previous({'h2','h1'}).get('id')}a{a_id.zfill(2)}"
                        header_tag["class"] = "article"
                    elif article_pattern1.search(header_tag.text.strip()):
                        a_id = article_pattern1.search(header_tag.text.strip()).group('s_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous(class_='navhead').get('id')}a{a_id.zfill(2)}"
                        header_tag["class"] = "navhead"

                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    if section_pattern.search(header_tag.text.strip()):
                        if  re.search(r'\[Reserved for future use(\.)?\](\.)?$|^§+\s\d+(-\d+)?(-\d+)?\.\sRepealed\.|\[Reserved\.\]\.$', header_tag.text.strip())\
                                and re.search(r'^§|^PART|^CHAPTER|^SUBCHAPTER',header_tag.find_next_sibling().text.strip()):
                            header_tag.name = "p"
                        else:
                            header_tag.name = "h3"

                    if section_pattern.search(header_tag.text.strip()):
                        if re.search(r'^§*\s*(?P<sec_id>\d+([a-z])*([A-Z])*(\.\d+)*(-\d+([a-z])*)*(\.\d+)*)\.*\s*Repealed',header_tag.text.strip()):
                            section_id = re.search(r'^§*\s*(?P<sec_id>\d+([a-z])*([A-Z])*(\.\d+)*)(-\d+([a-z])*)*(\.\d+)*\.*\s*Repealed',header_tag.text.strip()).group('sec_id')
                        else:
                            section_id = section_pattern.search(header_tag.text.strip()).group('sec_id')
                        curr_head_id = f"{header_tag.find_previous({'h2','h1'}).get('id')}s{section_id.zfill(2)}"

                        if curr_head_id in cur_head_list:
                            header_tag['id'] = f"{header_tag.find_previous({'h2','h1'}).get('id')}s{section_id.zfill(2)}.1."
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{section_id.zfill(2)}"
                        cur_head_list.append(curr_head_id)
                        header_tag["class"] = "section"


                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^History|^Cross References|^ANNOTATIONS|^Annotations|^Annotation|^OFFICIAL COMMENT',header_tag.text.strip()):
                        header_tag.name = "h4"
                        subsection_id = header_tag.text.strip().lower()
                        subsection_id = re.sub('[\s\W]','',subsection_id)
                        curr_tag_id = f"{header_tag.find_previous({'h3','h2','h1'}).get('id')}-{subsection_id}"

                        if curr_tag_id in cur_id_list:
                            header_tag['id'] = f"{header_tag.find_previous({'h3','h2','h1'}).get('id')}-{subsection_id}.1"
                        else:
                            header_tag['id'] = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{subsection_id}"

                        cur_id_list.append(header_tag['id'])

                elif header_tag.get("class") == "navhead":
                    if SUBCHAPTER_pattern.search(header_tag.text.strip()):
                        article_id = SUBCHAPTER_pattern.search(header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2', class_='chapter').get('id')}sub{article_id.zfill(2)}"
                        header_tag["class"] = "navhead"

                    if part_pattern.search(header_tag.text.strip()):
                        article_id = part_pattern.search(header_tag.text.strip()).group('p_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}p{article_id.zfill(2)}"
                        header_tag["class"] = "navhead"

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if not re.search('^Chapter|^Sec\.|^Executive Orders|^Orders',header_tag.text.strip()) and not len(header_tag.get_text(strip=True)) == 0 :
                        header_tag.name = "li"
                elif header_tag.get("class") == [self.class_regex["analysishead"]]:
                    if analysis_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h5"
                        analysis_id = analysis_pattern.search(header_tag.text.strip()).group('a_id')
                        analysis_tag_id = f"{header_tag.find_previous('h4').get('id')}-{analysis_id}"
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h4').get('id')}-{analysis_id}"

                    elif analysis_pattern1.search(header_tag.text.strip()):
                        header_tag.name = "h5"
                        analysis_id1 = re.sub(r'[\s\d.*]+', '', header_tag.text.strip()).lower()
                        header_tag['id'] = f"{analysis_tag_id}-{analysis_id1}"

                elif header_tag.get("class") == [self.class_regex["ol"]]:
                    if  re.search('^\d+\.0', header_tag.text.strip()):
                        header_tag.name = "h4"
                        section_id = re.search('^(?P<sec_id>\d+\.0)', header_tag.text.strip()).group('sec_id')
                        header_tag['id'] = f"{header_tag.find_previous('h3',class_='section').get('id')}sub{section_id.zfill(2)}"
                        header_tag["class"] = "subsection"

        print('tags replaced')


    def create_main_tag(self):
        """
                    - wrap all contents inside main tag(Except chapter index)
                """
        if re.search('constitution', self.html_file_name):
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find("h2")
            for main_tag in self.soup.find_all():
                if main_tag.find_next("h2") == first_chapter_header:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    if main_tag.name == "span" and not main_tag.get("class") == "gnrlbreak":
                        continue
                    elif main_tag.name == "b" or main_tag.name == "i" or main_tag.name == "br":
                        continue
                    else:
                        section_nav_tag.append(main_tag)

        else:
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find(['h2'])

            for main_tag in self.soup.body.findAll():
                if main_tag.find_next("h2") == first_chapter_header:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    if main_tag.name == "span" and not main_tag.get("class") == "gnrlbreak":
                        continue
                    elif main_tag.name == "b" or main_tag.name == "i" or main_tag.name == "br":
                        continue
                    else:
                        section_nav_tag.append(main_tag)


    def create_ul_tag(self):
        """
                   - wrap the list items with unordered tag
               """
        if re.search('us\.html$', self.html_file_name):
            pattern = re.compile('^Article')
        elif re.search('vt\.html$', self.html_file_name):
            pattern = re.compile('^Chapter')


        if re.search('constitution', self.html_file_name):
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if pattern.search(ul_tag.find_previous("p").text.strip()):
                        ul_tag.find_previous("nav").append(ul_tag.find_previous("p"))
                        ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.find_previous("p").wrap(self.soup.new_tag("nav"))
                        ul_tag.find_previous("nav").append(ul_tag)


        else:
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):

                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)

                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if ul_tag.find_previous("p").text.strip() == 'Chapter' or re.search(r'^PART \d+',ul_tag.find_previous("p").text.strip()):

                        ul_tag.find_previous("nav").append(ul_tag.find_previous("p"))
                        ul_tag.find_previous("nav").append(ul_tag)

                    elif ul_tag.find_previous("p").text.isupper():
                        if re.search(r'^SUBCHAPTER',ul_tag.find_previous("p").text.strip()):
                            ul_tag.find_previous('p').wrap(self.soup.new_tag("nav"))
                            ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.find_previous('p').wrap(self.soup.new_tag("nav"))
                        ul_tag.find_previous("nav").append(ul_tag)


        print("ul tag is created")



    def create_chapter_section_nav(self):

        count = 0
        for list_item in self.soup.find_all("li"):

            if re.search('constitution', self.html_file_name):
                if re.search(r'^[IXV]+\.|^Amendments|^Schedule', list_item.text.strip()):
                    if re.match(r'^[IXV]+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<chap>[IXV]+)\.', list_item.text.strip()).group(
                            "chap").zfill(2)
                        if list_item.find_previous("p").text.strip() == 'Chapter':
                            sub_tag = "c"
                        else:
                            sub_tag = "a"
                        if list_item.find_previous("p"):
                            if re.search(r'^Amendment', list_item.find_previous("p").text.strip()):

                                prev_id = list_item.find_previous("h1").get("id")
                                sub_tag = "am"
                            else:
                                prev_id = None
                        else:
                            prev_id = None
                    elif re.search(r'^Amendments', list_item.text.strip()):
                        chap_num = re.sub(r'[\W]', '', list_item.text.strip()).lower()
                        sub_tag = "a"
                        prev_id = None

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                elif re.search(r'^\d+\.\s\[.+\]\.', list_item.text.strip()):
                    chap_num = re.sub(r'[\W\s\d]','',list_item.text.strip()).lower()
                    sub_tag = "a"
                    prev_id = list_item.find_previous("h2").get("id")
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

            else:
                sec_pattern = re.compile(r'^(?P<sec_id>\d+([a-z])*([A-Z])*(\.\d+)*(-\d+([a-z])*)*(\.\d+)*(\.-\d+)*)\.*')
                sec_pattern1 = re.compile(r'^(?P<sec_id>\d[A-Z]*-\d{3}[A-Z]*)\.')
                sec_pattern2 = re.compile(r'^(?P<sec_id>\d+([a-z])*([A-Z])*(\.\d+)*)(,\s)*(-\d+([a-z])*)*(\.\d+)*(\.-\d+)*(\d+)*\.*\s\[(Repealed|Reserved for future use|Redesignated|Reserved)\.\]')

                if sec_pattern1.search(list_item.text.strip()):

                    if sec_pattern2.search(list_item.text.strip()):
                        chap_id = sec_pattern2.search(list_item.text.strip()).group('sec_id')
                    else:
                        chap_id = sec_pattern.search(list_item.text.strip()).group('sec_id')
                    sub_tag = "s"
                    if list_item.find_previous(class_='navhead'):
                        if re.search(r'^SUBCHAPTER \d+|^Article \d+', list_item.find_previous(class_={'navhead', 'chapter'}).text.strip()):
                            prev_id = list_item.find_previous(class_='navhead').get("id")

                    else:
                        prev_id = list_item.find_previous("h2").get("id")

                    self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None)

                elif sec_pattern.search(list_item.text.strip()):
                    if sec_pattern2.search(list_item.text.strip()):
                        chap_id = sec_pattern2.search(list_item.text.strip()).group('sec_id')
                    else:
                        chap_id = sec_pattern.search(list_item.text.strip()).group('sec_id')
                        chap_id = re.sub(r'\.$','',chap_id)

                    if list_item.find_previous(class_={'navhead','chapter'}):
                        if re.search(r'^PART \d+',list_item.find_previous(class_={'navhead','chapter'}).text.strip()):
                            sub_tag = "c"
                        else:
                            sub_tag = "s"
                        prev_id = list_item.find_previous(class_={'navhead','chapter'}).get("id")
                    else:
                        sub_tag = "c"
                        prev_id = list_item.find_previous("h1").get("id")
                    self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None)

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num):
        nav_list = []
        nav_link = self.soup.new_tag('a')
        nav_link.append(list_item.text)

        if re.search('constitution', self.html_file_name):
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                nav_link["href"] = f"#{self.title_id}{sub_tag}{chap_num}"
        else:
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                if sec_num:
                    nav_link["href"] = f"#t{self.title_id.zfill(2)}c{chap_num}s{sec_num}"
                else:
                    nav_link["href"] = f"#t{self.title_id.zfill(2)}{sub_tag}{chap_num}"
        nav_list.append(nav_link)
        list_item.contents = nav_list


    def create_analysis_nav(self):
        alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        salpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})

        if self.soup.find("p", class_='analysisnote'):
            for analysis_tag in self.soup.find_all("p", class_='analysisnote'):
                if re.search(r'^\d+\.*|^-', analysis_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(analysis_tag.text)
                    if re.search(r'^(?P<cid>\d+)\.*', analysis_tag.text.strip()):
                        case_id = re.search(r'^(?P<cid>\d+)\.*', analysis_tag.text.strip()).group("cid").lower()
                        rom_id = f"{analysis_tag.find_previous('h4').get('id')}-{case_id}"
                        nav_link["href"] = f"#{analysis_tag.find_previous('h4').get('id')}-{case_id}"

                    elif re.search(r'^-', analysis_tag.text.strip()):
                        case_id1 = re.sub(r'[\s.]','',analysis_tag.text.strip()).lower()
                        nav_link["href"] = f"#{rom_id}{case_id1}"

                    nav_list.append(nav_link)
                    analysis_tag.contents = nav_list


    def create_analysis_ul(self):
        for analysis_tag in self.soup.find_all(class_='analysisnote'):
            analysis_tag.name = "li"

            if re.search(r'^\d+\.|^-|^\d', analysis_tag.a.text.strip()):
                digit_tag = analysis_tag
                if re.search(r'^1\.', analysis_tag.a.text.strip()):
                    digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    analysis_tag.wrap(digit_ul)
                else:
                    digit_ul.append(analysis_tag)

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


    def convert_paragraph_to_alphabetical_ol_tags1(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        num_count = 1
        num_ol = self.soup.new_tag("ol")
        roman_ol = self.soup.new_tag("ol", type="i")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        num_ol1 = self.soup.new_tag("ol")
        ol_count = 1
        sec_alpha_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha1 = 'A'
        sec_alpha_id = None
        cap_alpha2 = 'A'
        num_tag = None

        for p_tag in self.soup.find_all():

            current_tag_text = p_tag.text.strip()

            if p_tag.i:
                p_tag.i.unwrap()

            if re.search(r'^4\.1 Term of permit\.', current_tag_text):
                print()

            if re.search(r'^\([ivx]+\)', current_tag_text) and main_sec_alpha not in ['i','v','x'] :

                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    prev_class = p_tag.find_previous('h4').get("class")

                    if prev_class == ['subsection']:
                        if sec_alpha_cur_tag:
                            sec_alpha_cur_tag.append(roman_ol)
                            prev_id1 = sec_alpha_cur_tag.get('id')
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                            main_sec_alpha = 'j'
                        elif num_tag:
                            num_tag.append(roman_ol)
                            prev_id1 = num_tag.get('id')
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                        else:
                            prev_id1 = f"{p_tag.find_previous('h4', class_='subsection').get('id')}ol{ol_count}"
                            prev_id1 = f'{prev_id1}'
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                    else:

                            prev_li = p_tag.find_previous("li")
                            prev_li.append(roman_ol)
                            prev_id1 = prev_li.get("id")
                            p_tag["id"] = f'{prev_li.get("id")}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                else:
                    roman_ol.append(p_tag)
                    rom_head = re.search(r'^\((?P<rom>[ivx]+)\)', current_tag_text).group("rom")

                    p_tag["id"] = f'{prev_id1}{rom_head}'
                    p_tag.string = re.sub(r'^\([ivx]+\)', '', current_tag_text)


                if re.search(rf'^\([ivx]+\)\s*\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivx]+\)\s*\(I\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[ivx]+)\)\s*\((?P<pid>I)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}{cur_tag1.group("pid")}'
                    cap_roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_roman_ol)

            elif re.search(r'^\d{0,2}\.\d+(\.\d+)*',current_tag_text) and p_tag.name == 'p':
                p_tag.name = "li"
                num_tag = p_tag
                main_sec_alpha = 'a'



                if re.search(r'^\d\.1\s',current_tag_text):

                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                else:
                    num_ol.append(p_tag)


                prev_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                num_id = re.search(r'^(?P<n_id>\d{0,2}\.\d+(\.\d+)*)',current_tag_text).group("n_id")
                p_tag["id"] = f'{prev_num_id}{num_id}'
                p_tag.string = re.sub(r'^\d{0,2}\.\d+\.*(\d+)*', '', p_tag.text.strip())



            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1
                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol",type="a")
                    p_tag.wrap(sec_alpha_ol)
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    if num_tag:
                        sec_alpha_id = num_tag.get('id')
                        num_tag.append(sec_alpha_ol)

                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s*\(\d+\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(\d+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    num_cur_tag1 = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>\d+)\)', current_tag_text)
                    num_id1 = f'{sec_alpha_id}{cur_tag.group("cid")}'
                    sec_alpha_id = f'{sec_alpha_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{num_id1}{cur_tag.group("pid")}'
                    num_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(num_ol1)
                    num_count = 2
                    cap_alpha1 = 'A'

                    if re.search(r'^\([a-z]\)\s*\(\d+\)\s?\(A\)', current_tag_text):
                        cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(\d+\)\s?\(A\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cap_alpha_cur_tag1 = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s?\((?P<pid>\d+)\)\s\(?(?P<nid>A)\)', current_tag_text)

                        cap_alpha_id1 = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_alpha_ol1.append(inner_li_tag)
                        num_cur_tag1.string = ""
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha1 = 'B'


            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                cap_alpha1 = 'A'
                cap_alpha2 = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous(['h5','h4','h3','h2']).get('id')}ol{ol_count}"

                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1


                if re.search(rf'^\(\d+\)\s*\([A-Z]\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type='A')
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\([A-Z]\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_alpha_cur_tag1 = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
                    if sec_alpha_cur_tag:
                        cap_alpha_id1 = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    else:
                        cap_alpha_id1 = f'{p_tag.find_previous({"h5","h4","h3","h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{p_tag.find_previous({"h5","h4","h3","h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    cap_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol1)
                    cap_alpha1 = 'B'

                    if re.search(r'^\(\d+\)\s?\([A-Z]\)\s?\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s?\([A-Z]\)\s?\(i\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s?\((?P<pid>[A-Z])\)\s\(?(?P<nid>i)\)', current_tag_text)
                        prev_id1 = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        roman_ol.append(inner_li_tag)
                        cap_alpha_cur_tag1.string = ""
                        cap_alpha_cur_tag1.append(roman_ol)


            elif re.search(rf'^\({cap_alpha2}{cap_alpha2}\)', current_tag_text):
                # print(current_tag_text)
                p_tag.name = "li"
                cap_alpha_ol1.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<p_id>{cap_alpha2}{cap_alpha2})\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_alpha_id1}{p_tag_id}'
                p_tag.string = re.sub(rf'^\({cap_alpha2}{cap_alpha2}\)', '', current_tag_text)
                cap_alpha2 = chr(ord(cap_alpha2) + 1)

            elif re.search(r'^\([IVX]+\)', current_tag_text) and p_tag.name == "p" and cap_alpha1 not in ['I','V','X']:
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag

                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    roman_cur_tag.append(cap_roman_ol)
                    prev_id1 = roman_cur_tag.get('id')

                else:
                    cap_roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[IVX]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)



            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                cap_alpha2 = 'A'
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)
                    if num_cur_tag1:
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha_id1 = num_cur_tag1.get("id")
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous(['h5','h4','h3','h2']).get('id')}ol{ol_count}"

                else:
                    cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                if cap_alpha1 =='Z':
                    cap_alpha1 ='A'

                else:
                    cap_alpha1 = chr(ord(cap_alpha1) + 1)

                if re.search(rf'^\([A-Z]\)\s*\([ivx]+\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s*\([ivx]+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[A-Z])\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)

                    if re.search(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', current_tag_text):
                        cap_roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cap_roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>[A-Z])\)\s?\((?P<pid>[ivx]+)\)\s\(?(?P<nid>I)\)', current_tag_text)
                        prev_id1 = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_roman_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(cap_roman_ol)

            elif re.search(r'^\([a-z][a-z]\)', current_tag_text):
                p_tag.name = "li"
                if re.search(r'^\(aa\)', current_tag_text):
                    alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol1)
                    cap_roman_cur_tag.append(alpha_ol1)

                else:
                    alpha_ol1.append(p_tag)


                p_tag_id = re.search(r'^\((?P<p_id>[a-z][a-z])\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_roman_cur_tag.get("id")}{p_tag_id}'
                p_tag.string = re.sub(r'^\([a-z][a-z]\)', '', current_tag_text)



            if re.search(r'^CASE NOTES', current_tag_text) or p_tag.name in ['h3','h4','h5']:
                ol_head = 1
                cap_alpha ='A'
                cap_alpha_cur_tag = None
                ol_head1 = 1
                num_count = 1
                num_cur_tag = None
                new_alpha = None
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                alpha_cur_tag = None
                cap_alpha_head = "A"
                num_count1 = 1
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha2 = "A"
                sec_alpha_id = None
                num_tag = None

        print('ol tags added')



    def add_citation(self):

        for tag in self.soup.find_all("p"):
            if tag.span:
                tag.span.unwrap()

            if re.search(r"\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*"
                         r"|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*"
                         r"|\d+,\sNo\.\s\d+",tag.text.strip()):
                text = str(tag)


                for match in set(x[0] for x in re.findall(r'(\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*'
                                                          r'|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*'
                                                          r'|\d+,\sNo\.\s\d+)'
                                                    ,tag.get_text())):

                    inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<p\sclass="\w\d+"\sid=".+">|<p\sclass="\w"\sid=".+">', '',
                                         text, re.DOTALL)

                    tag.clear()
                    text = re.sub(re.escape(match),
                                          f'<cite class="vt-code">{match}</cite>',
                                          inside_text, re.I)
                    tag.append(text)

        print("citation added")



    def add_watermark_and_remove_class_name(self):
        watermark_tag = self.soup.new_tag('p', Class='transformation')
        watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                          datetime.now().date())
        title_tag = self.soup.find("nav")
        if title_tag:
            title_tag.insert(0, watermark_tag)

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

        for all_tag in self.soup.findAll("p",class_="navhead"):
            all_tag.name = "p"
            del all_tag["class"]
            del all_tag["id"]

        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p','h2','h5']:
                del tag["class"]


        print("watermark added")


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

    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """
        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"../../cic-code-vt/transforms/vt/ocvt/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)



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
            self.class_regex = {'ul':'^I\.','head1': '^Constitution of the United States|^CONSTITUTION OF THE STATE OF VERMONT',
                                'head2': '^CHAPTER I','head3': r'^§ 1\.|^Section \d+\.','junk': '^Statute text',
                                'article':'——————————','head4': '^ANNOTATIONS','Analysishead':'^Analysis','analysis':'^1\.'}

            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_analysis_nav()
            self.create_analysis_ul()
            self.wrap_div_tags()
            self.add_citation()
            self.add_watermark_and_remove_class_name()


        else:
            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_analysis_nav()
            self.create_analysis_ul()
            self.wrap_div_tags()
            self.add_citation()
            self.convert_paragraph_to_alphabetical_ol_tags1()
            self.add_watermark_and_remove_class_name()
        self.write_soup_to_file()
        print(datetime.now() - start_time)