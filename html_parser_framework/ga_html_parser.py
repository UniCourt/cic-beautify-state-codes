import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexGA
import roman


class GAParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.judicial_decision_header_list: list = []
        self.file_no = None
        self.h2_pattern_text = None

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'head1': r'^CONSTITUTION OF THE', 'ul': r'^\[Preamble\]|^Article I',
                                        'head2': r'^Article I',
                                        'head4': '^JUDICIAL DECISIONS', 'ol': r'^\(\d\)|^1.', 'junk1': '^Annotations$',
                                        'head3': r'^Sec(tion)?\.? (I|1)|^Paragraph I\.|^Article I|^Sec.1.',
                                        'normalp': '^Editor\'s note', 'article': r'^ARTICLE I.'}
            self.h2_order = ['article']
            if int(self.release_number) <= 82:
                self.tag_type_dict['ul'] = r'^I\.'
        else:
            if int(self.release_number) <= 82:
                self.tag_type_dict: dict = {'head1': r'TITLE \d', 'ul': r'^Chap\.|^Art\.|^Sec\.',
                                            'head2': r'^CHAPTER \d|^ARTICLE \d|^Article \d',
                                            'head3': r'^\d+-\d+([a-z])?-\d+(\.\d+)?',
                                            'head4': '^JUDICIAL DECISIONS|OPINIONS OF THE ATTORNEY GENERAL',
                                            'ol': r'^\([a-z]\)', 'junk1': '^Annotations$', 'nav': r'^——————————',
                                            'part': r'^PART (1|A)', 'article': r'^ARTICLE I.',
                                            'table': 'TABLE OF EXEMPT ANABOLIC STEROID PRODUCTS'}

                self.h2_pattern_text = ['^(?P<tag>P)ART\s*(?P<id>[A-Z])']
            else:
                self.tag_type_dict: dict = {'head1': r'TITLE \d', 'ul': r'^Chap\.|^Art\.|^Sec\.',
                                            'head2': r'^CHAPTER \d|^ARTICLE \d|^Article \d',
                                            'head3': r'^\d+-\d+([a-z])?-\d+(\.\d+)?',
                                            'head4': '^JUDICIAL DECISIONS|OPINIONS OF THE ATTORNEY GENERAL',
                                            'ol': r'^\([a-z]\)', 'junk1': '^Annotations$', 'article': r'^ARTICLE I.'}

            self.file_no = re.search(r'gov\.ga\.ocga\.title\.(?P<fno>\d+)\.html', self.input_file_name).group(
                "fno")

            if self.file_no in ['11']:
                if int(self.release_number) <= 82:
                    self.h2_order = ['article']
                    self.h2_pattern_text = None
                else:
                    self.h2_order = ['article', 'part', 'subpart']
            else:
                self.h2_order = ['chapter', 'article', 'part', 'subpart']

            if self.file_no in ['13']:
                self.tag_type_dict['part'] = "^PART 2"
            if int(self.release_number) > 82:
                self.tag_type_dict['ul'] = r'^CHAPTER \d|^ARTICLE \d|^Article \d'

        self.h2_text: list = []
        self.h4_head: list = ['ENUMERATION OF ERRORS', 'COMMENT', 'JUDICIAL DECISIONS', 'RESEARCH REFERENCES',
                              'OPINIONS OF THE ATTORNEY GENERAL']
        self.watermark_text = """Release {0} of the Official Code of Georgia Annotated released {1}. 
                Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on {2}. 
                This document is not subject to copyright and is in the public domain.
                """
        self.regex_pattern_obj = CustomisedRegexGA()

    def replace_tags_titles(self):
        h2_part_pattern = re.compile(r'^part\s(?P<id>(\d+(\.\d)?([a-zA-Z])*)|([IVX]+)|([a-zA-Z]))', re.I)

        if self.file_no in ['36']:
            for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
                if not re.search(r'^(chapter|subchapter|article|part|subpart|subtitle|'
                                 r'^\d+(\.\d+)?|^\d+(\.\d+)?-\d+(\.\d+)?)', li_tag.text.strip(), re.I):
                    li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                    self.h2_text.append(li_tag_text)

        for rename_class_tag in self.soup.findAll():
            if int(self.release_number) <= 82 and rename_class_tag.get("class") == [self.tag_type_dict["part"]]:
                if h2_part_pattern.search(rename_class_tag.text.strip()):
                    pos = rename_class_tag.attrs['class'].index(self.tag_type_dict["part"])
                    rename_class_tag.attrs['class'][pos] = self.tag_type_dict["head2"]

        super(GAParseHtml, self).replace_tags_titles()

        chap_pattern = re.compile(r'^(?P<id>\d+[A-Z]?(\.\d+)?)\.', re.I)
        self.judicial_decision_header_list: list = []
        judicial_decision_id_list: list = []
        count = 1
        jdecision_id = None
        alpha = None
        id_list = []

        for p_tag in self.soup.find_all():
            if p_tag.get("class") in [[self.tag_type_dict["head2"]], [self.tag_type_dict["head3"]]]:
                if re.search(r'^APPENDIX\s?RULES|^RULES AND', p_tag.get_text().strip(), re.I):
                    p_tag.name = 'h2'
                    apdx_text = re.sub(r'\W+', '', p_tag.get_text().strip()).lower()
                    p_tag['id'] = f'{p_tag.find_previous("h1").get("id")}apr{apdx_text}'
                    p_tag['class'] = "apdxrules"

                elif int(self.release_number) <= 82 and chap_pattern.search(p_tag.text.strip()):
                    p_tag.name = "h3"
                    p_tag[
                        'id'] = f'{p_tag.find_previous("h2", class_="apdxrules").get("id")}{chap_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                elif re.search(r'^Rule \d+(-\d+-\.\d+)*(\s\(\d+\))*(\.\d+)?\.', p_tag.get_text().strip()):
                    p_tag.name = 'h3'
                    rule_id = re.search(r'^Rule (?P<r_id>\d+(-\d+-\.\d+)*(\s\(\d+\))*(\.\d+)?)\.',
                                        p_tag.get_text().strip()).group("r_id").replace(" ", '')
                    p_tag['id'] = f'{p_tag.find_previous("h2", class_="apdxrules").get("id")}r{rule_id.zfill(2)}'
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif self.file_no == "11":
                    if self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                        p_tag.name = "h2"
                        header_tag_id = f'{p_tag.findPrevious("h2", class_="oneh2").get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                        if header_tag_id in self.dup_id_list:
                            p_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                            self.id_count += 1
                        else:
                            p_tag["id"] = f'{header_tag_id}'
                            self.id_count = 1
                        p_tag["class"] = "twoh2"

                    elif re.search(r'^Part\s(?P<id>[A-Z])', p_tag.text.strip(), re.I):
                        p_tag.name = "h2"
                        header_tag_id = f'{p_tag.findPrevious("h2", class_="twoh2").get("id")}p{re.search(r"^Part (?P<id>[A-Z])", p_tag.text.strip(), re.I).group("id").zfill(2)}'
                        if header_tag_id in self.dup_id_list:
                            p_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                            self.id_count += 1
                        else:
                            p_tag["id"] = f'{header_tag_id}'
                            self.id_count = 1
                        p_tag["class"] = "threeh2"

                    elif p_tag.get("class") == [self.tag_type_dict["head3"]]:
                        if sec_id := getattr(self.parser_obj, "section_pattern").search(p_tag.text.strip()):
                            sec_id = re.sub(r'\s+|\.$', '', sec_id.group("id"))
                            if self.format_id(sec_id, p_tag):
                                sec_id = self.format_id(sec_id, p_tag)
                            p_tag.name = "h3"
                            if p_tag.find_previous({"h2", "h3"},
                                                   class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}):
                                header_tag_id = f'{p_tag.find_previous({"h2", "h3"}, class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}).get("id")}s{sec_id.zfill(2)}'
                                if header_tag_id in id_list:
                                    header_tag_id = f'{header_tag_id}.{self.h3_count:02}'
                                    p_tag["id"] = f'{header_tag_id}'
                                    self.h3_count += 1
                                else:
                                    p_tag["id"] = f'{header_tag_id}'
                                    self.h3_count = 1
                            else:
                                header_tag_id = f'{p_tag.find_previous("h1").get("id")}c{sec_id}'
                                if header_tag_id in id_list:
                                    header_tag_id = f'{header_tag_id}.{self.h3_count:02}'
                                    p_tag["id"] = f'{header_tag_id}'
                                    self.h3_count += 1
                                else:
                                    p_tag["id"] = f'{header_tag_id}'
                                    self.h3_count = 1

                            id_list.append(header_tag_id)
                        self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif int(self.release_number) <= 82 and p_tag.get("class") == [self.tag_type_dict["nav"]]:
                if self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()):
                    if self.file_no in ['38', '52'] and re.search(r'^Article [IVX]+', p_tag.text.strip(), re.I):
                        p_tag.name = "h4"
                        p_tag[
                            "id"] = f'{p_tag.findPrevious("h3").get("id")}a{self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                    else:
                        p_tag["class"] = "navhead"
                        p_tag["id"] = f'{p_tag.find_previous("h2").get("id")}' \
                                      f'a{self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                        self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                if self.file_no == "11" and self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                    if self.regex_pattern_obj.h2_part_pattern.search(p_tag.find_previous("h2").text.strip()):
                        p_tag.name = "h2"
                        header_tag_id = f'{p_tag.findPrevious("h2", class_="twoh2").get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                        if header_tag_id in self.dup_id_list:
                            p_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                            self.id_count += 1
                        else:
                            p_tag["id"] = f'{header_tag_id}'
                            self.id_count = 1
                        p_tag["class"] = "threeh2"

                    elif self.regex_pattern_obj.h2_article_pattern.search(p_tag.find_previous("h2").text.strip()):
                        if p_tag.find_next("p").find_next("p").get("class")[0] == self.tag_type_dict["nav"]:
                            p_tag["class"] = "navhead"
                            p_tag[
                                "id"] = f'{p_tag.find_previous("h2").get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                            p_tag.attrs['aria-labeledby'] = "nav"
                        else:
                            p_tag[
                                "id"] = f'{p_tag.find_previous("p", {"aria-labeledby": "nav"}).get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                            p_tag["class"] = "navhead"

                elif self.file_no == "11" and re.search(r'^Part\s(?P<id>[A-Z])', p_tag.text.strip()):
                    if p_tag.find_previous(class_="navhead", text=re.compile(r"^Part \d+")):
                        p_tag[
                            "id"] = f'{p_tag.find_previous(class_="navhead", text=re.compile(r"^Part [0-9]+")).get("id")}' \
                                    f'p{re.search(r"^Part (?P<id>[A-Z])", p_tag.text.strip()).group("id").zfill(2)}'
                        p_tag["class"] = "navhead"

                elif self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                    p_tag["class"] = "navhead"

                    if re.search(r'^Part\s(?P<id>[A-Z])', p_tag.text.strip()):
                        if p_tag.find_previous(class_="navhead", text=re.compile(r"^Part \d+")):
                            p_tag[
                                "id"] = f'{p_tag.find_previous(class_="navhead", text=re.compile(r"^Part [0-9]+")).get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                        elif p_tag.find_previous(class_="navhead", text=re.compile(r"^Article ")):
                            p_tag[
                                "id"] = f'{p_tag.find_previous(class_="navhead", text=re.compile(r"^Article ")).get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                        else:
                            p_tag[
                                "id"] = f'{p_tag.find_previous("h2").get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                    else:
                        if p_tag.find_previous(class_="navhead", text=re.compile(r"^Article ")):
                            p_tag[
                                "id"] = f'{p_tag.find_previous(class_="navhead", text=re.compile(r"^Article ")).get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                        else:
                            p_tag[
                                "id"] = f'{p_tag.find_previous("h2").get("id")}' \
                                        f'p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                if self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()):
                    p_tag["class"] = "navhead"
                    p_tag["id"] = f'{p_tag.find_previous(class_="navhead", text=re.compile(r"^Part ")).get("id")}' \
                                  f's{self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif self.tag_type_dict.get("article") and p_tag.get("class") and p_tag.get("class")[0] == \
                    self.tag_type_dict["article"]:
                if self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}' \
                                  f'{self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()).group("id")}'

            if p_tag.get("class") and p_tag.get("class")[0] == self.tag_type_dict["head4"]:
                if p_tag.text.strip() in self.h4_head:
                    self.replace_h4_tag_titles(p_tag, self.h4_count, None)

                if p_tag.name == "h4" and re.search(r'^JUDICIAL DECISIONS|^OPINIONS OF THE ATTORNEY GENERAL',
                                                    p_tag.text.strip(), re.I):
                    alpha_analysis_tag = None
                    jdecision_id = None

                    for tag in p_tag.find_next_siblings():
                        if int(self.release_number) <= 82 and re.search(r'^Analysis', tag.text.strip(), re.I):
                            tag.name = "li"
                            tag["class"] = "jdecisions"

                            self.recreating_tags()

                        if tag.get("class")[0] == self.tag_type_dict["ol"]:
                            if not re.search(r'^Analysis|^Editor’s notes\.', tag.text.strip()):
                                tag.name = "li"
                                tag["class"] = "jdecisions"
                                self.judicial_decision_header_list.append(tag.text.strip())
                        else:
                            break

                elif num_analysis_tag := re.search(r'^(?P<id>\d+)\.', p_tag.text.strip()):
                    p_tag.name = "h5"
                    if jdecision_id:
                        num_analysis_id = f'{jdecision_id}{num_analysis_tag.group("id")}'
                    else:
                        num_analysis_id = f'{p_tag.find_previous("h3").get("id")}-judicialdecision{num_analysis_tag.group("id")}'

                    if num_analysis_id in judicial_decision_id_list:
                        p_tag["id"] = f'{num_analysis_id}.{count:02}'
                        count += 1
                    else:
                        p_tag["id"] = f'{num_analysis_id}'
                        count = 1
                    judicial_decision_id_list.append(p_tag["id"])
                    alpha = "A"

                elif alpha and (re.search(rf'^{alpha}\.', p_tag.text.strip())
                                or re.search(rf'^{alpha.lower()}\.', p_tag.text.strip())):
                    p_tag.name = "h5"
                    alpha_analysis_id = f'{num_analysis_id}{alpha}'
                    if alpha_analysis_id in judicial_decision_id_list:
                        p_tag["id"] = f'{alpha_analysis_id}.{count:02}'
                        count += 1
                    else:
                        p_tag["id"] = f'{alpha_analysis_id}'
                        count = 1
                    alpha = chr(ord(alpha) + 1)
                    judicial_decision_id_list.append(p_tag["id"])

                elif p_tag.text.strip() in self.judicial_decision_header_list:
                    p_tag.name = "h5"
                    p_tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                    jdecision_id = f'{p_tag.find_previous("h3").get("id")}-judicialdecision-{p_tag_text}'
                    if jdecision_id in judicial_decision_id_list:
                        p_tag["id"] = f'{jdecision_id}.{count:02}'
                        count += 1
                    else:
                        p_tag["id"] = f'{jdecision_id}'
                        count = 1

                    judicial_decision_id_list.append(p_tag["id"])

            if p_tag.get("class") and p_tag.get("class")[0] == self.tag_type_dict["ol"]:
                if self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}' \
                                  f'{self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()).group("id")}'
                elif self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}' \
                                  f's{self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()).group("id")}'

    def add_anchor_tags(self):
        super(GAParseHtml, self).add_anchor_tags()

        rule_pattern = re.compile(r'^Rule (?P<rid>\d+(-\d+-\.\d+)*(\s\(\d+\))*(\.\d+)?)\.', re.I)
        chap_pattern = re.compile(r'^(?P<id>\d+[A-Z]?(\.\d+)?)\.', re.I)

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if re.search(r'^APPENDIX\s?RULES|^Rules and', li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    sub_tag = 'apr'
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)

                elif rule_pattern.search(li_tag.text.strip()):
                    rule_num = rule_pattern.search(li_tag.text.strip()).group("rid").replace(" ", '')
                    sub_tag = 'r'
                    prev_id = li_tag.find_previous("h2", class_="apdxrules").get("id")
                    self.s_nav_count += 1
                    cnav = f'cnav{self.s_nav_count:02}'
                    self.set_chapter_section_id(li_tag, rule_num, sub_tag, prev_id, cnav)

                elif int(self.release_number) <= 82 and \
                        chap_pattern.search(li_tag.text.strip()) and li_tag.get("class") != "jdecisions":
                    if int(self.release_number) <= 82 and self.file_no in ['11']:
                        tag = "a"
                        prev_tag = li_tag.find_previous("h1").get("id")
                    else:
                        if re.search(r'^Sec', li_tag.find_previous("p").text.strip()):
                            tag = ""
                            prev_tag = li_tag.find_previous("h2").get("id")
                        else:
                            tag = "c"
                            prev_tag = li_tag.find_previous("h1").get("id")
                    self.s_nav_count += 1
                    cnav = f'cnav{self.s_nav_count:02}'
                    self.set_chapter_section_id(li_tag,
                                                chap_pattern.search(li_tag.text.strip()).group("id").zfill(2),
                                                tag, prev_tag, cnav)
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
        num_count = 1
        small_roman = "i"
        cap_roman = "I"
        ol_count = 1
        inr_num_count = 1
        num = 1

        ol_terminator = None
        sec_alpha_cur_tag = None
        roman_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag = None
        cap_roman_tag = None

        sec_alpha_id = None
        num_id1 = None
        cap_alpha_id = None
        prev_id1 = None
        inr_num_id = None
        num_id = None

        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        smallroman_ol = self.soup.new_tag("ol", type="i")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inr_num_ol = self.soup.new_tag("ol")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")

        num_ol1 = self.soup.new_tag("ol")

        for p_tag in self.soup.body.find_all(['h2', 'h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()

            if p_tag.name == "p" and len(p_tag.text.strip()) > 0:

                if re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                    p_tag.name = "li"
                    sec_alpha_cur_tag = p_tag
                    ol_terminator = 1
                    inr_num_count = 1
                    cap_alpha_cur_tag = None

                    if re.search(r'^\(a\)', current_tag_text):
                        sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(sec_alpha_ol)
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                        if num_cur_tag1:
                            num_cur_tag1.append(sec_alpha_ol)
                            sec_alpha_id = num_cur_tag1.get("id")
                    else:
                        sec_alpha_ol.append(p_tag)

                    p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                    p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                    if not re.search(r'ol\d[A-Z]?\d+[a-z]$', p_tag.parent.find_next("li").get("id")):
                        num_count = 1

                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                    if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)
                        num_cur_tag1 = li_tag
                        cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                        num_id1 = f'{sec_alpha_cur_tag.get("id")}'
                        li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                        num_ol1.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(num_ol1)
                        num_count = 2

                        if re.search(rf'^\([a-z]\)\s*?\(\d+\)\s*?\(A\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            cap_alpha_cur_tag = inner_li_tag
                            inner_li_tag.string = re.sub(r'^\([a-z]\)\s*?\(\d+\)\s*?\(A\)', '', current_tag_text)
                            cap_alpha_id = f'{num_cur_tag1.get("id")}'
                            inner_li_tag[
                                "id"] = f'{num_cur_tag1.get("id")}A'
                            cap_alpha_ol.append(inner_li_tag)
                            num_cur_tag1.string = ""
                            num_cur_tag1.append(cap_alpha_ol)
                            cap_alpha = "B"

                elif re.search(rf'^\({num}\)', current_tag_text) and cap_alpha_cur_tag:

                    p_tag.name = "li"
                    num_cur_tag = p_tag
                    ol_terminator = 1

                    if re.search(r'^\(1\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)
                        num_id = cap_alpha_cur_tag.get("id")
                        cap_alpha_cur_tag.append(num_ol)
                    else:
                        num_ol.append(p_tag)

                    p_tag["id"] = f'{num_id}{num}'
                    p_tag.string = re.sub(rf'^\({num}\)', '', current_tag_text)
                    num += 1

                elif re.search(rf'^\({num_count}\)', current_tag_text):
                    p_tag.name = "li"
                    num_cur_tag1 = p_tag
                    small_roman = "i"
                    ol_terminator = 1

                    if re.search(r'^\(1\)', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol1)
                        if sec_alpha_cur_tag or cap_alpha_cur_tag:
                            if p_tag.find_previous("li") and p_tag.find_previous("li").get("id") and \
                                    re.search(r'ol', p_tag.find_previous("li").get("id")):
                                num_id1 = p_tag.find_previous("li").get("id")
                                p_tag.find_previous("li").append(num_ol1)
                        else:
                            num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    else:
                        num_ol1.append(p_tag)

                    p_tag["id"] = f'{num_id1}{num_count}'
                    p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                    num_count += 1

                    if not re.search(r'ol\d[A-Z]\d$|ol\d[-A-Z]+\d$', p_tag.parent.find_next("li").get("id")):
                        cap_alpha = "A"
                    if re.search(r'ol\d[A-Z]?\d$', p_tag.parent.find_next("li").get("id")):
                        main_sec_alpha = "a"

                    if re.search(rf'^\(\d+\)\s*\(A\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)', '', current_tag_text)
                        cap_alpha_cur_tag = li_tag
                        cap_alpha = re.search(r'^\((?P<cid>\d+)\)\s*\((?P<pid>A)\)', current_tag_text)
                        cap_alpha_id = num_cur_tag1.get("id")
                        li_tag["id"] = f'{num_cur_tag1.get("id")}{cap_alpha.group("pid")}'
                        cap_alpha_ol.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(cap_alpha_ol)
                        cap_alpha = "B"

                        if re.search(r'^\(\d+\)\s*\(\w\)\s?\(i\)', current_tag_text):
                            smallroman_ol = self.soup.new_tag("ol", type="i")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s?\(i\)', '', current_tag_text)
                            roman_cur_tag = inner_li_tag
                            prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                            inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                            smallroman_ol.append(inner_li_tag)
                            cap_alpha_cur_tag.string = ""
                            cap_alpha_cur_tag.append(smallroman_ol)
                            small_roman = "ii"

                    if re.search(rf'^\(\d+\)\s*\(a\)', current_tag_text):
                        sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s*\(a\)', '', current_tag_text)
                        sec_alpha_cur_tag = li_tag
                        sec_alpha_id = num_cur_tag1.get("id")
                        li_tag["id"] = f'{num_cur_tag1.get("id")}a'
                        sec_alpha_ol.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(sec_alpha_ol)
                        main_sec_alpha = "b"

                elif re.search(rf'^\({cap_roman}\)', current_tag_text):
                    p_tag.name = "li"
                    cap_roman_tag = p_tag
                    ol_terminator = 1

                    if re.search(r'^\(I\)', current_tag_text):
                        if re.search(r'^\(J\)', p_tag.find_next_sibling("p").text.strip()):
                            cap_alpha_ol.append(p_tag)
                            p_tag["id"] = f'{cap_alpha_id}-I'
                            p_tag.string = re.sub(rf'^\(I\)', '', current_tag_text)
                            cap_alpha = "J"
                        else:
                            roman_ol = self.soup.new_tag("ol", type="I")
                            p_tag.wrap(roman_ol)
                            if roman_cur_tag:
                                roman_cur_tag.append(roman_ol)
                                prev_id1 = roman_cur_tag.get("id")
                            else:
                                prev_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                            p_tag["id"] = f'{prev_id1}-{cap_roman}'
                            p_tag.string = re.sub(rf'^\({cap_roman}\)', '', current_tag_text)
                            cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)
                    else:
                        roman_ol.append(p_tag)

                        p_tag["id"] = f'{prev_id1}-{cap_roman}'
                        p_tag.string = re.sub(rf'^\({cap_roman}\)', '', current_tag_text)
                        cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                        if not re.search(r'ol\d+[A-Z]\w+-?\w*$|ol\d[a-z]\d+\w+-?\w+$',
                                         p_tag.parent.find_next("li").get("id")):
                            cap_alpha = "A"

                elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                    p_tag.name = "li"
                    cap_alpha_cur_tag = p_tag
                    small_roman = "i"
                    ol_terminator = 1
                    num = 1

                    if re.search(r'^\(A\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        p_tag.wrap(cap_alpha_ol)
                        if num_cur_tag1 or cap_roman_tag:
                            cap_alpha_id = p_tag.find_previous("li").get('id')
                            p_tag.find_previous("li").append(cap_alpha_ol)
                        else:
                            cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                        ol_count += 1
                    else:
                        cap_alpha_ol.append(p_tag)

                    p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                    p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                    if cap_alpha == "Z":
                        cap_alpha = "A"
                    else:
                        cap_alpha = chr(ord(cap_alpha) + 1)

                    if re.search(r'ol\d[A-Z]+$', p_tag.parent.find_next("li").get("id")):
                        num_count = 1

                    if re.search(rf'^\([A-Z]\)\s*\(i\)', current_tag_text):
                        smallroman_ol = self.soup.new_tag("ol", type="i")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\([A-Z]\)\s*\(i\)', '', current_tag_text)
                        roman_cur_tag = li_tag
                        prev_id1 = f'{cap_alpha_cur_tag.get("id")}i'
                        li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                        smallroman_ol.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(smallroman_ol)
                        small_roman = "ii"

                elif re.search(rf'^\({small_roman}\)', current_tag_text):
                    p_tag.name = "li"
                    roman_cur_tag = p_tag
                    ol_terminator = 1
                    cap_roman = "I"

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

                elif re.search(rf'^{inr_num_count}\.', current_tag_text):
                    p_tag.name = "li"
                    ol_terminator = 1

                    if re.search(r'^1\.', current_tag_text):
                        inr_num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(inr_num_ol)
                        if sec_alpha_cur_tag or num_cur_tag1:
                            inr_num_id = p_tag.find_previous("li").get('id')
                            p_tag.find_previous("li").append(inr_num_ol)
                        else:
                            inr_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    else:
                        inr_num_ol.append(p_tag)

                    p_tag["id"] = f'{inr_num_id}{inr_num_count}'
                    p_tag.string = re.sub(rf'{inr_num_count}\.', '', current_tag_text)
                    inr_num_count += 1

                elif re.search(r'^\(\d+\.\d+\)', current_tag_text) and self.file_no != '16':
                    if num_cur_tag1:
                        num_cur_tag1.append(p_tag)
                        num_cur_tag1 = p_tag
                        cap_alpha = "A"
                        small_roman = "i"
                        digit_tag_id = re.search(r'^\((?P<id>\d+\.\d+)\)', current_tag_text).group("id")
                        if sec_alpha_cur_tag:
                            p_tag["id"] = f"{sec_alpha_cur_tag.get('id')}{digit_tag_id}"
                        else:
                            p_tag[
                                "id"] = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}{digit_tag_id}"
                    else:
                        p_tag.insert_after(p_tag.find_next_sibling())
                    ol_terminator = 1

                elif re.search(r'^\(\w\.\d+\)', current_tag_text):
                    tag_id = re.search(r'^\((?P<id>\w\.\d+)\)', current_tag_text).group("id")
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(p_tag)
                        sec_alpha_cur_tag = p_tag
                        inr_num_count = 1
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(p_tag)
                        cap_alpha_cur_tag = p_tag
                    else:
                        p_tag.insert_after(p_tag.find_next_sibling())
                    p_tag["id"] = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}{tag_id}"

                    ol_terminator = 1

                elif ol_terminator:
                    if p_tag.find_previous("li") and self.tag_type_dict.get("article") and p_tag.get("class")[0] in [
                        self.tag_type_dict["ol"],
                        self.tag_type_dict["article"]] \
                            and not re.search(r'^(NOTICES:|ADDITIONAL INFORMATION:|TO SCHOOL OFFICIALS:)$|'
                                              r'^History\.|^Sec\. \d+\.', p_tag.text.strip()) and not p_tag.b:
                        p_tag.find_previous("li").append(p_tag)

            if p_tag.name in ['h3', 'h4', 'h5'] or re.search(r'^(NOTICES:|ADDITIONAL INFORMATION:|TO SCHOOL '
                                                             r'OFFICIALS:)$|^Sec\. \d+\.', p_tag.text.strip()):
                main_sec_alpha = 'a'
                cap_alpha = "A"
                num_count = 1
                inr_num_count = 1
                small_roman = "i"
                num = 1

                sec_alpha_cur_tag = None
                ol_terminator = None
                num_cur_tag1 = None
                roman_cur_tag = None
                cap_alpha_cur_tag = None
                cap_roman_tag = None

                if re.search(
                        r'^(NOTICES:|ADDITIONAL INFORMATION:|TO SCHOOL OFFICIALS:|ENUMERATION OF ERRORS)$|^Sec\. \d+\.',
                        p_tag.text.strip()):
                    ol_count += 1
                else:
                    ol_count = 1

        print('ol tags added')

    def create_analysis_nav_tag(self):
        analysis_num_tag_id = None
        analysis_tag = None
        analysis_tag_id = None
        analysis_num_tag = None
        alpha = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        inner_alpha_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for analysis_p_tag in self.soup.findAll(["li", "h4"]):
            if analysis_p_tag.name == "li" and analysis_p_tag.get("class") == "jdecisions":
                analysis_p_tag_text = re.sub(r'[\W\s]+', '', analysis_p_tag.text.strip()).lower()
                if num_analysis_tag := re.search(r'^(?P<id>\d+)\.', analysis_p_tag.text.strip()):
                    analysis_num_tag = analysis_p_tag
                    if analysis_tag:
                        analysis_num_tag_id = f'{analysis_tag_id}{num_analysis_tag.group("id")}'
                    else:
                        analysis_num_tag_id = f'#{analysis_p_tag.find_previous("h3").get("id")}-judicialdecision{num_analysis_tag.group("id")}'
                    a_tag_id = f'{analysis_num_tag_id}'

                    if re.search(r'^\d+\.', analysis_p_tag.find_previous("li").text.strip()):
                        inner_ul_tag.append(analysis_p_tag)
                    else:
                        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        analysis_p_tag.wrap(inner_ul_tag)
                        if analysis_tag:
                            analysis_tag.append(inner_ul_tag)
                    alpha = "A"

                elif alpha and re.search(rf'^({alpha}|{alpha.lower()})\.', analysis_p_tag.text.strip()):
                    a_tag_id = f'{analysis_num_tag_id}{alpha}'
                    if re.search(r'^[A-Za-z]+\.', analysis_p_tag.find_previous("li").text.strip()):
                        inner_alpha_ul_tag.append(analysis_p_tag)
                    else:
                        inner_alpha_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        analysis_p_tag.wrap(inner_alpha_ul_tag)
                        analysis_num_tag.append(inner_alpha_ul_tag)
                    alpha = chr(ord(alpha) + 1)

                else:
                    if analysis_p_tag.find_previous("h3"):
                        analysis_tag_id = f'#{analysis_p_tag.find_previous("h3").get("id")}-judicialdecision-{analysis_p_tag_text}'
                    analysis_tag = analysis_p_tag
                    if analysis_p_tag.find_previous().name not in ['a', 'li']:
                        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        analysis_p_tag.wrap(ul_tag)
                    else:
                        ul_tag.append(analysis_p_tag)
                    a_tag_id = analysis_tag_id
                anchor = self.soup.new_tag('a', href=a_tag_id)
                anchor.string = analysis_p_tag.text
                analysis_p_tag.string = ''
                analysis_p_tag.append(anchor)
            else:
                analysis_tag = None

        print("judicial decision nav created")

    def h2_set_id(self, header_tag):
        h2_id_count = 1
        header_tag.name = "h2"
        p_tag_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
        header_tag_id = f'{header_tag.find_previous("h1").get("id")}-{p_tag_text}'
        if header_tag_id in self.h2_rep_id:
            header_tag["id"] = f'{header_tag_id}.{h2_id_count:02}'
            h2_id_count += 1
        else:
            header_tag["id"] = f'{header_tag_id}'
            h2_id_count = 1
        header_tag["class"] = "gen"
        self.h2_rep_id.append(header_tag['id'])

    def recreating_tags(self):
        for p_tag in self.soup.findAll("li", class_="jdecisions"):
            if re.search(r'^Analysis', p_tag.text.strip(), re.I):
                rept_tag = re.split('\n', p_tag.text.strip())
                p_tag.clear()
                for tag_text in rept_tag:
                    if not re.search(r'^Analysis', tag_text.strip(), re.I):
                        new_tag = self.soup.new_tag("li")
                        new_tag.string = tag_text
                        new_tag["class"] = "jdecisions"
                        p_tag.append(new_tag)
                    else:
                        new_tag = self.soup.new_tag("p")
                        new_tag.string = tag_text
                        p_tag.append(new_tag)
                    self.judicial_decision_header_list.append(tag_text.strip())
                p_tag.unwrap()

    def add_anchor_tags_con(self):
        super(GAParseHtml, self).add_anchor_tags_con()

        article_pattern = re.compile(r'^(?P<id>[IVX]+[A-Z]?)\.')
        digit_pattern = re.compile(r'^(?P<id>\d+)\.')
        amend_pattern = re.compile(r'^\[?Amendment (?P<id>[IVX]+)]?')
        paragraph_pattern = re.compile(r'^Paragraph (?P<id>[IVX]+(-[A-Z])?)')

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if article_pattern.search(li_tag.text.strip()):
                    if li_tag.find_previous("h2"):
                        if re.search(r"^Paragraph", li_tag.find_previous("p").text.strip()):
                            tag = "p"
                            prev_tag_id = li_tag.find_previous("h3").get("id")
                        elif re.search(r'^Amend', li_tag.find_previous("p").text.strip()):
                            tag = "am"
                            prev_tag_id = li_tag.find_previous("h2").get("id")
                        else:
                            tag = "s"
                            prev_tag_id = li_tag.find_previous("h2").get("id")

                        self.s_nav_count += 1
                        self.set_chapter_section_id(li_tag,
                                                    article_pattern.search(li_tag.text.strip()).group('id').zfill(2),
                                                    sub_tag=f'-{tag}',
                                                    prev_id=prev_tag_id,
                                                    cnav=f'snav{self.s_nav_count:02}')
                    else:
                        self.c_nav_count += 1
                        self.set_chapter_section_id(li_tag,
                                                    article_pattern.search(li_tag.text.strip()).group('id').zfill(2),
                                                    sub_tag="ar",
                                                    prev_id=li_tag.find_previous("h1").get("id"),
                                                    cnav=f'cnav{self.c_nav_count:02}')

                elif app_tag := re.search(r'^APPENDIX (?P<id>(ONE|TWO|THREE|FOUR))', li_tag.text.strip()):
                    self.set_chapter_section_id(li_tag,
                                                app_tag.group('id').lower(),
                                                sub_tag="-ap",
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

                elif digit_pattern.search(li_tag.text.strip()) and li_tag.get("class") != "jdecisions":
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag,
                                                digit_pattern.search(li_tag.text.strip()).group('id').zfill(2),
                                                sub_tag=f'-s',
                                                prev_id=li_tag.find_previous("h2").get("id"),
                                                cnav=f'snav{self.s_nav_count:02}')

                elif amend_pattern.search(li_tag.text.strip()):
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag,
                                                amend_pattern.search(li_tag.text.strip()).group('id').zfill(2),
                                                sub_tag='-am',
                                                prev_id=li_tag.find_previous("h2").get("id"),
                                                cnav=f'snav{self.s_nav_count:02}')

                elif re.search(r'^\[Preamble]|^CONSTITUTION\s*OF THE|^PREAMBLE', li_tag.text.strip()):
                    self.c_nav_count = 1
                    tag_text = re.sub(r'[\W\s]+', '', li_tag.text.strip()).lower()
                    self.set_chapter_section_id(li_tag, tag_text,
                                                sub_tag='-',
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
                    self.c_nav_count = 2

                elif paragraph_pattern.search(li_tag.text.strip()):
                    self.s_nav_count += 1
                    prev_h3_tag = li_tag.find_previous(
                        lambda tag: tag.name in ['h3'] and re.search(r'^Section [IVX]+', tag.text.strip())).get("id")
                    self.set_chapter_section_id(li_tag,
                                                paragraph_pattern.search(li_tag.text.strip()).group("id").zfill(2),
                                                sub_tag='p',
                                                prev_id=prev_h3_tag,
                                                cnav=f'cnav{self.s_nav_count:02}')

    def replace_tags_constitution(self):
        paragraph_pattern = re.compile(r'^Paragraph (?P<id>[IVX]+(-[A-Z])?)')
        amend_pattern = re.compile(r'^\[?Amendment (?P<id>[IVX]+)]?')

        if int(self.release_number) in [85, 84, 83, 82, 81]:
            for rename_class_tag in self.soup.find_all():
                if rename_class_tag.get("class") == [self.tag_type_dict["head2"]]:
                    if self.regex_pattern_obj.section_pattern_con.search(rename_class_tag.text.strip()):
                        pos = rename_class_tag.attrs['class'].index(self.tag_type_dict["head2"])
                        rename_class_tag.attrs['class'][pos] = self.tag_type_dict["head3"]

            self.regex_pattern_obj.section_pattern_con = re.compile(r'^SEC(TION)?\.? (?P<id>([IVX]+[A-Z]?)|\d+)', re.I)

        super(GAParseHtml, self).replace_tags_constitution()

        judicial_decision_id_list: list = []
        paragraph_section_id_list: list = []
        jdecision_id = None
        alpha = None
        num_analysis_id = None
        count = 1
        h4_count = 1

        for header_tag in self.soup.find_all():
            if header_tag.name == "p":
                if header_tag.get("class") == [self.tag_type_dict["head1"]]:
                    if paragraph_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        prev_tag = header_tag.find_previous(
                            lambda tag: tag.name in ['h3'] and re.search(r'^SECTION [IVX]+', tag.text.strip())).get(
                            "id")
                        paragraph_section_id = f'{prev_tag}-p{paragraph_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                        if paragraph_section_id in paragraph_section_id_list:
                            header_tag[
                                "id"] = f'{paragraph_section_id}.{count:02}'
                            count += 1
                        else:
                            header_tag[
                                "id"] = f'{paragraph_section_id}'
                            count = 1

                        paragraph_section_id_list.append(header_tag["id"])

                elif header_tag.get("class") == [self.tag_type_dict["head2"]]:
                    if app_tag := re.search(r'^APPENDIX (?P<id>(ONE|TWO|THREE|FOUR))', header_tag.text.strip()):
                        header_tag.name = "h2"
                        header_tag[
                            "id"] = f'{header_tag.find_previous("h1").get("id")}-ap{app_tag.group("id").lower()}'

                    elif re.search(r'^\[Preamble]|^CONSTITUTION\nOF\s*THE\nSTATE OF GEORGIA|^PREAMBLE',
                                   header_tag.text.strip()):
                        header_tag.name = "h2"
                        tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                        header_tag['id'] = f'{header_tag.find_previous("h1").get("id")}-{tag_text}'

                elif header_tag.get("class") == [self.tag_type_dict["head3"]]:
                    if amend_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        header_tag[
                            "id"] = f'{header_tag.find_previous("h2").get("id")}-' \
                                    f'am{amend_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                    elif paragraph_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        prev_h3_tag = header_tag.find_previous(
                            lambda tag: tag.name in ['h3'] and re.search(r'^Section [IVX]+', tag.text.strip()))
                        header_tag[
                            "id"] = f'{prev_h3_tag.get("id")}' \
                                    f'p{paragraph_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

                    elif re.search(r'^\[Preamble]|^CONSTITUTION\nOF\s*THE\nSTATE OF GEORGIA', header_tag.text.strip()):
                        header_tag.name = "h2"
                        tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                        header_tag['id'] = f'{header_tag.find_previous("h1").get("id")}-{tag_text}'

            if header_tag.name == "h4" and header_tag.get("class") and \
                    header_tag.get("class")[0] == self.tag_type_dict["head4"] and \
                    re.search('constitution', self.input_file_name):
                if header_tag.text.strip() in self.h4_head:
                    header_tag.name = "h4"
                    header4_tag_text = re.sub(r'[\W.]+', '', header_tag.text.strip()).lower()
                    h4_tag_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'

                    if h4_tag_id in self.h4_cur_id_list:
                        header_tag['id'] = f'{h4_tag_id}.{h4_count}'
                        h4_count += 1
                    else:
                        header_tag['id'] = f'{h4_tag_id}'
                        h4_count = 1

            if header_tag.get("class") and header_tag.get("class")[0] == self.tag_type_dict["head4"]:
                if header_tag.name == "h4" and re.search(r'^JUDICIAL DECISIONS|^OPINIONS OF THE ATTORNEY GENERAL',
                                                         header_tag.text.strip(), re.I):
                    alpha_analysis_tag = None
                    jdecision_id = None

                    for tag in header_tag.find_next_siblings():
                        if int(self.release_number) <= 82 and re.search(r'^Analysis', tag.text.strip(), re.I):
                            tag.name = "li"
                            tag["class"] = "jdecisions"
                            self.recreating_tags()

                        if tag.get("class")[0] == self.tag_type_dict["ol"]:
                            if not re.search(r'^Analysis', tag.text.strip()):
                                tag.name = "li"
                                tag["class"] = "jdecisions"
                                self.judicial_decision_header_list.append(tag.text.strip())
                        else:
                            break

                elif num_analysis_tag := re.search(r'^(?P<id>\d+)\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    if jdecision_id:
                        num_analysis_id = f'{jdecision_id}{num_analysis_tag.group("id")}'
                    else:
                        num_analysis_id = f'{header_tag.find_previous("h3").get("id")}-judicialdecision{num_analysis_tag.group("id")}'

                    if num_analysis_id in judicial_decision_id_list:
                        header_tag["id"] = f'{num_analysis_id}.{count:02}'
                        count += 1
                    else:
                        header_tag["id"] = f'{num_analysis_id}'
                        count = 1
                    judicial_decision_id_list.append(header_tag["id"])
                    alpha = "A"

                elif alpha and (re.search(rf'^{alpha}\.', header_tag.text.strip())
                                or re.search(rf'^{alpha.lower()}\.', header_tag.text.strip())):
                    header_tag.name = "h5"
                    alpha_analysis_id = f'{num_analysis_id}{alpha}'
                    if alpha_analysis_id in judicial_decision_id_list:
                        header_tag["id"] = f'{alpha_analysis_id}.{count:02}'
                        count += 1
                    else:
                        header_tag["id"] = f'{alpha_analysis_id}'
                        count = 1
                    alpha = chr(ord(alpha) + 1)
                    judicial_decision_id_list.append(header_tag["id"])

                elif header_tag.text.strip() in self.judicial_decision_header_list:
                    header_tag.name = "h5"
                    p_tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    jdecision_id = f'{header_tag.find_previous("h3").get("id")}-judicialdecision-{p_tag_text}'
                    if jdecision_id in judicial_decision_id_list:
                        header_tag["id"] = f'{jdecision_id}.{count:02}'
                        count += 1
                    else:
                        header_tag["id"] = f'{jdecision_id}'
                        count = 1

                    judicial_decision_id_list.append(header_tag["id"])

            if header_tag.name == "h4" and re.search(r'^JUDICIAL DECISIONS|^OPINIONS OF THE ATTORNEY GENERAL',
                                                     header_tag.text.strip(), re.I):
                alpha_analysis_tag = None
                jdecision_id = None

                for tag in header_tag.find_next_siblings():
                    if int(self.release_number) <= 82 and re.search(r'^Analysis', tag.text.strip(), re.I):
                        tag.name = "li"
                        tag["class"] = "jdecisions"

                        self.recreating_tags()

                    if tag.get("class") and \
                            tag.get("class")[0] == self.tag_type_dict["ol"]:
                        if not re.search(r'^Analysis', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "jdecisions"
                            self.judicial_decision_header_list.append(tag.text.strip())
                    else:
                        break
