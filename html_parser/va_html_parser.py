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


class VAParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^\d+\-\d+\.\s*|^\d+\.\d+\.|^\d+\.\d+[A-Z]*-\d+\.', 'head2': '^Chapter \d+\.', 'head1': '^Title|^The Constitution of the United States of America',
                            'head3': r'^§\s\d+(\.\d+)*[A-Z]*\-\d+\.\s*','junk': '^Statute text','article':'——————————',  'head4': '^CASE NOTES','ol': r'^A\.\s', \
                            'head':'^§§\s*\d+-\d+\s*through\s*\d+-\d+\.|^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*|^Part \d+\.'}

        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name
        self.nd_list = []
        self.navhead = None
        self.snav_count = 1
        self.cnav_count = 1
        self.meta_tags = []

        self.watermark_text = """Release {0} of the Official Code of Virginia Annotated released {1}.
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

        with open(f'../transforms/va/ocva/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["article"]) if re.search('^——————————',text_junk.text.strip())]

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
                if p_tag.get("class") == [self.class_regex["casenav"]]:
                    if p_tag.br and re.search(r'^[IA1]\.', p_tag.text.strip()) and re.search(r'^CASE NOTES', p_tag.find_previous().text.strip()):
                        p_tag_text = p_tag.text.strip()
                        p_tag.clear()
                        rept_tag = re.split('\n', p_tag_text)
                        for tag_text in rept_tag:
                            new_tag = self.soup.new_tag("p")
                            new_tag.string = tag_text
                            p_tag.append(new_tag)
                            new_tag["class"] = "casenote"
                        p_tag.unwrap()

            else:

                if p_tag.get("class") == [self.class_regex["article"]]:
                    if re.search(r'^Article\s*\d+\.|^Subtitle\s*[IVX]+\.|^Part\s*[A-Z]+', p_tag.text.strip()):
                       p_tag["class"] = "navhead"

                if p_tag.get("class") == [self.class_regex["ul"]] or p_tag.get("class") == [self.class_regex["ol"]]:
                    if re.search(r'^(\d+(\.\d+)*[A-Z]*-\d{1,4}(\.\d+)*\..+\.\s*){1}', p_tag.text.strip()):
                        if p_tag.br:
                            string = p_tag.text.strip()

                            p_tag.clear()
                            rept_tag = re.split('(\d+(\.\d+)*[A-Z]*-\d{1,4}(\.\d+)*\..+\.\s*)', string)
                            for tag_text in rept_tag:
                                if tag_text:
                                    if re.search('^(\d+(\.\d+)*[A-Z]*-\d{1,4}(\.\d+)*\..+\.\s*)', tag_text):
                                        new_tag = self.soup.new_tag("p")
                                        new_tag.string = tag_text
                                        new_tag["class"] = [self.class_regex["ul"]]
                                        p_tag.append(new_tag)
                            p_tag.unwrap()

                if p_tag.get("class") == [self.class_regex["ol"]]:
                    if p_tag.br and re.search(r'^[IA1]\.', p_tag.text.strip()) and re.search(r'^CASE NOTES', p_tag.find_previous().text.strip()):
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
        cur_id_list = []
        cur_head_list = []
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if re.search('constitution\.va', self.html_file_name):
                    self.title_id  = 'constitution-va'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id  = 'constitution-us'


                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^The Constitution of the United States|^Constitution of Virginia',header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.wrap(self.soup.new_tag("nav"))
                        header_tag['id'] =  self.title_id
                    elif re.search(r'^ARTICLE [IVX]+\.*',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^ARTICLE (?P<ar_id>[IVX]+)\.*', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"
                    elif re.search(r'^SCHEDULE',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.sub(r'[\W]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id}"

                if header_tag.get("class") == [self.class_regex["amdhead"]]:
                    if re.search(r'^AMENDMENTS TO THE CONSTITUTION', header_tag.text.strip()):
                        header_tag.name = "h2"
                        amd_id = re.sub(r'[\W]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}am{amd_id}"

                if header_tag.get("class") == [self.class_regex["head3"]]:
                    if re.search(r'^(Section|§) \d+(-[A-Z])*\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = re.search(r'^(Section|§) (?P<sec_id>\d+(-[A-Z])*)\.', header_tag.text.strip()).group('sec_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{sec_id.zfill(2)}"

                    if re.search(r'^\[Amendment [IVX]+\]',header_tag.text.strip()):
                        header_tag.name = "h3"
                        amd_id =  re.search(r'^\[Amendment (?P<ar_id>[IVX]+)', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2').get('id')}s{amd_id.zfill(2)}"

                if header_tag.get("class") == [self.class_regex["article"]]:
                    if re.search(r'^Section \d+\.', header_tag.text.strip()):
                        header_tag.name = "h4"
                        sec_id = re.search(r'^Section (?P<sec_id>\d+)\.', header_tag.text.strip()).group('sec_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3').get('id')}-sub{sec_id.zfill(2)}"

                if header_tag.get("class") == [self.class_regex["ol"]]:
                    if re.search(r'^CASE NOTES', header_tag.text.strip()):
                        header_tag.name = "h4"
                        sec_id = re.sub(r'[\W]','',header_tag.text.strip()).lower()
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h3').get('id')}-{sec_id}"


                    if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[IVX]+)\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{tag_text}"
                            header_tag['class'] = 'casehead'

                    elif re.search(r'^[A-Z]\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[A-Z])\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casehead').get('id')}-{tag_text}"
                            header_tag['class'] = 'casesub'

                    elif re.search(r'^[0-9]+\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[0-9]+)\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casesub').get('id')}-{tag_text}"
                            header_tag['class'] = 'casedigit'

                    elif re.search(r'^[ivx]+\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[ivx]+)\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casealpha').get('id')}-{tag_text}"

                    elif re.search(r'^[a-z]\.', header_tag.text.strip()):
                            header_tag.name = "h5"
                            tag_text = re.search('^(?P<c_id>[a-z])\.', header_tag.text.strip()).group('c_id').lower()
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h5', class_='casedigit').get('id')}-{tag_text}"
                            header_tag['class'] = 'casealpha'

                if header_tag.get("class") == [self.class_regex["ul"]] and not re.search('^PREAMBLE|^Sec\.|^Article|^Amend\.',header_tag.text.strip()):
                    header_tag.name = "li"

            else:
                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^(Title)\s(?P<title_id>\d+)', header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag.wrap(self.soup.new_tag("nav"))
                        self.title_id = re.search(r'^(Title)\s(?P<title_id>\d+(\.\d+)*[A-Z]*)', header_tag.text.strip()).group('title_id').zfill(2)
                        header_tag['id']  =f"t{self.title_id}"

                    elif  re.search(r'^Article\s*(?P<ar_id>\d+(\.\d+)*)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^Article\s*(?P<ar_id>\d+(\.\d+)*)\.', header_tag.text.strip()).group('ar_id')
                        if header_tag.find_previous('h2',class_='chapter'):
                            header_tag['id'] = f"{header_tag.find_previous('h2',class_='chapter').get('id')}a{article_id.zfill(2)}"

                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2').get('id')}a{article_id.zfill(2)}"

                        self.snav_count = 1
                    elif re.search(r'^SUBTITLE\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^SUBTITLE\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()).group('sub_id')
                        header_tag[
                            'id'] = f"t{self.title_id.zfill(2)}s{article_id.zfill(2)}"
                        header_tag["class"] = "subtitle"
                        self.snav_count = 1

                    elif re.search(r'^PART\s*(?P<part_id>[A-Z]+)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^PART\s*(?P<part_id>[A-Z]+)\.', header_tag.text.strip()).group('part_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h2', class_='subtitle').get('id')}p{article_id.zfill(2)}"
                        header_tag["class"] = "part"
                        self.snav_count = 1

                elif header_tag.get("class") == [self.class_regex["head2"]] and re.search(r'^(Chapter)\s(?P<chap_id>\d+(\.\d+)*(:\d+)*)\.', header_tag.text.strip()) :
                    header_tag.name = "h2"
                    chapter_id = re.search(r'^(Chapter)\s(?P<chap_id>\d+(\.\d+)*(:\d+)*)\.', header_tag.text.strip()).group('chap_id')

                    if header_tag.find_previous('h2', class_ =['part','subtitle']):
                        header_tag['id'] = f"{header_tag.find_previous('h2', class_=['part','subtitle']).get('id')}c{chapter_id.zfill(2)}"
                    else:
                        header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"
                    header_tag["class"] = "chapter"
                    self.navhead = None
                    self.snav_count = 1


                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    header_tag.name = "h3"

                    section_id = re.search(r'^§+\s(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*(:\d+)*)\.*\s*', header_tag.text.strip()).group(
                        'sec_id')
                    curr_head_id = f"{header_tag.find_previous(['h2','h1']).get('id')}s{section_id.zfill(2)}"

                    if curr_head_id in cur_head_list:
                        header_tag['id'] = f"{header_tag.find_previous(['h2','h1']).get('id')}s{section_id.zfill(2)}.1."
                    else:
                        header_tag['id'] = f"{header_tag.find_previous(['h2', 'h1']).get('id')}s{section_id.zfill(2)}"
                    cur_head_list.append(curr_head_id)


                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^[IVX]+\.',header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[IVX]+)\.',header_tag.text.strip()).group('c_id').lower()

                        header_tag['id'] = f"{header_tag.find_previous('h4').get('id')}-{tag_text}"
                        header_tag['class'] = 'casehead'

                    elif re.search(r'^[A-Z]\.',header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[A-Z])\.',header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous('h5',class_='casehead').get('id')}-{tag_text}"
                        header_tag['class'] = 'casesub'

                    elif re.search(r'^[0-9]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[0-9]+)\.',header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous('h5',class_='casesub').get('id')}-{tag_text}"
                        header_tag['class'] = 'casedigit'

                    elif re.search(r'^[ivx]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[ivx]+)\.',header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous('h5',class_='casealpha').get('id')}-{tag_text}"

                    elif re.search(r'^[a-z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        tag_text = re.search('^(?P<c_id>[a-z])\.',header_tag.text.strip()).group('c_id').lower()
                        header_tag['id'] = f"{header_tag.find_previous('h5',class_='casedigit').get('id')}-{tag_text}"
                        header_tag['class'] = 'casealpha'

                    else:
                        header_tag.name = "h4"
                        subsection_id = header_tag.text.strip().lower()
                        subsection_id = re.sub('[\s]','',subsection_id)
                        curr_tag_id = f"{header_tag.find_previous(['h3','h2','h1']).get('id')}-{subsection_id}"

                        if curr_tag_id in cur_id_list:
                            if header_tag.find_previous('h3'):
                                header_tag['id'] = f"{header_tag.find_previous('h3').get('id')}-{subsection_id}.1"
                            elif header_tag.find_previous('h2'):
                                header_tag['id'] = f"{header_tag.find_previous('h2').get('id')}-{subsection_id}.1"
                            elif header_tag.find_previous('h1'):
                                header_tag['id'] = f"{header_tag.find_previous('h1').get('id')}-{subsection_id}.1"
                        else:
                            if header_tag.find_previous('h3'):
                                header_tag['id'] = f"{header_tag.find_previous('h3').get('id')}-{subsection_id}"
                            elif header_tag.find_previous('h2'):
                                header_tag['id'] = f"{header_tag.find_previous('h2').get('id')}-{subsection_id}"
                            elif header_tag.find_previous('h1'):
                                header_tag['id'] = f"{header_tag.find_previous('h1').get('id')}-{subsection_id}"
                        cur_id_list.append(header_tag['id'])

                elif header_tag.get("class") == "navhead":
                    header_tag.name = "h2"
                    if re.search(r'^Article\s*(?P<ar_id>\d+)\.', header_tag.text.strip()):
                        article_id = re.search(r'^Article\s*(?P<ar_id>\d+(\.\d+)*)\.', header_tag.text.strip()).group('ar_id')

                        if header_tag.find_previous('h2', class_='chapter'):
                            header_tag['id'] = f"{header_tag.find_previous('h2', class_='chapter').get('id')}a{article_id.zfill(2)}"
                        elif header_tag.find_previous('h2', class_='subtitle'):
                            header_tag[
                               'id'] = f"{header_tag.find_previous('h2', class_='subtitle').get('id')}a{article_id.zfill(2)}"
                        else:
                            header_tag[
                                'id'] = f"{header_tag.find_previous('h2').get('id')}a{article_id.zfill(2)}"

                    elif re.search(r'^Subtitle\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()):

                        article_id = re.search(r'^Subtitle\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()).group('sub_id')

                        header_tag[
                            'id'] = f"t{self.title_id.zfill(2)}s{article_id.zfill(2)}"

                    elif re.search(r'^Part\s*(?P<p_id>[A-Z]+)', header_tag.text.strip()):

                        article_id = re.search(r'^Part\s*(?P<p_id>[A-Z]+)', header_tag.text.strip()).group('p_id')

                        prev_tag = header_tag.find_previous_sibling(
                            lambda tag: tag.name == 'h2' and re.search(r'^Subtitle\s*(?P<sub_id>[IVX]+)\.', tag.text.strip()) and
                                        tag.get("class") == "navhead")
                        header_tag[
                            'id'] = f"{prev_tag.get('id')}p{article_id.zfill(2)}"
                    self.snav_count = 1

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if not re.search('^Chap\.|^Sec\.|^Part',header_tag.text.strip()) and not len(header_tag.get_text(strip=True)) == 0 :
                        header_tag.name = "li"

                        if re.search(r'^(?P<sec_id>\d+-\d+)\.\s*', header_tag.text.strip()):
                            chap_id = re.search(r'^(?P<sec_id>\d+-\d+(\.\d+)*)\.\s*', header_tag.text.strip()).group(
                                'sec_id')
                            sub_tag = "s"
                            prev_id = header_tag.find_previous("h2").get("id")

                            header_tag[
                                "id"] = f"{header_tag.find_previous('h2').get('id')}s{chap_id}-snav{self.snav_count:02}"
                            self.snav_count += 1


                elif header_tag.get("class") == [self.class_regex["head"]]:
                    if re.search(r'^§§\s*(?P<sec_id>\d+(\.\d+)*-\d+)\s*through\s*\d+-\d+\.', header_tag.text.strip()):
                        header_tag.name = "h3"
                        section_id = re.search(r'^§§\s*(?P<sec_id>\d+-\d+)\s*through\s*\d+-\d+\.', header_tag.text.strip()).group('sec_id')
                        header_tag['id'] = f"t{self.title_id.zfill(2)}c{section_id.zfill(2)}"
                    elif re.search(r'^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*', header_tag.text.strip()):
                        header_tag.name = "h3"
                        section_id = re.search(r'^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*', header_tag.text.strip()).group('sec_id')
                        header_tag['id'] = f"t{self.title_id.zfill(2)}s{section_id.zfill(2)}"

                    elif re.search(r'^Part \d+\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        chapter_id = re.search(r'^(Part)\s(?P<chap_id>\d+(\.\d+)*)\.',
                                               header_tag.text.strip()).group('chap_id')
                        header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"
                        header_tag["class"] = "chapter"
                        self.navhead = None
                        self.snav_count = 1

                elif header_tag.get("class") == [self.class_regex["article"]]:
                    if re.search(r'^ARTICLE [IVX]+', header_tag.text.strip()):
                        header_tag.name = "h4"
                        subsection_id = re.search(r'^ARTICLE (?P<ar_id>[IVX]+)', header_tag.text.strip()).group("ar_id")
                        header_tag["id"] = f"{header_tag.find_previous(['h3', 'h2', 'h1']).get('id')}-a{subsection_id}"

                    elif re.search(r'^SUBTITLE\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^SUBTITLE\s*(?P<sub_id>[IVX]+)\.', header_tag.text.strip()).group(
                            'sub_id')
                        header_tag[
                            'id'] = f"t{self.title_id.zfill(2)}s{article_id.zfill(2)}"
                        header_tag["class"] = "subtitle"
                        self.snav_count = 1

                elif header_tag.get("class") == [self.class_regex["ol"]]:
                    if re.search(r'^§\s\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        subsection_id = re.search(r'^§\s(?P<ar_id>\d+)\.', header_tag.text.strip()).group("ar_id")
                        header_tag["id"] = f"{header_tag.find_previous(['h4','h3', 'h2', 'h1']).get('id')}-sub{subsection_id}"

        print('tags replaced')


    def create_main_tag(self):
        """
                    - wrap all contents inside main tag(Except chapter index)
                """
        if re.search('constitution', self.html_file_name):
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find("h2")
            for main_tag in self.soup.find_all():
                if main_tag.name == "i":
                    main_tag.unwrap()
                if main_tag.find_next("h2") == first_chapter_header:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    section_nav_tag.append(main_tag)
                if main_tag.name == "span" or main_tag.name == "b" :
                    main_tag.find_previous().append(main_tag)
        else:
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find(['h2'])
            for main_tag in self.soup.findAll():
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


        main_tag = self.soup.find("main")
        if not main_tag:
            section_nav_tag = self.soup.new_tag("main")
            first_chapter_header = self.soup.find(['h3'])
            for main_tag in self.soup.findAll():
                if main_tag.find_next("h3") == first_chapter_header:
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

        print("main tag is created")


    def create_ul_tag(self):
        """
                   - wrap the list items with unordered tag
               """

        if re.search('constitution', self.html_file_name):
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if re.search(r'^Article|^PREAMBLE',ul_tag.find_previous("p").text.strip()):
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

                    if ul_tag.find_previous("p").text.strip() == 'Chap.' or ul_tag.find_previous("p").text.strip() == 'Part':
                        ul_tag.find_previous("nav").append(ul_tag.find_previous("p"))
                        ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.find_previous("p").wrap(self.soup.new_tag("nav"))
                        ul_tag.find_previous("nav").append(ul_tag)

        print("ul tag is created")


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


    def create_chapter_section_nav(self):

        count = 0
        for list_item in self.soup.find_all("li"):
            if re.search('constitution', self.html_file_name):
                if re.search(r'^[IXV]+\.|^AMENDMENTS|^Schedule', list_item.text.strip()):
                    if re.match(r'^[IXV]+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<chap>[IXV]+)\. ', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "a"

                        if list_item.find_previous("h2"):
                            if re.search(r'^AMENDMENTS|^Schedule', list_item.find_previous("h2").text.strip()):
                                prev_id = list_item.find_previous("h2").get("id")
                                sub_tag = "s"
                        else:
                            prev_id = None


                    elif re.search(r'^AMENDMENTS', list_item.text.strip()):
                        chap_num = re.sub(r'[\W]', '', list_item.text.strip()).lower()
                        sub_tag = "am"
                        prev_id = None

                    elif re.search(r'^Schedule', list_item.text.strip()):
                        chap_num = re.sub(r'[\W]', '', list_item.text.strip()).lower()
                        sub_tag = "a"
                        prev_id = None
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                elif re.search(r'^\d+(-[A-Z])*\.',list_item.text.strip()):
                    chap_num = re.search(r'^(?P<sec>\d+(-[A-Z])*)\. ', list_item.text.strip()).group(
                        "sec").zfill(2)
                    sub_tag = "s"
                    prev_id = list_item.find_previous("h2").get("id")
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)



            else:
                if re.search(r'^(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+(:\d+)*)\.*\s*', list_item.text.strip()):
                    chap_id = re.search(r'^(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*(:\d+)*)\.*\s*', list_item.text.strip()).group('sec_id')
                    sub_tag = "s"
                    prev_id = list_item.find_previous(['h2','h1']).get("id")
                    self.set_chapter_section_nav(list_item, chap_id.zfill(2), sub_tag, prev_id, None)


                elif re.search(r'^(?P<chap_id>\d+(\.\d+)*)\.', list_item.text.strip()):
                    chapter_id = re.search(r'^(?P<chap_id>\d+(\.\d+)*(:\d+)*)\.', list_item.text.strip()).group('chap_id')
                    sub_tag = "c"

                    if list_item.find_previous("h2",class_="navhead"):
                        prev_id = list_item.find_previous("h2").get("id")
                    else:
                        prev_id = None


                    self.set_chapter_section_nav(list_item, chapter_id.zfill(2), sub_tag, prev_id, None)

                    list_item["id"] = f"t{self.title}c{chapter_id.zfill(2)}-cnav{self.cnav_count:02}"
                    self.cnav_count += 1


    def create_case_note_nav(self):

        if self.soup.find("p",class_='casenote'):
            for case_tag in self.soup.find_all("p",class_='casenote'):
                if re.search(r'^[IVX]+\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[IVX]+)\.', case_tag.text.strip()).group("cid").lower()
                    rom_id = f"{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_link["href"] = f"#{case_tag.find_previous('h4').get('id')}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list


                elif re.search(r'^[A-Z]\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[A-Z])\.', case_tag.text.strip()).group("cid").lower()
                    alpha_id = f"{rom_id}-{case_id}"
                    nav_link["href"] = f"#{rom_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

                elif re.search(r'^[0-9]+\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[0-9]+)\.', case_tag.text.strip()).group("cid").lower()
                    digit_id = f"{alpha_id}-{case_id}"
                    nav_link["href"] = f"#{alpha_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

                elif re.search(r'^[ivx]+\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[ivx]+)\.', case_tag.text.strip()).group("cid").lower()
                    nav_link["href"] = f"#{salpha_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

                elif re.search(r'^[a-z]\.', case_tag.text.strip()):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(case_tag.text)
                    case_id = re.search(r'^(?P<cid>[a-z])\.', case_tag.text.strip()).group("cid").lower()
                    salpha_id = f"{digit_id}-{case_id}"
                    nav_link["href"] = f"#{digit_id}-{case_id}"
                    nav_list.append(nav_link)
                    case_tag.contents = nav_list

    def create_case_note_ul(self):
            for case_tag in self.soup.find_all(class_='casenote'):
                case_tag.name = "li"
                if re.search(r'^[IVX]+\.', case_tag.a.text.strip()):
                    rom_tag = case_tag
                    if re.search(r'^I\.', case_tag.a.text.strip()):
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                    else:
                        rom_ul.append(case_tag)

                elif re.search(r'^[A-Z]\.', case_tag.a.text.strip()):
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

                elif re.search(r'^[ivx]+\.', case_tag.a.text.strip()):
                    if re.search(r'^i\.', case_tag.a.text.strip()):
                        srom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(srom_ul)
                        salpha_tag.append(srom_ul)
                    else:
                        srom_ul.append(case_tag)
                    

                elif re.search(r'^[a-z]\.', case_tag.a.text.strip()):
                    salpha_tag = case_tag
                    if re.search(r'^a\.', case_tag.a.text.strip()):
                        salpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(salpha_ul)
                        digit_tag.append(salpha_ul)
                    else:
                        salpha_ul.append(case_tag)



    def create_and_wrap_with_div_tag(self):
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


        div_tag = self.soup.find("div")
        for header in self.soup.findAll('h3'):
            new_chap_div = self.soup.new_tag('div')
            sec_header = header.find_next_sibling()
            header.wrap(new_chap_div)
            while True:
                next_sec_tag = sec_header.find_next_sibling()
                if sec_header.name == 'h4':
                    new_sec_div = self.soup.new_tag('div')
                    tag_to_wrap = sec_header.find_next_sibling()
                    sec_header.wrap(new_sec_div)
                    while True:
                        next_tag = tag_to_wrap.find_next_sibling()
                        if tag_to_wrap.name == 'h5':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)

                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                if inner_tag.name == 'h6':
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
                        elif tag_to_wrap.name == 'h6':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)
                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                new_sub_sec_div.append(inner_tag)
                                next_tag = inner_next_tag
                                if not inner_next_tag or inner_next_tag.name in ['h4', 'h3', 'h5', 'h6']:
                                    break
                                inner_tag = inner_next_tag
                            tag_to_wrap = new_sub_sec_div
                        if not re.search(r'h\d', tag_to_wrap.name):
                            new_sec_div.append(tag_to_wrap)
                        next_sec_tag = next_tag
                        if not next_tag or next_tag.name in ['h4', 'h3']:
                            break
                        tag_to_wrap = next_tag
                    sec_header = new_sec_div
                new_chap_div.append(sec_header)
                if not next_sec_tag or next_sec_tag.name == 'h3':
                    break
                sec_header = next_sec_tag

        print('wrapped div tags')


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
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        cap_alpha_cur_tag = None
        main_sec_alpha1 = 'a'
        sec_alpha_cur_tag = None
        num_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha1 = 'A'
        n_tag = None

        for p_tag in self.soup.body.find_all():
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()


            if re.search(rf'^{cap_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                ol_head = 1
                cap_alpha_cur_tag = p_tag

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol",type="A")
                    p_tag.wrap(cap_alpha_ol)
                    cap_alpha_id = f"{p_tag.find_previous({'h5','h4','h3'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)
                cap_alpha = chr(ord(cap_alpha) + 1)

                if re.search(rf'^[A-Z]+\.\s*\d+\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[A-Z]+\.\s*\d+\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    num_cur_tag = li_tag
                    cur_tag = re.search(r'^(?P<cid>[A-Z])+\.\s*(?P<pid>\d+)\.', current_tag_text)
                    num_id = f'{cap_alpha_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{cap_alpha_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    ol_head = 2

                    if re.search(r'[A-Z]+\.\s*\d+\.\s*[a-z]+\.',current_tag_text):
                        sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'[A-Z]+\.\s*\d+\.\s*[a-z]+\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)

                        cur_tag = re.search(r'(?P<cid>[A-Z])+\.\s*(?P<pid>\d+)\.\s*(?P<nid>[a-z]+)\.', current_tag_text)
                        sec_alpha_id1 = f'{num_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        sec_alpha_ol1.append(inner_li_tag)
                        num_cur_tag.string = ""
                        num_cur_tag.append(sec_alpha_ol1)
                        main_sec_alpha1 = 'b'

            elif re.search(rf'^{ol_head}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha1 ='a'

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_id = f"{p_tag.find_previous({'h4','h3','h2','h1'}).get('id')}ol{ol_count}"
                    if cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(num_ol)
                        num_id = cap_alpha_cur_tag.get('id')
                    if n_tag:
                        n_tag.append(num_ol)
                        num_id = n_tag.get('id')
                else:
                    num_ol.append(p_tag)
                p_tag["id"] = f'{num_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1

                if re.search(r'^\d+\.\s*[a-z]+\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\d+\.\s*[a-z]+\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'(?P<pid>\d+)\.\s*(?P<nid>[a-z]+)\.', current_tag_text)
                    sec_alpha_id1 = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol1)
                    main_sec_alpha1 = 'b'

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol",type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        sec_alpha_id = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol)
                    elif num_cur_tag1:
                        sec_alpha_id = num_cur_tag1.get('id')
                        num_cur_tag1.append(sec_alpha_ol)
                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5','h4','h3','h2'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol",type="a")
                    p_tag.wrap(sec_alpha_ol1)

                    if num_cur_tag:
                        sec_alpha_id1 = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol1)
                    else:
                        sec_alpha_id1 = f"{p_tag.find_previous({'h5','h4','h3','h2'}).get('id')}ol{ol_count}"

                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)


            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                main_sec_alpha = 'a'
                cap_alpha1 = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5','h4','h3','h2'}).get('id')}ol{ol_count}"
                        main_sec_alpha = 'a'

                else:
                    num_ol1.append(p_tag)


                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1


            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)

                    if num_cur_tag1:
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha_id1 = num_cur_tag1.get("id")
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous({'h5','h4','h3','h2'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)

                if re.search(r'^\([A-Z]\)\s\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s\(i\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'\((?P<pid>[A-Z])\)\s*\((?P<nid>i)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("nid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)

            elif re.search(rf'^\(\d[a-z]\)', current_tag_text) and p_tag.name == "p":
                n_tag = p_tag
                n_id = re.search(rf'^\((?P<n_id>\d+[a-z])\)', current_tag_text).group("n_id")
                p_tag["id"] = f'{num_id1}-{n_id}'
                num_cur_tag1.append(p_tag)

            elif re.search(r'^\([ivx]+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                roman_cur_tag = p_tag
                ol_head = 1

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(roman_ol)
                        prev_id1 = sec_alpha_cur_tag.get("id")
                    elif cap_alpha_cur_tag1:
                        cap_alpha_cur_tag1.append(roman_ol)
                        prev_id1 = cap_alpha_cur_tag1.get('id')
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(roman_ol)
                        prev_id1 = cap_alpha_cur_tag.get("id")
                    elif num_cur_tag1:
                        num_cur_tag1.append(roman_ol)
                        prev_id1 = num_cur_tag1.get("id")
                    else:
                        prev_id1 = f"{p_tag.find_previous({'h5','h4','h3','h2'}).get('id')}ol{ol_count}"
                else:

                    roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[ivx]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([ivx]+\)', '', current_tag_text)


            if re.search(r'^CASE NOTES', current_tag_text) or p_tag.name in ['h3','h4','h5']:
                ol_head = 1
                cap_alpha ='A'
                cap_alpha_cur_tag = None
                num_count = 1
                num_cur_tag = None
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                n_tag =None

        print('ol tags added')


    def add_citation(self):

        title_01 = {'c01': ['1-1', '1-2', '1-2.1', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8', '1-9'],'c02': ['1-10', '1-11', '1-12', '1-13', '1-14', '1-15', '1-16', '1-17'],
                    'c03': ['1-18', '1-19', '1-20', '1-21'], 'c2.1a01': ['1-200', '1-201'],
                    'c2.1a02': ['1-202', '1-203', '1-204', '1-205', '1-206', '1-207', '1-208', '1-209', '1-210',
                                '1-211', '1-212', '1-213', '1-214', '1-215', '1-216', '1-217', '1-218', '1-219',
                                '1-220', '1-221', '1-222', '1-223', '1-224', '1-225', '1-226', '1-227', '1-228',
                                '1-229', '1-230', '1-231', '1-232', '1-233', '1-234', '1-235', '1-236', '1-237',
                                '1-238', '1-239', '1-240', '1-241', '1-242', '1-243', '1-244', '1-245', '1-246',
                                '1-247', '1-248', '1-249', '1-250', '1-251', '1-252', '1-253', '1-254', '1-255',
                                '1-256', '1-257', '1-208.1', '1-211.1', '1-219.1', '1-222.1', '1-240.1', '1-201',
                                '1-202', '1-203', '1-204', '1-205'],
                    'c3.1': ['1-300', '1-301', '1-302', '1-303', '1-304', '1-305', '1-306', '1-307', '1-308', '1-309','1-310', '1-311', '1-312', '1-313'],
                    'c04': ['1-400', '1-401', '1-402', '1-403', '1-404', '1-405', '1-406', '1-407', '1-408'],
                    'c05a01': ['1-500', '1-501', '1-502', '1-503', '1-504', '1-505', '1-506', '1-507', '1-508','1-509'],
                    'c05a02': ['1-510', '1-511', '1-512'],
                    'c06': ['1-600', '1-601', '1-602', '1-603', '1-604', '1-605', '1-606', '1-607', '1-608', '1-609',
                            '1-610']}

        title_11 = {'c01':['11-1','11-2','11-3','11-4','11-5','11-8','11-9','11-2.01','11-2.1','11-2.2','11-2.3','11-2.4','11-4.1','11-4.1:1','11-4.2','11-4.3','11-4.4','11-4.5','11-4.6','11-7.1','11-9.1','11-9.8'],
                    'c02':['11-10','11-11','11-12','11-13'],'c03':['11-14','11-15','11-16','11-16.1','11-16.2'],'c04':['11-17','11-17.1','11-18','11-4'],
                    'c4.1':['11-23.6'],'c05':['11-24'],'c06':['11-30'],'c6.1':['11-34.1','11-34.2','11-34.3','11-34.4'],'c07':['11-35']
                    }

        title_4_1 = {'s0Ic01': ['4.1-100', '4.1-100', '4.1-101', '4.1-101.01', '4.1-101.02', '4.1-101.03', '4.1-101.04','4.1-101.05', '4.1-101.06', '4.1-101.07', '4.1-101.08', '4.1-101.09', '4.1-101.010',
                         '4.1-101.011', '4.1-101.1', '4.1-102', '4.1-103', '4.1-103', '4.1-103.01', '4.1-103.02','4.1-103.03', '4.1-103.03', '4.1-103.1', '4.1-104', '4.1-105', '4.1-106', '4.1-107', '4.1-108',
                         '4.1-109','4.1-110', '4.1-111', '4.1-111', '4.1-112', '4.1-112.1', '4.1-112.2', '4.1-113', '4.1-113.1','4.1-114', '4.1-114', '4.1-115', '4.1-116', '4.1-117', '4.1-118', '4.1-119', '4.1-119',
                         '4.1-119', '4.1-119.1', '4.1-120', '4.1-121', '4.1-122', '4.1-123', '4.1-124', '4.1-124','4.1-125', '4.1-126', '4.1-127', '4.1-128', '4.1-129', '4.1-130', '4.1-131', '4.1-132','4.1-132', '4.1-133'],
              's0Ic02a01': ['4.1-200', '4.1-201', '4.1-201', '4.1-201.1', '4.1-201.1', '4.1-202', '4.1-203', '4.1-203', '4.1-203.1', '4.1-204', '4.1-204', '4.1-204', '4.1-205', '4.1-205'],
              's0Ic02a02': ['4.1-206', '4.1-206.1', '4.1-206.1', '4.1-206.2', '4.1-206.3', '4.1-206.3', '4.1-207','4.1-207.1', '4.1-208', '4.1-209', '4.1-209', '4.1-209.1', '4.1-209.1', '4.1-210',
                            '4.1-211', '4.1-211', '4.1-212','4.1-212', '4.1-212.1', '4.1-212.1', '4.1-212.1', '4.1-213', '4.1-214', '4.1-215','4.1-215', '4.1-216', '4.1-216', '4.1-216.1', '4.1-217', '4.1-218', '4.1-219', '4.1-220',
                            '4.1-221', '4.1-221', '4.1-221.1','4.1-221.1', '4.1-222', '4.1-223', '4.1-223', '4.1-224', '4.1-225', '4.1-225.1','4.1-225.1', '4.1-226', '4.1-227', '4.1-227', '4.1-228', '4.1-229'],
              's0Ic02a03': ['4.1-230', '4.1-230', '4.1-231', '4.1-231.1', '4.1-232', '4.1-232', '4.1-233', '4.1-233.1','4.1-234', '4.1-235', '4.1-236', '4.1-237', '4.1-238', '4.1-238', '4.1-239', '4.1-240'],
              's0Ic03a01': ['4.1-300', '4.1-301', '4.1-302', '4.1-302.1', '4.1-302.2', '4.1-303', '4.1-304', '4.1-305','4.1-306', '4.1-307', '4.1-308', '4.1-309', '4.1-309.1', '4.1-310', '4.1-310', '4.1-310.1',
                            '4.1-310.1', '4.1-311', '4.1-312', '4.1-313', '4.1-314', '4.1-315', '4.1-316', '4.1-317','4.1-318', '4.1-319', '4.1-320', '4.1-321', '4.1-322', '4.1-323'],
              's0Ic03a02': ['4.1-324', '4.1-325', '4.1-325', '4.1-325.01', '4.1-325.1', '4.1-325.1', '4.1-325.2','4.1-325.2', '4.1-326', '4.1-327', '4.1-327', '4.1-328', '4.1-329', '4.1-330', '4.1-331','4.1-332'],
              's0Ic03a03': ['4.1-333', '4.1-334', '4.1-335', '4.1-336', '4.1-337', '4.1-338', '4.1-339', '4.1-345','4.1-346', '4.1-347', '4.1-348', '4.1-349', '4.1-350', '4.1-351', '4.1-352', '4.1-353','4.1-354'],
              's0Ic04': ['4.1-400', '4.1-401', '4.1-402', '4.1-403', '4.1-404', '4.1-405', '4.1-406', '4.1-407','4.1-408', '4.1-409', '4.1-410', '4.1-411', '4.1-412', '4.1-413', '4.1-414', '4.1-415','4.1-416', '4.1-417', '4.1-418'],
              's0Ic05': ['4.1-500', '4.1-501', '4.1-502', '4.1-503', '4.1-504', '4.1-505', '4.1-506', '4.1-507','4.1-508', '4.1-509', '4.1-509.1', '4.1-510', '4.1-511', '4.1-512', '4.1-513', '4.1-514','4.1-515', '4.1-516', '4.1-517'],
              'sIIc06': ['4.1-600', '4.1-601', '4.1-602', '4.1-603', '4.1-604', '4.1-605', '4.1-606', '4.1-607','4.1-608', '4.1-609', '4.1-610', '4.1-611', '4.1-612', '4.1-613',
                         '4.1-614', '4.1-615', '4.1-616', '4.1-617', '4.1-618', '4.1-619', '4.1-620', '4.1-621','4.1-622', '4.1-623', '4.1-624', '4.1-625', '4.1-626', '4.1-627', '4.1-628'],
              'sIIc11': ['4.1-1100', '4.1-1101', '4.1-1101.1', '4.1-1105.1', '4.1-1107', '4.1-1108', '4.1-1109','4.1-1110', '4.1-1112', '4.1-1120', '4.1-1121'],
              'sIIc13': ['4.1-1302'],'sIIc15': ['4.1-1500', '4.1-1501', '4.1-1502', '4.1-1503']}

        title_6_2 = {'s0Ic01a01': ['6.2-100'],
              's0Ic01a02': ['6.2-101', '6.2-101.1', '6.2-102', '6.2-103', '6.2-104', '6.2-105', '6.2-106', '6.2-107'],
              's0Ic02a01': ['6.2-200', '6.2-201'], 's0Ic02a02': ['6.2-202', '6.2-203', '6.2-204'],
              's0Ic03a01': ['6.2-300'], 's0Ic03a02': ['6.2-301', '6.2-302', '6.2-303'],
              's0Ic03a03': ['6.2-304', '6.2-305', '6.2-306', '6.2-307', '6.2-308'],
              's0Ic03a04': ['6.2-309', '6.2-310', '6.2-311', '6.2-312', '6.2-313', '6.2-314', '6.2-315', '6.2-316',
                            '6.2-317', '6.2-318', '6.2-319', '6.2-320', '6.2-321', '6.2-322', '6.2-323',
                            '6.2-324', '6.2-325', '6.2-326', '6.2-327', '6.2-328', '6.2-329', ],

              's0Ic04a01': ['6.2-400', '6.2-401', '6.2-402', '6.2-403', '6.2-404', '6.2-405'],
              's0Ic04a02': ['6.2-406', '6.2-407', '6.2-408', '6.2-409', '6.2-410', '6.2-411', '6.2-412', '6.2-413',
                            '6.2-414', '6.2-415', '6.2-416', '6.2-417', '6.2-418', '6.2-419', '6.2-420', '6.2-421',
                            '6.2-422', '6.2-423'],
              's0Ic04a03': ['6.2-424', '6.2-425', '6.2-426', '6.2-427', '6.2-428', '6.2-429', '6.2-430', '6.2-431',
                            '6.2-432'],
              's0Ic04a04': ['6.2-433', '6.2-434', '6.2-435'],
              's0Ic04a05': ['6.2-436', '6.2-437'],
              's0Ic05': ['6.2-500', '6.2-501', '6.2-502', '6.2-503', '6.2-504', '6.2-505', '6.2-506', '6.2-507',
                         '6.2-508', '6.2-509', '6.2-510', '6.2-511', '6.2-512', '6.2-513'],
              'sIIc06a01': ['6.2-600', '6.2-601', '6.2-602', '6.2-603', '6.2-603.1'],
              'sIIc06a02': ['6.2-604', '6.2-605', '6.2-606', '6.2-607', '6.2-608', '6.2-609', '6.2-610', '6.2-611',
                            '6.2-612', '6.2-613', '6.2-614', '6.2-615', '6.2-616', '6.2-617', '6.2-618', '6.2-619',
                            '6.2-620'],
              'sIIc07': ['6.2-700', '6.2-701', '6.2-702', '6.2-703', '6.2-704', '6.2-705', '6.2-706', '6.2-707',
                         '6.2-708', '6.2-709', '6.2-710', '6.2-711', '6.2-712', '6.2-713', '6.2-714', '6.2-715'],

              'sIIc08a01': ['6.2-800', '6.2-801', '6.2-802', '6.2-803', '6.2-804', '6.2-805', '6.2-806', '6.2-807'],
              'sIIc08a02': ['6.2-808', '6.2-809', '6.2-810', '6.2-811', '6.2-812', '6.2-813', '6.2-814', '6.2-815',
                            '6.2-816', '6.2-817', '6.2-818'],
              'sIIc08a03': ['6.2-819', '6.2-820', '6.2-821'],
              'sIIc08a04': ['6.2-822', '6.2-823', '6.2-824', '6.2-825', '6.2-826', '6.2-827', '6.2-828', '6.2-829',
                            '6.2-830'],
              'sIIc08a05': ['6.2-831', '6.2-832', '6.2-833', '6.2-834', '6.2-835'],
              'sIIc08a06': ['6.2-836', '6.2-837', '6.2-838', '6.2-839', '6.2-840', '6.2-841', '6.2-842', '6.2-843',
                            '6.2-844', '6.2-845', '6.2-846', '6.2-847', '6.2-848'],
              'sIIc08a07': ['6.2-849', '6.2-850', '6.2-851', '6.2-852', '6.2-853', '6.2-854', '6.2-855', '6.2-856',
                            '6.2-857', '6.2-858', '6.2-859', ],
              'sIIc08a08': ['6.2-860', '6.2-861', '6.2-862', '6.2-863', '6.2-864', '6.2-865', '6.2-866', '6.2-867',
                            '6.2-868', '6.2-869'],
              'sIIc08a09': ['6.2-870', '6.2-871', '6.2-872', '6.2-873', '6.2-874', '6.2-875', '6.2-876', '6.2-877',
                            '6.2-878', '6.2-879', '6.2-880', '6.2-881', '6.2-882', '6.2-883',
                            '6.2-884', '6.2-885', '6.2-886', '6.2-887', '6.2-888'],
              'sIIc08a10': ['6.2-889', '6.2-890', '6.2-891', '6.2-892'],
              'sIIc08a11':['6.2 - 893','6.2 - 894','6.2 - 895','6.2 - 896','6.2 - 897'],
              'sIIc08a12':['6.2 - 898','6.2 - 899','6.2 - 900','6.2 - 901','6.2 - 902','6.2 - 903','6.2 - 904','6.2 - 905','6.2 - 906','6.2 - 907','6.2 - 908','6.2 - 909','6.2 - 910','6.2 - 911'],
              'sIIc08a13':['6.2 - 912','6.2 - 913','6.2 - 914','6.2 - 915','6.2 - 916','6.2 - 917','6.2 - 918','6.2 - 919','6.2 - 920','6.2 - 921','6.2 - 922','6.2 - 923','6.2 - 924'],
              'sIIc08a14':['6.2 - 925','6.2 - 926','6.2 - 927','6.2 - 928','6.2 - 929','6.2 - 930','6.2 - 931','6.2 - 932','6.2 - 933','6.2 - 934','6.2 - 935','6.2 - 936','6.2 - 937'],
              'sIIc08a15':['6.2 - 938','6.2 - 939','6.2 - 940','6.2 - 941','6.2 - 942','6.2 - 943','6.2 - 944','6.2 - 945','6.2 - 946'],
              'sIIc08a16':['6.2 - 947','6.2 - 948','6.2 - 949','6.2 - 950'],'sIIc08a17':['6.2 - 951','6.2 - 952','6.2 - 953'],
              'sIIc10a01':['6.2-1000', '6.2-1001', '6.2-1002', '6.2-1003','6.2-1004', '6.2-1005', '6.2-1006', '6.2-1007','6.2-1008', '6.2-1009', '6.2-1010', '6.2-1011',
               '6.2-1012'],'sIIc10a02': ['6.2-1013', '6.2-1014','6.2-1015', '6.2-1016','6.2-1017', '6.2-1018','6.2-1019', '6.2-1020','6.2-1021', '6.2-1022','6.2-1023', '6.2-1024',
               '6.2-1025', '6.2-1026','6.2-1027','6.2-1028', '6.2-1029','6.2-1030', '6.2-1031','6.2-1032', '6.2-1033','6.2-1034', '6.2-1035','6.2-1036', '6.2-1037',
               '6.2-1038', '6.2-1039','6.2-1040', '6.2-1041','6.2-1042', '6.2-1043','6.2-1044', '6.2-1045', '6.2-1046'],
        'sIIc10a03': [ '6.2-1047', '6.2-1048', '6.2-1049', '6.2-1050', '6.2-1051', '6.2-1052', '6.2-1053', '6.2-1054', '6.2-1055',
            '6.2-1056', '6.2-1057', '6.2-1058', '6.2-1059', '6.2-1060', '6.2-1061', '6.2-1062', '6.2-1063', '6.2-1064'],
        'sIIc10a04': ['6.2-1065', '6.2-1066', '6.2-1067', '6.2-1068', '6.2-1069', '6.2-1070', '6.2-1071', '6.2-1072',
                      '6.2-1073'],
        'sIIc10a05': ['6.2-1074', '6.2-1075', '6.2-1076', '6.2-1077', '6.2-1078', '6.2-1079', '6.2-1080'],
        'sIIc10a06': ['6.2-1081', '6.2-1082', '6.2-1083', '6.2-1084', '6.2-1085', '6.2-1086', '6.2-1087', '6.2-1088',
                      '6.2-1089', '6.2-1090', '6.2-1091', '6.2-1092', '6.2-1093',
                      '6.2-1094', '6.2-1095', '6.2-1096', '6.2-1097', '6.2-1098', '6.2-1099'],

        'sIIc11a01': ['6.2-1100', '6.2-1101', '6.2-1102', '6.2-1103', '6.2-1104', '6.2-1105', '6.2-1106', '6.2-1107',
                      '6.2-1108', '6.2-1109', '6.2-1110', '6.2-1111', '6.2-1112', '6.2-1113'],
        'sIIc11a02': ['6.2-1114', '6.2-1115', '6.2-1116', '6.2-1117', '6.2-1118', '6.2-1119', '6.2-1120', '6.2-1121',
                      '6.2-1122', '6.2-1123', '6.2-1124', '6.2-1125', '6.2-1126', '6.2-1127', '6.2-1128', '6.2-1129',
                      '6.2-1130', '6.2-1131', '6.2-1132',
                      ],
        'sIIc11a03': ['6.2-1133', '6.2-1134', '6.2-1135', '6.2-1136', '6.2-1137', '6.2-1138'],
        'sIIc11a04': ['6.2-1139', '6.2-1140', '6.2-1141', '6.2-1142', '6.2-1143', '6.2-1144', '6.2-1145', '6.2-1146',
                      '6.2-1147'],
        'sIIc11a05': ['6.2-1148', '6.2-1149', '6.2-1150', '6.2-1151', '6.2-1152', '6.2-1153', '6.2-1154', '6.2-1155',
                      '6.2-1156', '6.2-1157', '6.2-1158', '6.2-1159', '6.2-1160', '6.2-1161', '6.2-1162', '6.2-1163',
                      '6.2-1164', '6.2-1165'],
        'sIIc11a06': ['6.2-1166', '6.2-1167', '6.2-1168', '6.2-1169', '6.2-1170', '6.2-1171', '6.2-1172', '6.2-1173',
                      '6.2-1174', '6.2-1175', '6.2-1176', '6.2-1177', '6.2-1178'],
        'sIIc11a07': ['6.2-1179', '6.2-1180', '6.2-1181', '6.2-1182', '6.2-1183', '6.2-1184', '6.2-1185'],
        'sIIc11a08': ['6.2-1186', '6.2-1187', '6.2-1188', '6.2-1189', '6.2-1190'],
        'sIIc11a09': ['6.2-1191', '6.2-1192', '6.2-1193', '6.2-1194', '6.2-1195', '6.2-1196', '6.2-1197', '6.2-1198',
                      '6.2-1199', '6.2-1200', '6.2-1201', '6.2-1202', '6.2-1203', '6.2-1204', '6.2-1205'],
        'sIIc13a01': ['6.2-1300', '6.2-1301', '6.2-1302', '6.2-1303', '6.2-1304', '6.2-1305', '6.2-1306', '6.2-1307'],
        'sIIc13a02': ['6.2-1308', '6.2-1309', '6.2-1310', '6.2-1311', '6.2-1312', '6.2-1313', '6.2-1314', '6.2-1315',
                      '6.2-1316', '6.2-1317', '6.2-1318', '6.2-1319'],
        'sIIc13a03': ['6.2-1320', '6.2-1321', '6.2-1322', '6.2-1323', '6.2-1324', '6.2-1325', '6.2-1326'],
        'sIIc13a04': ['6.2-1327', '6.2-1328', '6.2-1329', '6.2-1330'],
        'sIIc13a05': ['6.2-1331', '6.2-1332', '6.2-1333', '6.2-1334', '6.2-1335', '6.2-1336', '6.2-1337', '6.2-1338',
                      '6.2-1339', '6.2-1340', '6.2-1341', '6.2-1342', '6.2-1343'],
        'sIIc13a06': ['6.2-1344', '6.2-1345', '6.2-1346', '6.2-1347', '6.2-1347.1'],
        'sIIc13a07': ['6.2-1348', '6.2-1349', '6.2-1350', '6.2-1351', '6.2-1352', '6.2-1353', '6.2-1354', '6.2-1355',
                      '6.2-1356', '6.2-1357'],
        'sIIc13a08': ['6.2-1358', '6.2-1359', '6.2-1360', '6.2-1361', '6.2-1362', '6.2-1363', '6.2-1364', '6.2-1365',
                      '6.2-1366', '6.2-1367', '6.2-1368', '6.2-1369'],
        'sIIc13a09': ['6.2-1370', '6.2-1371', '6.2-1372', '6.2-1373', '6.2-1374', '6.2-1375', '6.2-1376'],
        'sIIc13a010': ['6.2-1377', '6.2-1378'],
        'sIIc13a011': ['6.2-1379', '6.2-1380'],
        'sIIIc14': ['6.2-1400', '6.2-1401', '6.2-1402', '6.2-1403', '6.2-1404', '6.2-1405', '6.2-1406', '6.2-1407',
                    '6.2-1408', '6.2-1409', '6.2-1410', '6.2-1411', '6.2-1412',
                    '6.2-1413', '6.2-1414', '6.2-1415', '6.2-1416', '6.2-1417', '6.2-1418', '6.2-1419', '6.2-1420',
                    '6.2-1421'],
        'sIIIc15': ['6.2-1500', '6.2-1501', '6.2-1502', '6.2-1503', '6.2-1504', '6.2-1505', '6.2-1506', '6.2-1507',
                    '6.2-1508', '6.2-1508.1', '6.2-1509', '6.2-1510', '6.2-1511', '6.2-1512', '6.2-1513', '6.2-1514',
                    '6.2-1515', '6.2-1516', '6.2-1517', '6.2-1518', '6.2-1519', '6.2-1520', '6.2-1521', '6.2-1522',
                    '6.2-1523', '6.2-1523.1', '6.2-1523.2', '6.2-1523.3', '6.2-1524', '6.2-1525', '6.2-1526',
                    '6.2-1527', '6.2-1528', '6.2-1529', '6.2-1530',
                    '6.2-1531', '6.2-1532', '6.2-1533', '6.2-1534', '6.2-1535', '6.2-1536', '6.2-1537', '6.2-1538',
                    '6.2-1539', '6.2-1540', '6.2-1541', '6.2-1542', '6.2-1543'],
        'sIIIc16': ['6.2-1600', '6.2-1601', '6.2-1602', '6.2-1603', '6.2-1604', '6.2-1605', '6.2-1606', '6.2-1607',
                    '6.2-1608', '6.2-1609', '6.2-1610', '6.2-1611', '6.2-1612', '6.2-1613', '6.2-1614', '6.2-1615',
                    '6.2-1616', '6.2-1617', '6.2-1618', '6.2-1619', '6.2-1620', '6.2-1621', '6.2-1622', '6.2-1623',
                    '6.2-1624', '6.2-1625', '6.2-1626', '6.2-1627', '6.2-1628', '6.2-1629'],
        'sIIIc17': ['6.2-1700', '6.2-1701', '6.2-1702', '6.2-1703', '6.2-1704', '6.2-1705', '6.2-1706', '6.2-1707',
                    '6.2-1708', '6.2-1709', '6.2-1710', '6.2-1711', '6.2-1712', '6.2-1713', '6.2-1714',
                    '6.2-1715', '6.2-1716', '6.2-1717', '6.2-1718', '6.2-1719', '6.2-1720', '6.2-1721', '6.2-1701.1',
                    '6.2-1701.2', '6.2-1701.3', '6.2-1712.1'],
        'sIIIc18': ['6.2-1800', '6.2-1801', '6.2-1802', '6.2-1803', '6.2-1804', '6.2-1805', '6.2-1806', '6.2-1807',
                    '6.2-1808', '6.2-1809', '6.2-1810', '6.2-1811', '6.2-1812', '6.2-1813', '6.2-1814', '6.2-1815',
                    '6.2-1816',
                    '6.2-1817', '6.2-1818', '6.2-1819', '6.2-1820', '6.2-1821', '6.2-1822', '6.2-1823', '6.2-1824',
                    '6.2-1825', '6.2-1826', '6.2-1827', '6.2-1828', '6.2-1829', '6.2-1816.1', '6.2-1817.1',
                    '6.2-1818.1', '6.2-1818.2',
                    '6.2-1818.3', '6.2-1818.4'],
        'sIIIc19': ['6.2-1900', '6.2-1901', '6.2-1902', '6.2-1903', '6.2-1904', '6.2-1905', '6.2-1906', '6.2-1907',
                    '6.2-1908', '6.2-1909', '6.2-1910', '6.2-1911', '6.2-1912',
                    '6.2-1913', '6.2-1914', '6.2-1915', '6.2-1916', '6.2-1917', '6.2-1918', '6.2-1919', '6.2-1920',
                    '6.2-1921', '6.2-1904.1', '6.2-1906.1'],
        'sIIIc20': ['6.2-2000', '6.2-2001', '6.2-2002', '6.2-2003', '6.2-2004', '6.2-2005', '6.2-2006', '6.2-2007',
                    '6.2-2008', '6.2-2009', '6.2-2010', '6.2-2011', '6.2-2012', '6.2-2013', '6.2-2014', '6.2-2015',
                    '6.2-2016',
                    '6.2-2017', '6.2-2018', '6.2-2019', '6.2-2020', '6.2-2021', '6.2-2022', '6.2-2023', '6.2-2024',
                    '6.2-2025'],
        'sIIIc20.1': ['6.2-2026', '6.2-2027', '6.2-2028', '6.2-2029', '6.2-2030', '6.2-2031', '6.2-2032', '6.2-2033',
                      '6.2-2034', '6.2-2035', '6.2-2036', '6.2-2037', '6.2-2038', '6.2-2039', '6.2-2040', '6.2-2041',
                      '6.2-2042',
                      '6.2-2043', '6.2-2044', '6.2-2045', '6.2-2046', '6.2-2047', '6.2-2048', '6.2-2049', '6.2-2050'],

        'sIIIc21': ['6.2-2100', '6.2-2101', '6.2-2102', '6.2-2103', '6.2-2104', '6.2-2105', '6.2-2106', '6.2-2107',
                    '6.2-2108', '6.2-2109', '6.2-2110', '6.2-2111', '6.2-207.1'],
        'sIIIc22': ['6.2-2200', '6.2-2201', '6.2-2202', '6.2-2203', '6.2-2204', '6.2-2205', '6.2-2206', '6.2-2207',
                    '6.2-2208', '6.2-2209', '6.2-2210', '6.2-2211', '6.2-2212', '6.2-2213', '6.2-2214', '6.2-2215',
                    '6.2-2216', '6.2-2217', '6.2-2218', '6.2-2219', '6.2-2220', '6.2-2221', '6.2-2222', '6.2-2223',
                    '6.2-2224', '6.2-2225', '6.2-2226', '6.2-2227', '6.2-2215.1', '6.2-2216.1', '6.2-2216.2',
                    '6.2-2216.3', '6.2-2216.4', '6.2-2218.1'
                    ],
        'sIIIc23': ['6.2-2300', '6.2-2301', '6.2-2302', '6.2-2303', '6.2-2304', '6.2-2305', '6.2-2306', '6.2-2307',
                    '6.2-2308', '6.2-2309', '6.2-2310', '6.2-2311', '6.2-2312', '6.2-2313', '6.2-2314'],
        'sIIIc24': ['6.2-2400', '6.2-2401', '6.2-2402'],
        'sIIIc25': ['6.2-2500', '6.2-2501', '6.2-2502', '6.2-2503', '6.2-2504', '6.2-2505'],
        'sIIIc26': ['6.2-2600', '6.2-2601', '6.2-2602', '6.2-2603', '6.2-2604', '6.2-2605', '6.2-2606', '6.2-2607',
                    '6.2-2608', '6.2-2609', '6.2-2610', '6.2-2611', '6.2-2612', '6.2-2613', '6.2-2614', '6.2-2615',
                    '6.2-2616','6.2-2617', '6.2-2618', '6.2-2619', '6.2-2620', '6.2-2621', '6.2-2622'],}
        title_8_02 = {'c01': ['8.2-101', '8.2-102', '8.2-103', '8.2-104', '8.2-105', '8.2-106', '8.2-107'],
                      'c02': ['8.2-201', '8.2-202', '8.2-203', '8.2-204', '8.2-205', '8.2-206', '8.2-207', '8.2-208',
                              '8.2-209', '8.2-210'],
                      'c03': ['8.2-301', '8.2-302', '8.2-303', '8.2-304', '8.2-305', '8.2-306', '8.2-307', '8.2-308',
                              '8.2-309', '8.2-310', '8.2-311', '8.2-312', '8.2-313', '8.2-314', '8.2-315', '8.2-316',
                              '8.2-317', '8.2-318',
                              '8.2-319', '8.2-320', '8.2-321', '8.2-322', '8.2-323', '8.2-324', '8.2-325', '8.2-326',
                              '8.2-327', '8.2-328', '8.2-317.1'],
                      'c04': ['8.2-401', '8.2-402', '8.2-403'],
                      'c05': ['8.2-501', '8.2-502', '8.2-503', '8.2-504', '8.2-505', '8.2-506', '8.2-507', '8.2-508',
                              '8.2-509', '8.2-510', '8.2-511', '8.2-512', '8.2-513', '8.2-514', '8.2-515'],
                      'c06': ['8.2-601', '8.2-602', '8.2-603', '8.2-604', '8.2-605', '8.2-606', '8.2-607', '8.2-608',
                              '8.2-609', '8.2-610', '8.2-611', '8.2-612', '8.2-613', '8.2-614', '8.2-615', '8.2-616'],
                      'c07': ['8.2-701', '8.2-702', '8.2-703', '8.2-704', '8.2-705', '8.2-706', '8.2-707', '8.2-708',
                              '8.2-709', '8.2-710', '8.2-711', '8.2-712', '8.2-713', '8.2-714', '8.2-715', '8.2-716',
                              '8.2-717', '8.2-718',
                              '8.2-719', '8.2-720', '8.2-721', '8.2-722', '8.2-723', '8.2-724', '8.2-725']}

        title_8_2A = {
            'c01': ['8.2A-101', '8.2A-102', '8.2A-103', '8.2A-104', '8.2A-105', '8.2A-106', '8.2A-107', '8.2A-108',
                    '8.2A-109'],
            'c02': ['8.2A-201', '8.2A-202', '8.2A-203', '8.2A-204', '8.2A-205', '8.2A-206', '8.2A-207', '8.2A-208',
                    '8.2A-209', '8.2A-210', '8.2A - 211','8.2A - 212','8.2A - 213','8.2A - 214','8.2A - 215','8.2A - 216','8.2A - 217','8.2A - 218','8.2A - 219','8.2A - 220','8.2A - 221'],'c03':['8.2A-301', '8.2A-302',
                    '8.2A-303', '8.2A-304','8.2A-305', '8.2A-306','8.2A-307', '8.2A-308', '8.2A-309', '8.2A-310', '8.2A-311'],
                    'c04': ['8.2A-401','8.2A-402', '8.2A-403','8.2A-404','8.2A-405','8.2A-406','8.2A-407'],
        'c05a01': ['8.2A-501', '8.2A-502', '8.2A-503', '8.2A-504', '8.2A-505', '8.2A-506', '8.2A-507'],
        'c05a02': ['8.2A-508', '8.2A-509', '8.2A-510', '8.2A-511', '8.2A-512', '8.2A-513', '8.2A-514', '8.2A-515',
                   '8.2A-516', '8.2A-517', '8.2A-518', '8.2A-519', '8.2A-520', '8.2A-521', '8.2A-522'],
        'c05a03': ['8.2A-523', '8.2A-524', '8.2A-525', '8.2A-526', '8.2A-527', '8.2A-528', '8.2A-529', '8.2A-530',
                   '8.2A-531', '8.2A-532']}

        title_8_3A = {
            'c01': ['8.3A-101', '8.3A-102', '8.3A-103', '8.3A-104', '8.3A-105', '8.3A-106', '8.3A-107', '8.3A-108',
                    '8.3A-109', '8.3A-110', '8.3A-111', '8.3A-112', '8.3A-113', '8.3A-114', '8.3A-115', '8.3A-116',
                    '8.3A-117', '8.3A-118', '8.3A-119', '8.3A-118.1'],
            'c02': ['8.3A-201', '8.3A-202', '8.3A-203', '8.3A-204', '8.3A-205', '8.3A-206', '8.3A-207'],
            'c03': ['8.3A-301', '8.3A-302', '8.3A-303', '8.3A-304', '8.3A-305', '8.3A-306', '8.3A-307', '8.3A-308',
                    '8.3A-309', '8.3A-310', '8.3A-311', '8.3A-312'],
            'c04': ['8.3A-401', '8.3A-402', '8.3A-403', '8.3A-404', '8.3A-405', '8.3A-406', '8.3A-407', '8.3A-408',
                    '8.3A-409', '8.3A-410', '8.3A-411', '8.3A-412', '8.3A-413', '8.3A-414', '8.3A-415', '8.3A-416',
                    '8.3A-417', '8.3A-418', '8.3A-419', '8.3A-420'],
            'c05': ['8.3A-501', '8.3A-502', '8.3A-503', '8.3A-504', '8.3A-505'],
            'c06': ['8.3A-601', '8.3A-602', '8.3A-603', '8.3A-604', '8.3A-605']}

        title_8_4 = {'c01': ['8.4-101', '8.4-102', '8.4-103', '8.4-104', '8.4-105', '8.4-106', '8.4-107', '8.4-108', '8.4-109',
                    '8.4-110', '8.4-111', '8.4-105.1'],'c02': ['8.4-201', '8.4-202', '8.4-203', '8.4-204', '8.4-205', '8.4-206', '8.4-207', '8.4-208', '8.4-209',
                '8.4-210', '8.4-211', '8.4-212', '8.4-213', '8.4-214', '8.4-205.1', '8.4-207.1','8.4-207.2', '8.4-207.3', '8.4-211.1'],
                     'c03': ['8.4-301', '8.4-302', '8.4-303'], 'c04': ['8.4-401','8.4-402','8.4-403','8.4-404','8.4-405','8.4-406','8.4-407'],'c05': ['8.4-501', '8.4-502', '8.4-503', '8.4-504']}

        title_8_4 = { 'c01': ['8.4A-101', '8.4A-102', '8.4A-103', '8.4A-104', '8.4A-105', '8.4A-106', '8.4A-107', '8.4A-108'],
            'c02': ['8.4A-201', '8.4A-202', '8.4A-203', '8.4A-204', '8.4A-205', '8.4A-206', '8.4A-207', '8.4A-208','8.4A-209', '8.4A-210', '8.4A-211', '8.4A-212'],
            'c03': ['8.4A-301', '8.4A-302', '8.4A-303', '8.4A-304', '8.4A-305'],'c04': ['8.4A-401', '8.4A-402', '8.4A-403', '8.4A-404', '8.4A-405', '8.4A-406'],
            'c05': ['8.4A-501', '8.4A-502', '8.4A-503', '8.4A-504', '8.4A-505', '8.4A-506', '8.4A-507']}

        title_3_2 = {
            's0Ic01a01': ['3.2-100', '3.2-101', '3.2-102', '3.2-103', '3.2-104', '3.2-105', '3.2-106', '3.2-107',
                          '3.2-108', '3.2-101.1', '3.2-108.1'],
            's0Ic01a02': ['3.2-109', '3.2-110', '3.2-111', '3.2-112'], 's0Ic01a03': ['3.2-113', '3.2-114', '3.2-115'],
            's0Ic02a01': ['3.2-200', '3.2-201', '3.2-202', '3.2-203'], 's0Ic02a02': ['3.2-204', '3.2-205', '3.2-206'],
            's0Ic03': ['3.2-300', '3.2-301', '3.2-302'],
            's0Ic3.1': ['3.2-303', '3.2-304', '3.2-305', '3.2-306', '3.2-307', '3.2-308', '3.2-309', '3.2-310',
                        '3.2-311'],
            's0Ic04': ['3.2-400', '3.2-401', '3.2-402', '3.2 - 403','3.2 - 404','3.2 - 405','3.2 - 406','3.2 - 407','3.2 - 408','3.2 - 409','3.2 - 410'],
             's0Ic05':['3.2-500', '3.2-501', '3.2-502', '3.2 - 503','3.2 - 504','3.2 - 505','3.2 - 506'],
             's0Ic06': ['3.2-600','3.2-601','3.2-602','3.2 - 603','3.2 - 604'],'s0Ic07a01':['3.2-700', '3.2-701', '3.2-702', '3.2 - 703','3.2 - 704','3.2 - 705','3.2 - 706','3.2 - 707','3.2 - 708',
            '3.2 - 709','3.2 - 710','3.2 - 711','3.2 - 712','3.2 - 713'],'s0Ic07a02': ['3.2-714', '3.2-715', '3.2-716','3.2-717', '3.2-718', '3.2-719','3.2-720', '3.2-721', '3.2-722',
            '3.2-723', '3.2-724', '3.2-725','3.2-726', '3.2-727', '3.2-728','3.2-729', '3.2-730', '3.2-731'],
        's0Ic08': ['3.2-800', '3.2-801', '3.2-802', '3.2 - 803','3.2 - 804','3.2 - 805','3.2 - 806','3.2 - 807',
                   '3.2 - 808','3.2 - 809'],'s0Ic09':['3.2-900', '3.2-901'],'s0Ic10': ['3.2-1000', '3.2-1001', '3.2-1002', '3.2-1003', '3.2-1004',
        '3.2-1005', '3.2-1006', '3.2-1007', '3.2-1008', '3.2-1009','3.2-1010', '3.2-1011']}


        title_2_2 = {
            's0Ip0Ac01a01': ['2.2-100', '2.2-101', '2.2-102', '2.2-103', '2.2-104', '2.2-105', '2.2-106', '2.2-107',
                             '2.2-108', '2.2-109', '2.2-110', '2.2-111', '2.2-112', '2.2-113', '2.2-114', '2.2-115',
                             '2.2-116', '2.2-117', '2.2-118', '2.2-119', '2.2-120', '2.2-121', '2.2-122', '2.2-123',
                             '2.2-124', '2.2-125', '2.2-126', '2.2-109.01', '2.2-115.1'],
            's0Ip0Ac01a02': ['2.2-127', '2.2-128', '2.2-129', '2.2-130', '2.2-131', '2.2-132', '2.2-133'],
            's0Ip0Ac01a03': ['2.2-134', '2.2-135'],
            's0Ip0Ac02a01': ['2.2-200', '2.2-201', '2.2-202'],
            's0Ip0Ac02a02': ['2.2-203', '2.2-203.1', '2.2-203.2', '2.2-203.2:1', '2.2-203.2:2', '2.2-203.2:3',
                             '2.2-203.2:4', '2.2-203.2:4', '2.2-203.2:5'],
            's0Ip0Ac02a2.1': ['2.2-203.3'],
            's0Ip0Ac02a03': ['2.2-204', '2.2-204', '2.2-205', '2.2-205.1', '2.2-205.2', '2.2-206', '2.2-206.1',
                             '2.2-206.2', '2.2-206.3', '2.2-207'],
            's0Ip0Ac02a04': ['2.2-208', '2.2-208.1', '2.2-210'],
            's0Ip0Ac02a05': ['2.2-211'],
            's0Ip0Ac02a06': ['2.2-212', '2.2-213', '2.2-213.1', '2.2-213.2', '2.2-213.3', '2.2-213.4', '2.2-213.5',
                             '2.2-214', '2.2-214.1'],
            's0Ip0Ac02a6.1': ['2.2-214.2', '2.2-214.3'],
            's0Ip0Ac02a07': ['2.2-215', '2.2-216', '2.2-217', '2.2-218', '2.2-220', '2.2-220.1', '2.2-220.2',
                             '2.2-220.3', '2.2-220.4'],
            's0Ip0Ac02a08': ['2.2-221', '2.2-221.1', '2.2-222', '2.2-222.1', '2.2-222.2', '2.2-222.3', '2.2-222.4',
                             '2.2-223', '2.2-224', '2.2-224.1'],
            's0Ip0Ac02a09': ['2.2-225', '2.2-225.1', '2.2-226', '2.2-227'],
            's0Ip0Ac02a10': ['2.2-228', '2.2-229'],
            's0Ip0Ac02a11': ['2.2-230', '2.2-231', '2.2-233'],
            's0Ip0Ac02a12': ['2.2-234', '2.2-235'],
            's0Ip0Ac03': ['2.2-300', '2.2-301', '2.2-302', '2.2-302.1', '2.2-303'],
            's0Ip0Ac3.1': ['2.2-304', '2.2-305', '2.2-306'],
            's0Ip0Ac3.2a01': ['2.2-307', '2.2-308', '2.2-309', '2.2-309.1', '2.2-309.2', '2.2-309.3', '2.2-309.4',
                              '2.2-310', '2.2-311', '2.2-312', '2.2-313'],
            's0Ip0Ac3.2a02': ['2.2-314', '2.2-315', '2.2-316'],
            's0Ip0Ac3.2a03': ['2.2-317', '2.2-318'],
            's0Ip0Ac3.2a04': ['2.2-319', '2.2-320'],
            's0Ip0Ac3.2a05': ['2.2-321'],
            's0Ip0Ac3.2a06': ['2.2-322'],
            's0Ip0Ac04a01': ['2.2-400', '2.2-401', '2.2-402', '2.2-403', '2.2-404', '2.2-405', '2.2-406', '2.2-407',
                             '2.2-408', '2.2-409', '2.2-410', '2.2-401.01', '2.2-401.1', '2.2-406.1'],
            's0Ip0Ac04a02': ['2.2-411', '2.2-412', '2.2-413', '2.2-414', '2.2-415', '2.2-416', '2.2-417'],
            's0Ip0Ac04a03': ['2.2-418', '2.2-419', '2.2-420', '2.2-421', '2.2-422', '2.2-423', '2.2-424', '2.2-425',
                             '2.2-426', '2.2-427', '2.2-428', '2.2-429', '2.2-430', '2.2-431', '2.2-432', '2.2-433',
                             '2.2-434', '2.2-435'],
            's0Ip0Ac4.1': ['2.2-435.1', '2.2-435.2', '2.2-435.3', '2.2-435.4', '2.2-435.5'],'s0Ip0Ac4.2':['2.2-435.6','2.2-435.7','2.2-435.8','2.2-435.9','2.2-435.10'],
            's0Ip0Ac4.2:1': ['2.2-435.11'],'s0Ip0Ac4.2:2': ['2.2-435.12'],'s0Ip0Ac4.3': ['2.2-436', '2.2-437'],
        's0Ip0Ac4.4': ['2.2-438', '2.2-439', '2.2-440', '2.2-441', '2.2-442', '2.2-443', '2.2-444', '2.2-445','2.2-446', '2.2-447', '2.2-448', '2.2-449'],
        's0Ip0Bc05a01': ['2.2-500', '2.2-501', '2.2-502', '2.2-503', '2.2-504', '2.2-505', '2.2-506', '2.2-507','2.2-507.1', '2.2-507.2', '2.2-507.3', '2.2-508', '2.2-509', '2.2-509.1', '2.2-510',
        '2.2-510.1', '2.2-510.2', '2.2-511', '2.2-511.1', '2.2-512', '2.2-513', '2.2-514', '2.2-515', '2.2-515.1',
         '2.2-515.2', '2.2-516'],'s0Ip0Bc05a02': ['2.2-517'],'s0Ip0Bc05a03': ['2.2-518', '2.2-519'],
        's0Ip0Bc05a04': ['2.2-520', '2.2-521', '2.2 - 522','2.2 - 523','2.2 - 524'],'s0Ip0Cc06a01':['2.2-600', '2.2-601','2.2-601.1', '2.2-602',
        '2.2-603', '2.2-604','2.2-604.1','2.2-604.2','2.2-604.2', '2.2-605','2.2-606', '2.2-607','2.2-608', '2.2-608.1','2.2-609',
         '2.2-610', '2.2-611','2.2-612', '2.2-613','2.2-614', '2.2-614.1','2.2-614.2','2.2-614.2:1','2.2-614.3','2.2-614.4','2.2-614.5'],
         's0Ip0Cc06a02': ['2.2-615', '2.2-616', '2.2-617', '2.2-618', '2.2-619', '2.2-620', '2.2-621'],
        's0Ip0Cc07': ['2.2-700', '2.2-701', '2.2-702', '2.2-703', '2.2-704', '2.2-705', '2.2-706', '2.2-707', '2.2-708','2.2-709', '2.2-710', '2.2-711', '2.2-712', '2.2-713', '2.2-714', '2.2-715', '2.2-716', '2.2-717',
                      '2.2-718', '2.2-719', '2.2-720' ],
        's0Ip0Cc08a01': ['2.2-800', '2.2-801', '2.2-802', '2.2-803', '2.2-803.1', '2.2-804', '2.2-805', '2.2-806','2.2-807', '2.2-808', '2.2-809', '2.2-810', '2.2-811', '2.2-812', '2.2-813', '2.2-813.1',
                         '2.2-813.2'],'s0Ip0Cc08a02': ['2.2-814', '2.2-815', '2.2-816'],'s0Ip0Cc09': ['2.2-900', '2.2-904.2'],
        's0Ip0Cc9.1': ['2.2-905', '2.2-906'],'s0Ip0Cc10': [' 2.2-1000', '2.2-1001'],
        's0Ip0Cc11a01': ['2.2-1100', '2.2-1101', '2.2-1102'],
        's0Ip0Cc11a02': ['2.2-1103', '2.2-1104', '2.2-1105', '2.2-1106', '2.2-1107', '2.2-1108'],
        's0Ip0Cc11a03': ['2.2-1109', '2.2-1110', '2.2-1111', '2.2-1112', '2.2-1113', '2.2-1114', '2.2-1115', '2.2-1116',
                         '2.2-1117', '2.2-1118', '2.2-1119', '2.2-1120', '2.2-1121', '2.2-1122',
                         '2.2-1123', '2.2-1124', '2.2-1125', '2.2-1126', '2.2-1127', '2.2-1128'],
        's0Ip0Cc11a04': ['2.2-1129', '2.2-1130', '2.2-1131', '2.2-1132', '2.2-1133', '2.2-1134', '2.2-1135', '2.2-1136',
                         '2.2-1137', '2.2-1138', '2.2-1139', '2.2-1140', '2.2-1141', '2.2-1142',
                         '2.2-1143', '2.2-1144', '2.2-1145', '2.2-1146', '2.2-1147', '2.2-1148', '2.2-1149', '2.2-1150',
                         '2.2-1151', '2.2-1152', '2.2-1153', '2.2-1154', '2.2-1155', '2.2-1156', '2.2-1157', '2.2-1158',
                         '2.2-1159', '2.2-1160', '2.2-1161'],
        's0Ip0Cc11a05': ['2.2-1162', '2.2-1163', '2.2-1164', '2.2-1165', '2.2-1166', '2.2-1167'],
        's0Ip0Cc11a06': ['2.2-1168', '2.2-1169', '2.2-1170', '2.2-1171', '2.2-1172'],
        's0Ip0Cc11a07': ['2.2-1173', '2.2-1174', '2.2-1175', '2.2-1176', '2.2-1177', '2.2-1178', '2.2-1179', '2.2-1180',
                         '2.2-1181'],
        's0Ip0Cc11a08': ['2.2-1182', '2.2-1183'],
        's0Ip0Cc12': [
            '2.2-1200', '2.2-1201', '2.2-1202', '2.2-1203', '2.2-1204', '2.2-1205', '2.2-1206', '2.2-1207', '2.2-1208',
            '2.2-1209', '2.2-1210', '2.2-1211', '2.2-1212', '2.2-1213', '2.2-1201.1'],
        's0Ip0Cc13': ['2.2-1300', '2.2-1301', '2.2-1302', '2.2-1303', '2.2-1304'],
        's0Ip0Cc14': ['2.2-1400', '2.2-1401', '2.2-1402', '2.2-1403', '2.2-1404'],
        's0Ip0Cc15': ['2.2-1500', '2.2-1501', '2.2-1502', '2.2-1503', '2.2-1504', '2.2-1505', '2.2-1506', '2.2-1507',
                      '2.2-1508', '2.2-1509', '2.2-1510', '2.2-1511', '2.2-1512', '2.2-1513', '2.2-1514', '2.2-1501.1',
                      '2.2-1502.1',
                      '2.2-1503.1', '2.2-1503.2', '2.2-1503.3', '2.2-1509.1', '2.2-1509.2', '2.2-1509.3', '2.2-1509.4'],
        's0Ip0Cc15.1': ['2.2-1515', '2.2-1516', '2.2-1517', '2.2-1518', '2.2-1519', '2.2-1520'],
        's0Ip0Cc16': ['2.2-1600', '2.2-1601', '2.2-1602', '2.2-1603', '2.2-1604', '2.2-1605', '2.2-1606'],
        's0Ip0Cc16.1a01': ['2.2-1603', '2.2-1604', '2.2-1605', '2.2-1606', '2.2-1607', '2.2-1608', '2.2-1609',
                           '2.2-1610'],
        's0Ip0Cc16.1a02': ['2.2-1611', '2.2-1612', '2.2-1613', '2.2-1614', '2.2-1615', '2.2-1616'],
        's0Ip0Cc16.1a03': ['2.2-1617'],
        's0Ip0Cc17': ['2.2-1700', '2.2-1701', '2.2-1702', '2.2-1703', '2.2-1704', '2.2-1705', '2.2-1706', '2.2-1707',
                      '2.2-1708', '2.2-1709', '2.2-1710'],
        's0Ip0Cc18a01': ['2.2-1800', '2.2-1801', '2.2-1802', '2.2-1803', '2.2-1804', '2.2-1805', '2.2-1806', '2.2-1807',
                         '2.2-1808', '2.2-1809', '2.2-1810', '2.2-1811', '2.2-1812'],
        's0Ip0Cc18a02': ['2.2-1813', '2.2-1814', '2.2-1815', '2.2-1816', '2.2-1817', '2.2-1818'],
        's0Ip0Cc18a03': ['2.2-1819', '2.2-1820', '2.2-1821', '2.2-1822', '2.2-1823', '2.2-1824', '2.2-1825', '2.2-1826',
                         '2.2-1827'],
        's0Ip0Cc18a04': ['2.2-1828', '2.2-1829', '2.2-1830', '2.2-1831'],
        's0Ip0Cc18a4.1': ['2.2-1831.1', '2.2-1831.2', '2.2-1831.3', '2.2-1831.4', '2.2-1831.5'],
        's0Ip0Cc18a5': ['2.2-1832', '2.2-1833', '2.2-1834', '2.2-1835', '2.2-1836', '2.2-1837', '2.2-1838', '2.2-1839',
                        '2.2-1840', '2.2-1841', '2.2-1842', '2.2-1843'],
        's0Ip0Cc19': ['2.2-1900', '2.2-1901', '2.2-1902', '2.2-1903', '2.2-1904', '2.2-1905'],
        's0Ip0Cc20': ['2.2-2000', '2.2-2000.1', '2.2-2001', '2.2-2001.1', '2.2-2001.2', '2.2-2001.3', '2.2-2001.4',
                      '2.2-2001.5', '2.2-2001.6', '2.2-2002', '2.2-2002.1', '2.2-2002.2', '2.2-2003', '2.2-2004',
                      '2.2-2004.1'],
        's0Ip0Cc20.1a01': ['2.2-2005', '2.2-2006', '2.2-2007', '2.2-2008', '2.2-2009', '2.2-2010', '2.2-2011',
                           '2.2-2012', '2.2-2013', '2.2-2014', '2.2-2015'],
        's0Ip0Cc20.1a02': ['2.2-2016', '2.2-2017', '2.2-2018', '2.2-2019', '2.2-2020', '2.2-2021'],
        's0Ip0Cc20.1a03': ['2.2-2022', '2.2-2023', '2.2-2024'],
        's0Ip0Cc20.1a04': ['2.2-2025', '2.2-2026', '2.2-2027', '2.2-2028', '2.2-2029', '2.2-2030'],
        's0Ip0Cc20.1a05': ['2.2-2031'],
        's0Ip0Cc20.1a06': ['2.2-2032'],
        's0Ip0Cc20.1a07': ['2.2-2033', '2.2-2034'],
        's0Ip0Dc21': ['2.2-2100', '2.2-2101', '2.2-2102', '2.2-2103', '2.2-2104', '2.2-2105', '2.2-2106'],
        's0Ip0Dc22a01': ['2.2-2200'],
        's0Ip0Dc22a02': ['2.2-2201', '2.2-2202', '2.2-2203', '2.2-2204', '2.2-2205', '2.2-2206', '2.2-2207', '2.2-2208',
                         '2.2-2209', '2.2-2210', '2.2-2211', '2.2-2212', '2.2-2213', '2.2-2214',
                         '2.2-2215', '2.2-2216', '2.2-2217'],
        's0Ip0Dc22a03': ['2.2-2218', '2.2-2219', '2.2-2220', '2.2-2221', '2.2-2222', '2.2-2223', '2.2-2224', '2.2-2225',
                         '2.2-2226', '2.2-2227', '2.2-2228', '2.2-2229', '2.2-2230', '2.2-2231', '2.2-2232',
                         '2.2-2233'],
        's0Ip0Dc22a04': ['2.2-2234', '2.2-2235', '2.2-2236', '2.2-2237', '2.2-2238', '2.2-2239', '2.2-2240', '2.2-2241',
                         '2.2-2242', '2.2-2243', '2.2-2244', '2.2-2245', '2.2-2246'],
        's0Ip0Dc22a05': ['2.2-2247', '2.2-2248', '2.2-2249', '2.2-2250', '2.2-2251', '2.2-2252', '2.2-2253', '2.2-2254',
                         '2.2-2255', '2.2-2256', '2.2-2257', '2.2-2258', '2.2-2259'],
        's0Ip0Dc22a06':['2.2-2260', '2.2-2261', '2.2-2262', '2.2-2263', '2.2-2264', '2.2-2265', '2.2-2266', '2.2-2267', '2.2-2268', '2.2-2269', '2.2-2270', '2.2-2271', '2.2-2272', '2.2-2273', '2.2-2274', '2.2-2275', '2.2-2276', '2.2-2277','2.2-2278'],
        's0Ip0Dc22a07':['2.2-2279', '2.2-2280', '2.2-2281', '2.2-2282', '2.2-2283', '2.2-2284', '2.2-2285', '2.2-2286', '2.2-2287', '2.2-2288', '2.2-2289', '2.2-2290', '2.2-2291', '2.2-2292', '2.2-2293', '2.2-2294', '2.2-2295', '2.2-2296', '2.2-2297', '2.2-2298', '2.2-2299', '2.2-2300', '2.2-2301', '2.2-2302', '2.2-2303', '2.2-2304', '2.2-2305', '2.2-2306', '2.2-2307',
            '2.2-2308', '2.2-2309', '2.2-2310', '2.2-2311', '2.2-2312', '2.2-2313', '2.2-2314'],
        's0Ip0Dc22a08': ['2.2-2315', '2.2-2316', '2.2-2317', '2.2-2318', '2.2-2319', '2.2-2320', '2.2-2321', '2.2-2322',
                         '2.2-2323', '2.2-2324', '2.2-2325', '2.2-2326', '2.2-2327'],
        's0Ip0Dc22a09': ['2.2-2328', '2.2-2329', '2.2-2330', '2.2-2331', '2.2-2332', '2.2-2333', '2.2-2334',
                         '2.2-2335'],
        's0Ip0Dc22a10': ['2.2-2336', '2.2-2337', '2.2-2338', '2.2-2339', '2.2-2340', '2.2-2341', '2.2-2342', '2.2-2343',
                         '2.2-2344', '2.2-2345', '2.2-2346', '2.2-2347', '2.2-2348', '2.2-2349', '2.2-2350'],
        's0Ip0Dc22a11': ['2.2-2351', '2.2-2352', '2.2-2353', '2.2-2354', '2.2-2355', '2.2-2356', '2.2-2357', '2.2-2358',
                         '2.2-2359', '2.2-2360', '2.2-2361', '2.2-2362', '2.2-2363', '2.2-2364'],
        's0Ip0Dc22a12': ['2.2-2365', '2.2-2366', '2.2-2367', '2.2-2368', '2.2-2369', '2.2-2370', '2.2-2371', '2.2-2372',
                         '2.2-2373', '2.2-2374', '2.2-2375', '2.2-2376', '2.2-2377', '2.2-2378', '2.2-2379',
                         '2.2-2380'],
        's0Ip0Dc24a01': ['2.2-2400', '2.2-2401', '2.2-2402'],
        's0Ip0Dc24a02': ['2.2-2403'],
        's0Ip0Dc24a03': ['2.2-2404', '2.2-2405', '2.2-2406'],
        's0Ip0Dc24a04': ['2.2-2407', '2.2-2408'],
        's0Ip0Dc24a05': ['2.2-2409', '2.2-2410'],
        's0Ip0Dc24a06': ['2.2-2411', '2.2-2412'],
        's0Ip0Dc24a07': ['2.2-2413', '2.2-2414'],
        's0Ip0Dc24a08': ['2.2-2415', '2.2-2416', '2.2-2417', '2.2-2418', '2.2-2419', '2.2-2420'],
        's0Ip0Dc24a09': ['2.2-2421', '2.2-2422'],
        's0Ip0Dc24a10': ['2.2-2423'],
        's0Ip0Dc24a11': ['2.2-2424', '2.2-2425'],
        's0Ip0Dc24a12': ['2.2-2426', '2.2-2427', '2.2-2428', '2.2-2429', '2.2-2430', '2.2-2431', '2.2-2432',
                         '2.2-2433'],
        's0Ip0Dc24a13': ['2.2-2434'],
        's0Ip0Dc24a14': ['2.2-2435', '2.2-2436', '2.2-2437'],
        's0Ip0Dc24a15': ['2.2-2438', '2.2-2439'],
        's0Ip0Dc24a16': ['2.2-2441', '2.2-2442', '2.2-2443', '2.2-2444', '2.2-2445', '2.2-2446', '2.2-2447'],
        's0Ip0Dc24a17': ['2.2-2448', '2.2-2449', '2.2-2450', '2.2-2451'],
        's0Ip0Dc24a18': ['2.2-2452', '2.2-2453', '2.2-2454'],
        's0Ip0Dc24a19': ['2.2-2455', '2.2-2456'],
        's0Ip0Dc24a20': ['2.2-2457', '2.2-2458'],
        's0Ip0Dc24a21': ['2.2-2459', '2.2-2460', '2.2-2461'],
        's0Ip0Dc24a22': ['2.2-2462', '2.2-2463', '2.2-2464'],
        's0Ip0Dc24a23': ['2.2-2465', '2.2-2466', '2.2-2467', '2.2-2468', '2.2-2469'],
        's0Ip0Dc24a24': ['2.2-2470', '2.2-2471', '2.2-2472', '2.2-2473', '2.2-2474', '2.2-2475', '2.2-2476',
                         '2.2-2477'],
        's0Ip0Dc24a25': ['2.2-2478', '2.2-2479', '2.2-2480', '2.2-2481', '2.2-2482', '2.2-2483'],
        's0Ip0Dc24a26': ['2.2-2484', '2.2-2485', '2.2-2486', '2.2-2487', '2.2-2488', '2.2-2489', '2.2-2480', '2.2-2481',
                         '2.2-2482', '2.2-2483', '2.2-2484', '2.2-2485', '2.2-2486',
                         '2.2-2487', '2.2-2488', '2.2-2489', '2.2-2490'],
        's0Ip0Dc24a27': ['2.2-2491', '2.2-2492', '2.2-2493', '2.2-2494', '2.2-2495'],
        's0Ip0Dc24a28': ['2.2-2496', '2.2-2497', '2.2-2498', '2.2-2499'],
        's0Ip0Dc24a29': ['2.2-2491.1', '2.2-2491.2', '2.2-2491.3', '2.2-2491.4'],
        's0Ip0Dc24a30': ['2.2-2491.5', '2.2-2491.6', '2.2-2491.7', '2.2-2491.8'],
        's0Ip0Dc25a01': ['2.2-500', '2.2-501', '2.2-502'],
        's0Ip0Dc25a02': ['2.2-503', '2.2-504', '2.2-505'],
        's0Ip0Dc25a03': ['2.2-506', '2.2-507'],
        's0Ip0Dc25a04': ['2.2-508', '2.2-509', '2.2-510'],
        's0Ip0Dc25a05': ['2.2-511', '2.2-512'],
        's0Ip0Dc25a06': ['2.2-513', '2.2-514', '2.2-515', '2.2-516', '2.2-517'],
        's0Ip0Dc25a07': ['2.2-518', '2.2-519', '2.2-520', '2.2-521', '2.2-522', '2.2-523'],
        's0Ip0Dc25a07.1': ['2.2-524', '2.2-525', '2.2-526', '2.2-527', '2.2-528', '2.2-529'],
        's0Ip0Dc25a08': ['2.2-530', '2.2-531'],
        's0Ip0Dc25a09': ['2.2-532', '2.2-533', '2.2-534', '2.2-535', '2.2-536'],
        's0Ip0Dc25a010': ['2.2-537', '2.2-538', '2.2-539', '2.2-540', '2.2-541', '2.2-542', '2.2-543'],
        's0Ip0Dc25a011': ['2.2-544', '2.2-545', '2.2-546', '2.2-547', '2.2-548', '2.2-549', '2.2-550'],
        's0Ip0Dc25a012': ['2.2-551', '2.2-552', '2.2-553', '2.2-554', '2.2-555', '2.2-556', '2.2-557'],
        's0Ip0Dc25a013': ['2.2-558', '2.2-559', '2.2-560', '2.2-561', '2.2-562', '2.2-563', '2.2-564'],
        's0Ip0Dc26a01': ['2.2-2600', '2.2-2601', '2.2-2602'],
        's0Ip0Dc26a02': ['2.2-2603', '2.2-2604'],
        's0Ip0Dc26a03': ['2.2-2605', '2.2-2606', '2.2-2607', '2.2-2608'],
        's0Ip0Dc26a04': ['2.2-2609', '2.2-2610'],
        's0Ip0Dc26a05': ['2.2-2611', '2.2-2612', '2.2-2613'],
        's0Ip0Dc26a06': ['2.2-2614', '2.2-2615', '2.2-2616'],
        's0Ip0Dc26a07': ['2.2-2617', '2.2-2618', '2.2-2619'],
        's0Ip0Dc26a08': ['2.2-2620', '2.2-2621', '2.2-2622', '2.2-2623', '2.2-2624', '2.2-2625'],
        's0Ip0Dc26a09': ['2.2-2626', '2.2-2627'],
        's0Ip0Dc26a10': ['2.2-2628', '2.2-2629'],
        's0Ip0Dc26a11': ['2.2-2630', '2.2-2631'],
        's0Ip0Dc26a12': ['2.2-2632', '2.2-2633', '2.2-2634', '2.2-2635', '2.2-2636', '2.2-2637', '2.2-2638',
                         '2.2-2639'],
        's0Ip0Dc26a13': ['2.2-2640', '2.2-2641'],
        's0Ip0Dc26a14': ['2.2-2642', '2.2-2643'],
        's0Ip0Dc26a15': ['2.2-2644', '2.2-2645', '2.2-2646', '2.2-2647'],
        's0Ip0Dc26a16': ['2.2-2648', '2.2-2649'],
        's0Ip0Dc26a17': ['2.2-2650'],
        's0Ip0Dc26a18': ['2.2-2651'],
        's0Ip0Dc26a19': ['2.2-2652', '2.2-2653', '2.2-2654'],
        's0Ip0Dc26a20': ['2.2-2655', '2.2-2656'],
        's0Ip0Dc26a21': ['2.2-2657', '2.2-2658', '2.2-2659', '2.2-2660', '2.2-2661', '2.2-2662', '2.2-2663'],
        's0Ip0Dc26a22': ['2.2-2664'],
        's0Ip0Dc26a23': ['2.2-2665', '2.2-2666'],
        's0Ip0Dc26a23.1': ['2.2-2666.1', '2.2-2666.2', '2.2-2666.3'],
        's0Ip0Dc26a24': ['2.2-2667', '2.2-2668'],
        's0Ip0Dc26a25': ['2.2-2669', '2.2-2670', '2.2-2671', '2.2-2672', '2.2-2673', '2.2-2674'],
        's0Ip0Dc26a26': ['2.2-2674', '2.2-2678'],
        's0Ip0Dc26a27': ['2.2-2679', '2.2-2680'],
        's0Ip0Dc26a28': ['2.2-2681', '2.2-2682'],
        's0Ip0Dc26a29': ['2.2-2683', '2.2-2684', '2.2-2685', '2.2-2686', '2.2-2687', '2.2-2688', '2.2-2689'],
        's0Ip0Dc26a30': ['2.2-2690', '2.2-2691', '2.2-2692', '2.2-2693', '2.2-2694', '2.2-2695'],
        's0Ip0Dc26a31': ['2.2-2696', '2.2-2697'],
        's0Ip0Dc26a32': ['2.2-2698', '2.2-2699'],
        's0Ip0Dc26a33': ['2.2-2699.1', '2.2-2699.2'],
        's0Ip0Dc26a34': ['2.2-2699.3', '2.2-2699.4'],
        's0Ip0Dc26a35': ['2.2-2699.5', '2.2-2699.6', '2.2-2699.7'],
        's0Ip0Dc26a36': ['2.2-2699.8', '2.2-2699.9', '2.2-2699.10', '2.2-2699.11', '2.2-2699.12'],
        's0Ip0Dc26a37': ['2.2-2699.13', '2.2-2699.14'],
        's0Ip0Dc27a01': ['2.2-2700', '2.2-2701', '2.2-2702', '2.2-2703', '2.2-2704'],
        's0Ip0Dc27a02': ['2.2-2705', '2.2-2706', '2.2-2707', '2.2-2708'],
        's0Ip0Dc27a03': ['2.2-2709', '2.2-2710'],
        's0Ip0Dc27a04': ['2.2-2711'],
        's0Ip0Dc27a05': ['2.2-2712', '2.2-2713', '2.2-2714'],
        's0Ip0Dc27a06': ['2.2-2715', '2.2-2716', '2.2-2717', '2.2-2718', '2.2-2719'],
        's0Ip0Dc27a07': ['2.2-2720', '2.2-2721', '2.2-2722', '2.2-2723', '2.2-2724'],
        's0Ip0Dc27a08': ['2.2-2725', '2.2-2726', '2.2-2727', '2.2-2728', '2.2-2729', '2.2-2730', '2.2-2731'],
        's0Ip0Dc27a09': ['2.2-2732', '2.2-2733'],
        's0Ip0Dc27a10': ['2.2-2734', '2.2-2735', '2.2-2736', '2.2-2737'],
        's0Ip0Dc27a11': ['2.2-2738', '2.2-2739', '2.2-2740', '2.2-2741', '2.2-2742', '2.2-2743'],
        's0Ip0Dc27.1': ['2.2-2744', '2.2-2745', '2.2-2746', '2.2-2747', '2.2-2748', '2.2-2749', '2.2-2750', '2.2-2751',
                        '2.2-2752', '2.2-2753', '2.2-2754', '2.2-2755', '2.2-2756', '2.2-2757'],
        's0Ip0Ec28': ['2.2-2800', '2.2-2801', '2.2-2802', '2.2-2803', '2.2-2804', '2.2-2805', '2.2-2806', '2.2-2807',
                      '2.2-2808', '2.2-2809', '2.2-2810', '2.2-2811', '2.2-2812', '2.2-2813', '2.2-2814', '2.2-2815',
                      '2.2-2816', '2.2-2817', '2.2-2818', '2.2-2819', '2.2-2820', '2.2-2821', '2.2-2822', '2.2-2823',
                      '2.2-2824', '2.2-2825', '2.2-2826', '2.2-2827', '2.2-2828', '2.2-2829', '2.2-2830', '2.2-2831',
                      '2.2-2832'],
        's0Ip0Ec29': ['2.2-2900', '2.2-2901', '2.2-2902', '2.2-2903', '2.2-2904', '2.2-2905'],
        's0Ip0Ec30': ['2.2-3000', '2.2-3001', '2.2-3002', '2.2-3003', '2.2-3004', '2.2-3005', '2.2-3006', '2.2-3007',
                      '2.2-3008'],
        's0Ip0Ec30.1': ['2.2-3009', '2.2-3010', '2.2-3011', '2.2-3012', '2.2-3013', '2.2-3014'],
        's0Ip0Ec31a01': ['2.2-3100', '2.2-3101'],
        's0Ip0Ec31a02': ['2.2-3102', '2.2-3103', '2.2-3104'],
        's0Ip0Ec31a03': ['2.2-3105', '2.2-3106', '2.2-3107', '2.2-3108', '2.2-3109', '2.2-3110'],
        's0Ip0Ec31a04': ['2.2-3111', '2.2-3112'],
        's0Ip0Ec31a05': ['2.2-3113', '2.2-3114', '2.2-3115', '2.2-3116', '2.2-3117', '2.2-3118'],
        's0Ip0Ec31a06': ['2.2-3119'],
        's0Ip0Ec31a07': ['2.2-3120', '2.2-3121', '2.2-3122', '2.2-3123', '2.2-3124', '2.2-3125', '2.2-3126',
                         '2.2-3127'],
        's0Ip0Ec31a08': ['2.2-3128', '2.2-3129', '2.2-3130', '2.2-3131'],
        's0Ip0Ec31a09': ['2.2-3132'],
        's0Ip0Ec32': ['2.2-3200', '2.2-3201', '2.2-3202', '2.2-3203', '2.2-3204', '2.2-3205', '2.2-3206'],
        'sIIp0Ac33': ['2.2-3300', '2.2-3301', '2.2-3302', '2.2-3303', '2.2-3304', '2.2-3305', '2.2-3306', '2.2-3307',
                      '2.2-3308', '2.2-3309', '2.2-3310', '2.2-3311', '2.2-3312', '2.2-3313',
                      '2.2-3314', '2.2-3315', '2.2-3316', '2.2-3317', '2.2-3318', '2.2-3319', '2.2-3320', '2.2-3321',
                      '2.2-3322'],
        'sIIp0Ac34': ['2.2-3400', '2.2-3401', '2.2-3402'],
        'sIIp0Ac35': ['2.2-3500', '2.2-3501', '2.2-3502', '2.2-3503', '2.2-3504'],
        'sIIp0Ac36': ['2.2-3600', '2.2-3601', '2.2-3602', '2.2-3603', '2.2-3604', '2.2-3605'],
        'sIIp0Bc37': ['2.2-3700', '2.2-3701', '2.2-3702', '2.2-3703', '2.2-3704', '2.2-3705', '2.2-3706', '2.2-3707',
                      '2.2-3708', '2.2-3709', '2.2-3710', '2.2-3711', '2.2-3712', '2.2-3713', '2.2-3714', '2.2-3715'],
        'sIIp0Bc38': ['2.2-3800', '2.2-3801', '2.2-3802', '2.2-3803', '2.2-3804', '2.2-3805', '2.2-3806', '2.2-3807',
                      '2.2-3808', '2.2-3809'],
        'sIIp0Bc38.1': ['2.2-3815','2.2-3816'],'sIIp0Bc38.2':['2.2-3817', '2.2-3818', '2.2-3819'],
                                                           'sIIp0Bc39': ['2.2-3900', '2.2-3901', '2.2-3902', '2.2-3903',
                                                                         '2.2-3904', '2.2-3905', '2.2-3906', '2.2-3907',
                                                                         '2.2-3908', '2.2-3909'],
        'sIIp0Bc40a01': ['2.2-4000', '2.2-4001', '2.2-4002', '2.2-4003', '2.2-4004'],
        'sIIp0Bc40a02': ['2.2-4005', '2.2-4006', '2.2-4007', '2.2-4008', '2.2-4009', '2.2-4010', '2.2-4011', '2.2-4012',
                         '2.2-4013', '2.2-4014', '2.2-4015', '2.2-4016'],
        'sIIp0Bc40a03': ['2.2-4017', '2.2-4018', '2.2-4019', '2.2-4020', '2.2-4021', '2.2-4022', '2.2-4023'],
        'sIIp0Bc40a04': ['2.2-4024', '2.2-4024.1', '2.2-4024.2'],
        'sIIp0Bc40a05': ['2.2-4025', '2.2-4026', '2.2-4027', '2.2-4028', '2.2-4029', '2.2-4030'],
        'sIIp0Bc40a06': ['2.2-4031', '2.2-4032', '2.2-4033'],
        'sIIp0Bc41': ['2.2 - 4100','2.2 - 4101','2.2 - 4102','2.2 - 4103','2.2 - 4104'],'sIIp0Bc41.1':['2.2-4115','2.2-4116','2.2-4117','2.2-4118','2.2-4119'],
        'sIIp0Bc42': ['2.2-4200', '2.2-4201'],
        'sIIp0Bc43a01': ['2.2-4300', '2.2-4301', '2.2-4302', '2.2-4302.1', '2.2-4302.2'],
        'sIIp0Bc43a02': ['2.2-4303', '2.2-4304', '2.2-4305', '2.2-4306', '2.2-4307', '2.2-4308', '2.2-4309', '2.2-4310',
                         '2.2-4311', '2.2-4312', '2.2-4313', '2.2-4314', '2.2-4315', '2.2-4316', '2.2-4317',
                         '2.2-4318', '2.2-4319', '2.2-4320', '2.2-4321', '2.2-4322', '2.2-4323', '2.2-4324', '2.2-4325',
                         '2.2-4326', '2.2-4327', '2.2-4328', '2.2-4329', '2.2-4330', '2.2-4331', '2.2-4332', '2.2-4333',
                         '2.2-4334',
                         '2.2-4335', '2.2-4336', '2.2-4337', '2.2-4338', '2.2-4339', '2.2-4340', '2.2-4341',
                         '2.2-4342'],
        'sIIp0Bc43a03': ['2.2-4343', '2.2-4344', '2.2-4345', '2.2-4346'],
        'sIIp0Bc43a04': ['2.2-4347', '2.2-4348', '2.2-4349', '2.2-4350', '2.2-4351', '2.2-4352', '2.2-4353', '2.2-4354',
                         '2.2-4355', '2.2-4356'],
        'sIIp0Bc43a05': ['2.2-4357', '2.2-4358', '2.2-4359', '2.2-4360', '2.2-4361', '2.2-4362', '2.2-4363', '2.2-4364',
                         '2.2-4365', '2.2-4366'],
        'sIIp0Bc43a06': ['2.2-4367', '2.2-4368', '2.2-4369', '2.2-4370', '2.2-4371', '2.2-4372', '2.2-4373', '2.2-4374',
                         '2.2-4375', '2.2-4376', '2.2-4377'],
        'sIIp0Bc43.1a01': ['2.2-4378', '2.2-4379'],
        'sIIp0Bc43.1a02': ['2.2-4380'],
        'sIIp0Bc43.1a03': ['2.2-4381'],
        'sIIp0Bc43.1a04': ['2.2-4382'],
        'sIIp0Bc43.1a05': ['2.2-4383'],
        'sIIp0Bc44': ['2.2-4400', '2.2-4401', '2.2-4402', '2.2-4403', '2.2-4404', '2.2-4405', '2.2-4406', '2.2-4407',
                      '2.2-4408', '2.2-4409', '2.2-4410', '2.2-4411'],
        'sIIp0Bc45': ['2.2-4500', '2.2-4501', '2.2-4502', '2.2-4503', '2.2-4504', '2.2-4505', '2.2-4506', '2.2-4507',
                      '2.2-4508', '2.2-4509', '2.2-4510', '2.2-4511', '2.2-4512',
                      '2.2-4513', '2.2-4514', '2.2-4515', '2.2-4516', '2.2-4517', '2.2-4518', '2.2-4519'],
        'sIIp0Bc46': ['2.2-4600', '2.2-4601', '2.2-4602', '2.2-4603', '2.2-4604', '2.2-4605', '2.2-4606'],
        'sIIp0Bc47': ['2.2-4700', '2.2-4701', '2.2-4702', '2.2-4703', '2.2-4704', '2.2-4705'],
        'sIIp0Bc48': ['2.2-4800', '2.2-4801', '2.2-4802', '2.2-4803', '2.2-4804', '2.2-4805', '2.2-4806', '2.2-4807',
                      '2.2-4808', '2.2-4809'],
        'sIIp0Bc49': ['2.2-4900', '2.2-4901', '2.2-4902', '2.2-4903', '2.2-4904', '2.2-4905', '2.2-4906'],
        'sIIp0Bc50': ['2.2-5000', '2.2-5001', '2.2-5002', '2.2-5003'],
        'sIIp0Bc50.1': ['2.2-5004', '2.2-5005'],
        'sIIp0Bc51': ['2.2-5100', '2.2-5101', '2.2-5102', '2.2-5103', '2.2-5104', '2.2-5102.1'],
        'sIIp0Bc51.1': ['2.2-5105', '2.2-5106', '2.2-5107', '2.2-5108'],
        'sIIp0Bc52': ['2.2-5200', '2.2-5201', '2.2-5202', '2.2-5203', '2.2-5204', '2.2-5205', '2.2-5206', '2.2-5207',
                      '2.2-5208', '2.2-5209', '2.2-5210', '2.2-5211', '2.2-5212', '2.2-5213', '2.2-5214'],
        'sIIp0Bc53': ['2.2-5300', '2.2-5301', '2.2-5302', '2.2-5303', '2.2-5304', '2.2-5305', '2.2-5306', '2.2-5307',
                      '2.2-5308'],
        'sIIp0Bc54': ['2.2-5400', '2.2-5401', '2.2-5402', '2.2-5403', '2.2-5404', '2.2-5405', '2.2-5406', '2.2-5407',
                      '2.2-5408'],
        'sIIp0Bc55': ['2.2-5500', '2.2-5501', '2.2-5502', '2.2-5503', '2.2-5504', '2.2-5505', '2.2-5506', '2.2-5507',
                      '2.2-5508', '2.2-5509'],
        'sIIp0Bc55.1': ['2.2-5510', '2.2-5511'],
        'sIIp0Bc55.2': ['2.2-5512', '2.2-5513'],
        'sIIp0Bc55.3': ['2.2-5514'],
        'sIIp0Bc55.4': ['2.2-5515'],
        'sIIp0Cc56': ['2.2-5600', '2.2-5601', '2.2-5602', '2.2-5603'],
        'sIIp0Cc57': ['2.2-5700', '2.2-5701', '2.2-5702'],
        'sIIp0Cc58': ['2.2-5800', '2.2-5801', '2.2-5802', '2.2-5803'],
        'sIIp0Cc59': ['2.2-5900', '2.2-5901'],
        'sIIp0Cc60': ['2.2-6000'],

        }

        title_5_1 = {
                        'c01a01': ['5.1-1', '5.1-1.1', '5.1-1.2', '5.1-1.3', '5.1-1.4', '5.1-1.5', '5.1-1.6', '5.1-1.7',
                                   '5.1-2', '5.1-2.1', '5.1-2.2', '5.1-2.3', '5.1-2.4', '5.1-2.5', '5.1-2.6', '5.1-2.7',
                                   '5.1-2.8', '5.1-2.9', '5.1-2.10', '5.1-2.11', '5.1-2.12', '5.1-2.13', '5.1-2.14',
                                   '5.1-2.15', '5.1-2.16', '5.1-2.17', '5.1-2.18', '5.1-2.19', '5.1-2.20', '5.1-2.21',
                                   '5.1-2.22', '5.1-2.23',
                                   '5.1-2.24', '5.1-3', '5.1-4', '5.1-5', '5.1-6', '5.1-7', '5.1-7.1', '5.1-7.2',
                                   '5.1-7.3', '5.1-8', '5.1-9', '5.1-9.1', '5.1-9.2', '5.1-9.3', '5.1-9.4', '5.1-9.5',
                                   '5.1-9.6', '5.1-9.7', '5.1-9.8', '5.1-9.9',
                                   '5.1-10', '5.1-11', '5.1-12'],
                        'c01a02': ['5.1-13', '5.1-14', '5.1-15', '5.1-16', '5.1-17', '5.1-18', '5.1-19', '5.1-20',
                                   '5.1-21', '5.1-22', '5.1-23', '5.1-24', '5.1-25'],
                        'c01a03': ['5.1-25.1', '5.1-25.2', '5.1-25.3', '5.1-25.4'],
                        'c02': ['5.1-26', '5.1-27', '5.1-28', '5.1-29', '5.1-30'],
                        'c2.1': ['5.1-30.1', '5.1-30.2', '5.1-30.3', '5.1-30.4', '5.1-30.5', '5.1-30.6', '5.1-30.7',
                                 '5.1-30.8', '5.1-30.9', '5.1-30.10'],
                        'c03a01': ['5.1-31', '5.1-32', '5.1-33', '5.1-34', '5.1-35', '5.1-36', '5.1-37', '5.1-38',
                                   '5.1-39', '5.1-40', '5.1-41'],
                        'c03a02': ['5.1-42', '5.1-43', '5.1-44', '5.1-45', '5.1-46'],
                        'c03a03': ['5.1-47', '5.1-48'],
                        'c04': ['5.1-49', '5.1-50'],
                        'c05': ['5.1-51', '5.1-52', '5.1-53', '5.1-54', '5.1-55'],
                        'c06': ['5.1-56', '5.1-57', '5.1-58', '5.1-59', '5.1-60', '5.1-61', '5.1-62', '5.1-63',
                                '5.1-64', '5.1-65', '5.1-66', '5.1-67', '5.1-68', '5.1-69', '5.1-70', '5.1-71',
                                '5.1-72',
                                '5.1-73', '5.1-74', '5.1-75', '5.1-76'],
                        'c07': ['5.1-77', '5.1-78', '5.1-79', '5.1-80', '5.1-81', '5.1-82'],
                        'c08': ['5.1-83', '5.1-84', '5.1-85', '5.1-86', '5.1-87', '5.1-88'],
                        'c8.1': ['5.1-88.1', '5.1-88.2', '5.1-88.3', '5.1-88.4', '5.1-88.5', '5.1-88.6'],
                        'c8.2': ['5.1-88.7', '5.1-88.8', '5.1-88.9', '5.1-88.10'],
                        'c09a01': ['5.1-89', '5.1-90', '5.1-91', '5.1-92', '5.1-93'],
                        'c09a02': ['5.1-94', '5.1-95', '5.1-96', '5.1-97', '5.1-98', '5.1-99', '5.1-100', '5.1-101',
                                   '5.1-102'],
                        'c09a03': ['5.1-103', '5.1-104', '5.1-105', '5.1-106'],
                        'c09a04': ['5.1-107'],
                        'c09a05': ['5.1-108', '5.1-109', '5.1-110', '5.1-111', '5.1-112'],
                        'c09a06': ['5.1-113', '5.1-114', '5.1-115'],
                        'c09a07': ['5.1-116', '5.1-117', '5.1-118', '5.1-119', '5.1-120'],
                        'c09a08':['5.1-121', '5.1-122', '5.1-123', '5.1-124', '5.1-125', '5.1-126', '5.1-127', '5.1-128', '5.1-129', '5.1-130', '5.1-131', '5.1-132', '5.1-133', '5.1-134', '5.1-135', '5.1-136', '5.1-137', '5.1-138', '5.1-139'],
                    'c09a09':['5.1-140', '5.1-141', '5.1-142', '5.1-143', '5.1-144', '5.1-145', '5.1-146', '5.1-147',
                              '5.1-148', '5.1-149', '5.1-150', '5.1-151'],
                             'c10': ['5.1-152', '5.1-153', '5.1-154', '5.1-155', '5.1-156', '5.1-157', '5.1-158',
                                     '5.1-159', '5.1-160', '5.1-161', '5.1-162', '5.1-163', '5.1-164', '5.1-165',
                                     '5.1-166', '5.1-167', '5.1-168', '5.1-169', '5.1-170',
                                     '5.1-171', '5.1-172', '5.1-173', '5.1-174', '5.1-175', '5.1-176', '5.1-177',
                                     '5.1-178']}

        title_10_1 = {'sIIc11a06': ['10.1-1149', '10.1-1150'],
                      'sIIc15': ['10.1-1500', '10.1-1501', '10.1-1502', '10.1-1503', '10.1-1504'],
                      'sIIc69': ['15.2-6900']}

        title_16_1 = {'c11a14': ['16.1-323', '16.1-323.1']}

        title_22_1 = {'c13a02': ['22.1-218.1'], 'c15a05': ['22.1-316', '22.1-317', '22.1-318'],
                      'c17': ['22.1-336', '22.1-337', '22.1-338'], 'c23': ['22.1-358', '22.1-359'],
                      'c24': ['22.1-360', '22.1-361']}

        title_28_2 = {'sIIc10a01': ['28.2-1000', '28.2-1000.1', '28.2-1000.2'],
                                    'sIIc10a02': ['28.2-1001', '28.2-1002', '28.2-1003', '28.2-1004', '28.2-1005',
                                                  '28.2-1006', '28.2-1007']}

        title_29_1 = {'c05a2.1': ['29.1-530.5']}

        title_33_1 = {'c03a10': ['33.1-320.1', '33.1-320.2'], 'c10.1': ['33.1-391.2'], 'c17': ['33.1-464'],
                      'c18': ['33.1-465']}

        title_38_2 = {'c61': ['38.2-6100', '38.2-6101', '38.2-6102', '38.2-6103', '38.2-6104', '38.2-6105', '38.2-6106',
                              '38.2-6107', '38.2-6108', '38.2-6109', '38.2-6110', '38.2-6111', '38.2-6112',
                              '38.2-6113'],
                      'c62': ['38.2-6200', '38.2-6201']}

        title_42_1 = {'c06': ['42.1-75']}

        title_45_1 = {'c20': ['45.1-271'], 'c24': ['45.1-381', '45.1-382']}

        title_46_2 = {'sIIc03a18': ['46.2-483', '46.2-484', '46.2-485', '46.2-486', '46.2-487', '46.2-488'],
                      'sIIIc08a18': ['46.2-944', '46.2-945', '46.2-946']}

        title_53_1 = {'c04a04': ['53.1-166', '53.1-167'],
                      'c04a05': ['53.1-168', '53.1-169''53.1-170', '53.1-171''53.1-172', '53.1-173''53.1-174',
                                 '53.1-175', '53.1-176', '53.1-177', '53.1-178'],
                      'c04a06': ['53.1-176.1', '53.1-176.2', '53.1-176.3'],
                      'c08': ['53.1-210', '53.1-211', '53.1-212', '53.1-213', '53.1-214', '53.1-215'],
                      'c09': ['53.1-216', '53.1-217']}

        title_54_1 = {
            'c30a06': ['54.1-3030', '54.1-3031', '54.1-3032', '54.1-3033', '54.1-3034', '54.1-3035', '54.1-3036',
                       '54.1-3037', '54.1-3038', '54.1-3039', '54.1-3040']}

        title_59_1 = {'c29a05': ['59.1-394.1', '59.1-394.2', '59.1-394.3', '59.1-394.4']}

        title_62_1 = {'c05': ['62.1-64', '62.1-65', '62.1-66', '62.1-67', '62.1-68', '62.1-69'],
                                    'c5.2': ['62.1-69.5'], 'c5.4': ['62.1-69.34', '62.1-69.35'],
                                    'c5.5': ['62.1-69.36', '62.1-69.37', '62.1-69.38', '62.1-69.39', '62.1-69.40',
                                             '62.1-69.41', '62.1-69.42', '62.1-69.43', '62.1-69.44'],
                                    'c5.6': ['62.1-69.45', '62.1-69.46', '62.1-69.47', '62.1-69.48', '62.1-69.49',
                                             '62.1-69.50', '62.1-69.51', '62.1-69.52'],
                                    'c06': ['62.1-70', '62.1-71', '62.1-72', '62.1-73', '62.1-74', '62.1-75', '62.1-76',
                                            '62.1-77', '62.1-77.1', '62.1-78', '62.1-79'],
                                    'c6.1': ['62.1-79.1', '62.1-79.2']}

        title_63_1 = {'': ['63.1-1']}

        title_63_2 = {'c10': ['63.2-1000'],
                      'c11': ['63.2-1100', '63.2-1101', '63.2-1102', '63.2-1103', '63.2-1104', '63.2-1105']}

        title_30 = {'c15': ['30-154.1'], 'c19': ['30-171', '30-172', '30-172'],
                    'c36': ['30-240', '30-241', '30-242', '30-243', '30-244', '30-245', '30-246', '30-247', '30-248',
                            '30-249', '30-250', '30-251', '30-252', '30-253', '30-254', '30-255', '32.1-291.1',
                            '32.1-291.2', '32.1-291.3', '32.1-291.4', '32.1-291.5', '32.1-291.6', '32.1-291.7',
                            '32.1-291.8', '32.1-291.9', '32.1-291.10', '32.1-291.11', '32.1-291.12', '32.1-291.13',
                            '32.1-291.14',
                            '32.1-291.15', '32.1-291.16', '32.1-291.17', '32.1-291.18', '32.1-291.19', '32.1-291.20',
                            '32.1-291.21', '32.1-291.22', '32.1-291.23', '32.1-291.24', '32.1-291.25'],
                    }

        title_44 = {'c01a04': ['44-54.1', '44-54.2', '44-54.3'], 'c01a07': ['44-75.1']}

        title_56 = {'': ['56-529', '56-530']}




        target = "_blank"

        for tag in self.soup.find_all("p"):
            if tag.span:
                tag.span.unwrap()

            if re.search(r"§{0,2}\s\d+(\.\d+)*-\d+(\.\d+)*\.*\s*(:\d+)*|\d+\sVa.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*)", tag.text.strip()):
                text = str(tag)

                # for match in set(x[0] for x in re.findall(r'(§\s*\d+(\.\d+)*-\d+(\.\d+)*(:\d+)*|'
                #                                               r'§§\s*\d+(\.\d+)*-\d+(\.\d+)*(:\d+)*|'
                #                                               r'\s*\d+(\.\d+)*-\d+(\.\d+)*(:\d+)*|\d+\sVa.\s\d+|S\.E\. \d+|'
                #                                               r'Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*))',
                #                                               tag.get_text())):




                for match in set(x[0] for x in re.findall(r'(§{0,2}\s\d+(\.\d+)*-\d+(\.\d+)*\.*\s*(:\d+)*|\d+\sVa\.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*))',
                                                              tag.get_text())):


                    inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|^<p\sclass="\w\d+"\sid=".+">|</p>$', '',
                                         text, re.DOTALL)

                    if re.search(r"§*\s*(?P<sec_id>\d+(\.\d+)*-\d+(\.\d+)*(:\d+)*)", match.strip()):
                        cite_id = re.search(r"§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+)(\.\d+)*)\.*\s*", match.strip())
                        title_id = f'title_{cite_id.group("title_id").zfill(2)}'
                        if cite_id.group("title_id").zfill(2) == self.title_id:
                            target = "_self"
                        else:
                            target = "_blank"


                        if not re.search(r"^§*\s*\d+\.\d+",cite_id.group("title_id").zfill(2)):
                            if cite_id.group("title_id").zfill(2) in ['01','11'] :
                                    for key,value in eval(title_id).items():
                                        if cite_id.group("sec_id") in value:
                                            tag.clear()
                                            chap_id = key

                                            tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'
                                            class_name = "ocva"
                                            format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                            text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                            tag.append(text)

                            elif cite_id.group("title_id").zfill(2) in ['30','56','44']:
                                for key, value in eval(title_id).items():
                                    if cite_id.group("sec_id") in value:
                                        tag.clear()
                                        chap_id = key
                                        tag_id = f'gov.va.compact.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'
                                        class_name = "ocva"
                                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                        text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                        tag.append(text)

                            elif cite_id.group("title_id").zfill(2) in ['02','03','04','05','06','07','08','09','10','12','13','14']:
                                tag.clear()
                                tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}c{cite_id.group("sec_id")}'

                                class_name = "ocva"
                                format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                tag.append(text)

                        else:
                            if cite_id.group("title_id").zfill(2) in ['2.1','3.1','7.1','8.01','8.03','8.05','8.05A','8.06A']:
                                tag.clear()

                                # tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}s{cite_id.group("sec_id")}'

                                tag_id = f'gov.va.code.title.0{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}s{cite_id.group("title_id")}-1'

                                class_name = "ocva"
                                format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                tag.append(text)

                            elif cite_id.group("title_id").zfill(2) in ['15.1','14.1','13.1','12.1']:
                                tag.clear()
                                tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}s{cite_id.group("sec_id")}'
                                class_name = "ocva"
                                format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                tag.append(text)

                            elif cite_id.group("title_id").zfill(2) in ['2.2','3.2','4.1','5.1','6.2','8.001','8.02','8.02A','8.03A','8.04','8.04A']:

                                title = re.sub('\.', r'_', cite_id.group("title_id"))
                                title_dict_id = f'title_{title}'

                                for key, value in eval(title_dict_id).items():
                                    if cite_id.group("sec_id") in value:
                                        tag.clear()
                                        chap_id = key
                                        tag_id = f'gov.va.code.title.0{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'

                                        class_name = "ocva"
                                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                        text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                        tag.append(text)

                            elif cite_id.group("title_id").zfill(2) in ['10.1','16.1','22.1','28.2','29.1','33.1','38.2','42.1','45.1','46.2','53.1','54.1','59.1','62.1','63.1','63.2']:
                                title = re.sub('\.', r'_', cite_id.group("title_id"))
                                title_dict_id = f'title_{title}'

                                for key, value in eval(title_dict_id).items():
                                    if cite_id.group("sec_id") in value:
                                        tag.clear()
                                        chap_id = key
                                        tag_id = f'gov.va.compact.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'
                                        class_name = "ocva"
                                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                        text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                                        tag.append(text)

                    elif re.search(r'Titles (\d+(\.\d+)*)',match.strip()):
                        tag.clear()
                        t_id = re.search(r'Titles (?P<t_id>\d+(\.\d+)*)',match.strip()).group('t_id').zfill(2)

                        tag_id = f'gov.va.code.title.0{t_id}.html'
                        class_name = "ocva"
                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                        text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
                        tag.append(text)


                    elif re.search(r'\d+\sVa\.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+', match.strip()):
                        tag.clear()
                        class_name = "va_code"

                        format_text = f'<cite class="{class_name}">{match}</cite>'
                        text = re.sub(fr'{re.escape(match)}', format_text, inside_text, re.I)
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

        for all_tag in self.soup.findAll("h2",class_="navhead"):
            all_tag.name = "p"
            del all_tag["class"]
            del all_tag["id"]

        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p','h2']:
                del tag["class"]


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

        for tag in self.meta_tags:
            cleansed_tag = re.sub(r'/>', ' />', str(tag))
            soup_str = re.sub(rf'{tag}', rf'{cleansed_tag}', soup_str, re.I)

        with open(f"../../cic-code-va/transforms/va/ocva/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str.replace('<br/>','<br />'))


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
            self.class_regex = {'ul':'^I\.','head2': '^Chapter \d+\.', 'head1': '^The Constitution of the United States|Constitution of Virginia',
                            'head3': r'^§ 1\.|^Section \d+\.','junk': '^Statute text','article':'——————————', 'ol': r'^A\.\s', 'head4': '^CASE NOTES', \
                            'amdhead':'^AMENDMENTS TO THE CONSTITUTION','casenav':'^I\.'}

            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_case_note_nav()
            self.create_case_note_ul()
            self.create_and_wrap_with_div_tag()
            self.convert_paragraph_to_alphabetical_ol_tags1()
            self.add_watermark_and_remove_class_name()


        else:
            self.generate_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_case_note_nav()
            self.create_case_note_ul()
            self.create_and_wrap_with_div_tag()
            self.convert_paragraph_to_alphabetical_ol_tags1()
            self.add_citation()
            self.add_watermark_and_remove_class_name()


        self.write_soup_to_file()
        print(datetime.now() - start_time)
