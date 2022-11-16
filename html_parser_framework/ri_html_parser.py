"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""
import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexRI
import roman
from loguru import logger


class RIParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.file_no = None

    def pre_process(self):
        """directory to store regex patterns """

        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES',
                'ul': r'^Preamble', 'head2': '^Article I',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_p': '^—', 'head4': r'Compiler’s Notes\.',
                'history': r'History of Section\.'}
            self.h2_order = ['article']
            self.h2_text_con: list = ['Articles of Amendment']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+[A-Z]?(\.\d+)?', 'ul': r'^Chapter \d+',
                                        'head2': r'^Chapter \d+', 'history': r'^History of Section\.',
                                        'head4': r'^Compiler’s Notes\.|^Repealed Sections\.',
                                        'head3': r'^\d+[A-Z]?(\.\d+)?-\d+-\d+',
                                        'junk1': '^Text|^Annotations', 'ol_p': r'^\([A-Z a-z0-9]\)'}
            self.file_no = re.search(r'gov\.ri\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if self.file_no in ['02', '31', '44', '07']:
                self.h2_order = ['chapter', 'part']
            elif self.file_no in ['06A']:
                self.h2_order = ['chapter', 'part', 'subpart']
            elif self.file_no in ['21', '42', '34']:
                self.h2_order = ['chapter', 'article']
            elif self.file_no in ['15', '23', '07']:
                self.h2_order = ['chapter', 'article', 'part']
            else:
                self.h2_order = ['chapter']
            if self.release_number == '73' and self.file_no in ['07']:
                self.h2_order = ['chapter', 'article', 'part', 'subpart']
            self.h2_pattern_text: list = [r'^(?P<tag>C)hapters (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)']

        self.h4_head: list = ['Compiler’s Notes.', 'History of Section', 'Compiler\'s Notes.',
                              'Variations from Uniform Code.', 'Comparative Provisions.', 'Obsolete Sections.',
                              'Omitted Sections.', 'Reserved Sections.', 'Compiler\'s Notes', 'Cross References.',
                              'Subsequent Reenactments.', 'Abridged Life Tables and Tables of Work Life Expectancies.',
                              'Definitional Cross References.', 'Contingent Effective Dates.',
                              'Comparative Legislation.', 'Sunset Provision.',
                              'Sunset Provisions.', 'Legislative Findings.', 'Contingently Repealed Sections.',
                              'Transferred Sections.', 'Collateral References.', 'NOTES TO DECISIONS',
                              'Retroactive Effective Dates.', 'Repealed Sections.',
                              'Effective Dates.', 'Law Reviews.', 'Rules of Court.', 'OFFICIAL COMMENT',
                              'Superseded Sections.', 'Repeal of Sunset Provision.', 'Legislative Findings and Intent.',
                              'Official Comment.', 'Official Comments', 'Repealed and Reenacted Sections.',
                              'COMMISSIONER’S COMMENT', 'Comment.', 'History of Amendment.',
                              'Federal Act References.', 'Reenactments.', 'Severability.', 'Delayed Effective Dates.',
                              'Delayed Effective Date.', 'Delayed Repealed Sections.']

        self.watermark_text = """Release {0} of the Official Code of Rhode Island Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
                """
        self.regex_pattern_obj = CustomisedRegexRI()

    def replace_tags_titles(self):

        notes_to_decision_list: list = []
        count = 1
        schedule_pattern = re.compile(r'^Schedule (?P<id>[IVX]+)', re.I)
        notetag_id = None
        note_tag_id = None

        super(RIParseHtml, self).replace_tags_titles()
        for p_tag in self.soup.find_all():
            if p_tag.get("class") == [self.tag_type_dict["head4"]] and p_tag.name == "p":
                if p_tag.text.strip() in notes_to_decision_list:
                    p_tag.name = "h5"
                    p_tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                    if re.search(r'^—\s?[\w“]+', p_tag.text.strip()):
                        note_tag_id = f'{notetag_id}-{p_tag_text}'
                        if note_tag_id in notes_to_decision_list:
                            p_tag["id"] = f'{note_tag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{note_tag_id}'
                            count = 1
                    elif re.search(r'^— —\s?[\w“]+', p_tag.text.strip()):
                        inner_note_tag_id = f'{note_tag_id}-{p_tag_text}'
                        if inner_note_tag_id in notes_to_decision_list:
                            p_tag["id"] = f'{inner_note_tag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{inner_note_tag_id}'
                            count = 1
                    else:
                        notetag_id = f'{p_tag.find_previous("h3").get("id")}-notestodecisions-{p_tag_text}'
                        if notetag_id in notes_to_decision_list:
                            p_tag["id"] = f'{notetag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{notetag_id}'
                            count = 1

                    notes_to_decision_list.append(p_tag["id"])

            elif p_tag.get("class") == [self.tag_type_dict["history"]] and p_tag.name == "p":
                if article_tag := self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}a' \
                                  f'{self.regex_pattern_obj.h2_article_pattern.search(p_tag.text.strip()).group("id")}'

                elif schedule_pattern.search(p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}a' \
                                  f'{schedule_pattern.search(p_tag.text.strip()).group("id")}'

            if p_tag.name == "h4" and re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                                p_tag.text.strip(), re.I):
                for tag in p_tag.find_next_siblings():
                    if tag.get("class") == [self.tag_type_dict["history"]]:
                        if not re.search(r'^(Analysis|Cited|Compiler’s Notes\.)', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            notes_to_decision_list.append(tag.text.strip())
                    else:
                        break
        self.recreate_tag()

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_Notes_to_decision_analysis_nav_tag_con()
        else:
            self.create_Notes_to_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")

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
        small_roman = "i"
        main_sec_alpha1 = 'a'
        cap_alpha1 = 'A'
        sec_alpha = "a"

        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        roman_ol = self.soup.new_tag("ol", type="i")
        sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
        num_ol1 = self.soup.new_tag("ol")
        cap_roman_ol = self.soup.new_tag("ol", type="I")

        cap_alpha_cur_tag = None
        sec_alpha_cur_tag = None
        num_cur_tag = None
        previous_li_tag = None
        small_roman_tag = None
        cap_roman_cur_tag = None

        inner_num_count = None
        sec_alpha_id = None
        prev_num_id = None
        sec_alpha_id1 = None
        num_id1 = None
        num_id = None
        cap_alpha_id = None
        prev_id = None

        for p_tag in self.soup.body.find_all(['h2', 'h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()

            if re.search(rf'^\({small_roman}\)', current_tag_text) and (
                    num_cur_tag or sec_alpha_cur_tag or cap_roman_cur_tag):
                p_tag.name = "li"
                small_roman_tag = p_tag
                cap_rom = "I"

                if re.search(r'^\(i\)', current_tag_text):
                    if re.search(r'^\(j\)|History of Section|^\(1\)',p_tag.find_next_sibling("p", class_=self.tag_type_dict["history"]).text.strip()) or \
                            (re.search(r'^\(2\)', p_tag.find_next_sibling("p", class_=self.tag_type_dict["history"]).text.strip()) and inner_num_count != 2):
                        sec_alpha_ol.append(p_tag)
                        p_tag["id"] = f'{sec_alpha_id}i'
                        p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                        main_sec_alpha = "j"
                        num_count = 1
                    else:
                        roman_ol = self.soup.new_tag("ol", type="i")
                        p_tag.wrap(roman_ol)

                        if cap_roman_cur_tag or num_cur_tag or sec_alpha_cur_tag or cap_alpha_cur_tag:
                            if re.search(r'ol', p_tag.find_previous("li").get("id")) and previous_li_tag:
                                prev_num_id = p_tag.find_previous("li").get("id")
                                p_tag.find_previous("li").append(roman_ol)

                        p_tag["id"] = f'{prev_num_id}{small_roman}'
                        p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                        small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()
                else:
                    roman_ol.append(p_tag)

                    p_tag["id"] = f'{prev_num_id}{small_roman}'
                    p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                    small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                if not re.search(r'ol\d\w+\d+[A-Z]i$|ol\d[a-z]\d+[A-Z]\d+\w*$', p_tag.parent.find_next("li").get("id")):
                    cap_alpha = "A"
                if not re.search(r'ol\d[a-z]\d+[A-Z]\d+\w*$|ol\d[a-z][ivx]+\d[ivx]+$|ol\d[a-z]\d+\w*$',
                                 p_tag.parent.find_next("li").get("id")):
                    inner_num_count = 1

                if re.search(r'^\([ivx]+\)\s*\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivx]+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cap_alpha_id = f'{small_roman_tag.get("id")}'
                    li_tag["id"] = f'{cap_alpha_id}A'
                    cap_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"

                if re.search(r'^\([ivx]+\)\s*\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\(1\)', '', current_tag_text)
                    num_cur_tag = li_tag
                    num_id = f'{small_roman_tag.get("id")}'
                    li_tag["id"] = f'{num_id}1'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    num_count = 2
                previous_li_tag = p_tag

            elif re.search(rf'^\({main_sec_alpha1}\)', current_tag_text) and p_tag.name == "p" and sec_alpha_cur_tag:
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                sec_alpha = "a"
                small_roman = "i"

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)
                    if num_cur_tag or cap_roman_cur_tag:
                        sec_alpha_id1 = p_tag.find_previous("li").get("id")
                        p_tag.find_previous("li").append(sec_alpha_ol1)

                    else:
                        sec_alpha_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha1}\)', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

                if re.search(r'^\(\w\)\s*\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\(1\)', '', current_tag_text)
                    num_cur_tag = li_tag
                    num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_id}1'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    num_count = 2

                if re.search(r'^\(\w\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\w\)\s*\(i\)', '', current_tag_text)
                    small_roman_tag = li_tag
                    prev_num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    small_roman = 'ii'
                    cap_alpha = "A"
                previous_li_tag = p_tag

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                sec_alpha = "a"
                small_roman = "i"
                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_cur_tag.get("id")
                    elif cap_roman_cur_tag:
                        cap_roman_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = cap_roman_cur_tag.get("id")
                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if alpha_tag := re.search(r'^\(c\) — \((?P<alpha>f)\) \[Deleted', current_tag_text):
                    main_sec_alpha = chr(ord(alpha_tag.group("alpha")) + 1)

                if not re.search(r'ol\d\d+[a-z]$|ol\d[A-Z]\d[a-z]$|ol\d[a-z]\d+[A-Za-z]\d?$',
                                 p_tag.parent.find_next("li").get("id")):
                    num_count = 1

                if re.search(r'^\(\w\)\s*\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\w\)\s*\(1\)', '', current_tag_text)
                    num_cur_tag = li_tag
                    num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_id}1'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    num_count = 2

                if re.search(r'^\(\w\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\w\)\s*\(i\)', '', current_tag_text)
                    small_roman_tag = li_tag
                    prev_num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    small_roman = 'ii'
                    cap_alpha = "A"

                previous_li_tag = p_tag

            elif re.search(rf'^\({inner_num_count}\)', current_tag_text) and p_tag.name == "p" and (
                    num_cur_tag or sec_alpha_cur_tag or cap_alpha_cur_tag):
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha1 = 'a'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag or cap_alpha_cur_tag:
                        if re.search(r'ol', p_tag.find_previous("li").get("id")) and previous_li_tag:
                            num_id1 = p_tag.find_previous("li").get("id")
                            p_tag.find_previous("li").append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                        main_sec_alpha = 'a'
                        cap_alpha = "A"
                        small_roman = "i"
                else:
                    num_ol1.append(p_tag)
                    if not re.search(r'ol\d[a-z]\d+[A-Z]\d+$|ol\d[A-Z][ivx]+\d+$|ol\d[a-z]\d+$|ol\d+[a-z][ivx]+\d',
                                     p_tag.parent.find_next("li").get("id")):
                        cap_alpha = "A"
                        small_roman = "i"
                    if not re.search(r'ol\d\d+[a-z][ivx]+\d?$|ol\d[a-z]\w*\d?$',
                                     p_tag.parent.find_next("li").get("id")):
                        main_sec_alpha = "a"

                p_tag["id"] = f'{num_id1}{inner_num_count}'
                p_tag.string = re.sub(rf'^\({inner_num_count}\)', '', current_tag_text)
                inner_num_count += 1
                previous_li_tag = p_tag

                if re.search(r'^\(\d+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\d+\)\s*\(i\)', '', current_tag_text)
                    small_roman_tag = li_tag
                    prev_num_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    small_roman = 'ii'
                    cap_alpha = "A"

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = "A"
                small_roman = "i"
                main_sec_alpha1 = "a"
                inner_num_count = None

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol", type="1")
                    p_tag.wrap(num_ol)
                    if sec_alpha_cur_tag or small_roman_tag or cap_alpha_cur_tag:
                        if p_tag.find_previous("li").get("id") and \
                                re.search(r'ol', p_tag.find_previous("li").get("id")) and previous_li_tag:
                            num_id = p_tag.find_previous("li").get('id')
                            p_tag.find_previous("li").append(num_ol)
                        else:
                            num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                    else:
                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    num_ol.append(p_tag)
                    if not re.search(r'ol\d[a-z]\d+$|ol\d[a-z]$|ol\d[A-Z][ivx]+$|ol\d\d+[a-z][ivx]+\d?$',
                                     p_tag.parent.find_next("li").get("id")):
                        main_sec_alpha = "a"
                        small_roman = "i"
                    if not re.search(r'ol\d[A-Z]\d+$|ol\d[a-z]\d+[A-Z]\d+$', p_tag.parent.find_next("li").get("id")):
                        cap_alpha = "A"

                p_tag["id"] = f'{num_id}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1
                previous_li_tag = p_tag

                if re.search(r'^\(\d+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\d+\)\s*\(i\)', '', current_tag_text)
                    small_roman_tag = li_tag
                    prev_num_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    small_roman = 'ii'
                    cap_alpha = "A"

                if re.search(r'^\(\d+\)\s*\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\d+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cap_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}A'
                    cap_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"

                if re.search(r'^\(\d+\)\s*\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\d+\)\s*\(a\)', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    sec_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = 'b'

                    if re.search(r'^\(\d+\)\s*\(\w\)\s?\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s?\(i\)', '', current_tag_text)
                        small_roman_tag = inner_li_tag
                        prev_num_id = f'{sec_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}i'
                        roman_ol.append(inner_li_tag)
                        sec_alpha_cur_tag.string = ""
                        sec_alpha_cur_tag.append(roman_ol)
                        small_roman = "ii"
                        main_sec_alpha = 'b'

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                cap_rom = "I"
                inner_num_count = 1

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    if num_cur_tag or small_roman_tag:
                        if re.search(r'ol', p_tag.find_previous("li").get("id")) and previous_li_tag:
                            cap_alpha_id = p_tag.find_previous("li").get("id")
                            p_tag.find_previous("li").append(cap_alpha_ol)
                        else:
                            cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                    else:
                        cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                if cap_alpha == "Z":
                    cap_alpha = "A"
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)
                previous_li_tag = p_tag

                if re.search(r'ol\d[A-Z]$', p_tag.parent.find_next("li").get("id")):
                    num_count = 1

                if re.search(r'^\(\w\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\(\w\)\s*\(i\)', '', current_tag_text)
                    small_roman_tag = li_tag
                    prev_num_id = f'{cap_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)
                    small_roman = 'ii'

            elif re.search(rf'^\({sec_alpha}{sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1
                sec_alpha_ol.append(p_tag)
                sec_alpha_tag = re.search(r'^\((?P<id>[a-z][a-z])\)', current_tag_text)
                p_tag["id"] = f'{sec_alpha_id}{sec_alpha_tag.group("id")}'
                p_tag.string = re.sub(r'^\([a-z][a-z]\)', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)
                inner_num_count = None

            elif re.search(rf'^\({cap_alpha1}{cap_alpha1}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                cap_rom = "I"
                inner_num_count = None
                cap_alpha_ol.append(p_tag)
                cap_alpha_tag1 = re.search(r'^\((?P<id>[A-Z][A-Z])\)', current_tag_text)
                p_tag["id"] = f'{cap_alpha_id}{cap_alpha_tag1.group("id")}'
                p_tag.string = re.sub(r'^\([A-Z][A-Z]\)', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)

            elif re.search(rf'^{ol_head}\.', current_tag_text) and \
                    p_tag.name == "p" and p_tag.get("class") != "casenote":
                p_tag.name = "li"
                num_cur_tag = p_tag
                inner_num_count = None

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(num_ol)
                        num_id = sec_alpha_cur_tag.get("id")
                    else:
                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                else:
                    num_ol.append(p_tag)
                p_tag["id"] = f'{num_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1
                ol_head1 += 1
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_rom}\)', current_tag_text):
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag
                inner_num_count = None

                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    if cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(cap_roman_ol)
                        prev_id = cap_alpha_cur_tag.get("id")
                    elif small_roman_tag:
                        small_roman_tag.append(cap_roman_ol)
                        prev_id = small_roman_tag.get("id")
                    else:
                        prev_id = p_tag.find_previous({"h5", "h4", "h3"}).get("id")
                else:
                    cap_roman_ol.append(p_tag)
                p_tag["id"] = f'{prev_id}ol{ol_count}{cap_rom}'
                p_tag.string = re.sub(rf'^\({cap_rom}\)', '', current_tag_text)
                cap_rom = roman.toRoman(roman.fromRoman(cap_rom.upper()) + 1)
                previous_li_tag = p_tag

            elif p_tag.name == "p" and p_tag.get("class") and p_tag.get("class") == [self.tag_type_dict['history']] \
                    and previous_li_tag:
                if not re.search(r'^History of Section\.|^Cross references:|^Click to view',
                                 current_tag_text) and self.file_no != '44':
                    previous_li_tag.append(p_tag)
                    inner_num_count = 1
                    ol_count += 1

            if re.search(r'^History of Section|^History\.|^Cross references:|^Section \d+\.',
                         current_tag_text) or p_tag.name in ['h3','h4','h5']:
                ol_count = 1
                ol_head = 1
                ol_head1 = 1
                cap_alpha = 'A'
                num_count = 1
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                cap_alpha1 = "A"
                cap_rom = "I"
                small_roman = "i"
                sec_alpha = "a"
                previous_li_tag = None
                cap_roman_cur_tag = None
                cap_alpha_cur_tag = None
                num_cur_tag = None
                sec_alpha_cur_tag = None
                inner_num_count = None

        print('ol tags added')

    def recreate_tag(self):
        for r_tag in self.soup.find_all(class_=self.tag_type_dict['history']):
            if new_tag := re.search(r'^(?P<text>Section\s(?P<id>\d+)\.\s[^.]+\.)', r_tag.text.strip()):
                new_p_tag = self.soup.new_tag("p")
                new_p_tag.string = re.sub(r'^Section\s\d+\.\s[^.]+\.', '', r_tag.text.strip())
                r_tag.string = new_tag.group("text")
                r_tag.name = "h5"
                r_tag["id"] = f'{r_tag.find_previous("h4").get("id")}s{new_tag.group("id")}'
                r_tag.insert_after(new_p_tag)

    def replace_tags_constitution(self):
        notetag_id = None
        count = None
        note_tag_id = None
        notes_to_decision_list = []

        for li_tag in self.soup.findAll(class_=self.tag_type_dict["ul"]):
            if not re.search(r'^article ', li_tag.text.strip(), re.I):
                li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                self.h2_text_con.append(li_tag_text)

        super(RIParseHtml, self).replace_tags_constitution()
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4" and re.search(r'^NOTES TO DECISIONS$|^Notes to Unpublished Decisions$',
                                                p_tag.text.strip(), re.I):
                for tag in p_tag.find_next_siblings():
                    if tag.get("class") == [self.tag_type_dict["ol_of_p"]]:
                        if not re.search(r'^(Analysis|Cited|Compiler’s Notes\.)', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            notes_to_decision_list.append(tag.text.strip())
                    else:
                        break
            elif p_tag.get("class") == [self.tag_type_dict["head4"]] and p_tag.name == "p":
                if p_tag.text.strip() in notes_to_decision_list:
                    p_tag.name = "h5"
                    p_tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                    if re.search(r'^—\s?[\w“]+', p_tag.text.strip()):
                        note_tag_id = f'{notetag_id}-{p_tag_text}'
                        if note_tag_id in notes_to_decision_list:
                            p_tag["id"] = f'{note_tag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{note_tag_id}'
                            count = 1
                    elif re.search(r'^— —\s*[\w“]+', p_tag.text.strip()):
                        inner_note_tag_id = f'{note_tag_id}-{p_tag_text}'
                        if inner_note_tag_id in notes_to_decision_list:
                            p_tag["id"] = f'{inner_note_tag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{inner_note_tag_id}'
                            count = 1
                    else:
                        notetag_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notestodecisions-{p_tag_text}'
                        if notetag_id in notes_to_decision_list:
                            p_tag["id"] = f'{notetag_id}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{notetag_id}'
                            count = 1
                    notes_to_decision_list.append(p_tag["id"])

            elif p_tag.get("class") == [self.tag_type_dict["head2"]] and p_tag.name == "p":
                if re.search(r'^Articles of Amendment', p_tag.text.strip()):
                    p_tag.name = "h2"
                    p_tag[
                        "id"] = f'{p_tag.find_previous("h1").get("id")}-{re.sub(r" +", "", p_tag.text.strip()).lower()}'
