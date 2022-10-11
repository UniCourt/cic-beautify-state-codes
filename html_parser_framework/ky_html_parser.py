import re
import roman
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexKY
from loguru import logger


class KYParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.am_nav_count = None
        self.nd_list = []

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'ul': '^(§ )|^(ARTICLE)', 'head2': '^(§|ARTICLE|PREAMBLE)',
                                        'head1': '^(CONSTITUTION OF KENTUCKY)|^(THE CONSTITUTION OF THE UNITED STATES OF AMERICA)',
                                        'head3': r'^(Section|§)',
                                        'junk1': '^(Text)', 'ol_p': r'^(\(1\))',
                                        'head4': '^(NOTES TO DECISIONS)|^(Compiler’s Notes.)'}
            self.h2_order: list = ['article']
            self.h2_text_con: list = []
            self.file_no = None
        else:
            self.tag_type_dict: dict = {'ul': '^CHAPTER', 'head2': '^CHAPTER',
                                        'head1': '^(TITLE)|^(CONSTITUTION OF KENTUCKY)',
                                        'head3': r'^([^\s]+[^\D]+)',
                                        'junk1': '^(Text)', 'ol_p': r'^(\(1\))', 'head4': '^(NOTES TO DECISIONS)',
                                        'nd_nav': r'^1\.'}
            self.h2_text: list = []
            self.file_no = re.search(r'gov\.ky\.krs\.title\.(?P<fno>\w+(\.\d)*)\.html', self.input_file_name).group(
                "fno")

            if self.file_no in ['33']:
                self.h2_order: list = ['chapter', 'subchapter', 'article', 'part']
            elif self.file_no in ['12']:
                self.h2_order: list = ['chapter']

            else:
                self.h2_order: list = ['chapter', 'article', 'part', 'subpart']

            if self.file_no in ['29']:
                self.h2_rename_pattern = [r'^(?P<tag>A)rticle (?P<id>3)\. Negotiable Instruments',
                                          '^(?P<tag>A)rticle (?P<id>4)\. Bank Deposits and Collections',
                                          '^(?P<tag>A)rticle (?P<id>4A)\. Funds Transfers',
                                          '^(?P<tag>A)rticle (?P<id>5)\. Letters of Credit',
                                          '^(?P<tag>A)rticle (?P<id>6)\. Bulk Transfers',
                                          '^(?P<tag>A)rticle (?P<id>7)\. Warehouse Receipts, Bills of Lading, and Other Documents '
                                          'of Title',
                                          '^(?P<tag>A)rticle (?P<id>8)\. Investment Securities',
                                          '^(?P<tag>A)rticle (?P<id>9)\. Secured Transactions — Sales of Accounts, Contract Rights '
                                          'and Chattel Paper\.',
                                          '^(?P<tag>A)rticle (?P<id>10)\. Other Provisions',
                                          '^(?P<tag>A)rticle (?P<id>11)\. Transition']

        self.h4_head: list = ['NOTES TO UNPUBLISHED DECISIONS', 'Official Comment', 'History.',
                              'Compiler’s Notes.', 'NOTES TO DECISIONS', 'Notes to Unpublished Decisions']

        self.watermark_text = """Release {0} of the Official Code of Kentucky Annotated released {1}
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexKY()

    def replace_tags_titles(self):
        repeated_header_list = []
        nd_tag_text = []

        for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
            if self.file_no in ['18', '12']:
                if not re.search(r'^(chapter|article|part|subpart)', li_tag.text.strip(), re.I):
                    li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                    self.h2_text.append(li_tag_text)
            else:
                if not re.search(r'^(chapter|subchapter|article|part|subpart)', li_tag.text.strip(), re.I):
                    li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                    self.h2_text.append(li_tag_text)

        super(KYParseHtml, self).replace_tags_titles()

        for p_tag in self.soup.find_all():
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["ul"]]:
                    p_tag.name = "li"
                    p_tag.wrap(self.ul_tag)

                elif p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    if re.match(r'^—?\d{1,3}\D\.?(\d\.)*', p_tag.text.strip()) \
                            and not re.match(r'^(\d+\D\.\d\d+)|^\d+-', p_tag.text.strip()) and \
                            p_tag.find_previous("h4") and \
                            re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                      p_tag.find_previous("h4").text.strip(), re.I):
                        p_tag.name = "h5"
                        sub_sec_text = re.sub(r'\W+', '', p_tag.get_text()).lower()
                        nd_tag_text.append(sub_sec_text)

                        if not re.match(r'^(\d+\.?\s*[—-])|^(—\d+\.?\s*[—-])', p_tag.text.strip()):
                            prev_head_tag = p_tag.find_previous("h4").get("id")
                            sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                            if sub_sec_id in repeated_header_list:
                                sub_sec_id = f"{prev_head_tag}-{sub_sec_text}.01"
                            else:
                                sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                            p_tag["id"] = sub_sec_id
                            repeated_header_list.append(sub_sec_id)

                        elif re.match(r'^(—?\d+\.?\s*—\s*[“a-zA-Z\d.]+)', p_tag.text.strip()):
                            prev_sub_tag = sub_sec_id
                            if self.release_number == '83' and self.file_no == '08' and \
                                    re.search(r'^—2\.— Burden of Proof\.', p_tag.text.strip()):
                                inner_sec_id1 = f"{p_tag.find_previous('h4').get('id')}-{sub_sec_text}"
                            else:
                                inner_sec_id1 = f"{prev_sub_tag}-{sub_sec_text}"
                            if inner_sec_id1 in repeated_header_list:
                                inner_sec_id1 = f"{inner_sec_id1}.01"
                            else:
                                inner_sec_id1 = f"{inner_sec_id1}"
                            p_tag["id"] = inner_sec_id1
                            repeated_header_list.append(inner_sec_id1)

                        elif re.match(r'^(—?\d+\.?\s*—\s*—\s*[“a-zA-Z\d]+)', p_tag.text.strip()):
                            prev_child_tag = inner_sec_id1
                            innr_sec_id2 = f"{prev_child_tag}-{sub_sec_text}"

                            if innr_sec_id2 in repeated_header_list:
                                innr_sec_id2 = f"{innr_sec_id2}.01"
                            else:
                                innr_sec_id2 = f"{innr_sec_id2}"

                            p_tag["id"] = innr_sec_id2
                            repeated_header_list.append(innr_sec_id2)

                        elif re.match(r'^(—?\d+\.?\s*—\s*—\s*—\s*[“a-zA-Z\d]+)', p_tag.text.strip()):
                            prev_child_id1 = innr_sec_id2
                            innr_subsec_header_tag_id = f"{prev_child_id1}-{sub_sec_text}"

                            if innr_subsec_header_tag_id in repeated_header_list:
                                innr_subsec_header_tag_id = f"{innr_subsec_header_tag_id}.01"
                            else:
                                innr_subsec_header_tag_id = f"{innr_subsec_header_tag_id}"

                            p_tag["id"] = innr_subsec_header_tag_id
                            repeated_header_list.append(innr_subsec_header_tag_id)

                elif p_tag.get("class") == [self.tag_type_dict["ol_p"]] or \
                        p_tag.get("class") == [self.tag_type_dict["nd_nav"]]:
                    if self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()):
                        self.replace_h4_tag_titles(p_tag, None,
                                                   self.regex_pattern_obj.h2_article_pattern.search(
                                                       p_tag.text.strip()).group(
                                                       "id"))
                    elif self.regex_pattern_obj.h5_section_pattern.search(p_tag.text.strip()):
                        if self.file_no not in ['08', '11']:
                            p_tag.name = "h5"
                            p_tag[
                                "id"] = f'{p_tag.find_previous({"h4", "h3"}).get("id")}sec{self.regex_pattern_obj.h5_section_pattern.search(p_tag.text.strip()).group("id")}'

            elif p_tag.name == "h4" and re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                                  p_tag.text.strip(), re.I):
                for tag in p_tag.find_next_siblings():
                    if tag.get("class") == [self.tag_type_dict["ol_p"]]:
                        if not re.search(r'^(Analysis|Cited|Compiler’s Notes\.)', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                    else:
                        break

    def h2_set_id(self, header_tag):
        h2_id_count = 1
        header_tag.name = "h2"
        p_tag_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
        if self.file_no == '29':
            header_tag_id = f'{header_tag.find_previous(class_={"oneh2", "title", "threeh2"}).get("id")}-{p_tag_text}'
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

    def add_anchor_tags(self):
        super(KYParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if re.search(r'^APPENDIXRULES', li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    sub_tag = 'apr'
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)

            elif li_tag.name in ['h2', 'h3', 'h4']:
                self.a_nav_count = 0
                self.c_nav_count = 0
                self.p_nav_count = 0
                self.s_nav_count = 0

    def ol_count_increment(self, current_id, ol_count):
        if current_id in self.ol_list:
            ol_count += 1
        else:
            ol_count = 1
        return ol_count

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
        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        cap_roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")
        num_ol1 = self.soup.new_tag("ol")
        innr_alpha_ol = self.soup.new_tag("ol", type="a")
        roman_ol = self.soup.new_tag("ol", type="i")
        ol_count = 1
        self.ol_list = []
        ol_head1 = 1
        inner_num_count = 1
        sec_alpha = 'a'
        small_roman = "i"
        cap_rom = "I"
        inner_sec_alpha = "a"
        cap_roman_cur_tag = None
        prev_head_id = None
        prev_num_id = None
        num_cur_tag = None
        alpha_cur_tag = None
        cap_alpha_cur_tag = None
        prevnum_id = None
        prev_id = None
        prevnum_id1 = None
        prev_id1 = None
        alpha_cur_tag1 = None
        previous_li_tag = None
        num_tag = None

        for p_tag in self.soup.body.find_all(['h2', 'h3', 'h4', 'h5', 'p']):
            if p_tag.i:
                p_tag.i.unwrap()
            if p_tag.span:
                p_tag.span.unwrap()

            current_tag_text = p_tag.text.strip()

            if p_tag.name == "h3":
                num_cur_tag = None

            if re.search(rf'^\({ol_head}\)', current_tag_text):
                p_tag.name = "li"
                num_cur_tag = p_tag
                alpha_cur_tag = None

                main_sec_alpha = "a"
                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)

                    if cap_roman_cur_tag:
                        cap_roman_cur_tag.append(num_ol)
                        prev_num_id = f'{cap_roman_cur_tag.get("id")}'
                        cap_alpha = 'A'

                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(num_ol)
                        prev_num_id = f'{cap_alpha_cur_tag.get("id")}'

                    elif alpha_cur_tag1:
                        alpha_cur_tag1.append(num_ol)
                        prev_num_id = f'{alpha_cur_tag1.get("id")}'

                    else:
                        cap_alpha = 'A'
                        ol_count = self.ol_count_increment(
                            f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}',
                            ol_count)
                        prev_num_id = f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}'
                        self.ol_list.append(prev_num_id)

                else:
                    num_ol.append(p_tag)
                    if not cap_alpha_cur_tag:
                        cap_alpha = 'A'

                p_tag["id"] = f'{prev_num_id}{ol_head}'
                p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
                ol_head += 1
                ol_head1 += 1

                if re.search(r'^\(\d+\)(\s)*\([a-z]\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)*\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)*\((?P<pid>\w)\)', current_tag_text)
                    prevnum_id = f'{prev_num_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_num_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
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
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)\s(?P<nid>\d+)\.', current_tag_text)
                        prev_id = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}'
                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        num_ol1.append(inner_li_tag)
                        alpha_cur_tag.string = ""
                        alpha_cur_tag.append(num_ol1)
                        num_count = 2
                previous_li_tag = p_tag

            elif re.search(rf'^\(\s*{main_sec_alpha}\s*\)', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                num_count = 1
                ol_head1 = 1

                if re.search(r'^\(a\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol)
                    if num_cur_tag:
                        prevnum_id = num_cur_tag.get("id")
                        num_cur_tag.append(alpha_ol)
                    elif num_tag:
                        prevnum_id = num_tag.get("id")
                        num_tag.append(alpha_ol)
                    else:
                        prevnum_id = f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}'
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
                previous_li_tag = p_tag

            elif re.search(r'^\(\s*\d\d\s*\)', current_tag_text):
                p_tag.name = "li"
                p_tag_text = re.search(r'^\(\s*(?P<id>\d\d)\s*\)', current_tag_text).group("id")
                alpha_ol.append(p_tag)
                p_tag["id"] = f'{prevnum_id}{p_tag_text}'
                p_tag.string = re.sub(r'^\(\s*\d\d\s*\)', '', current_tag_text)
                previous_li_tag = p_tag

            elif re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha = 'a'
                num_tag = p_tag
                inner_sec_alpha = "a"

                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    if alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)
                    elif cap_alpha_cur_tag:
                        prev_id = cap_alpha_cur_tag.get("id")
                        cap_alpha_cur_tag.append(num_ol1)
                    elif num_cur_tag:
                        prev_id = num_cur_tag.get("id")
                        num_cur_tag.append(num_ol1)
                    else:
                        ol_count = self.ol_count_increment(
                            f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}',
                            ol_count)
                        prev_id = f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}'
                        self.ol_list.append(prev_id)

                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{prev_id}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1

                if re.search(r'^\d+\.\s?a\.', current_tag_text):
                    innr_alpha_ol = self.soup.new_tag("ol", type="a")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\d+\.\s?a\.', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag1 = inner_li_tag
                    cur_tag = re.search(r'^(?P<cid>\d+)\.\s?(?P<pid>a)\.', current_tag_text)
                    prevnum_id1 = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                    inner_li_tag[
                        "id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    innr_alpha_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, innr_alpha_ol)
                    sec_alpha = 'b'
                previous_li_tag = p_tag

            elif re.search(rf'^{inner_num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_num_tag = p_tag

                if re.search(r'^1\.', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if alpha_cur_tag:
                        inner_prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(inner_num_ol)
                    elif num_cur_tag:
                        inner_prev_id = num_cur_tag.get("id")
                        num_cur_tag.append(inner_num_ol)
                    else:
                        ol_count = self.ol_count_increment(
                            f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}',
                            ol_count)
                        inner_prev_id = f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}'
                        self.ol_list.append(inner_prev_id)
                else:
                    inner_num_ol.append(p_tag)

                p_tag["id"] = f'{inner_prev_id}{inner_num_count}'
                p_tag.string = re.sub(rf'^{inner_num_count}\.', '', current_tag_text)
                inner_num_count += 1

            elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag1 = p_tag
                ol_head1 = 1
                small_roman = "i"

                if re.search(r'^a\.', current_tag_text):
                    innr_alpha_ol = self.soup.new_tag("ol", type="a")
                    previd = p_tag.find_previous("li")
                    p_tag.wrap(innr_alpha_ol)
                    prevnum_id1 = previd.get("id")
                    previd.append(innr_alpha_ol)
                    p_tag["id"] = f'{prevnum_id1}{sec_alpha}'
                else:
                    innr_alpha_ol.append(p_tag)
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
                    small_roman = "ii"
                previous_li_tag = p_tag

            elif re.search(rf'^{cap_alpha}\.|^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                num_count = 1
                if re.search(r'^A\.|^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    ol_count = self.ol_count_increment(
                        f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}',
                        ol_count)

                    prev_id1 = f'{p_tag.find_previous({"h5", "h4", "h3"}).get("id")}ol{ol_count}'
                    self.ol_list.append(prev_id1)
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.|^\({cap_alpha}\)', '', current_tag_text)

                if cap_alpha == 'Z':
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)
                previous_li_tag = p_tag

            elif re.search(rf'^{inner_sec_alpha}\.', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                ol_head1 = 1
                if re.search(r'^a\.', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol)
                    if num_tag:
                        prevnum_id = num_tag.get("id")
                        num_tag.append(alpha_ol)
                    else:
                        num_count = 1
                        prevnum_id = f'{p_tag.find_previous({"h4", "h3"}).get("id")}ol{ol_count}'
                else:
                    alpha_ol.append(p_tag)
                    if not num_tag:
                        num_count = 1

                p_tag["id"] = f'{prevnum_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\(\s*{inner_sec_alpha}\s*\)', '', current_tag_text)
                inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

            elif re.search(rf'^{cap_rom}\.', current_tag_text):
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag
                ol_head = 1

                if re.search(r'^I\.', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    prev_id1 = p_tag.find_previous({"h5", "h4", "h3"}).get("id")
                else:
                    cap_roman_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}ol{ol_count}{cap_rom}'
                p_tag.string = re.sub(rf'^{cap_rom}\.', '', current_tag_text)
                cap_rom = roman.toRoman(roman.fromRoman(cap_rom.upper()) + 1)
                previous_li_tag = p_tag

            elif re.search(rf'^{small_roman}\.', current_tag_text) and alpha_cur_tag1:
                p_tag.name = "li"
                if re.search(r'^i\.', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)

                    alpha_cur_tag1.append(roman_ol)
                    prev_id1 = alpha_cur_tag1.get("id")
                else:
                    roman_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}{small_roman}'
                p_tag.string = re.sub(rf'^{small_roman}\.', '', current_tag_text)
                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()
                previous_li_tag = p_tag

            elif p_tag.get("class") == [self.tag_type_dict['head4']] and p_tag.name == "p":
                if p_tag.b:
                    previous_li_tag = None
                if previous_li_tag and re.search(r'^Official Comment$', p_tag.find_previous("h4").text.strip(), re.I):
                    previous_li_tag.append(p_tag)

            elif p_tag.get("class") == [self.tag_type_dict['ol_p']] and p_tag.name == "p" and previous_li_tag:
                if self.file_no == '42' and re.search(r'^Click to view', p_tag.text.strip(), re.I):
                    ol_head = 1

                if re.search(r'^\([a-z][a-z]\)', p_tag.text.strip()):
                    p_tag.name = "li"
                    alpha_cur_tag = p_tag
                    num_count = 1
                    ol_head1 = 1
                    alpha_ol.append(p_tag)
                    pid = re.search(r'\((?P<id>[a-z][a-z])\)', p_tag.text.strip()).group("id")
                    p_tag["id"] = f'{prevnum_id}{pid}'
                    p_tag.string = re.sub(rf'^\([a-z][a-z]\)', '', current_tag_text)
                elif not re.search(r'^(History|SECTION (\d+|[A-Z])|Click to view)', p_tag.find_next("p").text.strip(),
                                   re.I) and \
                        not re.search(r'^(History|SECTION (\d+|[A-Z])|Click to view)', p_tag.text.strip(), re.I):
                    previous_li_tag.append(p_tag)

            if re.search(r'^History|^Cross references:|^OFFICIAL COMMENT|^SECTION (\d+|[A-Z])[^-]',
                         current_tag_text, re.I) or p_tag.name in ['h3', 'h4', 'h5']:
                ol_head = 1
                ol_head1 = 1
                num_count = 1
                num_cur_tag = None
                main_sec_alpha = 'a'
                sec_alpha = 'a'
                alpha_cur_tag = None
                cap_alpha = "A"
                small_roman = "i"
                cap_rom = "I"
                inner_sec_alpha = "a"
                cap_alpha_cur_tag = None
                cap_roman_cur_tag = None
                alpha_cur_tag1 = None
                previous_li_tag = None
                num_tag = None

        logger.info("ol tag created")

    def create_analysis_nav_tag(self):
        super(KYParseHtml, self).create_Notes_to_decision_analysis_nav_tag()
        logger.info("note to decision nav created")

    def add_anchor_tags_con(self):
        super(KYParseHtml, self).add_anchor_tags_con()
        self.am_nav_count = 0
        for li_tag in self.soup.findAll("li"):
            if not li_tag.get("id"):
                if amd_id := re.search(r'^AMENDMENT (?P<id>[IVX]+)', li_tag.text.strip()):
                    self.am_nav_count += 1
                    self.set_chapter_section_id(li_tag, amd_id.group("id"),
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous("h2").get("id"),
                                                cnav=f'amnav{self.am_nav_count:02}')

    def replace_tags_constitution(self):
        sub_sec_id = None
        inner_sec_id1 = None
        innr_sec_id2 = None

        for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
            li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
            self.h2_text_con.append(li_tag_text)

        super(KYParseHtml, self).replace_tags_constitution()

        repeated_header_list = []
        nd_tag_text = []

        for p_tag in self.soup.findAll():
            if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.match(r'^—?\d{1,3}\D\.?(\d\.)*', p_tag.text.strip()) \
                        and not re.match(r'^(\d+\D\.\d\d+)|^\d+-', p_tag.text.strip()) and \
                        p_tag.find_previous("h4") and \
                        re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                  p_tag.find_previous("h4").text.strip(), re.I):
                    p_tag.name = "h5"
                    sub_sec_text = re.sub(r'\W+', '', p_tag.get_text()).lower()
                    nd_tag_text.append(sub_sec_text)

                    if not re.match(r'^(\d+\.?\s*[—-])|^(—\d+\.?\s*[—-])', p_tag.text.strip()):
                        prev_head_tag = p_tag.find_previous("h4").get("id")
                        sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                        if sub_sec_id in repeated_header_list:
                            sub_sec_id = f"{prev_head_tag}-{sub_sec_text}.01"
                        else:
                            sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                        p_tag["id"] = sub_sec_id
                        repeated_header_list.append(sub_sec_id)

                    elif re.match(r'^(—?\d+\.?\s*—\s*[“a-zA-Z\d.]+)', p_tag.text.strip()):
                        prev_sub_tag = sub_sec_id
                        inner_sec_id1 = f"{prev_sub_tag}-{sub_sec_text}"
                        if inner_sec_id1 in repeated_header_list:
                            inner_sec_id1 = f"{inner_sec_id1}.01"
                        else:
                            inner_sec_id1 = f"{inner_sec_id1}"
                        p_tag["id"] = inner_sec_id1
                        repeated_header_list.append(inner_sec_id1)

                    elif re.match(r'^(—?\d+\.?\s*—\s*—\s*[“a-zA-Z\d]+)', p_tag.text.strip()):
                        prev_child_tag = inner_sec_id1
                        innr_sec_id2 = f"{prev_child_tag}-{sub_sec_text}"

                        if innr_sec_id2 in repeated_header_list:
                            innr_sec_id2 = f"{innr_sec_id2}.01"
                        else:
                            innr_sec_id2 = f"{innr_sec_id2}"

                        p_tag["id"] = innr_sec_id2
                        repeated_header_list.append(innr_sec_id2)

                    elif re.match(r'^(—?\d+\.?\s*—\s*—\s*—\s*[“a-zA-Z\d]+)', p_tag.text.strip()):
                        prev_child_id1 = innr_sec_id2
                        innr_subsec_header_tag_id = f"{prev_child_id1}-{sub_sec_text}"

                        if innr_subsec_header_tag_id in repeated_header_list:
                            innr_subsec_header_tag_id = f"{innr_subsec_header_tag_id}.01"
                        else:
                            innr_subsec_header_tag_id = f"{innr_subsec_header_tag_id}"

                        p_tag["id"] = innr_subsec_header_tag_id
                        repeated_header_list.append(innr_subsec_header_tag_id)

                elif p_tag.name == "h4" and re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                                      p_tag.text.strip(), re.I):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["ol_p"]]:
                            if not re.search(r'^(Analysis|Cited|Compiler’s Notes\.|Cross-References)',
                                             tag.text.strip()):
                                tag.name = "li"
                                tag["class"] = "note"
                        else:
                            break
