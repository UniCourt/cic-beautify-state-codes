import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexVA
import roman


class VAParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.title_name = None
        self.file_no = None
        self.nd_list = []

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {
                'head1': r'^THE CONSTITUTION OF THE UNITED STATES OF AMERICA|Constitution of Virginia|^The Constitution of the United States',
                'ul': r'^PREAMBLE|^Article', 'head2': r'^Article I\.',
                'head3': r'^§ 1\.|^Section \d+\.', 'junk1': '^Text', 'article': '——————————',
                'ol_p': r'^A\.\s', 'head4': '^CASE NOTES',
                'amdhead': '^AMENDMENTS TO THE CONSTITUTION', 'casenav': r'^I\.'}

            self.h2_order: list = ['article']

            if self.release_number in ['86', '87']:
                self.tag_type_dict['ul'] = '^Article I\.'
                self.tag_type_dict['head2'] = '^Article I'
            if re.search('compact\.constitution', self.input_file_name):
                self.tag_type_dict['head1'] = r'^The Constitution of the United States'
                self.tag_type_dict['ul'] = r'^PREAMBLE'
                self.tag_type_dict['head3'] = r'^§ 1\.|^Section \d+\.'
                self.tag_type_dict['head2'] = r'^Article I\.'
                self.tag_type_dict['junk1'] = r'^Statute text'
        else:
            if self.release_number in ['83', '84', '85']:
                self.tag_type_dict: dict = {'ul': r'^Chap.$|^\d.',
                                            'head1': r'^Title|^The Constitution of the United States of America',
                                            'head2': r'^Chapter \d+\.|^PART 1\.',
                                            'head3': r'^§\s\d+(\.\d+)*[A-Z]*\-\d+\.\s*|^§',
                                            'junk1': '^Text|^Statute text',
                                            'article': '——————————',
                                            'head4': '^CASE NOTES', 'ol_p': r'^1\.\s', 'ol': 'I.'}
            else:
                self.tag_type_dict: dict = {'ul': r'^(Chapter|PART) \d+\.|^Chap.|^\d.',
                                            'head1': r'^Title|^The Constitution of the United States of America',
                                            'head2': r'^Chapter \d+\.|^PART 1\.|^§',
                                            'head3': r'^§\s\d+(\.\d+)*[A-Z]*\-\d+\.\s*|^§',
                                            'junk1': '^Text|^Statute text',
                                            'article': '——————————',
                                            'head4': '^CASE NOTES', 'ol_p': r'^A\.\s'}

            self.h2_text: list = []
            title_name = re.search(r'gov\.va\.(?P<title>code|compact)\.title\.(?P<fno>\w+(\.\d+[A-Z]?)*)\.html',
                                   self.input_file_name)
            self.file_no = title_name.group("fno")
            self.title_name = title_name.group("title")

            if self.file_no in ['58.1', '06.2', '04.1', '10.1', '15.2', '23.1', '33.2', '37.2', '46.2', '45.2', '55.1',
                                '54.1', '63.2', '64.2', '28.2', '58.1'] and title_name.group("title") == "code":
                self.h2_order: list = ['subtitle', 'chapter', 'article', 'part']
            elif self.file_no in ['03.2', '02.2']:
                self.h2_order: list = ['subtitle', 'part', 'chapter', 'article']
            elif self.file_no in ['08.01A', '08.02', '08.02A', '08.03', '08.03A', '08.04', '08.04A',
                                  '08.05', '08.07', '08.08A', '08.09A']:
                self.h2_order: list = ['part']
            elif self.file_no in ['28.2', '10.1', '03.2', '02.2'] and title_name.group("title") == "compact":
                self.h2_order: list = ['subtitle', 'chapter', 'article']
            else:
                self.h2_order: list = ['chapter', 'article']

            if self.file_no in ['46.2'] and title_name.group("title") == "compact":
                self.h2_order: list = ['subtitle', 'chapter', 'article']
            if self.file_no in ['45.2'] and self.release_number in ['84', '83', '85']:
                self.h2_order: list = ['subtitle', 'chapter', 'article']
            if self.file_no in ['45.2', '64.2'] and self.release_number in ['87', '86', '85'] and title_name.group(
                    "title") == "code":
                self.h2_order: list = ['subtitle', 'part', 'chapter', 'article', ]

        self.h2_pattern_text = ['^(?P<tag>P)art\s*(?P<id>[A-Z0-9])\.', '^(?P<tag>P)ART\s*(?P<id>[A-Z])\.']

        self.h4_head: list = ['VIRGINIA COMMENT', 'Cross references:', 'OFFICIAL COMMENT', 'History.',
                              'Compiler’s Notes.', 'NOTES TO DECISIONS', 'CASE NOTES']

        self.watermark_text = """Release {0} of the Official Code of Virginia Annotated released {1}.
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """
        self.regex_pattern_obj = CustomisedRegexVA()

    def replace_tags_titles(self):
        for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
            if not re.search(r'^(chapter|subchapter|article|part|subpart|subtitle|'
                             r'^\d+(\.\d+)?|^\d+(\.\d+)?-\d+(\.\d+)?)', li_tag.text.strip(), re.I):
                li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                self.h2_text.append(li_tag_text)

        if self.file_no in ['02.2', '45.2'] and self.release_number in ['84']:
            self.regex_pattern_obj.h2_part_pattern = re.compile(r'^part\s?(?P<id>([A-Z0-9]{1,2}))$', re.I)

        super(VAParseHtml, self).replace_tags_titles()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_rom_id = None
        h5_alpha_id = None
        h5_num_id = None
        h5_s_alpha_id = None
        nav_article_pattern = re.compile(r'^Article (?P<id>\d+(\.\d+)?(:\d+)?)\.', re.I)
        h4_article_pattern = re.compile(r'^Article (?P<id>[IVX]+)', re.I)
        dup_h5_id_list: list = []

        for header_tag in self.soup.find_all():
            if sec_tag := re.search(r'^SECTION\s?(?P<id>\d+)\.?', header_tag.text.strip()):
                self.replace_h4_tag_titles(header_tag, self.h4_count, sec_tag.group("id"))

            if header_tag.name == "h3":
                cap_roman = "I"
                h5_num_id = None
                h5_s_alpha_id = None
            if header_tag.get("class") == [self.tag_type_dict["head4"]] or \
                    (header_tag.get("class") == [self.tag_type_dict["ol_p"]] and self.release_number == '85' and
                     self.release_number in ['55.1']):
                if header_tag.text.strip() in self.h4_head:
                    self.replace_h4_tag_titles(header_tag, self.h4_count, None)
                else:
                    if re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_rom_id = f"{header_tag.find_previous('h3').get('id')}-notetodecisison-{h5_rom_text}"
                        header_tag['id'] = h5_rom_id
                        cap_alpha = 'A'
                        cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                    elif cap_alpha and re.search(fr'^{cap_alpha}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                        header_tag['id'] = h5_alpha_id
                        cap_alpha = chr(ord(cap_alpha) + 1)
                        cap_num = 1

                    elif cap_num and re.search(fr'^{cap_num}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', header_tag.text.strip()).group("h5_id")
                        h5_num_id = f"{h5_alpha_id}-{h5_num_text}"
                        header_tag['id'] = h5_num_id
                        cap_num += 1

                    elif re.search(r'^[ivx]+\.(?!e\.)', header_tag.text.strip()) and h5_s_alpha_id:
                        header_tag.name = "h5"
                        h5_s_rom_text = re.search(r'^(?P<h5_id>[ivx]+)\.', header_tag.text.strip()).group("h5_id")
                        h5_s_rom_id = f"{h5_s_alpha_id}-{h5_s_rom_text}"
                        header_tag['id'] = h5_s_rom_id

                    elif re.search(r'^[a-z]+\.(?!e\.)', header_tag.text.strip()) and h5_num_id:
                        header_tag.name = "h5"
                        h5_s_alpha_text = re.search(r'^(?P<h5_id>\w+)\.', header_tag.text.strip()).group("h5_id")
                        h5_s_alpha_id = f"{h5_num_id}-{h5_s_alpha_text}"
                        if h5_s_alpha_id in dup_h5_id_list:
                            h5_s_alpha_id = f"{h5_num_id}-{h5_s_alpha_text}.{count}"
                            count += 1
                        else:
                            count = 1

                        header_tag['id'] = h5_s_alpha_id
                        dup_h5_id_list.append(h5_s_alpha_id)

            elif header_tag.get("class") == [self.tag_type_dict["article"]] or \
                    header_tag.get("class") == [self.tag_type_dict["ol_p"]]:

                if (self.title_name == "compact" and self.release_number in ['87', '86']) or (
                        self.release_number in ['83', '84', '85']):
                    if nav_article_pattern.search(header_tag.text.strip()):
                        header_tag["class"] = "navhead"
                        header_tag[
                            "id"] = f'{header_tag.find_previous({"h2", "h1"}).get("id")}a{nav_article_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                    elif h4_article_pattern.search(header_tag.text.strip()):
                        self.replace_h4_tag_titles(header_tag, 1,
                                                   self.regex_pattern_obj.h2_article_pattern.search(
                                                       header_tag.text.strip()).group("id"))
                    elif self.regex_pattern_obj.h2_subtitle_pattern.search(header_tag.text.strip()):
                        if not header_tag.text.strip().isupper():
                            header_tag["class"] = "navhead"
                            header_tag[
                                "id"] = f'{header_tag.find_previous("h1").get("id")}s{self.regex_pattern_obj.h2_subtitle_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                    elif self.regex_pattern_obj.h2_part_pattern.search(header_tag.text.strip()):
                        header_tag["class"] = "navhead"
                        header_tag[
                            "id"] = f'{header_tag.find_previous(class_="navhead", text={self.regex_pattern_obj.h2_subtitle_pattern, nav_article_pattern}).get("id")}' \
                                    f'p{self.regex_pattern_obj.h2_part_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                elif self.file_no in ['16.1'] and self.regex_pattern_obj.h2_article_pattern.search(
                        header_tag.text.strip()):
                    if self.release_number in ['87', '86']:
                        header_tag.name = "h4"
                        header_tag[
                            "id"] = f'{header_tag.find_previous("h3").get("id")}a{self.regex_pattern_obj.h2_article_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                    else:
                        header_tag["class"] = "navhead"
                        header_tag[
                            "id"] = f'{header_tag.find_previous("h2").get("id")}a{self.regex_pattern_obj.h2_article_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                elif h4_article_pattern.search(header_tag.text.strip()):
                    self.replace_h4_tag_titles(header_tag, self.h4_count,
                                               self.regex_pattern_obj.h2_article_pattern.search(
                                                   header_tag.text.strip()).group("id"))

            elif header_tag.get("class") == [self.tag_type_dict["head3"]]:
                if re.search(r'^United States Census of \d+\.', header_tag.text.strip()):
                    header_tag.name = "h3"
                    header_tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    header_tag["id"] = f'{header_tag.find_previous("h2").get("id")}-{header_tag_text}'
                elif self.release_number == '87' and self.file_no in ['03.2']:
                    if h5_tag := re.search(r'^§ (?P<id>\d+)\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        header_tag["id"] = f"{header_tag.find_previous({'h4', 'h3'}).get('id')}-{h5_tag.group('id')}"

            if re.search(r'^(Analysis|CASE NOTES)$', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["ol_p"]] and \
                            not re.search(r'^Analysis$', tag.text.strip()):
                        tag["class"] = "casenote"
                        tag.name = "li"
                    else:
                        break

        self.recreating_tag()

    def add_anchor_tags(self):
        super(VAParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.findAll(["li", 'h2', 'h3', 'h4']):
            if li_tag.name == "li" and not li_tag.get("id"):
                if re.search(r'^APPENDIXRULES', li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    sub_tag = 'apr'
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)
                elif self.regex_pattern_obj.h2_chapter_pattern.search(li_tag.text.strip()):
                    self.p_nav_count += 1
                    cnav = f'cnav{self.p_nav_count:02}'
                    self.set_chapter_section_id(li_tag, self.regex_pattern_obj.h2_chapter_pattern.search(
                        li_tag.text.strip()).group(("id")),
                                                "c", li_tag.find_previous("h2").get("id"), cnav)
                elif re.search(r'^(?P<id>\d+(\.\d+)?[A-Z]?-\d+(\.\d+)?(:\d+)?(\.\d+)?)',
                               li_tag.text.strip()):
                    self.s_nav_count += 1
                    cnav = f'snav{self.s_nav_count:02}'
                    if self.release_number in ['83', '84', '85'] and (
                            self.file_no in ['08.05A', '08.10', '08.11', '41.1'] or
                            (self.file_no in [
                                '03.2'] and self.title_name == "compact")):
                        tag = "c"
                    else:
                        tag = "s"
                    self.set_chapter_section_id(li_tag,
                                                re.search(r'^(?P<id>\d+(\.\d+)?[A-Z]?-\d+(\.\d+)?(:\d+)?(\.\d+)?)',
                                                          li_tag.text.strip()).group(("id")),
                                                tag, li_tag.find_previous(class_={"navhead1", "navhead", "gen",
                                                                                  "oneh2", "twoh2", "threeh2", "fourh2",
                                                                                  "title"}).get("id"), cnav)
                elif re.search(r'^(?P<id>\d+(\.\d+)?)', li_tag.text.strip()) and (self.release_number in ['83', '84',
                                                                                                          '85'] or self.title_name == "compact"):
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    if re.search(r'^(Part|Sec\.)', li_tag.find_previous("p").text.strip()):
                        tag = li_tag.find_previous("p").text.strip()[0].lower()
                    else:
                        tag = "c"
                    self.set_chapter_section_id(li_tag,
                                                re.search(r'^(?P<id>\d+(\.\d+)?)', li_tag.text.strip()).group(("id")),
                                                tag, li_tag.find_previous(class_={"navhead", "title"}).get("id"), cnav)

            if li_tag.name == "li" and self.file_no == '03.2' and self.release_number in ['83', '84', '85'] and \
                    li_tag.a and re.search(r'^3\.2-31(0[0-9]|1[0-1])\.', li_tag.a.text.strip()):
                li_tag["id"] = li_tag.get("id").replace("p0Cc30.1", "p0Dc31")
                li_tag.a["href"] = li_tag.a.get("href").replace("p0Cc30.1", "p0Dc31")

            if li_tag.name == "li" and self.file_no == '15.2' and self.release_number not in ['83', '84', '85'] and \
                    li_tag.a and re.search(r'^United States Census of \d+\.', li_tag.a.text.strip()):
                li_tag_text = re.sub(r'[\W\s]+', '', li_tag.a.text.strip()).lower()
                li_tag_id = f'{li_tag.find_previous("h2").get("id")}-{li_tag_text}'
                li_tag["id"] = li_tag_id
                li_tag.a["href"] = f'#{li_tag_id}'

            elif li_tag.name in ['h2', 'h3', 'h4']:
                self.a_nav_count = 0
                self.c_nav_count = 0
                self.p_nav_count = 0
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
        ol_count = 1
        ol_head1 = 1
        cap_rom = "I"
        main_sec_alpha1 = 'a'
        cap_alpha1 = 'A'

        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
        num_ol1 = self.soup.new_tag("ol", type="1")
        cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
        roman_ol = self.soup.new_tag("ol", type="i")
        cap_roman_ol = self.soup.new_tag("ol", type="I")

        cap_alpha_cur_tag = None
        sec_alpha_cur_tag = None
        num_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        n_tag = None
        roman_cur_tag = None
        previous_li_tag = None

        cap_alpha_id = None
        num_id = None
        sec_alpha_id = None
        sec_alpha_id1 = None
        num_id1 = None
        cap_alpha_id1 = None
        prev_id1 = None
        prev_id = None

        for p_tag in self.soup.body.find_all(['h2', 'h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()

            if re.search(rf'^{cap_alpha}\.', current_tag_text) and \
                    p_tag.name == "p" and p_tag.get("class") != "casenote":
                p_tag.name = "li"
                ol_head = 1
                cap_alpha_cur_tag = p_tag
                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)
                if cap_alpha == "Z":
                    cap_alpha = "A"
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

                if re.search(r'^[A-Z]+\.\s*\d+\.', current_tag_text):
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
                    if re.search(r'[A-Z]+\.\s*\d+\.\s*[a-z]+\.', current_tag_text):
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
                previous_li_tag = p_tag

            elif re.search(rf'^{ol_head}\.', current_tag_text) and \
                    p_tag.name == "p" and p_tag.get("class") != "casenote":
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha1 = "A"

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                    if cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(num_ol)
                        num_id = cap_alpha_cur_tag.get('id')
                        main_sec_alpha = "a"
                        main_sec_alpha1 = "a"
                    elif n_tag:
                        n_tag.append(num_ol)
                        num_id = n_tag.get('id')
                        main_sec_alpha = "a"
                        main_sec_alpha1 = "a"
                    elif cap_alpha_cur_tag1:
                        cap_alpha_cur_tag1.append(num_ol)
                        num_id = cap_alpha_cur_tag1.get("id")
                        main_sec_alpha = 'a'
                        main_sec_alpha1 = "a"
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(num_ol)
                        num_id = sec_alpha_cur_tag.get('id')

                else:
                    num_ol.append(p_tag)
                    if not sec_alpha_cur_tag:
                        main_sec_alpha = "a"

                p_tag["id"] = f'{num_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1
                ol_head1 += 1

                if re.search(r'^\d+\.\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\d+\.\s?\(i\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'\d+\.\s*\((?P<nid>i)\)', current_tag_text)
                    prev_id1 = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{prev_id1}{cur_tag.group("nid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)

                if re.search(r'^\d+\.\s*[a-z]+\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\d+\.\s*[a-z]+\.', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'(?P<pid>\d+)\.\s*(?P<nid>[a-z]+)\.', current_tag_text)
                    sec_alpha_id1 = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol1)
                    main_sec_alpha1 = 'b'

                if re.search(r'^\d+\.\s*\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\d+\.\s*\(a\)', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    sec_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = 'b'
                    num_count = 1
                    if re.search(r'^\d+\.\s*\([a-z]\)\s*\(1\)', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\d+\.\s*\([a-z]\)\s*\(1\)', '', current_tag_text)
                        num_cur_tag1 = inner_li_tag
                        num_id1 = f'{sec_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                        num_ol1.append(inner_li_tag)
                        sec_alpha_cur_tag.string = ""
                        sec_alpha_cur_tag.append(num_ol1)
                        num_count = 2

                if re.search(r'^\d+\.\s*\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\d+\.\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag1 = li_tag
                    cap_alpha_id1 = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}A'
                    cap_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_alpha_ol1)
                    cap_alpha1 = 'B'
                    cap_rom = "I"
                previous_li_tag = p_tag

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        sec_alpha_id = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol)
                        num_count = 1
                    elif num_cur_tag1:
                        sec_alpha_id = num_cur_tag1.get('id')
                        num_cur_tag1.append(sec_alpha_ol)
                    else:
                        ol_head = 1
                        num_count = 1
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                    if re.search(r'ol\da$', p_tag.parent.find_next("li").get("id")):
                        num_count = 1

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(r'^\(\w\)\s*\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\(1\)', '', current_tag_text)
                    num_cur_tag1 = li_tag
                    num_id1 = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_id1}1'
                    num_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol1)
                    num_count = 2
                previous_li_tag = p_tag

            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)
                    if num_cur_tag:
                        sec_alpha_id1 = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol1)
                    elif roman_cur_tag:
                        sec_alpha_id1 = roman_cur_tag.get("id")
                        roman_cur_tag.append(sec_alpha_ol1)
                    elif num_cur_tag1:
                        sec_alpha_id1 = num_cur_tag1.get("id")
                        num_cur_tag1.append(sec_alpha_ol1)
                    else:
                        sec_alpha_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"

                else:
                    sec_alpha_ol1.append(p_tag)

                    if p_tag.parent.find_next("li").get("id") and \
                            not re.search(r'ol\d+[a-z]$', p_tag.parent.find_next("li").get("id")):
                        ol_head = 1
                        num_count = 1

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

                if re.search(r'^[a-z]+\.\s1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'[a-z]+\.\s1\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'(?P<pid>[a-z]+)\.\s*1\.', current_tag_text)
                    num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol1)
                    ol_head = 2

                if re.search(r'^[a-z]+\.\s?\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[a-z]+\.\s?\(1\)', '', current_tag_text)
                    num_cur_tag = li_tag
                    num_id1 = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    num_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol1)
                    num_count = 2
                previous_li_tag = p_tag

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                cap_alpha1 = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol", type="1")
                    p_tag.wrap(num_ol1)
                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                        main_sec_alpha = 'a'
                else:
                    num_ol1.append(p_tag)
                    if re.search(r'ol\d1$', p_tag.parent.find_next("li").get("id")):
                        main_sec_alpha = 'a'

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1
                previous_li_tag = p_tag

                if re.search(r'^\(\d+\)\s*\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\d+\)\s*\(a\)', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    sec_alpha_id = f'{num_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_cur_tag1.get("id")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = 'b'

            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag
                cap_rom = "I"

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)

                    if num_cur_tag1 or num_cur_tag or roman_cur_tag:
                        cap_alpha_id1 = p_tag.find_previous("li").get("id")
                        p_tag.find_previous("li").append(cap_alpha_ol1)
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)

                if re.search(r'^\([A-Z]\)\s\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s\(i\)', '', current_tag_text)
                    cur_tag = re.search(r'\((?P<pid>[A-Z])\)\s*\((?P<nid>i)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("nid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)

                if re.search(r'^\([A-Z]+\)\s\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]+\)\s\(1\)', '', current_tag_text)
                    num_cur_tag1 = li_tag
                    num_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{num_id1}1'
                    num_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol1)
                    num_count = 2

                if re.search(r'^\([A-Z]\)\s\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s\(I\)', '', current_tag_text)
                    cur_tag = re.search(r'\((?P<pid>[A-Z])\)\s*\((?P<nid>I)\)', current_tag_text)
                    prev_id = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("nid")}'
                    cap_roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_roman_ol)
                    cap_rom = "II"

                previous_li_tag = p_tag

            elif re.search(rf'^\(\d[a-z]\)', current_tag_text) and p_tag.name == "p":
                n_tag = p_tag
                n_id = re.search(rf'^\((?P<n_id>\d+[a-z])\)', current_tag_text).group("n_id")
                p_tag["id"] = f'{num_id1}-{n_id}'
                num_cur_tag1.append(p_tag)
                previous_li_tag = p_tag

            elif re.search(rf'^\([a-z]\d\)', current_tag_text) and p_tag.name == "p":
                alpha_tag = p_tag
                n_id = re.search(rf'^\((?P<n_id>[a-z]\d+)\)', current_tag_text).group("n_id")
                p_tag["id"] = f'{sec_alpha_cur_tag.get("id")}-{n_id}'
                sec_alpha_cur_tag.append(p_tag)
                previous_li_tag = p_tag

            elif re.search(r'^\([ivx]+\)|^[ivx]+\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^\(i\)|^i\.', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    if sec_alpha_cur_tag or cap_alpha_cur_tag1 or cap_alpha_cur_tag and num_cur_tag1:
                        prev_id1 = p_tag.find_previous("li").get("id")
                        p_tag.find_previous("li").append(roman_ol)
                    else:
                        prev_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    roman_ol.append(p_tag)

                rom_head = re.search(r'(?P<rom>[ivx]+)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([ivx]+\)|^[ivx]+\.', '', current_tag_text)
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_rom}\)', current_tag_text):
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag

                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    if cap_alpha_cur_tag1:
                        cap_alpha_cur_tag1.append(cap_roman_ol)
                        prev_id = cap_alpha_cur_tag1.get("id")
                    else:
                        prev_id = p_tag.find_previous({"h5", "h4", "h3"}).get("id")
                else:
                    cap_roman_ol.append(p_tag)
                p_tag["id"] = f'{prev_id}ol{ol_count}{cap_rom}'
                p_tag.string = re.sub(rf'^\({cap_rom}\)', '', current_tag_text)
                cap_rom = roman.toRoman(roman.fromRoman(cap_rom.upper()) + 1)
                previous_li_tag = p_tag

            elif re.search(r'^Article [IVX]+ ', current_tag_text) and p_tag.name == "p" and p_tag.find_previous(
                    "li") and not re.search(r'^Article I ', current_tag_text):
                if num_cur_tag:
                    num_cur_tag.append(p_tag)

            elif p_tag.get("class") == [self.tag_type_dict['ol_p']] and p_tag.name == "p" and previous_li_tag:
                if p_tag.b:
                    pass
                elif not re.search(r'^History\.|^Cross references:', current_tag_text):
                    previous_li_tag.append(p_tag)

            if re.search(r'^CASE NOTES|^(ARTICLE|Article) [IVX]+\.|^§\s\d+\.|^History\.|^Cross references:',
                         current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                ol_head = 1
                ol_head1 = 1
                cap_alpha = 'A'
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                num_count = 1
                cap_alpha1 = "A"
                cap_rom = "I"
                cap_alpha_cur_tag = None
                num_cur_tag = None
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                n_tag = None
                roman_cur_tag = None
                previous_li_tag = None
                cap_alpha_cur_tag1 = None

        print('ol tags added')

    def create_analysis_nav_tag(self):
        if self.release_number in ['85'] and self.file_no in ['55.1']:
            tag_class = self.tag_type_dict["ol"]
        elif self.release_number in ['85', '84', '83'] and re.search('constitution', self.input_file_name):
            tag_class = self.tag_type_dict["casenav"]
        else:
            tag_class = self.tag_type_dict["ol_p"]

        for tag in self.soup.find_all(class_=tag_class):
            if re.search(r'^I\.', tag.text.strip()) and tag.find_previous(re.compile('^h[1-4]$')).name == "h4":
                tag_data = tag.text.split('\n')
                tag_data = [i for i in tag_data if i]
                for tag_text in tag_data:
                    new_li_tag = self.soup.new_tag("p", **{'class': 'casenote'})
                    new_li_tag.string = tag_text
                    tag.insert_before(new_li_tag)
                tag.decompose()

        super(VAParseHtml, self).create_case_note_analysis_nav_tag()
        print("case note analysis nav created")

    def h2_set_id(self, header_tag):
        h2_id_count = 1
        header_tag.name = "h2"
        p_tag_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()

        if self.file_no in ['28.2', '54.1', '10.1'] or self.file_no in ['15.2', '58.1'] and self.release_number in \
                ['87', '86']:
            header_tag_id = f'{header_tag.find_previous(class_={"title", "navhead"}).get("id")}-{p_tag_text}'
        else:
            header_tag_id = f'{header_tag.find_previous(class_={"oneh2", "title"}).get("id")}-{p_tag_text}'

        if header_tag_id in self.h2_rep_id:
            header_tag["id"] = f'{header_tag_id}.{h2_id_count:02}'
            h2_id_count += 1
        else:
            header_tag["id"] = f'{header_tag_id}'
            h2_id_count = 1
        header_tag["class"] = "gen"
        self.h2_rep_id.append(header_tag['id'])

    def recreating_tag(self):
        count = 1
        for tag in self.soup.find_all():
            if tag.name == "li" and (self.title_name == "compact" or
                                     self.release_number in ['83', '84', '85']):
                if re.search(r'^\d+(\.\d+)?-\d+(\.\d+)?', tag.text.strip()):
                    tag_data = tag.text.split('\n')
                    tag_data = [i for i in tag_data if i]
                    for tag_text in tag_data:
                        new_li_tag = self.soup.new_tag("li")
                        new_li_tag.string = tag_text
                        tag.insert_before(new_li_tag)
                    tag.decompose()
            if tag.name == "p" and tag.get("class") == [self.tag_type_dict["ol_p"]] and self.file_no not in ['10.1']:
                if h5_tag := re.search(r'^§ (?P<id>\d+)\.', tag.text.strip()):
                    if tag.b:
                        new_h5_tag = self.soup.new_tag("h5")
                        new_h5_tag.string = tag.b.text.strip()
                        new_h5_tag_id = f'{tag.find_previous("h4").get("id")}{h5_tag.group("id")}'
                        if new_h5_tag_id in self.dup_id_list:
                            new_h5_tag_id = f'{tag.find_previous("h4").get("id")}{h5_tag.group("id")}.{count}'
                            count += 1
                        else:
                            count = 1
                        new_h5_tag["id"] = f'{new_h5_tag_id}'
                        tag.b.decompose()
                        tag.insert_before(new_h5_tag)
                        self.dup_id_list.append(new_h5_tag_id)
                    else:
                        h5_tag = self.soup.new_tag("h5")
                        h5_tag.string = re.search(r'^(?P<text>§ \d+)\.', tag.text.strip()).group("text")
                        new_h5_tag_id = f'{tag.find_previous({"h4", "h3"}).get("id")}{re.search(r"^§ (?P<id>[0-9]+)", tag.text.strip()).group("id")}'
                        if new_h5_tag_id in self.dup_id_list:
                            new_h5_tag_id = f'{tag.find_previous("h4").get("id")}{re.search(r"^§ (?P<id>[0-9]+)", tag.text.strip()).group("id")}.{count}'
                            count += 1
                        else:
                            count = 1
                        h5_tag["id"] = f'{new_h5_tag_id}'
                        tag.string = re.sub(r'^(?P<text>§ \d+)\.', '', tag.text.strip())
                        tag.insert_before(h5_tag)
                        self.dup_id_list.append(new_h5_tag_id)

    def wrap_inside_main_tag(self):

        """wrap inside main tag"""

        if (self.title_name == "compact" and self.release_number not in ['83', '84', '85'] and self.file_no not in [
            '63.1']) or \
                (self.release_number in ['83', '84', '85'] and
                 self.file_no in ['02.2', '03.2', '10.1', '06.2', '04.1', '46.2', '28.2', '54.1', '63.2', '23.1',
                                  '64.2', '55.1', '37.2', '45.2', '15.2', '33.2']):
            main_tag = self.soup.new_tag('main')
            chap_nav = self.soup.find('nav')
            h2_tag = self.soup.find("h2")
            tag_to_wrap = h2_tag.find_previous_sibling()

            for tag in tag_to_wrap.find_next_siblings():
                tag.wrap(main_tag)

            for nav_tag in chap_nav.find_next_siblings():
                if nav_tag.name != "main":
                    nav_tag.wrap(chap_nav)
        else:
            super(VAParseHtml, self).wrap_inside_main_tag()

    def replace_tags_constitution(self):
        super(VAParseHtml, self).replace_tags_constitution()

        section_pattern = re.compile(r'^Section (?P<id>\d+)\.')
        amd_pattern = re.compile(r'^\[Amendment (?P<id>[IVX]+)]')
        dup_h5_id_list = []
        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_rom_id = None
        h5_alpha_id = None
        h5_num_id = None
        h5_s_alpha_id = None
        self.h4_count = 1

        for tag in self.soup.findAll():
            if tag.name == "p":
                if tag.get("class") == [self.tag_type_dict['head1']] or \
                        tag.get("class") == [self.tag_type_dict['amdhead']]:
                    if self.regex_pattern_obj.h2_article_pattern_con.search(tag.text.strip()):
                        tag.name = "h2"
                        tag[
                            "id"] = f'{self.soup.find("h1").get("id")}-a{self.regex_pattern_obj.h2_article_pattern_con.search(tag.text.strip()).group("id").zfill(2)}'
                        tag["class"] = 'oneh2'
                    elif re.search(r'^\[\s?Preamble\s?]$|^AMENDMENTS TO THE CONSTITUTION$', tag.text.strip()):
                        tag.name = "h2"
                        tag_text = re.sub(r'\W+', '', tag.text.strip()).lower()
                        tag["id"] = f'{self.soup.find("h1").get("id")}-{tag_text}'
                        tag["class"] = 'oneh2'

                elif tag.get("class") == [self.tag_type_dict['head3']]:
                    if section_pattern.search(tag.text.strip()):
                        tag.name = "h3"
                        tag["id"] = f'{tag.find_previous("h2").get("id")}-' \
                                    f's{section_pattern.search(tag.text.strip()).group("id").zfill(2)}'

                    elif amd_pattern.search(tag.text.strip()):
                        tag.name = "h3"
                        tag["id"] = f'{tag.find_previous("h2").get("id")}-' \
                                    f'a{amd_pattern.search(tag.text.strip()).group("id").zfill(2)}'

                    elif re.search(r'^\[\s?Preamble\s?]$|^AMENDMENTS TO THE CONSTITUTION$', tag.text.strip()):
                        tag.name = "h2"
                        tag_text = re.sub(r'\W+', '', tag.text.strip()).lower()
                        tag["id"] = f'{self.soup.find("h1").get("id")}-{tag_text}'
                        tag["class"] = 'oneh2'

                elif tag.get("class") == [self.tag_type_dict["head4"]] or \
                        tag.get("class") == [self.tag_type_dict["ol_p"]]:

                    if tag.text.strip() in self.h4_head:
                        self.replace_h4_tag_titles(tag, self.h4_count, None)
                    else:
                        if re.search(rf'^{cap_roman}\.', tag.text.strip()):
                            tag.name = "h5"
                            h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', tag.text.strip()).group("h5_id")
                            h5_rom_id = f"{tag.find_previous('h3').get('id')}-notetodecisison-{h5_rom_text}"
                            tag['id'] = h5_rom_id
                            cap_alpha = 'A'
                            cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                        elif cap_alpha and re.search(fr'^{cap_alpha}\.', tag.text.strip()):
                            tag.name = "h5"
                            h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', tag.text.strip()).group("h5_id")
                            h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                            tag['id'] = h5_alpha_id
                            cap_alpha = chr(ord(cap_alpha) + 1)
                            cap_num = 1

                        elif cap_num and re.search(fr'^{cap_num}\.', tag.text.strip()):
                            tag.name = "h5"
                            h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', tag.text.strip()).group("h5_id")
                            h5_num_id = f"{h5_alpha_id}-{h5_num_text}"
                            tag['id'] = h5_num_id
                            cap_num += 1

                        elif re.search(r'^[ivx]+\. ', tag.text.strip()) and h5_s_alpha_id:
                            tag.name = "h5"
                            h5_s_rom_text = re.search(r'^(?P<h5_id>[ivx]+)\.', tag.text.strip()).group("h5_id")
                            h5_s_rom_id = f"{h5_s_alpha_id}-{h5_s_rom_text}"
                            tag['id'] = h5_s_rom_id

                        elif re.search(r'^[a-z]+\.(?!e\.)', tag.text.strip()) and h5_num_id:
                            tag.name = "h5"
                            h5_s_alpha_text = re.search(r'^(?P<h5_id>\w+)\.', tag.text.strip()).group("h5_id")
                            h5_s_alpha_id = f"{h5_num_id}-{h5_s_alpha_text}"
                            if h5_s_alpha_id in dup_h5_id_list:
                                h5_s_alpha_id = f"{h5_num_id}-{h5_s_alpha_text}.{count}"
                                count += 1
                            else:
                                count = 1

                            tag['id'] = h5_s_alpha_id
                            dup_h5_id_list.append(h5_s_alpha_id)

            elif tag.name == "h3":
                cap_roman = "I"
                h5_num_id = None
                h5_s_alpha_id = None

            if re.search(r'^(Analysis|CASE NOTES)$', tag.text.strip()):
                for analysis_tag in tag.find_next_siblings():
                    if analysis_tag.get('class') == [self.tag_type_dict["ol_p"]] and \
                            not re.search(r'^Analysis$', analysis_tag.text.strip()):
                        analysis_tag["class"] = "casenote"

                    else:
                        break

    def add_anchor_tags_con(self):
        super(VAParseHtml, self).add_anchor_tags_con()

        section_pattern = re.compile(r'^Section (?P<id>\d+)\.')
        amd_pattern = re.compile(r'^\[Amendment (?P<id>[IVX]+)]')

        for li_tag in self.soup.findAll("li"):
            if not li_tag.get("id") and li_tag.get("class") != "casenote":
                if chap_tag := re.search(r'^(?P<id>[IVX]+)\.', li_tag.text.strip()):
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_tag.group("id"),
                                                sub_tag="ar",
                                                prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                cnav=f'snav{self.s_nav_count:02}')
                elif section_pattern.search(li_tag.text.strip()):
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li_tag,
                                                section_pattern.search(li_tag.text.strip()).group("id").zfill(2),
                                                sub_tag="-s",
                                                prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                cnav=f'snav{self.c_nav_count:02}')
                elif amd_pattern.search(li_tag.text.strip()):
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag,
                                                amd_pattern.search(li_tag.text.strip()).group("id").zfill(2),
                                                sub_tag="-a",
                                                prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                cnav=f'snav{self.s_nav_count:02}')
                elif re.search(r'^\[\s?Preamble\s?]$', li_tag.text.strip()):
                    tag_text = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag, tag_text,
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'snav{self.s_nav_count:02}')
