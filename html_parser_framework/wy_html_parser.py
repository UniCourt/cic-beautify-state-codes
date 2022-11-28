import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexWY
from loguru import logger


class WYParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.file_no = None

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {
                'head1': r'^Constitution of the State of Wyoming|THE CONSTITUTION OF THE UNITED STATES OF AMERICA',
                'ul': r'^(PREAMBLE|Preamble)', 'head2': r'Article \d\.',
                'head4': r'^History\.', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$', 'head': r'^Section added\.',
                'head3': r'^§ \d|^sec\.|^Section \d', }

            self.h2_order: list = ['article']

        else:
            self.tag_type_dict: dict = {'head1': r'Title \d+', 'ul': r'^Chapter \d',
                                        'head2': r'^Chapter \d |^Article \d+ ',
                                        'head4': r'History\.', 'head3': r'^§ \d+-\d+-\d+', 'ol_p': r'^\(\d\)',
                                        'head': r'^Law reviews\. —',
                                        'junk1': '^Annotations$', }

            self.file_no = re.search(r'gov\.wy\.code\.title\.(?P<fno>\w+(\.\d)*)\.html', self.input_file_name).group(
                "fno")

            if re.search(r'40\.html', self.input_file_name.strip()):
                self.h2_order: list = ['chapter', 'article', 'part']
            elif re.search(r'34\.1\.html', self.input_file_name.strip()):
                self.h2_order: list = ['article', 'part', 'subpart']
                self.tag_type_dict: dict = {'head1': r'Title \d+', 'ul': r'^Article \d',
                                            'head2': r'^Article \d+ ',
                                            'head4': r'History\.', 'head3': r'^§ \d+(\.\d)*-\d+-\d+',
                                            'ol_p': r'^\(\d\)',
                                            'head': r'^Law reviews\. —',
                                            'junk1': '^Annotations$', }
            else:
                self.h2_order: list = ['chapter', 'article', 'division']

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.watermark_text = """Release {0} of the Official Code of Kentucky Annotated released {1}
                        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 2.3 on {2}.
                        This document is not subject to copyright and is in the public domain.
                        """
        self.h2_text = []
        self.regex_pattern_obj = CustomisedRegexWY()

    def replace_tags_titles(self):

        for revised_article_tag in self.soup.findAll("p", class_=self.tag_type_dict["head2"],
                                                     text=re.compile(r'^Revised Article (?P<id>\d)')):
            revised_article_tag["class"] = "oneh2"
            revised_article_tag.name = "h2"
            revised_article_tag[
                'id'] = f"t{self.file_no}-{re.sub(r'[ ]', '', revised_article_tag.text.strip()).lower()}"

        for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
            if not re.search(r'^(chapter|subchapter|article|part|subpart|subtitle|division|'
                             r'^§*\s*\d+(\.\d+)*-\d+(\.[A-Z]+)*-\d+(\.\d+)*)', li_tag.text.strip(), re.I):
                li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                self.h2_text.append(li_tag_text)

        self.recreate_tag()

        super(WYParseHtml, self).replace_tags_titles()

        h4_article_pattern = re.compile(r'^Article (?P<id>[IVX]+)', re.I)
        h5_section_pattern = re.compile(r'^Section (?P<id>[A-Z])\.', re.I)
        h4_section_pattern = re.compile(r'^Section (?P<id>\d+) ', re.I)
        part_pattern = re.compile(r'^(Part|Division) (?P<id>\d+)\.')
        Revised_Article_pattern = re.compile(r'^Revised Article (?P<id>\d)')
        h4_article_count = 1
        h4_id_list = []
        annotation_id_list: list = []
        alpha = "A"
        h5_rom_id = None
        h5_count = 1

        for p_tag in self.soup.find_all():
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["head2"]]:
                    if Revised_Article_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h2"
                        p_tag_text = re.sub(r'\W+', '', p_tag.text.strip()).lower()
                        p_tag['id'] = f'{p_tag.find_previous("h1").get("id")}-{p_tag_text}'
                        p_tag['class'] = "oneh2"
                    elif part_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h2"
                        p_tag[
                            'id'] = f'{p_tag.find_previous("h2", class_="oneh2").get("id")}p{part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                        p_tag['class'] = "twoh2"

                elif p_tag.get("class") == [self.tag_type_dict["head"]]:
                    if re.search(r'^([A-Z]\.|[IVX]+\.)', p_tag.text.strip()):
                        if re.search(r'^[IVX]+\.', p_tag.text.strip()):
                            p_tag.name = "h5"
                            h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', p_tag.text.strip()).group("h5_id")
                            h5_rom_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecisison-{h5_rom_text}'
                            if h5_rom_id in annotation_id_list:
                                p_tag["id"] = f'{h5_rom_id}.{h5_count}'
                                h5_count += 1
                            else:
                                p_tag["id"] = f'{h5_rom_id}'
                                h5_count = 1
                            annotation_id_list.append(h5_rom_id)
                            alpha = 'A'
                        elif alpha:
                            if re.search(fr'^{alpha}\.', p_tag.text.strip()):
                                p_tag.name = "h5"
                                h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', p_tag.text.strip()).group("h5_id")
                                h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                                p_tag['id'] = h5_alpha_id
                                alpha = chr(ord(alpha) + 1)

                elif p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    if h4_article_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h4"
                        h4_article_id = f'{p_tag.find_previous("h3").get("id")}-a{h4_article_pattern.search(p_tag.text.strip()).group("id")}'
                        if h4_article_id in h4_article_id:
                            p_tag[
                                'id'] = f'{p_tag.find_previous("h3").get("id")}-a{h4_article_pattern.search(p_tag.text.strip()).group("id")}.{h4_article_count}'
                            h4_article_count += 1
                        else:
                            p_tag[
                                'id'] = f'{p_tag.find_previous("h3").get("id")}-a{h4_article_pattern.search(p_tag.text.strip()).group("id")}'
                            h4_article_count = 1

                        h4_id_list.append(h4_article_id)

                    elif h5_section_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h5"
                        p_tag[
                            'id'] = f'{p_tag.find_previous("h4").get("id")}-s{h5_section_pattern.search(p_tag.text.strip()).group("id")}'

                    elif h4_section_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h4"
                        p_tag[
                            'id'] = f'{p_tag.find_previous("h3").get("id")}-s{h4_section_pattern.search(p_tag.text.strip()).group("id")}'

                    elif re.search(r'^([A-Z]\.|[IVX]+\.) ', p_tag.text.strip()) and self.file_no not in ['33', '41']:
                        p_tag["class"] = 'casenote'

            elif p_tag.name == "h3":
                if tag := re.search(r'^§* (?P<id>\d+-\d+-\d+)( through \d+-\d+-\d+)*\.\s*\[(Repealed and '
                                    r')*Renumbered\.]$', p_tag.text.strip()):
                    p_tag["id"] = f'{p_tag.find_previous("h2").get("id")}s{tag.group("id")}'

    def add_anchor_tags(self):
        super(WYParseHtml, self).add_anchor_tags()

        part_pattern = re.compile(r'^(Part|Division) (?P<id>\d+)\.')
        Revised_Article_pattern = re.compile(r'^Revised Article (?P<id>\d)')

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if re.search(r'^APPENDIXRULES', li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    sub_tag = 'apr'
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)
                elif Revised_Article_pattern.search(li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, "-",
                                                li_tag.find_previous("h1").get("id"), cnav)
                elif part_pattern.search(li_tag.text.strip()):
                    chap_num = part_pattern.search(li_tag.text.strip()).group("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, "p",
                                                li_tag.find_previous("h2", class_="oneh2").get("id"), cnav)

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
        small_roman = "i"
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        roman_ol = self.soup.new_tag("ol", type="i")
        cap_roman_ol = self.soup.new_tag("ol", type="I")
        num_ol1 = self.soup.new_tag("ol")
        head_ol = self.soup.new_tag("ol")
        cap_alpha1_ol = self.soup.new_tag("ol", type="A")
        sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
        ol_count = 1
        rom_count = 1
        p_id_count = 1
        cap_alpha_cur_tag = None
        main_sec_alpha1 = 'a'
        sec_alpha_cur_tag = None
        cap_alpha1 = 'A'
        cap_alpha2 = 'a'
        cap_alpha1_cur_tag = None
        ol_head_tag = None
        sec_alpha_id = None
        prev_id1 = None
        roman_cur_tag = None
        cap_alpha_id = None
        prev_rom_id = None
        cap_roman_tag = None
        num_id1 = None
        ol_head_id = None
        cap_alpha1_id = None
        sec_alpha_id1 = None
        roman_tag = None
        previous_li_tag = None
        inner_alpha_tag = None
        dup_ol_id = []

        for p_tag in self.soup.body.find_all(['h2', 'h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                roman_tag = None

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                if main_sec_alpha in ["h", "k", "u", "w"]:
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
                previous_li_tag = p_tag

            elif re.search(r'^\([ivxl]+\)', current_tag_text) and p_tag.name == "p":
                if re.search(r'^\(i\)', current_tag_text):
                    p_tag.name = "li"
                    roman_cur_tag = p_tag
                    ol_head = 1
                    cap_alpha = 'A'
                    roman_ol = self.soup.new_tag("ol", type="i")
                    roman_tag = p_tag
                    p_tag.wrap(roman_ol)
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(roman_ol)
                        prev_id1 = sec_alpha_cur_tag.get("id")
                    else:
                        ol_count += 1
                        prev_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    if roman_tag:
                        p_tag.name = "li"
                        roman_cur_tag = p_tag
                        ol_head = 1
                        cap_alpha = 'A'
                        roman_ol.append(p_tag)

                if roman_tag:
                    rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                    p_tag_id = f'{prev_id1}{rom_head.group("rom")}'
                    if p_tag_id in dup_ol_id:
                        p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}.{p_id_count}'
                        p_id_count += 1
                    else:
                        p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                        p_id_count = 1

                    p_tag.string = re.sub(r'^\([ivxl]+\)', '', current_tag_text)
                    dup_ol_id.append(p_tag_id)

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
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p" and roman_cur_tag:
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

                if cap_alpha in ["H", "K", "U", "W"]:
                    cap_alpha = chr(ord(cap_alpha) + 2)
                elif cap_alpha == 'Z':
                    cap_alpha = 'A'
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
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha2}{cap_alpha2}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_ol.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<p_id>{cap_alpha2}{cap_alpha2})\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{sec_alpha_id}{p_tag_id}'
                p_tag.string = re.sub(rf'^\({cap_alpha2}{cap_alpha2}\)', '', current_tag_text)
                cap_alpha2 = chr(ord(cap_alpha2) + 1)
                previous_li_tag = p_tag

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
                p_tag_rom_id = f'{prev_rom_id}{rom_head.group("rom")}'
                if p_tag_rom_id in dup_ol_id:
                    p_tag["id"] = f'{prev_rom_id}{rom_head.group("rom")}.{rom_count}'
                    rom_count += 1
                else:
                    p_tag["id"] = f'{prev_rom_id}{rom_head.group("rom")}'
                    rom_count = 1

                p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)
                dup_ol_id.append(p_tag_rom_id)
                previous_li_tag = p_tag

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    if cap_roman_tag or cap_alpha1_cur_tag or inner_alpha_tag:
                        num_id1 = p_tag.find_previous("li").get('id')
                        p_tag.find_previous("li").append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1
                previous_li_tag = p_tag

            elif re.search(rf'^\([a-z]\)', current_tag_text) and p_tag.name == "p" and sec_alpha_cur_tag:
                if sec_alpha_cur_tag:
                    p_tag.name = "li"
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    sec_alpha_cur_tag.append(p_tag)
                    sec_id = re.search(rf'^\((?P<s_id>[a-z])\)', current_tag_text).group("s_id")
                    if self.soup.find("li", id=f'{sec_alpha_id}{sec_id}'):
                        p_tag["id"] = f'{sec_alpha_id}{sec_id}.1'
                    else:
                        p_tag["id"] = f'{sec_alpha_id}{sec_id}'
                    sec_alpha_cur_tag = p_tag
                    p_tag.string = re.sub(rf'^\([a-z]\)', '', current_tag_text)
                previous_li_tag = p_tag

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
                previous_li_tag = p_tag

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
                previous_li_tag = p_tag

            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p" and \
                    ol_head_tag:
                p_tag.name = "li"
                inner_alpha_tag = p_tag

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)
                    if ol_head_tag:
                        ol_head_tag.append(sec_alpha_ol1)
                        sec_alpha_id1 = f"{ol_head_tag.get('id')}"

                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)
                previous_li_tag = p_tag

                if re.search(r'ol\d[A-Z]?\d+[a-z]$', p_tag.parent.find_next("li").get("id")):
                    num_count = 1

            elif p_tag.name == "p" and previous_li_tag:
                if not re.search(r'^History\.?|^Cross references:', current_tag_text):
                    previous_li_tag.append(p_tag)
                else:
                    previous_li_tag = None

            if re.search(r'^CASE NOTES|^Article [IVX]+', current_tag_text) or p_tag.name in ['h2', 'h3', 'h4', 'h5']:
                ol_head = 1
                ol_count = 1
                cap_alpha = 'A'
                cap_alpha_cur_tag = None
                num_count = 1
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha2 = 'a'
                small_roman = "i"
                cap_roman_tag = None
                cap_alpha1_cur_tag = None
                ol_head_tag = None
                previous_li_tag = None
                roman_tag = None
                roman_cur_tag = None
                sec_alpha_cur_tag = None
                inner_alpha_tag = None

        logger.info("ol tags added")

    def create_analysis_nav_tag(self):
        super(WYParseHtml, self).create_case_note_analysis_nav_tag()
        logger.info("case note decision nav created")

    def replace_tags_constitution(self):
        super(WYParseHtml, self).replace_tags_constitution()
        for header_tag in self.soup.find_all():
            if header_tag.get("class") == "section":
                if self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()):
                    if header_tag.find_previous("h3") and \
                            re.search(r'^Amendment \d+', header_tag.find_previous("h3").text.strip()):
                        header_tag.name = "h4"
                        chap_no = self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()).group('id')
                        header_tag[
                            "id"] = f'{header_tag.find_previous("h3", class_="gen").get("id")}-s{chap_no.zfill(2)}'
                        header_tag["class"] = "section"
                        self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def add_anchor_tags_con(self):
        super(WYParseHtml, self).add_anchor_tags_con()
        for li_tag in self.soup.findAll("li"):
            if not li_tag.get("id"):
                if re.search(r'^Amendment \d+', li_tag.text.strip(), re.I):
                    chap_num = re.search(r'^Amendment (?P<id>\d+)', li_tag.text.strip(), re.I).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

    def recreate_tag(self):
        for tag in self.soup.findAll("p", class_=self.tag_type_dict["head"]):
            if re.search(r'^([A-Z]\.|[IVX]+\.) ', tag.text.strip()):
                if re.search(r'^([A-Z]\.|[IVX]+\.).+[IVX]+\.', tag.text.strip()):
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = tag.b.text
                    new_p_tag["class"] = [self.tag_type_dict['head']]
                    tag.insert_after(new_p_tag)
                    tag.b.clear()
                    tag["class"] = [self.tag_type_dict['head4']]

    def h2_set_id(self, header_tag):
        h2_id_count = 1
        header_tag.name = "h2"
        p_tag_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
        if self.file_no == '17':
            header_tag_id = f'{header_tag.find_previous(class_={"twoh2"}).get("id")}-{p_tag_text}'
        else:
            header_tag_id = f'{header_tag.find_previous(class_={"oneh2", "title"}).get("id")}-{p_tag_text}'

        if header_tag_id in self.h2_rep_id:
            header_tag["id"] = f'{header_tag_id}.{h2_id_count:02}'
            h2_id_count += 1
        else:
            header_tag["id"] = f'{header_tag_id}'
        self.h2_rep_id.append(header_tag['id'])
