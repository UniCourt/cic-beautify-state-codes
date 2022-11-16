import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexNC
import roman


class NCParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.file_no = None

    def pre_process(self):
        self.regex_pattern_obj = CustomisedRegexNC()
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'head1': r'^Constitution of North Carolina|CONSTITUTION OF THE UNITED STATES',
                                        'ul': r'^(Article|Preamble)', 'head2': '^(ARTICLE|Article) I',
                                        'head4': '^CASE NOTES', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$',
                                        'head': r'^Section added\.',
                                        'head3': r'^§ \d|^sec\.|^Section \d', 'nav': r'^Subchapter I\.|^——————————'}
            self.h2_order: list = ['article', '', '', '', '']
            self.h2_text_con = ['100A Amendments']
            self.h3_pattern_text_con = ['^Amendment (?P<id>[IVX]+)\.']
        else:
            self.tag_type_dict: dict = {'head1': r'Chapter \d+',
                                        'ul': r'^Article|^1\.|^(?P<sec_id>\d+([A-Z])*-\d+(\.\d+)*)|^§|^Article 1.',
                                        'head2': r'^ARTICLE \d+\.|^Article 1.|^ARTICLE I\.',
                                        'head4': '^CASE NOTES|^OFFICIAL COMMENT',
                                        'head3': r'^§* \d+([A-Z])*-\d+(-\d+)*(\.|,| through)|^§',
                                        'ol_p': r'^\(\d\)|^I\.',
                                        'junk1': '^Annotations$|^Text$', 'nav': r'^Subchapter I\.|^——————————'}

            self.h2_pattern_text = [r'^(?P<tag>Article)\s*(?P<id>(\d+([A-Z])*)|(\d+(\.\d+)*))']
            self.file_no = re.search(r'gov\.nc\.stat\.title\.(?P<fno>\w+)\.html', self.input_file_name).group("fno")

            if self.file_no == "104D":
                self.tag_type_dict["ul"] = "Subchapter"
            if self.file_no in ['035A', '001', '007A', '007B', '014', '015A', '054', '076A', '105', '113',
                                '146', '156', '159', '163', '115C']:
                self.h2_order: list = ['subchapter', 'article', 'part', '', '']
            elif self.file_no in ['010B', '030', '037A', '050A', '055', '055A', '059', '057D',
                                  '099E', '108A', '106', '131E', '143B', '045']:
                self.h2_order: list = ['article', 'part', '', '', '']
            else:
                self.h2_order: list = ['article', '', '', '', '']

            self.h3_pattern_text = ['^§*\s*(?P<id>\d+([A-Z])*-\d+([A-Z]|\.\d+)*)']
            self.h2_text = ['Standby Guardians.']

        self.h4_head: list = ['Revision of title. —', 'Cross references. —', 'Law reviews. —', 'Editor\'s notes. —',
                              'History.', 'Effective dates. —', 'CASE NOTES', 'OFFICIAL COMMENT', 'Official Comment',
                              'Official Commentary', 'Editor\'s notes.', 'North Carolina Comment', 'Editor’s Note.']

        self.watermark_text = """Release {0} of the Official Code of North Carolina Annotated released {1}. 
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
                This document is not subject to copyright and is in the public domain.
                """

    def replace_tags_titles(self):
        super(NCParseHtml, self).replace_tags_titles()
        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_rom_id = None
        h5_alpha_id = None

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^CASE NOTES$|^Analysis$|^Official Comment', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_alpha = None
                    cap_num = None
                    h5_rom_id = None
                    h5_alpha_id = None

                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-notetodecisison-{h5_rom_text}"
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
                elif re.search(r'^—\w+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    h5_id = f"{header_tag.find_previous('h4').get('id')}-{h5_text}"
                    header_tag['id'] = h5_id

            if header_tag.get("class") == [self.tag_type_dict["nav"]]:
                if nav_tag := re.search(r'^Part (?P<id>\d+[A-Z]*)\.', header_tag.text.strip()):
                    header_tag["class"] = "navhead"
                    header_tag["id"] = f"{header_tag.find_previous('h2').get('id')}p{nav_tag.group('id').zfill(2)}"
                elif nav_tag := re.search(r'^Subchapter (?P<id>[IVX]+)\.', header_tag.text.strip()):
                    header_tag["class"] = "navhead"
                    header_tag[
                        "id"] = f"{header_tag.find_previous({'h2', 'h1'}).get('id')}s{nav_tag.group('id').zfill(2)}"
                elif article_tag := re.search(r'^ARTICLE (?P<id>[IVX]+)\.', header_tag.text.strip()):
                    header_tag.name = "h4"
                    header_tag[
                        "id"] = f"{header_tag.find_previous('h3').get('id')}-a{article_tag.group('id').zfill(2)}"

            if re.search(r'^Analysis', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]]:
                        break
                    else:
                        tag["class"] = "casenote"
                        tag.name = "li"

            if self.file_no == "104D" and \
                    header_tag.get("class") == [self.tag_type_dict["head2"]]:
                if re.search(r'^ARTICLE [IVX]+\.', header_tag.text.strip()):
                    new_tag_text = re.sub(r'^ARTICLE [IVX]+\.\s[a-zA-Z ]+\.', '', header_tag.text.strip())
                    new_tag = self.soup.new_tag("p")
                    new_tag.string = new_tag_text
                    header_tag_string = re.search(r'(?P<txt>^ARTICLE (?P<id>[IVX]+)\.\s[a-zA-Z, ]+\.)',
                                                  header_tag.text.strip())
                    header_tag.string = header_tag_string.group("txt")
                    header_tag.insert_after(new_tag)
                    header_tag.name = "h4"
                    header_tag["id"] = f"{header_tag.find_previous('h3').get('id')}a{header_tag_string.group('id')}"

    def add_anchor_tags(self):
        super(NCParseHtml, self).add_anchor_tags()
        if self.file_no in ['080', '045', '115C']:
            for li_tag in self.soup.findAll():
                if not li_tag.a and li_tag.name == "li":
                    if re.search(r'^\d+', li_tag.text.strip()):
                        chap_num = re.search(r'^(?P<id>\d+[A-Z]*)', li_tag.text.strip()).group("id")
                        sub_tag = 'a'
                        if li_tag.find_previous(class_="navhead"):
                            prev_id = li_tag.find_previous(class_="navhead").get("id")
                        else:
                            prev_id = li_tag.find_previous("h1").get("id")
                        self.c_nav_count += 1
                        cnav = f'anav{self.c_nav_count:02}'
                        self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)

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
        global prev_num_id, prevnum_id, alpha_cur_tag1, cap_alpha_cur_tag, num_cur_tag, prev_id, prevnum_id1
        main_sec_alpha = 'a'
        cap_alpha = 'A'
        ol_head = 1
        num_count = 1
        ol_count = 1
        ol_head1 = 1
        sec_alpha = 'a'
        ol_list = []

        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        num_ol1 = self.soup.new_tag("ol")
        inner_alpha_ol = self.soup.new_tag("ol", type="a")
        cap_roman_ol = self.soup.new_tag("ol", type="I")
        roman_ol = self.soup.new_tag("ol", type="i")

        alpha_cur_tag = None

        previous_li_tag = None
        num_tag = None
        cap_roman_cur_tag = None

        prev_head_id = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            if p_tag.i:
                p_tag.i.unwrap()
            if p_tag.span:
                p_tag.span.unwrap()
            current_tag_text = p_tag.text.strip()

            if p_tag.name == "h3":
                num_cur_tag = None
            elif p_tag.name == "p":
                if re.search(rf'^\({ol_head}\)', current_tag_text):
                    p_tag.name = "li"
                    num_cur_tag = p_tag
                    cap_alpha = 'A'
                    sec_alpha = 'a'
                    if re.search(r'^\(1\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)
                        if alpha_cur_tag:
                            alpha_cur_tag.append(num_ol)
                            prev_num_id = f'{alpha_cur_tag.get("id")}{ol_head}'
                            p_tag["id"] = f'{alpha_cur_tag.get("id")}{ol_head}'
                        elif num_tag:
                            num_tag.append(num_ol)
                            prev_num_id = f'{num_tag.get("id")}{ol_head}'
                            p_tag["id"] = f'{num_tag.get("id")}{ol_head}'
                        else:
                            prev_head_id = p_tag.find_previous({"h4", "h3"}).get("id")
                            prev_num_id = f'{prev_head_id}ol{ol_count}'
                            p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
                        if prev_head_id in ol_list:
                            ol_count += 1
                        else:
                            ol_count = 1
                        ol_list.append(prev_head_id)
                    else:
                        num_ol.append(p_tag)
                        p_tag["id"] = f'{prev_num_id}{ol_head}'
                        p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)

                    p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
                    ol_head += 1
                    ol_head1 += 1

                    if re.search(r'^\(\d+\)(\s)*a\.', current_tag_text):
                        inner_alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+(\w)?\)(\s)*a\.', '', current_tag_text)
                        alpha_cur_tag1 = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+(\w)?)\)(\s)*(?P<pid>a)', current_tag_text)
                        prevnum_id1 = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}a'
                        inner_alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(inner_alpha_ol)
                        sec_alpha = "b"

                    if re.search(r'^\(\d+\)(\s)*\([a-z]\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)(\s)*\(\w\)', '', current_tag_text)
                        alpha_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)*\((?P<pid>\w)\)', current_tag_text)
                        prevnum_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(alpha_ol)
                        main_sec_alpha = "b"
                        num_count = 1

                        if re.search(r'^\(\d+\)(\s)?\([a-z]\)\s\d+\.', current_tag_text):
                            num_ol1 = self.soup.new_tag("ol")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\d+\)(\s)?\([a-z]\)\s\d+\.', '', current_tag_text)
                            inner_li_tag.append(current_tag_text)
                            cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)\s(?P<nid>\d+)\.',
                                                current_tag_text)
                            prev_id = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}'
                            inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                            num_ol1.append(inner_li_tag)
                            alpha_cur_tag.string = ""
                            alpha_cur_tag.append(num_ol1)
                            num_count = 2
                    previous_li_tag = p_tag

                elif re.search(rf'^\(\s?{main_sec_alpha}\s?\)', current_tag_text):
                    p_tag.name = "li"
                    alpha_cur_tag = p_tag
                    ol_head = 1

                    if re.search(r'^\(a\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(alpha_ol)
                        if num_tag:
                            num_tag.append(p_tag)
                            prevnum_id = num_tag.get("id")
                        else:
                            prevnum_id = f'{p_tag.find_previous({"h4", "h3"}).get("id")}ol{ol_count}'
                            p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                    else:
                        alpha_ol.append(p_tag)
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                    p_tag.string = re.sub(rf'^\(\s*{main_sec_alpha}\s*\)', '', current_tag_text)
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                    if re.search(r'^\(\w\)\s?1\.', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\w\)\s?1\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        alpha_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w)\)\s*(?P<pid>1)\.', current_tag_text)
                        prev_id = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}'
                        inner_li_tag[
                            "id"] = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        num_ol1.append(inner_li_tag)
                        p_tag.string = ""
                        p_tag.insert(0, num_ol1)
                        num_count = 2
                        sec_alpha = 'a'

                    if re.search(r'^\(\w\)\s?\(1\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\w\)\s?\(1\)', '', current_tag_text)
                        alpha_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>1)\)', current_tag_text)
                        prev_num_id = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}'
                        inner_li_tag[
                            "id"] = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        num_ol.append(inner_li_tag)
                        p_tag.string = ""
                        p_tag.insert(0, num_ol)
                        ol_head = 2

                    previous_li_tag = p_tag

                elif re.search(rf'^{num_count}\.', current_tag_text):
                    p_tag.name = "li"
                    num_tag = p_tag

                    if re.search(r'^1\.', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol1)
                        if alpha_cur_tag1:
                            prev_id = alpha_cur_tag1.get("id")
                            alpha_cur_tag1.append(num_ol1)
                        elif cap_alpha_cur_tag:
                            prev_id = cap_alpha_cur_tag.get("id")
                            cap_alpha_cur_tag.append(num_ol1)
                        elif num_cur_tag:
                            prev_id = num_cur_tag.get("id")
                            num_cur_tag.append(num_ol1)
                        else:
                            prev_id = f'{p_tag.find_previous({"h4", "h3"}).get("id")}ol{ol_count}'
                    else:
                        num_ol1.append(p_tag)
                    p_tag["id"] = f'{prev_id}{num_count}'
                    p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                    num_count += 1

                    if re.search(r'^\d+\.\s?a\.', current_tag_text):
                        inner_alpha_ol = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\d+\.\s?a\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        alpha_cur_tag1 = inner_li_tag
                        cur_tag = re.search(r'^(?P<cid>\d+)\.\s?(?P<pid>a)\.', current_tag_text)
                        prevnum_id1 = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                        inner_li_tag[
                            "id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        inner_alpha_ol.append(inner_li_tag)
                        p_tag.string = ""
                        p_tag.insert(0, inner_alpha_ol)
                        sec_alpha = 'b'
                    previous_li_tag = p_tag

                elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                    p_tag.name = "li"
                    alpha_cur_tag1 = p_tag
                    if not num_tag:
                        num_count = 1
                    if re.search(r'^a\.', current_tag_text):
                        inner_alpha_ol = self.soup.new_tag("ol", type="a")
                        previd = p_tag.find_previous("li")
                        p_tag.wrap(inner_alpha_ol)
                        prevnum_id1 = previd.get("id")
                        previd.append(inner_alpha_ol)
                        p_tag["id"] = f'{prevnum_id1}{sec_alpha}'
                    else:
                        inner_alpha_ol.append(p_tag)
                        p_tag["id"] = f'{prevnum_id1}{sec_alpha}'

                    p_tag.string = re.sub(rf'^{sec_alpha}\.', '', current_tag_text)
                    sec_alpha = chr(ord(sec_alpha) + 1)

                    if re.search(r'^\w+\.\s?i\.', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\w+\.\s?i\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cur_tag = re.search(r'^(?P<cid>\w+)\.\s?(?P<pid>i)\.', current_tag_text)
                        prev_id1 = f'{alpha_cur_tag1.get("id")}'
                        inner_li_tag[
                            "id"] = f'{alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'
                        roman_ol.append(inner_li_tag)
                        p_tag.string = ""
                        p_tag.insert(0, roman_ol)
                    previous_li_tag = p_tag

                elif re.search(rf'^{cap_alpha}\.', current_tag_text):
                    p_tag.name = "li"
                    cap_alpha_cur_tag = p_tag

                    if re.search(r'^A\.', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        p_tag.wrap(cap_alpha_ol)
                        if cap_roman_cur_tag:
                            cap_roman_cur_tag.append(cap_alpha_ol)
                            prev_id1 = cap_roman_cur_tag.get("id")
                        else:
                            prev_id1 = p_tag.find_previous({"h4", "h3"}).get("id")

                    else:
                        cap_alpha_ol.append(p_tag)

                    p_tag["id"] = f'{prev_id1}ol{ol_count}{cap_alpha}'
                    p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)

                    if cap_alpha == 'Z':
                        cap_alpha = 'A'
                    else:
                        cap_alpha = chr(ord(cap_alpha) + 1)
                    if re.search(r'^ARTICLE (?P<id>[IVX]+)\.', p_tag.find_previous("h4").text.strip()):
                        num_count = 1
                    previous_li_tag = p_tag

                elif re.search(r'^[IVX]+\.', current_tag_text):
                    p_tag.name = "li"
                    cap_roman_cur_tag = p_tag

                    if re.search(r'^I\.', current_tag_text):
                        cap_roman_ol = self.soup.new_tag("ol", type="I")
                        p_tag.wrap(cap_roman_ol)
                        if num_tag:
                            num_tag.append(cap_roman_ol)
                            prev_id1 = num_tag.get("id")
                        else:
                            prev_id1 = p_tag.find_previous({"h4", "h3"}).get("id")
                    else:
                        cap_roman_ol.append(p_tag)

                    rom_head = re.search(r'^(?P<rom>[IVX]+)\.', current_tag_text)

                    p_tag["id"] = f'{prev_id1}ol{ol_count}{rom_head.group("rom")}'
                    p_tag.string = re.sub(r'^[IVX]+\.', '', current_tag_text)
                    previous_li_tag = p_tag

                elif re.search(r'^[ivx]+\.', current_tag_text) and alpha_cur_tag1:
                    p_tag.name = "li"
                    roman_cur_tag = p_tag

                    if re.search(r'^i\.', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        p_tag.wrap(roman_ol)
                        alpha_cur_tag1.append(roman_ol)
                        prev_id1 = alpha_cur_tag1.get("id")
                    else:
                        roman_ol.append(p_tag)

                    rom_head = re.search(r'^(?P<rom>[ivx]+)\.', current_tag_text)
                    p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                    p_tag.string = re.sub(r'^[ivx]+\.', '', current_tag_text)
                    previous_li_tag = p_tag

                elif re.search(r'^\(\d\w\)', current_tag_text) and num_cur_tag:
                    num_cur_tag.append(p_tag)

                    if re.search(r'^\(\d\w\)\s?a\.', current_tag_text) and num_cur_tag:
                        inner_alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+(\w)?\)(\s)*a\.', '', current_tag_text)
                        alpha_cur_tag1 = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+(\w)?)\)(\s)*(?P<pid>a)', current_tag_text)
                        prevnum_id1 = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}a'
                        inner_alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(inner_alpha_ol)
                        num_cur_tag.append(p_tag)
                        sec_alpha = "b"
                    previous_li_tag = p_tag

                elif p_tag.get("class") == [self.tag_type_dict["ol_p"]] \
                        and not re.search(r'^HISTORY:|^History', current_tag_text) and previous_li_tag:
                    if previous_li_tag:
                        if re.search(r'^a\.', current_tag_text):
                            p_tag.name = "li"
                            alpha_cur_tag1 = p_tag
                            num_count = 1
                            inner_alpha_ol = self.soup.new_tag("ol", type="a")
                            p_tag.wrap(inner_alpha_ol)
                            if re.search(r'^\(\d\w\)', p_tag.find_previous("p").text.strip()):
                                p_tag.find_previous("p").append(inner_alpha_ol)
                                prev_p_id = re.search(r'^\((?P<id>\d\w)\)',
                                                      p_tag.find_previous("p").text.strip()).group('id')
                                prevnum_id1 = f'{num_cur_tag.get("id")}{prev_p_id}'
                                p_tag["id"] = f'{num_cur_tag.get("id")}{prev_p_id}a'
                            else:
                                previous_li_tag.append(inner_alpha_ol)
                                prevnum_id1 = p_tag.find_previous("li").get("id")
                                p_tag["id"] = f'{prevnum_id1}a'
                            p_tag.string = re.sub(r'^a\.', '', current_tag_text)
                            sec_alpha = 'b'
                        else:
                            previous_li_tag.append(p_tag)

            if re.search(r'^History|^Cross references:|^OFFICIAL COMMENT', current_tag_text) or \
                    p_tag.name in ['h3', 'h4', 'h5']:
                ol_head = 1
                ol_head1 = 1
                num_count = 1
                main_sec_alpha = 'a'
                sec_alpha = 'a'
                cap_alpha = "A"
                num_cur_tag = None
                alpha_cur_tag = None
                cap_alpha_cur_tag = None
                alpha_cur_tag1 = None
                previous_li_tag = None
                num_tag = None
                cap_roman_cur_tag = None

        print("ol tag created")

    def create_analysis_nav_tag(self):
        super(NCParseHtml, self).create_case_note_analysis_nav_tag()
        print("Case Notes nav created")

    def replace_tags_constitution(self):

        super(NCParseHtml, self).replace_tags_constitution()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_rom_id = None
        h5_alpha_id = None

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^CASE NOTES$|^Analysis$|^Official Comment', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_alpha = None
                    cap_num = None
                    h5_rom_id = None
                    h5_alpha_id = None

                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f"{header_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-notetodecisison-{h5_rom_text}"
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
                elif re.search(r'^—\w+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    h5_id = f"{header_tag.find_previous('h4').get('id')}-{h5_text}"
                    header_tag['id'] = h5_id

            if re.search(r'^Analysis', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]]:
                        break
                    else:
                        tag["class"] = "casenote"
                        tag.name = "li"

            if self.file_no == "104D" and \
                    header_tag.get("class") == [self.tag_type_dict["head2"]]:
                if re.search(r'^ARTICLE [IVX]+\.', header_tag.text.strip()):
                    new_tag_text = re.sub(r'^ARTICLE [IVX]+\.\s[a-zA-Z ]+\.', '', header_tag.text.strip())
                    new_tag = self.soup.new_tag("p")
                    new_tag.string = new_tag_text
                    header_tag_string = re.search(r'(?P<txt>^ARTICLE (?P<id>[IVX]+)\.\s[a-zA-Z, ]+\.)',
                                                  header_tag.text.strip())
                    header_tag.string = header_tag_string.group("txt")
                    header_tag.insert_after(new_tag)
                    header_tag.name = "h4"
                    header_tag["id"] = f"{header_tag.find_previous('h3').get('id')}a{header_tag_string.group('id')}"
