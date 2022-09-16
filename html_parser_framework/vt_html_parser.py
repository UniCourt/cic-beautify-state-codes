import re
from base_html_parser import ParseHtml
import roman
from regex_pattern import CustomisedRegexVT


class VTParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.file_no = None
        self.h2_pattern_text = None

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'ul': r'^Chapter I|^PREAMBLE|I\.',
                                        'head1': '^Constitution of the United States|'
                                                 'CONSTITUTION OF THE STATE OF VERMONT',
                                        'head2': '^CHAPTER I|^PREAMBLE', 'head3': r'^§ 1\.|^Section \d+\.',
                                        'junk1': '^Annotations',
                                        'article': '——————————', 'head4_1': '^1\.', 'head4': '^ANNOTATIONS',
                                        'ol_p': r'^Analysis', }
            if self.release_number == '84' and re.search(r'us\.html$', self.input_file_name):
                self.h2_order: list = ['chapter', '', '', '', '']
            elif self.release_number == '85' and re.search(r'vt\.html$', self.input_file_name):
                self.h2_order: list = ['chapter', '', '', '', '']
            elif re.search(r'vt\.html$', self.input_file_name):
                self.h2_order: list = ['chapter', '', '', '', '']
            else:
                self.h2_order: list = ['article', 'amendment', '', '', '']

            self.h2_pattern_text: list = ['PREAMBLE', 'DELEGATION AND DISTRIBUTION OF POWERS',
                                          'LEGISLATIVE DEPARTMENT', 'EXECUTIVE DEPARTMENT',
                                          'JUDICIARY DEPARTMENT', 'QUALIFICATIONS OF FREEMEN AND FREEWOMEN',
                                          'ELECTIONS; OFFICERS; TERMS OF OFFICE', 'OATH OF ALLEGIANCE; OATH OF OFFICE',
                                          'IMPEACHMENT', 'MILITIA', 'GENERAL PROVISIONS',
                                          'AMENDMENT OF THE CONSTITUTION',
                                          'TEMPORARY PROVISIONS', '']
        else:
            if int(self.release_number) >= int('84'):
                self.tag_type_dict: dict = {'ul': r'^(Chapter|Article)\s*\d+\.', 'head2': r'^(CHAPTER|Article) \d+\.',
                                            'head1': r'^TITLE',
                                            'head3': r'^§ \d+((-|—)\d+)*\.', 'junk1': '^Annotations',
                                            'article': '——————————',
                                            'ol_p': r'^\(A\)', 'head4': '^History'}
            else:
                self.tag_type_dict: dict = {'ul': r'^\d+\.', 'head2': r'^CHAPTER \d+\.',
                                            'head1': r'^TITLE \d',
                                            'head3': r'^§ \d+(-\d+)*\.', 'junk1': '^Annotations',
                                            'article': '——————————',
                                            'ol_p': r'^\(A\)', 'head4': '^History', 'analysishead': r'^\d+\.',
                                            'part': r'^PART \d'}

            self.file_no = re.search(r'gov\.vt\.vsa\.title\.(?P<fno>\w+)\.html', self.input_file_name).group("fno")

            if int(self.release_number) <= 83 and self.file_no in ['11C', '09A', '27A']:
                self.tag_type_dict['head2'] = r'^ARTICLE \d'

            if self.file_no in ['18', '05', '03', '10', '09', '08', '06', '12', '13', '14', '16', '20', '16A',
                                '24', '24A', '33', '30', '29']:
                self.h2_order: list = ["part", "chapter", 'subchapter', 'article', '']

            elif self.file_no in ['27A'] and self.release_number == '84':
                self.h2_order: list = ["part", "article", '', '', '']

            elif self.file_no in ['09A', '11C', '27A']:
                self.h2_order: list = ["article", "part", '', '', '']

            elif self.file_no in ['32']:
                if int(self.release_number) <= 83:
                    self.h2_order: list = ["subtitle", "part", 'chapter', 'subchapter', 'article', '', '']
                else:
                    self.h2_order: list = ["subtitle", 'chapter', 'subchapter', 'article', '', '']
                self.h2_rename_pattern = [r'^(?P<tag>Part)\s*(?P<id>\d+)', r'^(?P<tag>Chapter) (?P<id>\d{3})\.']

            else:
                self.h2_order: list = ["chapter", 'subchapter', 'article', 'part', '']

            self.h2_text: list = ['Regulations Chapter 1. Game', 'Title Five Tables',
                                  'Table 2 Derivation of Sections',
                                  'Aeronautics and Surface Transportation Generally', 'Executive Orders']

        self.h2_pattern_text = [r'^(?P<tag>Part)\s*(?P<id>\d+)']

        if self.file_no == '14':
            self.h2_rename_pattern = [r'^(?P<tag>Part) (?P<id>\d)\. Receipts',
                                      r'^(?P<tag>S)ubchapter (?P<id>5). Allocation of Disbursements During '
                                      r'Administration of Trust', '^(?P<tag>C)hapter (?P<id>119). Uniform Management '
                                                                  r'of Institutional Funds Act',
                                      r'^(?P<tag>C)hapter (?P<id>120). Uniform Prudent Management of Institutional '
                                      r'Funds Act', '^(?P<tag>C)hapter (?P<id>121). Durable Power of '
                                                    'Attorney for Health Care',
                                      '^(?P<tag>C)hapter (?P<id>123). Powers of Attorney',
                                      '^(?P<tag>C)hapter (?P<id>125). Vermont Revised Uniform Fiduciary Access to '
                                      'Digital Assets Act'
                                      ]
        elif self.file_no == '24A':
            self.h2_rename_pattern = [r'^§ (?P<id>1401)\.(?P<tag>Boundaries)']

        if self.file_no == '03A':
            self.tag_type_dict['head3'] = r'^Executive Order No\. \d-\d'

        self.h4_head: list = ['OFFICIAL COMMENT','History', 'Compiler’s Notes.', 'CROSS REFERENCES', 'ANNOTATIONS', 'Notes to Opinions']

        self.watermark_text = """Release {0} of the Official Code of Vermont Annotated released {1}.
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexVT()

    def replace_tags_titles(self):

        if int(self.release_number) <= 83:
            if self.file_no in ['09A', '27A']:
                title_tag = self.soup.find("p", class_=self.tag_type_dict["head2"])
                self.replace_h1_tags_titles(title_tag)
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            if self.file_no in ['03']:
                h2_title_tag_pattern = re.compile(r'^TITLE\s*3\s*Executive\s*Appendix\s*(?P<id>Executive Orders)')
                for h2_title_tag in self.soup.find_all("p", class_=self.tag_type_dict['head2']):
                    if h2_title_tag_pattern.search((h2_title_tag.text.strip())):
                        h2_title_tag.name = "h2"
                        h2_title_tag["class"] = "oneh2"
                        h2_title_tag['id'] = f't{self.file_no}-executiveorders'
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            for rename_class_tag in self.soup.find_all("p", class_=self.tag_type_dict["ol_p"]):
                if self.regex_pattern_obj.rename_class_section_pattern.search(rename_class_tag.text.strip()):
                    pos = rename_class_tag.attrs['class'].index(self.tag_type_dict["ol_p"])
                    rename_class_tag.attrs['class'][pos] = self.tag_type_dict["head3"]
            for rename_class_tag in self.soup.find_all("p", class_=self.tag_type_dict["article"]):
                if self.regex_pattern_obj.h2_chapter_pattern.search(rename_class_tag.text.strip()):
                    pos = rename_class_tag.attrs['class'].index(self.tag_type_dict["article"])
                    rename_class_tag.attrs['class'][pos] = self.tag_type_dict["head2"]
                elif self.regex_pattern_obj.h2_subchapter_pattern.search(
                        rename_class_tag.text.strip()) and self.file_no == '20' \
                        and not rename_class_tag.text.strip().isupper():
                    pos = rename_class_tag.attrs['class'].index(self.tag_type_dict["article"])
                    rename_class_tag.attrs['class'][pos] = self.tag_type_dict["head1"]

        super(VTParseHtml, self).replace_tags_titles()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_alpha_id = None
        h5_rom_id = None
        cap_roman_tag = None
        annotation_id = None
        analysis_id1 = None
        annotation_text_list: list = []
        annotation_id_list: list = []
        h5_count = 1
        subtitle_nav_tag = None
        h4_pattern = re.compile(r'Annotations From Former §*? \d+')

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if h4_pattern.search(header_tag.text.strip()):
                    self.replace_h4_tag_titles(header_tag, self.h4_count)
                if re.search(r'^CASE NOTES$|^Analysis$|^ANNOTATIONS$', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_roman_tag = None
                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    cap_roman_tag = header_tag
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecisison-{h5_rom_text}'

                    if h5_rom_id in annotation_id_list:
                        header_tag["id"] = f'{h5_rom_id}.{h5_count}'
                        h5_count += 1
                    else:
                        header_tag["id"] = f'{h5_rom_id}'
                        h5_count = 1

                    annotation_id_list.append(h5_rom_id)
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

                elif re.search(r'^0\.5\.\s[a-zA-Z]+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    header_tag['id'] = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-annotation-0.5'

                elif annotation_id and re.search(r'^—[a-zA-Z]+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    tag_text = re.sub(r'[\W\s.]+', '', header_tag.text.strip()).lower()
                    inner_head_id = f'{annotation_id}-{tag_text}'
                    if inner_head_id in annotation_id_list:
                        header_tag["id"] = f'{inner_head_id}.{h5_count}'
                        h5_count += 1
                    else:
                        header_tag["id"] = f'{inner_head_id}'
                        h5_count = 1
                    annotation_id_list.append(inner_head_id)

                else:
                    annotation_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    if annotation_text in annotation_text_list and re.search(r'^ANNOTATIONS$', header_tag.find_previous(
                            "h4").text.strip()):
                        header_tag.name = "h5"
                        if cap_roman_tag:
                            annotation_id = f'{cap_roman_tag.get("id")}-{annotation_text}'
                        else:
                            annotation_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{annotation_text}'

                        if annotation_id in annotation_id_list:
                            header_tag["id"] = f'{annotation_id}.{h5_count}'
                            h5_count += 1
                        else:
                            header_tag["id"] = f'{annotation_id}'
                            h5_count = 1
                        annotation_id_list.append(annotation_id)

            if re.search(r'^Analysis$|^ANNOTATIONS$', header_tag.text.strip(), re.I):
                for tag in header_tag.find_next_siblings():
                    if int(self.release_number) >= 84:
                        if tag.get('class') == [self.tag_type_dict["head4"]]:
                            break
                        else:
                            tag["class"] = "casenote"
                            annotation_text_list.append(re.sub(r'[\W\s]+', '', tag.text.strip()).lower())

            if int(self.release_number) <= 83 and header_tag.get("class") == [self.tag_type_dict["analysishead"]]:
                if header_tag.find_previous("h4") and not h4_pattern.search(
                        header_tag.find_previous("h4").text.strip()):
                    previous_header_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-annotation'
                else:
                    previous_header_id = header_tag.find_previous({"h4", "h3", "h2", "h1"}).get("id")

                if re.search(r'^0\.5\.\s[a-zA-Z]+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    header_tag['id'] = f'{previous_header_id}-0.5'

                elif re.search(r'^\d{1,2}\.', header_tag.text.strip()) and not \
                        re.search(r'^OFFICIAL COMMENT',header_tag.find_previous("h4").text.strip()):
                    header_tag.name = "h5"
                    analysis_id = re.search(r'^(?P<a_id>\d{1,2})\.', header_tag.text.strip()).group("a_id")
                    analysis_id1 = f"{previous_header_id}-{analysis_id}"

                    if analysis_id1 in annotation_id_list:
                        header_tag["id"] = f'{analysis_id1}.{h5_count}'
                        h5_count += 1
                    else:
                        header_tag["id"] = f'{analysis_id1}'
                        h5_count = 1

                elif re.search(r'^\*\d{1,2}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    analysis_id = re.sub(r'[\W\d]', '', header_tag.text.strip()).lower()
                    header_id = f"{analysis_id1}-{analysis_id}"

                    if header_id in annotation_id_list:
                        header_tag["id"] = f'{header_id}.{h5_count}'
                        h5_count += 1
                    else:
                        header_tag["id"] = f'{header_id}'
                        h5_count = 1

                annotation_id_list.append(header_tag.get("id"))

            if (self.file_no in ['27A', '09A'] and self.regex_pattern_obj.h2_part_pattern.search(
                    header_tag.text.strip()) and header_tag.name == "p") or \
                    (self.regex_pattern_obj.h2_part_pattern.search(
                        header_tag.text.strip()) and header_tag.name == "p" and header_tag.text.strip().isupper()):
                header_tag["class"] = "navhead"
                if subtitle_nav_tag:
                    header_tag[
                        "id"] = f'{subtitle_nav_tag.get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'
                else:
                    header_tag[
                        "id"] = f'{header_tag.find_previous({"h1", "h2"}).get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

            if self.regex_pattern_obj.h2_subchapter_pattern.search(header_tag.text.strip()) and header_tag.name == "p":
                header_tag["class"] = "navhead"
                header_tag[
                    "id"] = f'{header_tag.find_previous("h2").get("id")}s{self.regex_pattern_obj.h2_subchapter_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

            if self.regex_pattern_obj.h2_subtitle_pattern.search(header_tag.text.strip()) and header_tag.name == "p":
                subtitle_nav_tag = header_tag
                header_tag["class"] = "navhead"
                header_tag[
                    "id"] = f'{header_tag.find_previous("h1").get("id")}s{self.regex_pattern_obj.h2_subtitle_pattern.search(header_tag.text.strip()).group("id").zfill(2)}'

    def add_anchor_tags(self):
        super(VTParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.find_all("li"):
            if not li_tag.get("id") and re.search(r'^Part \d+\.', li_tag.text.strip()):
                chap_num = re.search(r'^Part (?P<id>\d+)\.', li_tag.text.strip()).group("id")
                self.c_nav_count += 1
                self.set_chapter_section_id(li_tag, chap_num,
                                            sub_tag="p",
                                            prev_id=li_tag.find_previous("h1").get("id"),
                                            cnav=f'cnav{self.c_nav_count:02}')

            elif not li_tag.get("id") and re.search(r'^Executive Order No\. (?P<id>\d+-\d+)', li_tag.text.strip()):
                chap_num = re.search(r'^Executive Order No\. (?P<id>\d+-\d+)', li_tag.text.strip()).group("id")
                self.c_nav_count += 1
                self.set_chapter_section_id(li_tag, chap_num,
                                            sub_tag="s",
                                            prev_id=li_tag.find_previous("h2").get("id"),
                                            cnav=f'cnav{self.c_nav_count:02}')

            if int(self.release_number) <= 83 and self.file_no in ['27A', '09A'] and \
                    li_tag.a.text.strip() in ['1.', '2.', '3.', '4.', '2A.', '4A.', '5.', '6.', '7.', '8.', '9.']:
                li_tag["id"] = str(li_tag.get("id")).replace('c', 'a')
                li_tag.a["href"] = str(li_tag.a.get("href")).replace('c', 'a')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        inner_alpha = 'a'
        num_count = 1
        inner_num_count = 1
        num_ol = self.soup.new_tag("ol")
        roman_ol = self.soup.new_tag("ol", type="i")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        num_ol1 = self.soup.new_tag("ol")
        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
        inner_num_ol = self.soup.new_tag("ol")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        cap_roman_ol = self.soup.new_tag("ol", type="I")
        cap_roman_ol1 = self.soup.new_tag("ol", type="I")
        alpha_ol1 = self.soup.new_tag("ol", type="a")
        cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
        ol_count = 1
        sec_alpha_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha = 'A'
        cap_alpha1 = 'A'
        cap_alpha2 = 'A'
        small_roman = "i"
        cap_rom = "I"
        inner_cap_rom = "I"
        sec_alpha_id = None
        prev_id1 = None
        num_id = None
        cap_alpha_id = None
        cap_alpha_id1 = None
        num_tag = None
        previous_li_tag = None
        cap_roman_cur_tag = None
        num_id1 = None
        inner_num_cur_tag = None
        cap_roman_cur_tag1 = None
        cap_alpha_cur_tag = None
        roman_cur_tag = None
        prev_id_rom = None
        inner_sec_alpha_id = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()
            if re.search(rf'^\({small_roman}\)', current_tag_text) and cap_alpha_cur_tag1:
                p_tag.name = "li"
                roman_cur_tag = p_tag
                cap_rom = "I"
                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    prev_class = p_tag.find_previous({'h4', 'h3'}).get("class")
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
                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                if re.search(rf'^\([ivx]+\)\s*\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivx]+\)\s*\(I\)', '', current_tag_text)
                    cap_roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[ivx]+)\)\s*\((?P<pid>I)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}{cur_tag1.group("pid")}'
                    cap_roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_roman_ol)
                previous_li_tag = p_tag

            elif re.search(r'^\d{0,2}\.\d+(\.\d+)*', current_tag_text) and p_tag.name == 'p':
                p_tag.name = "li"
                num_tag = p_tag
                main_sec_alpha = 'a'

                prev_h3 = re.search(r'\d+([a-b])*$', p_tag.find_previous("h3").get("id").strip()).group()
                if re.search(rf'^1\.0|{prev_h3}\.(0|1)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                else:
                    num_ol.append(p_tag)
                prev_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                num_id = re.search(r'^(?P<n_id>\d{0,2}\.\d+(\.\d+)*)', current_tag_text).group("n_id")
                p_tag["id"] = f'{prev_num_id}{num_id}'
                p_tag.string = re.sub(r'^\d{0,2}\.\d+\.*(\d+)*', '', p_tag.text.strip())
                previous_li_tag = p_tag

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1
                cap_alpha_cur_tag1 = None

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    if num_tag:
                        sec_alpha_id = num_tag.get('id')
                        num_tag.append(sec_alpha_ol)
                    elif cap_roman_cur_tag1:
                        sec_alpha_id = cap_roman_cur_tag1.get('id')
                        cap_roman_cur_tag1.append(sec_alpha_ol)
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
                        cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s?\((?P<pid>\d+)\)\s\(?(?P<nid>A)\)',current_tag_text)
                        cap_alpha_id1 = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}'
                        inner_li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_alpha_ol1.append(inner_li_tag)
                        num_cur_tag1.string = ""
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha1 = 'B'
                previous_li_tag = p_tag

            elif re.search(rf'^{inner_alpha}\.', current_tag_text):
                p_tag.name = "li"
                inner_sec_alpha_tag = p_tag
                if re.search(r'^a\.', current_tag_text):
                    inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inner_sec_alpha_ol)
                    inner_sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    if inner_num_cur_tag:
                        inner_sec_alpha_id = inner_num_cur_tag.get('id')
                        inner_num_cur_tag.append(inner_sec_alpha_ol)
                else:
                    inner_sec_alpha_ol.append(p_tag)
                p_tag["id"] = f'{inner_sec_alpha_id}{inner_alpha}'
                p_tag.string = re.sub(rf'^{inner_alpha}\.', '', current_tag_text)
                inner_alpha = chr(ord(inner_alpha) + 1)
                previous_li_tag = p_tag

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
                    elif inner_num_cur_tag:
                        num_id1 = inner_num_cur_tag.get('id')
                        inner_num_cur_tag.append(num_ol1)
                    elif cap_roman_cur_tag1:
                        num_id1 = cap_roman_cur_tag1.get("id")
                        cap_roman_cur_tag1.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"
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
                        cap_alpha_id1 = f'{p_tag.find_previous({"h5", "h4", "h3", "h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}'

                        li_tag[
                            "id"] = f'{p_tag.find_previous({"h5", "h4", "h3", "h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol1)
                    cap_alpha1 = 'B'

                    if re.search(r'^\(\d+\)\s*\([A-Z]\)\s*\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s*\([A-Z]\)\s*\(i\)', '', current_tag_text)
                        roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s?\((?P<pid>[A-Z])\)\s*\(?(?P<nid>i)\)',current_tag_text)
                        prev_id1 = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}'
                        inner_li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        roman_ol.append(inner_li_tag)
                        cap_alpha_cur_tag1.string = ""
                        cap_alpha_cur_tag1.append(roman_ol)
                        small_roman = 'ii'
                        cap_rom = "I"
                previous_li_tag = p_tag

            elif re.search(rf'^{inner_num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_num_cur_tag = p_tag
                num_count = 1
                inner_alpha = 'a'

                if re.search(r'^1\.', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if cap_roman_cur_tag1:
                        cap_roman_cur_tag1.append(inner_num_ol)
                        num_id = cap_roman_cur_tag1.get('id')
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(inner_num_ol)
                        num_id = cap_alpha_cur_tag.get('id')
                    else:
                        num_id = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"

                else:
                    inner_num_ol.append(p_tag)

                p_tag["id"] = f'{num_id}{inner_num_count}'
                p_tag.string = re.sub(rf'^{inner_num_count}\.', '', current_tag_text)
                inner_num_count += 1
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha2}{cap_alpha2}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha_ol1.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<p_id>{cap_alpha2}{cap_alpha2})\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_alpha_id1}{p_tag_id}'
                p_tag.string = re.sub(rf'^\({cap_alpha2}{cap_alpha2}\)', '', current_tag_text)
                cap_alpha2 = chr(ord(cap_alpha2) + 1)
                previous_li_tag = p_tag

            elif re.search(rf'^{cap_alpha}\.', current_tag_text) and p_tag.name == "p":
                inner_num_count = 1
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    if cap_roman_cur_tag1:
                        cap_roman_cur_tag1.append(cap_alpha_ol)
                        cap_alpha_id = cap_roman_cur_tag1.get("id")
                    else:
                        cap_alpha_id = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{cap_alpha_id}-{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)
                if cap_alpha == 'Z':
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_rom}\)', current_tag_text) and p_tag.name == "p" \
                    and cap_alpha1 not in ['I', 'V', 'X'] and p_tag.get("class") != "casenote":
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag
                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    roman_cur_tag.append(cap_roman_ol)
                    prev_id1 = roman_cur_tag.get('id')
                else:
                    cap_roman_ol.append(p_tag)
                p_tag["id"] = f'{prev_id1}{roman.fromRoman(cap_rom.upper())}'
                p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)
                cap_rom = roman.toRoman(roman.fromRoman(cap_rom.upper()) + 1)

                if re.search(rf'^\([IVX]+\)\s*\(aa\)', current_tag_text):
                    alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([IVX]+\)\s*\(aa\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_roman_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[IVX]+)\)\s*\((?P<pid>aa)\)', current_tag_text)
                    li_tag["id"] = f'{cap_roman_cur_tag.get("id")}{cur_tag.group("pid")}'
                    alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(alpha_ol1)
                previous_li_tag = p_tag

            elif re.search(rf'^{inner_cap_rom}\.', current_tag_text) and p_tag.name == "p" \
                    and cap_alpha1 not in ['I', 'V', 'X'] and p_tag.get("class") != "casenote":
                p_tag.name = "li"
                cap_roman_cur_tag1 = p_tag
                main_sec_alpha = 'a'
                cap_alpha = "A"
                inner_num_count = 1
                if re.search(r'^I\.', current_tag_text):
                    cap_roman_ol1 = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol1)
                    prev_id_rom = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    cap_roman_ol1.append(p_tag)
                p_tag["id"] = f'{prev_id_rom}{inner_cap_rom}'
                p_tag.string = re.sub(r'^[IVX]+\.', '', current_tag_text)
                inner_cap_rom = roman.toRoman(roman.fromRoman(inner_cap_rom.upper()) + 1)
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                cap_alpha2 = 'A'
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag
                small_roman = "i"
                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)
                    if num_cur_tag1:
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha_id1 = num_cur_tag1.get("id")
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol1.append(p_tag)
                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                if cap_alpha1 == 'Z':
                    cap_alpha1 = 'A'
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
                    small_roman = "ii"
                    cap_rom = "I"

                    if re.search(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', current_tag_text):
                        cap_roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cap_roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>[A-Z])\)\s?\((?P<pid>[ivx]+)\)\s\(?(?P<nid>I)\)',
                                            current_tag_text)
                        prev_id1 = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}'
                        inner_li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_roman_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(cap_roman_ol)
                previous_li_tag = p_tag

            elif re.search(r'^\([a-z][a-z]\)', current_tag_text) and cap_roman_cur_tag:
                p_tag.name = "li"
                if re.search(r'^\(aa\)', current_tag_text):
                    alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol1)
                    cap_roman_cur_tag.append(alpha_ol1)
                elif alpha_ol1:
                    alpha_ol1.append(p_tag)
                p_tag_id = re.search(r'^\((?P<p_id>[a-z][a-z])\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_roman_cur_tag.get("id")}{p_tag_id}'
                p_tag.string = re.sub(r'^\([a-z][a-z]\)', '', current_tag_text)
                previous_li_tag = p_tag

            elif p_tag.get("class") == [self.tag_type_dict["ol_p"]] \
                    and not re.search(r'^HISTORY:|^History', current_tag_text) and previous_li_tag:
                if previous_li_tag:
                    previous_li_tag.append(p_tag)

            if re.search(r'^CASE NOTES|^HISTORY:', current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                num_count = 1
                ol_count = 1
                inner_num_count = 1
                main_sec_alpha = 'a'
                inner_alpha = 'a'
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha2 = "A"
                cap_alpha = 'A'
                inner_cap_rom = "I"
                sec_alpha_id = None
                num_tag = None
                small_roman = "i"
                alpha_ol1 = None
                cap_alpha_cur_tag1 = None
                cap_roman_cur_tag = None
                previous_li_tag = None
                cap_roman_cur_tag1 = None
                inner_num_cur_tag = None
                cap_alpha_cur_tag = None
        print('ol tags added')

    def create_analysis_nav_tag(self):
        if self.release_number in ['83', '82', '81']:
            digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
            inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
            digit_id = None
            num_tag = None
            digit_tag = None
            case_tag_id = None
            for analysis_p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['ol_p']}):
                if re.search(r'^Analysis', analysis_p_tag.text.strip()):
                    rept_tag = re.split('\n', analysis_p_tag.text.strip())
                    analysis_p_tag.clear()
                    for tag_text in rept_tag:
                        new_tag = self.soup.new_tag("p")
                        new_tag.string = tag_text
                        analysis_p_tag.append(new_tag)
                        if not re.search(r'Analysis', tag_text):
                            new_tag["class"] = "analysisnote"
                    analysis_p_tag.unwrap()

            for analysis_tag in self.soup.find_all("p", class_="analysisnote"):
                if re.search(r'^\d+\.*|^-', analysis_tag.text.strip()):
                    analysis_tag.name = "li"
                    if re.search(r'^0\.5\.', analysis_tag.text.strip()):
                        num_tag = analysis_tag
                        digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        analysis_tag.wrap(digit_ul)
                        case_tag_id = f'#{analysis_tag.find_previous({"h3", "h2"}).get("id")}-annotation-0.5'

                    elif re.search(r'^\d+\.*', analysis_tag.text.strip()):
                        digit_tag = analysis_tag
                        if re.search(r'^1\.', analysis_tag.text.strip()):
                            if num_tag:
                                digit_ul.append(analysis_tag)
                            else:
                                digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                                analysis_tag.wrap(digit_ul)
                        else:
                            digit_ul.append(analysis_tag)
                            num_tag = None
                        p_tag_num = re.search(r'^(?P<num>\d+)', analysis_tag.text.strip()).group("num")
                        digit_id = f'#{analysis_tag.find_previous({"h3", "h2"}).get("id")}-annotation-{p_tag_num}'
                        case_tag_id = f'#{analysis_tag.find_previous({"h3", "h2"}).get("id")}-annotation-{p_tag_num}'

                    elif re.search(r'^-', analysis_tag.text.strip()):
                        case_id1 = re.sub(r'[\W\d]', '', analysis_tag.text.strip()).lower()
                        case_tag_id = f"{digit_id}-{case_id1}"
                        if re.search(r'^\d', analysis_tag.find_previous("li").text.strip()):
                            inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_tag.wrap(inner_ul)
                            digit_tag.append(inner_ul)
                        else:
                            inner_ul.append(analysis_tag)
                    anchor = self.soup.new_tag('a', href=case_tag_id)
                    anchor.string = analysis_tag.text
                    analysis_tag.string = ''
                    analysis_tag.append(anchor)
        else:
            super(VTParseHtml, self).create_case_note_analysis_nav_tag()
        print("Case Notes nav created")

    def replace_tags_constitution(self):
        super(VTParseHtml, self).replace_tags_constitution()
        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_alpha_id = None
        h5_rom_id = None
        cap_roman_tag = None
        annotation_id = None
        annotation_text_list: list = []
        annotation_id_list: list = []
        h5_count = 1
        h3_count = 1

        for header_tag in self.soup.find_all():
            if int(self.release_number) <= 83:
                if header_tag.get('class') and header_tag.get("class")[0] == self.tag_type_dict["head4_1"]:
                    if re.search(fr'^\d+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', header_tag.text.strip()).group("h5_id")
                        h5_num_id = f"{header_tag.find_previous({'h3', 'h2'}).get('id')}-annotation-{h5_num_text}"
                        if h5_num_id in annotation_id_list:
                            header_tag['id'] = f'{h5_num_id}.{h5_count}'
                            h5_count += 1
                        else:
                            h5_count = 1
                            header_tag['id'] = h5_num_id

                        annotation_id_list.append(h5_num_id)
                    elif re.search(r'^\*\d{1,2}\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        analysis_id = re.sub(r'[\W\d]', '', header_tag.text.strip()).lower()
                        header_tag['id'] = f"{h5_num_id}-{analysis_id}"
                elif header_tag.get('class') and \
                        header_tag.get("class")[0] == self.tag_type_dict["head1"] and header_tag.name == "p":
                    if h3_tag := re.search(r'^AMENDMENT (?P<id>[IVX]+)\.', header_tag.text.strip()):
                        header_tag.name = "h2"
                        header_tag['id'] = f'{header_tag.find_previous("h1").get("id")}-ammendmentam{h3_tag.group("id").zfill(2)}'
                        header_tag['class'] = "oneh2"
                    else:
                        header_tag.name = "h2"
                        header_tag['id'] = f'{header_tag.find_previous("h1").get("id")}-ammendment'

            if header_tag.get('class') and header_tag.get("class")[0] == self.tag_type_dict["head4"]:
                if re.search(r'^CASE NOTES$|^Analysis$|^ANNOTATIONS$', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_roman_tag = None
                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()) and \
                        re.search(r'^ANNOTATIONS$', header_tag.find_previous("h4").text.strip()):
                    header_tag.name = "h5"
                    cap_roman_tag = header_tag
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecisison-{h5_rom_text}'
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
                elif annotation_id and re.search(r'^—[a-zA-Z]+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    tag_text = re.sub(r'[\W\s.]+', '', header_tag.text.strip()).lower()
                    inner_head_id = f'{annotation_id}-{tag_text}'
                    if inner_head_id in annotation_id_list:
                        header_tag["id"] = f'{inner_head_id}.{h5_count}'
                        h5_count += 1
                    else:
                        header_tag["id"] = f'{inner_head_id}'
                        h5_count = 1
                    annotation_id_list.append(inner_head_id)
                else:
                    annotation_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    if annotation_text in annotation_text_list and re.search(r'^ANNOTATIONS$', header_tag.find_previous(
                            "h4").text.strip()):
                        header_tag.name = "h5"
                        if cap_roman_tag:
                            annotation_id = f'{cap_roman_tag.get("id")}-{annotation_text}'
                        else:
                            annotation_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{annotation_text}'
                        if annotation_id in annotation_id_list:
                            header_tag["id"] = f'{annotation_id}.{h5_count}'
                            h5_count += 1
                        else:
                            header_tag["id"] = f'{annotation_id}'
                            h5_count = 1
                        annotation_id_list.append(annotation_id)
            if int(self.release_number) >= 84 and re.search(r'^Analysis|^ANNOTATIONS', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') and \
                            tag.get('class')[0] == self.tag_type_dict["head4"]:
                        break
                    else:
                        tag["class"] = "casenote"
                        annotation_text_list.append(re.sub(r'[\W\s]+', '', tag.text.strip()).lower())
            if header_tag.name == "h3" and re.search(r'^§ 1401\.Boundaries$', header_tag.text.strip()):
                tag_id = re.search(r'^§ (?P<id>1401)\.Boundaries$', header_tag.text.strip()).group("id")
                header_tag["id"] = f'{header_tag.find_previous("h2", class_="twoh2").get("id")}s{tag_id}'
            if int(self.release_number) <= 83 and re.search(r'vt\.html$', self.input_file_name) \
                    and re.search(r'^\[.+]$', header_tag.text.strip()):
                header_tag.name = "h3"
                header_tag['id'] = f"{header_tag.find_previous('h2').get('id')}-s{h3_count:02}"
                h3_count += 1

    def add_anchor_tags_con(self):
        for li_tag in self.soup.findAll("li"):
            if not li_tag.get("id"):
                if tag := re.search(r'^(?P<id>[IVX]+)\.', li_tag.text.strip()):
                    chap_num = tag.group("id")
                    self.c_nav_count += 1
                    if li_tag.find_previous("p") and \
                            re.search(r'^(Section\.?|Chapter|Sec\.|Article|Amendment)$', li_tag.find_previous("p").text.strip()):
                        s_tag = f'{li_tag.find_previous("p").text.strip()[:2].lower()}'
                    else:
                        s_tag = 'ch'
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag=f'{s_tag}',
                                                prev_id=li_tag.find_previous({"h2","h1"}).get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
                elif tag := re.search(r'^(?P<id>\d+)\.', li_tag.text.strip()):
                    chap_num = tag.group("id")
                    if re.search(r'^Section$', li_tag.find_previous().text.strip()):
                        self.s_nav_count = 0
                    self.s_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-s",
                                                prev_id=li_tag.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.s_nav_count:02}')
                elif re.search(r'^Amendments$',li_tag.text.strip()):
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li_tag, "ammendment",
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

    def wrap_inside_main_tag(self):

        """wrap inside main tag"""

        main_tag = self.soup.new_tag('main')
        chap_nav = self.soup.find('nav')

        h2_tag = self.soup.find("h2")
        tag_to_wrap = h2_tag.find_previous_sibling()

        if tag_to_wrap:
            for tag in tag_to_wrap.find_next_siblings():
                tag.wrap(main_tag)

        for nav_tag in chap_nav.find_next_siblings():
            if nav_tag.name != "main":
                nav_tag.wrap(chap_nav)

    def format_id(self, section_id, tag):
        if int(self.release_number) <= 83:
            if sec_id := re.search(
                    r'(?P<id>\d+\w?)(\.)?\s?-\d+\w?\.\s*\[?(Repealed|Reserved|Redesignated|Omitted)\.?]?',
                    tag.text.strip()):
                return sec_id.group("id")
            elif re.search(r'\.', section_id):
                return re.sub(r'\.', '', section_id)
            else:
                return section_id
        else:
            pass
