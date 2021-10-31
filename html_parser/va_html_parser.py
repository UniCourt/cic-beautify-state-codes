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


class vaParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^\d+\-\d+\.\s*|^\d+\.\d+\.|^\d+\.\d+[A-Z]*-\d+\.', 'head2': '^Chapter \d+\.', 'head1': '^Title|^The Constitution of the United States of America',
                            'head3': r'^§\s\d+(\.\d+)*[A-Z]*\-\d+\.\s*','junk': '^Statute text','article':'——————————', 'ol': r'^A\.\s', 'head4': '^CASE NOTES', \
                            'head':'^§§\s*\d+-\d+\s*through\s*\d+-\d+\.|^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*|^Part \d+\.'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name
        self.nd_list = []
        self.navhead = None
        self.snav_count = 1
        self.cnav_count = 1

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
            if p_tag.get("class") == [self.class_regex["article"]]:
                if re.search(r'^Article\s*\d+\.|^Subtitle\s*[IVX]+\.|^Part\s*[A-Z]+', p_tag.text.strip()):
                   p_tag["class"] = "navhead"
                #    self.navhead = 1
                #
                #
                # else:
                #
                #     if p_tag.find_previous('p', class_='navhead'):
                #         p_tag.find_previous('p', class_='navhead').append(p_tag.text)
                #         p_tag.clear()
                #         p_tag.unwrap()


            if p_tag.get("class") == [self.class_regex["ul"]]:

                # if re.search(r'^(\d+-\d{3}\..+\.\s*){1}', p_tag.text.strip()):

                if re.search(r'^(\d+(\.\d+)*[A-Z]*-\d{4}(\.\d+)*\..+\.\s*){1}', p_tag.text.strip()):
                    if p_tag.br:
                        string = p_tag.text.strip()

                        p_tag.clear()
                        rept_tag = re.split('(\d+(\.\d+)*[A-Z]*-\d{4}(\.\d+)*\..+\.\s*)', string)
                        for tag_text in rept_tag:
                            if tag_text:
                                if re.search('^(\d+(\.\d+)*[A-Z]*-\d{4}(\.\d+)*\..+\.\s*)', tag_text):
                                    new_tag = self.soup.new_tag("p")
                                    new_tag.string = tag_text
                                    new_tag["class"] = [self.class_regex["ul"]]

                                    p_tag.append(new_tag)


                        p_tag.unwrap()

    def replace_tags(self):
        cur_id_list = []
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if re.search('constitution\.va', self.html_file_name):
                    self.title_id  = 'constitution-va'
                elif re.search('constitution\.us', self.html_file_name):
                    self.title_id  = 'constitution-us'


                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^The Constitution of the United States|^Constitution of Virginia',header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag['id'] =  self.title_id
                    elif re.search(r'^ARTICLE [IVX]+\.',header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^ARTICLE (?P<ar_id>[IVX]+)\.', header_tag.text.strip()).group('ar_id')
                        header_tag[
                            'id'] = f"{header_tag.find_previous('h1').get('id')}a{article_id.zfill(2)}"

                if header_tag.get("class") == [self.class_regex["ul"]] and not re.search('^PREAMBLE|^Sec\.',header_tag.text.strip()):
                    header_tag.name = "li"



            #titlefiles
            else:
                if header_tag.get("class") == [self.class_regex["head1"]]:
                    if re.search(r'^(Title)\s(?P<title_id>\d+)', header_tag.text.strip()):
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag.wrap(self.soup.new_tag("nav"))
                        self.title_id = re.search(r'^(Title)\s(?P<title_id>\d+(\.\d+)*[A-Z]*)', header_tag.text.strip()).group('title_id').zfill(2)
                        header_tag['id']  =f"tself.title_id"

                    elif  re.search(r'^Article\s*(?P<ar_id>\d+)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        article_id = re.search(r'^Article\s*(?P<ar_id>\d+)\.', header_tag.text.strip()).group('ar_id')
                        header_tag['id'] = f"{header_tag.find_previous('h2',class_='chapter').get('id')}a{article_id.zfill(2)}"
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

                    # if header_tag.find_previous('h2',class_="part"):
                    #     header_tag['id'] = f"{header_tag.find_previous('h2', class_='part').get('id')}c{chapter_id.zfill(2)}"
                    # elif header_tag.find_previous('h2',class_="subtitle"):
                    #     header_tag[
                    #         'id'] = f"{header_tag.find_previous('h2', class_='subtitle').get('id')}c{chapter_id.zfill(2)}"
                    # else:
                    #     header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"

                    # if header_tag.find_previous('h2'):
                    #     header_tag['id'] = f"{header_tag.find_previous('h2').get('id')}c{chapter_id.zfill(2)}"
                    # else:
                    #     header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"

                    if header_tag.find_previous('h2', class_ =['part','subtitle']):
                        header_tag['id'] = f"{header_tag.find_previous('h2', class_=['part','subtitle']).get('id')}c{chapter_id.zfill(2)}"
                    else:
                        header_tag['id'] = f"t{self.title_id.zfill(2)}c{chapter_id.zfill(2)}"



                    header_tag["class"] = "chapter"
                    self.navhead = None
                    self.snav_count = 1


                elif header_tag.get("class") == [self.class_regex["head3"]]:
                    header_tag.name = "h3"

                    section_id = re.search(r'^§+\s(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*)\.*\s*', header_tag.text.strip()).group(
                        'sec_id')

                    header_tag['id'] = f"{header_tag.find_previous(['h2','h1']).get('id')}s{section_id.zfill(2)}"


                elif header_tag.get("class") == [self.class_regex["head4"]]:
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
                        article_id = re.search(r'^Article\s*(?P<ar_id>\d+)\.', header_tag.text.strip()).group('ar_id')

                        if header_tag.find_previous('h2', class_='chapter'):
                            header_tag['id'] = f"{header_tag.find_previous('h2', class_='chapter').get('id')}a{article_id.zfill(2)}"
                        else:
                           header_tag[
                               'id'] = f"{header_tag.find_previous('h2', class_='subtitle').get('id')}a{article_id.zfill(2)}"


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
                if main_tag.find_next("h2") == first_chapter_header:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    section_nav_tag.append(main_tag)

                if main_tag.name == "span" or main_tag.name == "b" or main_tag.name == "i":
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

                    if re.match(r'Preamble', ul_tag.find_previous().text.strip()):
                        ul_tag.find_previous("nav").append(ul_tag.find_previous())
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
                if re.search(r'^[IXV]+\.|^AMENDMENTS', list_item.text.strip()):
                    if re.match(r'^[IXV]+\.', list_item.text.strip()):
                        chap_num = re.search(r'^(?P<chap>[IXV]+)\. ', list_item.text.strip()).group(
                            "chap").zfill(2)
                        sub_tag = "a"
                        prev_id = None


                    # elif re.match(r'^ARTICLE', list_item.text.strip()):
                    #     chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[A-Z]+))|^(AMENDMENTS)',
                    #                          list_item.text.strip()).group(
                    #         "ar").zfill(2)
                    #     sub_tag = "-ar"
                    #     prev_id = None
                    #
                    # elif re.match(r'^Section', list_item.text.strip()):
                    #     if list_item.find_previous("h3"):
                    #         prev_id = list_item.find_previous("h3").get("id")
                    #     else:
                    #         prev_id = list_item.find_previous("h2").get("id")
                    #
                    #     chap_num = re.search(r'^(Section\s?(?P<sec>\d+).)', list_item.text.strip()).group("sec").zfill(
                    #         2)
                    #     nav_list = []
                    #     sub_tag = "s"
                    #
                    # elif re.match(r'^AMENDMENTS', list_item.text.strip()):
                    #     chap_num = re.sub(r'[\W]', '', list_item.text.strip())
                    #     sub_tag = "-am"
                    #     prev_id = None
                    #
                    # elif re.match(r'^AMENDMENT', list_item.text.strip()):
                    #     chap_num = re.search(r'AMENDMENT (?P<chap>[I,V,X]+)', list_item.text.strip()).group("chap")
                    #     prev_id = list_item.find_previous("h2", class_="amendh2").get("id")
                    #     sub_tag = "-amend"

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

            # title files
            else:
                if re.search(r'^(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+)\.*\s*', list_item.text.strip()):
                    chap_id = re.search(r'^(?P<sec_id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*)\.*\s*', list_item.text.strip()).group('sec_id')
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



    # create div tags
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
        sec_alpha_cur_tag = None
        flag = None

        for p_tag in self.soup.find_all():
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()

            #A.
            if re.search(rf'^{cap_alpha}\.', current_tag_text):

                p_tag.name = "li"
                ol_head = 1
                cap_alpha_cur_tag = p_tag

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol",type="A")
                    p_tag.wrap(cap_alpha_ol)
                    cap_alpha_id = f"{p_tag.find_previous('h3').get('id')}ol{ol_count}"

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


            #1.
            elif re.search(rf'^{ol_head}\.', current_tag_text) and p_tag.name == "p":

                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha1 ='a'

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)

                    num_id = f"{p_tag.find_previous('h3').get('id')}ol{ol_count}"

                    if cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(num_ol)
                        num_id = cap_alpha_cur_tag.get('id')

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





            #(a)
            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) :

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
                        sec_alpha_id = f"{p_tag.find_previous(['h5','h4','h3','h2']).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)


            #a.
            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) :
                # print(current_tag_text)

                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^a\.', current_tag_text):
                    # print(current_tag_text)
                    sec_alpha_ol1 = self.soup.new_tag("ol",type="a")
                    p_tag.wrap(sec_alpha_ol1)


                    if num_cur_tag:
                        sec_alpha_id1 = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol1)
                    else:
                        sec_alpha_id1 = f"{p_tag.find_previous(['h5','h4','h3','h2']).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

            # (1)
            elif re.search(rf'^\({num_count}\)', current_tag_text):
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                main_sec_alpha = 'a'


                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous(['h5','h4','h3','h2']).get('id')}ol{ol_count}"
                        main_sec_alpha = 'a'

                else:
                    num_ol1.append(p_tag)

                    # if not sec_alpha_cur_tag:
                    #     main_sec_alpha = 'a'


                p_tag["id"] = f'{num_id1}{ol_head}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

            elif re.search(r'^\([ivx]+\)', current_tag_text):
                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")

                    p_tag.wrap(roman_ol)
                    sec_alpha_cur_tag.append(roman_ol)
                    prev_id1 = sec_alpha_cur_tag.get("id")

                else:

                    roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[ivx]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([ivx]+\)', '', current_tag_text)

            #
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

        print('ol tags added')



    def add_citation(self):

        title_01 = {'c01': ['1-1', '1-2', '1-2.1', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8', '1-9'],
                    'c2.1': ['1-200', '1-201','1-202','1-203','1-204','1-205','1-206', '1-207','1-208','1-209','1-210','1-211', '1-212','1-213','1-214','1-215','1-216'
                            , '1-217','1-218','1-219','1-220','1-221', '1-222','1-223','1-224','1-225','1-226', '1-227','1-228','1-229','1-230','1-231'
                            , '1-232','1-233','1-234','1-235','1-236', '1-237','1-238','1-239','1-240','1-241', '1-242','1-243','1-244','1-245','1-246'
                        , '1-247', '1-248', '1-249', '1-250', '1-251', '1-252','1-253','1-254','1-255','1-256', '1-257','1-208.1','1-211.1','1-219.1','1-222.1','1-240.1', '1-201','1-202','1-203','1-204','1-205'],

                    'c3.1': ['1-300','1-301','1-302','1-303','1-304','1-305','1-306','1-307','1-308','1-309','1-310','1-311','1-312','1-313'],
                    'c04':['1-400','1-401','1-402','1-403','1-404','1-405','1-406','1-407','1-408'],
                    'c05':['1-500','1-501','1-502','1-503','1-504','1-505','1-506','1-507','1-508','1-509','1-510','1-511','1-512'],
                    'c06':['1-600','1-601','1-602','1-603','1-604','1-605','1-606','1-607','1-608','1-609','1-610']
                    }

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








        title_article_01 = {'c2.1a01': ['1-200', '1-201'],
                            'c2.1a02': ['1-202', '1-203', '1-204', '1-205', '1-206', '1-207', '1-208', '1-209', '1-210',
                                    '1-211', '1-212', '1-213', '1-214', '1-215', '1-216'
                                , '1-217', '1-218', '1-219', '1-220', '1-221', '1-222', '1-223', '1-224', '1-225',
                                    '1-226', '1-227', '1-228', '1-229', '1-230', '1-231'
                                , '1-232', '1-233', '1-234', '1-235', '1-236', '1-237', '1-238', '1-239', '1-240',
                                    '1-241', '1-242', '1-243', '1-244', '1-245', '1-246'
                                , '1-247', '1-248', '1-249', '1-250', '1-251', '1-252', '1-253', '1-254', '1-255',
                                    '1-256', '1-257', '1-208.1', '1-211.1', '1-219.1', '1-222.1', '1-240.1', '1-201',
                                    '1-202', '1-203', '1-204', '1-205'],
                            'c05a01':['1-500','1-501','1-502','1-503','1-504','1-505','1-506','1-507','1-508','1-509'],
                            'c05a02':['1-510','1-511','1-512']}












        tag_id = None
        target = "_blank"

        for tag in self.soup.find_all(["p"]):


            if tag.span:
                tag.span.unwrap()




            if re.search(r"§*\s(?P<sec_id>\d+(\.\d+)*-\d+(\.\d+)*)\.*\s*", tag.text.strip()):
                text = str(tag)

                for match in set(x[0] for x in re.findall(r'(§\s*\d+(\.\d+)*-\d+(\.\d+)*|'
                                                          r'§§\s*\d+(\.\d+)*-\d+(\.\d+)*|'
                                                          r'\s*\d+(\.\d+)*-\d+(\.\d+)*)',
                                                    tag.get_text())):



                    inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|^<li\sclass="\w\d+"\sid=".+">|</li>$', '',
                                         text, re.DOTALL)


                    if re.search(r"§*\s*(?P<sec_id>\d+(\.\d+)*-\d+(\.\d+)*)", match.strip()):

                        tag.clear()
                        cite_id = re.search(r"§*\s*(?P<sec_id>(?P<title_id>\d+(\.\d+)*)-(?P<chap_id>\d+)(\.\d+)*)\.*\s*", match.strip())

                        title_id = f'title_{cite_id.group("title_id").zfill(2)}'
                        article_id = f'title_article_{cite_id.group("title_id").zfill(2)}'

                        if cite_id.group("title_id").zfill(2) == self.title_id:
                            target = "_self"
                        else:
                            target = "_blank"


                        if not re.search(r"^§*\s*\d+\.\d+",cite_id.group("title_id").zfill(2)):

                            if not cite_id.group("title_id").zfill(2) in ['02','03','04','05','06','07','08','09','10','12','13','14'] and int(cite_id.group("title_id").zfill(2))<=15 :

                                    for key,value in eval(title_id).items():
                                        if cite_id.group("sec_id") in value:
                                            chap_id = key


                                    if article_id == 'title_article_01':
                                        for key,value in eval(article_id).items():
                                            if cite_id.group("sec_id") in value:
                                                art_id = key

                                                tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{art_id}s{cite_id.group("sec_id")}'
                                                break
                                            else:
                                                tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'

                                    else:
                                        tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}{chap_id}s{cite_id.group("sec_id")}'

                            else:
                                tag_id = f'gov.va.code.title.{cite_id.group("title_id").zfill(2)}.html#t{cite_id.group("title_id").zfill(2)}c{cite_id.group("sec_id")}'


                        else:
                            if cite_id.group("title_id").zfill(2) in ['2.1','3.1','7.1','8.1','8.03','8.5','8.5A']:
                                tag_id = f'gov.va.code.title.0{cite_id.group("title_id").zfill(2)}.html#t0{cite_id.group("title_id").zfill(2)}s{cite_id.group("sec_id")}'

                            else:
                                print(match)






                        class_name = "ocva"
                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
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

            # if all_tag.get("class") == "navhead":
            #
            #     all_tag.name = "p"
            #     del all_tag["class"]

        # for all_tag in self.soup.findAll():
        #     if all_tag.get("class"):
        #         print(all_tag)
        #         all_tag_class = str(all_tag.get("class"))
        #         # print(all_tag_class)
        #         if re.match(r'^\[\'p\d\'\]',all_tag_class.strip()):
        #             del all_tag["class"]


        # for all_li in self.soup.find_all("li"):
        #     if re.search(r'^<li\s*class="p\d"', all_li.text.strip()):
        #         all_li.unwrap()


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
        with open(f"/home/mis/PycharmProjects/code-vt/transforms/va/ocva/r{self.release_number}/{self.html_file_name}", "w") as file:
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
            self.class_regex = {'ul':'^I\.','head2': '^Chapter \d+\.', 'head1': '^The Constitution of the United States|Constitution of Virginia',
                            'head3': r'^§ 1\.|^Section 1\.','junk': '^Statute text','article':'——————————', 'ol': r'^A\.\s', 'head4': '^CASE NOTES', \
                            'head':'^§§\s*\d+-\d+\s*through\s*\d+-\d+\.|^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*|^Part \d+\.'}

            self.get_class_name()
            self.remove_junk()

            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            # self.create_and_wrap_with_div_tag()
            #
            # self.add_citation()
            # self.add_watermark_and_remove_class_name()


        else:
            self.get_class_name()
            self.remove_junk()
            self.recreate_tag()
            self.replace_tags()
            self.create_main_tag()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            self.create_and_wrap_with_div_tag()
            # self.convert_paragraph_to_alphabetical_ol_tags1()
            self.add_citation()
            self.add_watermark_and_remove_class_name()


        self.write_soup_to_file()
        print(datetime.now() - start_time)
