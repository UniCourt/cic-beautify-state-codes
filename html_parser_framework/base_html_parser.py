import copy
import importlib
import os
import re
from datetime import datetime

import roman
from bs4 import BeautifulSoup, Doctype
from regex_pattern import RegexPatterns
from loguru import logger


class ParseHtml:

    def __init__(self, state_key, path, release_number, input_file_name):

        """Meta Data"""
        self.h3_pattern_text_con = None
        self.h2_rename_pattern = None
        self.chp_nav_count = 0
        self.h2_pattern_text_con = None
        self.h2_text_con = None
        self.h2_text = None
        self.h3_pattern_text = None
        self.h2_pattern_text = None
        self.id_list = []
        self.file_name = None
        self.tag = None
        self.state_key = state_key
        self.path = path
        self.release_number = release_number
        self.input_file_name = input_file_name

        self.parser_obj = None
        self.junk_tag_class = None
        self.h2_order = None
        self.title = None
        self.ul_tag = None

        self.cite_pattern = None
        self.release_date = None
        self.watermark_text = None
        self.path_in = None
        self.path_out = None
        self.h4_head = None
        self.tag_type_dict = None
        self.soup = None

        self.s_nav_count = 0
        self.p_nav_count = 0
        self.a_nav_count = 0
        self.c_nav_count = 0

        self.h4_cur_id_list: list = []
        self.meta_tags: list = []
        self.list_ids: list = []
        self.dup_id_list: list = []
        self.h2_rep_id: list = []
        self.h2_id_count = 1
        self.id_count = 1
        self.list_id_count = 1
        self.h3_count = 1

        self.meta_data = {"file_name": self.input_file_name, "state_key": self.state_key,
                          "release_number": self.release_number}

        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.regex_pattern_obj = RegexPatterns()

    def pre_process(self):
        pass

    def set_release_date(self):
        date_dictionary = {}
        with open('release_dates.txt') as file:
            for line in file:
                (key, value) = line.split()
                date_dictionary[key] = value

        release_date_pattern = fr'{self.state_key}_r{self.release_number}'

        if release_date_pattern in date_dictionary:
            self.release_date = date_dictionary[release_date_pattern]
        else:
            logger.error("release date is missing in release_date file")

        self.parser_obj = getattr(importlib.import_module('regex_pattern'), f'CustomisedRegex{self.state_key}')()

    def set_page_soup(self):
        """
                - Read the input html to parse and convert it to Beautifulsoup object
                - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
                  which is syntax of html tag in html 5
                - add attribute 'lang' to html tag with value 'en'
        """

        with open(self.path) as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        logger.info(f"soup is created for {self.meta_data}")

    def generate_class_name_dict(self):
        """
          - Find the textutil generated class names for each type of tag (h1, h2, ....)
             using re pattern specified in self.tag_type_dict
        """

        for key, value in self.tag_type_dict.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.tag_type_dict.get(key), tag.get_text().strip(), re.I)
                            and tag.attrs["class"][0] not in self.tag_type_dict.values())
            if tag_class:
                self.tag_type_dict[key] = tag_class.get('class')[0]

        logger.info(f"updated class dict is {self.tag_type_dict}")

    def replace_h1_tags_titles(self, header_tag):
        """
            -  This method is called by replace_tags_titles with tag as args
            - The class,name and id is set for the tag

        """

        if self.regex_pattern_obj.h1_pattern.search(header_tag.text.strip()):
            header_tag.name = "h1"
            title_no = self.regex_pattern_obj.h1_pattern.search(header_tag.text.strip()).group('id')
            self.title = title_no
            header_tag["class"] = "title"
            header_tag["id"] = f't{title_no.zfill(2)}'
            header_tag.wrap(self.soup.new_tag("nav"))

    def set_id_for_h2_tags(self, header_tag, text, prev, cur):

        """
            - This method is called by replace_h2_tags_titles method with
            tag,text, prev (previous tag class),cur(current tag class) args
            - With the args passed the name,id and class is updated

        """

        pattern = f'h2_{text}_pattern'
        instance = getattr(self.parser_obj, pattern)

        if instance.search(header_tag.text.strip()) and instance.search(header_tag.text.strip()).group('id'):
            header_tag.name = "h2"
            chap_no = instance.search(header_tag.text.strip()).group('id')
            if header_tag.findPrevious("h2", class_=prev):
                header_tag_id = f'{header_tag.findPrevious("h2", class_=prev).get("id")}{text[0]}{chap_no.zfill(2)}'
                if header_tag_id in self.dup_id_list:
                    header_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                    self.id_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.id_count = 1
                header_tag["class"] = cur
            else:
                header_tag_id = f'{header_tag.findPrevious("h1").get("id")}{text[0]}{chap_no.zfill(2)}'

                if header_tag_id in self.dup_id_list:
                    header_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                    self.id_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.id_count = 1

                header_tag["class"] = "oneh2"
            self.dup_id_list.append(header_tag_id)

    def set_id_for_h2_tags_con(self, header_tag, text, prev, cur):

        """
            - This method is called by replace_h2_tags_titles method with
            tag,text, prev (previous tag class),cur(current tag class) args
            - With the args passed the name,id and class is updated

        """

        pattern = f'h2_{text}_pattern_con'
        instance = getattr(self.parser_obj, pattern)

        if instance.search(header_tag.text.strip()) and instance.search(header_tag.text.strip()).group('id'):
            header_tag.name = "h2"
            chap_no = instance.search(header_tag.text.strip()).group('id')
            if header_tag.findPrevious("h2", class_=prev):
                header_tag_id = f'{header_tag.findPrevious("h2", class_=prev).get("id")}{text[:2]}{chap_no.zfill(2)}'
                if header_tag_id in self.dup_id_list:
                    header_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                    self.id_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.id_count = 1
                header_tag["class"] = cur
            else:
                header_tag_id = f'{header_tag.findPrevious("h1").get("id")}{text[:2]}{chap_no.zfill(2)}'

                if header_tag_id in self.dup_id_list:
                    header_tag["id"] = f'{header_tag_id}.{self.id_count:02}'
                    self.id_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.id_count = 1

                header_tag["class"] = "oneh2"
            self.dup_id_list.append(header_tag_id)

    def replace_h2_tags_titles(self, header_tag):

        """
            - This method is called by replace_tags_titles method with
                   tag as args
            - With the args passed the name,id and class is updated using sub method
             set_id_for_h2_tags.

        """

        text = re.search(r'^\S+', header_tag.text.strip()).group().lower()

        if text == self.h2_order[0]:
            pattern = f'h2_{text}_pattern'
            instance = getattr(self.parser_obj, pattern)

            if instance.search(header_tag.text.strip()):
                header_tag.name = "h2"
                chap_no = instance.search(header_tag.text.strip()).group('id')
                header_tag_id = f'{self.soup.find("h1").get("id")}{text[0]}{chap_no.zfill(2)}'
                if header_tag_id in self.h2_rep_id:
                    header_tag["id"] = f'{header_tag_id}.{self.h2_id_count:02}'
                    self.h2_id_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.h2_id_count = 1

                header_tag["class"] = "oneh2"
                self.h2_rep_id.append(header_tag_id)

        elif text == self.h2_order[1]:
            self.set_id_for_h2_tags(header_tag, text, prev={"gen", "oneh2"}, cur="twoh2")

        elif text == self.h2_order[2]:
            self.set_id_for_h2_tags(header_tag, text, prev={"twoh2", "oneh2", "gen"}, cur="threeh2")

        elif text == self.h2_order[3]:
            self.set_id_for_h2_tags(header_tag, text, prev={"oneh2", "twoh2", "threeh2", "gen"}, cur="fourh2")

        elif self.h2_pattern_text:
            for list_pattern in self.h2_pattern_text:
                h2_pattern = re.compile(list_pattern)
                if h2_tag := h2_pattern.search(header_tag.text.strip()):
                    header_tag.name = "h2"
                    if header_tag.find_previous("h2"):
                        prev_header_tag = header_tag.find_previous(
                            lambda tag: tag.name == 'h2' and not h2_pattern.search(tag.text.strip()) and
                                        not re.search(rf'{h2_tag.group("tag").lower()}', tag.get("id").strip()))

                        if re.search(r'(1|A|I)\.', header_tag.text.strip()):
                            prev_header_tag = header_tag.find_previous(
                                lambda tag: tag.name == 'h2' and not h2_pattern.search(tag.text.strip()) and
                                            not re.search(rf'{h2_tag.group("tag")}', tag.get("id").strip()))
                            self.prev_class_name = prev_header_tag.get("class")
                        else:
                            prev_header_tag = header_tag.find_previous("h2", class_=self.prev_class_name)

                    else:
                        prev_header_tag = self.soup.find("h1")
                        self.prev_class_name = prev_header_tag.get("class")

                    header_tag[
                        "id"] = f'{prev_header_tag.get("id")}{h2_tag.group("tag").lower()}{h2_tag.group("id").zfill(2)}'
                    header_tag["class"] = "gen"

        if self.h2_rename_pattern:
            for list_pattern in self.h2_rename_pattern:
                h2_pattern = re.compile(list_pattern)
                if h2_tag := h2_pattern.search(header_tag.text.strip()):
                    prev_header_tag = header_tag.find_previous(
                        lambda tag: tag.name == 'h2' and not h2_pattern.search(tag.text.strip()) and
                                    not re.search(rf'{h2_tag.group("tag").lower()}', tag.get("id").strip()))
                    header_tag[
                        "id"] = f'{prev_header_tag.get("id")}{h2_tag.group("tag").lower()}{h2_tag.group("id").zfill(2)}'
                    header_tag.name = "h2"

    def replace_h3_titles(self, header_tag, h3_id_list):
        if sec_id := getattr(self.parser_obj, "section_pattern").search(header_tag.text.strip()):
            sec_id = re.sub(r'\s+|\.$', '', sec_id.group("id"))
            if self.format_id(sec_id, header_tag):
                sec_id = self.format_id(sec_id, header_tag)
            header_tag.name = "h3"
            if header_tag.find_previous({"h2", "h3"}, class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}):
                header_tag_id = f'{header_tag.find_previous({"h2", "h3"}, class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}).get("id")}s{sec_id.zfill(2)}'
                if header_tag_id in h3_id_list:
                    header_tag_id = f'{header_tag_id}.{self.h3_count:02}'
                    header_tag["id"] = f'{header_tag_id}'
                    self.h3_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.h3_count = 1
            else:
                header_tag_id = f'{header_tag.find_previous("h1").get("id")}c{sec_id}'
                if header_tag_id in h3_id_list:
                    header_tag_id = f'{header_tag_id}.{self.h3_count:02}'
                    header_tag["id"] = f'{header_tag_id}'
                    self.h3_count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    self.h3_count = 1

            h3_id_list.append(header_tag_id)

        elif getattr(self.parser_obj, "section_pattern_1") and getattr(self.parser_obj, "section_pattern_1").search(
                header_tag.text.strip()):
            if sec_id := getattr(self.parser_obj, "section_pattern_1").search(header_tag.text.strip()):
                sec_id = re.sub(r'\s+|\.$', '', sec_id.group("id"))
                header_tag.name = "h3"
                if header_tag.find_previous({"h2", "h3"}, class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}):
                    header_tag_id = f'{header_tag.find_previous({"h2", "h3"}, class_={"oneh2", "twoh2", "threeh2", "fourh2", "gen"}).get("id")}s{sec_id.zfill(2)}'
                    if header_tag_id in h3_id_list:
                        header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                        self.h3_count += 1
                    else:
                        header_tag["id"] = f'{header_tag_id}'
                        self.h3_count = 1
                else:
                    header_tag_id = f'{header_tag.find_previous("h1").get("id")}s{sec_id}'
                    if header_tag_id in h3_id_list:
                        header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                        self.h3_count += 1
                    else:
                        header_tag["id"] = f'{header_tag_id}'
                        self.h3_count = 1

                h3_id_list.append(header_tag_id)

        else:
            if self.h3_pattern_text:
                for list_pattern in self.h3_pattern_text:
                    h3_pattern = re.compile(list_pattern)
                    if h3_tag := h3_pattern.search(header_tag.text.strip()):
                        header_tag.name = "h3"
                        sec_id = h3_tag.group("id")
                        if header_tag.find_previous("h2", class_={"oneh2", "twoh2", "threeh2", "fourh2"}):
                            header_tag_id = f'{header_tag.find_previous("h2", class_={"oneh2", "twoh2", "threeh2", "fourh2"}).get("id")}s{sec_id.zfill(2)}'
                            if header_tag_id in h3_id_list:
                                header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                                self.h3_count += 1
                            else:
                                header_tag["id"] = f'{header_tag_id}'
                                self.h3_count = 1
                        else:
                            header_tag_id = f'{header_tag.find_previous("h1").get("id")}s{sec_id.zfill(2)}'
                            if header_tag_id in h3_id_list:
                                header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                                self.h3_count += 1
                            else:
                                header_tag["id"] = f'{header_tag_id}'
                                self.h3_count = 1

                        h3_id_list.append(header_tag_id)

    def replace_h4_tag_titles(self, header_tag, h4_count, id):

        """
            - if the text of the tag matches to the text in the list h4.head,
            then the tag name, id is updated
        """

        header_tag.name = "h4"
        if id:
            header4_tag_text = id
        else:
            header4_tag_text = re.sub(r'[\W.]+', '', header_tag.text.strip()).lower()
        h4_tag_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'

        if h4_tag_id in self.h4_cur_id_list:
            header_tag['id'] = f'{h4_tag_id}.{h4_count}'
            h4_count += 1
        else:
            header_tag['id'] = f'{h4_tag_id}'

        self.h4_cur_id_list.append(h4_tag_id)

    def replace_tags_titles(self):

        """
            based on the class of the tag ,the tag name is updated
        """
        self.h4_count = 1
        h3_id_list: list = []
        self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        self.get_h2_order()
        for header_tag in self.soup.find_all("p"):
            if header_tag.get("class") == [self.tag_type_dict["head1"]]:
                self.replace_h1_tags_titles(header_tag)
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                self.replace_h2_tags_titles(header_tag)

            elif header_tag.get("class") == [self.tag_type_dict["head2"]]:
                self.replace_h2_tags_titles(header_tag)
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                header_tag_text = re.sub(r'\W+', '', header_tag.text.strip())
                if self.h2_text and header_tag_text in self.h2_text:
                    self.h2_set_id(header_tag)
                else:
                    self.replace_h3_titles(header_tag, h3_id_list)

            elif header_tag.get("class") == [self.tag_type_dict["head3"]]:
                self.replace_h3_titles(header_tag, h3_id_list)
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if header_tag.text.strip() in self.h4_head:
                    self.replace_h4_tag_titles(header_tag, self.h4_count, None)
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif header_tag.get("class") == [self.tag_type_dict["ul"]]:
                if not re.search(r'^(Section\.?|Chapter|Sec\.|Chap.)$', header_tag.text.strip()):
                    header_tag.name = "li"
                    header_tag.wrap(self.ul_tag)

            elif header_tag.name == "p":
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        logger.info("Tags are replaced in the base class")

    def set_chapter_section_id(self, list_item, chap_num, sub_tag, prev_id, cnav):
        """
            - This method is called by add_anchor_tags ,
            this will set tag id and reference link to the list_item
        """
        li_list = []
        li_link = self.soup.new_tag('a')
        li_link.append(list_item.text)
        li_link_id = f"{prev_id}{sub_tag}{chap_num.zfill(2)}"
        li_list.append(li_link)
        list_item.contents = li_list
        if li_link_id in self.list_ids:
            li_link_id = f"{li_link_id}.{self.list_id_count:02}"
            list_item['id'] = f'{li_link_id}-{cnav}'
            list_item.a['href'] = f'#{li_link_id}'
            self.list_id_count += 1
        else:
            li_link_id = f"{prev_id}{sub_tag}{chap_num.zfill(2)}"
            list_item['id'] = f'{li_link_id}-{cnav}'
            list_item.a['href'] = f'#{li_link_id}'
            self.list_id_count = 1

        self.list_ids.append(li_link_id)

    def add_anchor_tags(self):

        """
            - adding id and reference link to the li tag by calling
            set_chapter_section_id  method

        """
        pnav_count = 1

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and len(li_tag.text.strip()) > 0 and \
                    li_tag.get('class') and li_tag.get('class')[0] == self.tag_type_dict['ul']:
                text = re.search(r'^\S+', li_tag.text.strip()).group().lower()
                pattern = f'h2_{text}_pattern'
                li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                if text == self.h2_order[0]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.c_nav_count += 1
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag=f"{text[0]}",
                                                    prev_id=li_tag.find_previous("h1").get("id"),
                                                    cnav=f'{text[0]}nav{self.c_nav_count:02}')
                elif text == self.h2_order[1]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()) and instance.search(li_tag.text.strip()).group('id'):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.a_nav_count += 1
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag=f"{text[0]}",
                                                    prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                    cnav=f'{text[0]}nav{self.a_nav_count:02}')
                elif text == self.h2_order[2]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.p_nav_count += 1
                        if li_tag.find_previous("h2", class_={"twoh2", "gen"}) or li_tag.find_previous("h3",
                                                                                                       class_="twoh2"):
                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag=f"{text[0]}",
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'{text[0]}nav{self.p_nav_count:02}')
                elif text == self.h2_order[3]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.s_nav_count += 1
                        if li_tag.find_previous("h2", class_={"threeh2", "gen"}):
                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag=f"{text[0]}",
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'{text[0]}nav{self.s_nav_count:02}')

                elif getattr(self.parser_obj, "section_pattern").search(li_tag.text.strip()):
                    sec_num = getattr(self.parser_obj, "section_pattern").search(li_tag.text.strip()).group("id")
                    sec_num = re.sub(r'\s+|\.$', '', sec_num)
                    if self.format_id(sec_num, li_tag):
                        sec_num = self.format_id(sec_num, li_tag)
                    if li_tag.find_previous(class_={"gen", "oneh2", "twoh2", "threeh2", "fourh2"}):
                        prev_id = li_tag.find_previous(
                            class_={"navhead1", "navhead", "gen", "oneh2", "twoh2", "threeh2", "fourh2"}).get(
                            "id")
                        prev_p_tag = li_tag.find_previous("p")
                        if prev_p_tag and re.search(r'^(Section\.?|Chapter|Sec\.)$', prev_p_tag.text.strip()):
                            sub_tag = prev_p_tag.text.strip()[0].lower()
                        else:
                            sub_tag = 's'
                    else:
                        prev_id = li_tag.find_previous(class_={"navhead1", "navhead", "title"}).get("id")
                        sub_tag = 'c'

                    self.s_nav_count += 1
                    cnav = f'snav{self.s_nav_count:02}'
                    self.set_chapter_section_id(li_tag, sec_num, sub_tag, prev_id, cnav)

                elif self.h2_text and li_tag_text in self.h2_text:
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    if li_tag.find_previous("li") and li_tag.find_previous("li").get("id"):
                        self.chp_nav_count = int(
                            re.search(r'-(?P<ntag>\w+)nav(?P<ncount>\d+)',
                                      li_tag.find_previous("li").get("id").strip()).group(
                                "ncount")) + 1
                        ntag = f"{re.search(r'-(?P<ntag>[a-z]+)nav(?P<ncount>[0-9]+)', li_tag.find_previous('li').get('id').strip()).group('ntag')}"
                    else:
                        self.chp_nav_count += 1
                        ntag = "c"
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous(
                                                    class_={"title", "oneh2", "twoh2", "threeh2", "fourh2"}).get("id"),
                                                cnav=f'{ntag}nav{self.chp_nav_count:02}')

                elif self.h2_pattern_text:
                    for list_pattern in self.h2_pattern_text:
                        h2_pattern = re.compile(list_pattern)
                        if h2_tag := h2_pattern.search(li_tag.text.strip()):
                            self.p_nav_count += 1
                            self.set_chapter_section_id(li_tag, h2_tag.group("id"),
                                                        sub_tag=h2_tag.group("tag").lower(),
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'{h2_tag.group("tag")}nav{self.p_nav_count:02}')
                elif self.h3_pattern_text:
                    for list_pattern in self.h3_pattern_text:
                        h3_pattern = re.compile(list_pattern)
                        if h3_tag := h3_pattern.search(li_tag.text.strip()):
                            self.a_nav_count += 1
                            self.set_chapter_section_id(li_tag, h3_tag.group("id"),
                                                        sub_tag='s',
                                                        prev_id=li_tag.find_previous(
                                                            class_={"navhead1", "navhead", "oneh2", "twoh2",
                                                                    "threeh2"}).get(
                                                            "id"),
                                                        cnav=f'cnav{self.a_nav_count:02}')

            if self.h2_rename_pattern and li_tag.name == "li" and li_tag.a:
                for list_tag in self.h2_rename_pattern:
                    tag_pattern = re.compile(list_tag)
                    if tag := tag_pattern.search(li_tag.a.text.strip()):
                        li_tag[
                            "id"] = f'{li_tag.find_previous("h2").get("id")}{tag.group("tag").lower()}{tag.group("id").zfill(2)}-pnav{pnav_count}'
                        li_tag.a[
                            "href"] = f'#{li_tag.find_previous("h2").get("id")}{tag.group("tag").lower()}{tag.group("id").zfill(2)}'
                        pnav_count += 1

            elif li_tag.name in ['h2', 'h3', 'h4']:
                self.a_nav_count = 0
                self.c_nav_count = 0
                self.p_nav_count = 0
                self.s_nav_count = 0

        logger.info("anchor tags are added in base class")

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """ this method is defined in the child class"""
        pass

    def create_analysis_nav_tag(self):
        """this method is defined in the child class"""
        pass

    def create_judicial_decision_analysis_nav_tag(self):

        """
            - Analysis classes are defined based on the header of the analysis tag.
            -  This method creates JUDICIAL DECISIONS analysis nav tag

        """

        a_tag_list = []
        analysis_tag = None
        analysis_tag_id = None
        analysis_num_tag_id = None
        analysis_num_tag = None
        a_tag_id = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        inner_alpha_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for analysis_p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['ol_p']}):
            if re.search(r'^Analysis', analysis_p_tag.text.strip()):
                for a_tag in analysis_p_tag.find_next_siblings():
                    if a_tag.get("class") == [self.tag_type_dict['ol_p']]:
                        a_tag.name = "li"
                        a_tag_text = re.sub(r'[\W_]+', '', a_tag.text.strip()).strip().lower()
                        a_tag_list.append(a_tag_text)
                        if re.search(r'^\d+\.', a_tag.text.strip()):
                            if re.search(r'^1\.', a_tag.text.strip()):
                                inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                a_tag.wrap(inner_ul_tag)
                                if analysis_tag:
                                    analysis_tag.append(inner_ul_tag)
                            else:
                                inner_ul_tag.append(a_tag)
                            analysis_num_tag_id = f"{analysis_tag_id}-{a_tag_text}"
                            a_tag_id = f"{analysis_tag_id}-{a_tag_text}"

                        elif re.search(r'^[a-z]\.', a_tag.text.strip()):
                            if re.search(r'^a\.', a_tag.text.strip()):
                                inner_alpha_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                a_tag.wrap(inner_alpha_ul_tag)
                                a_tag.find_previous("li").append(inner_alpha_ul_tag)
                            else:
                                inner_alpha_ul_tag.append(a_tag)
                            a_tag_id = f"{analysis_num_tag_id}-{a_tag_text}"

                        else:
                            if a_tag.find_previous().name == "a":
                                ul_tag.append(a_tag)
                            else:
                                ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                a_tag.wrap(ul_tag)
                            analysis_tag = a_tag
                            analysis_tag_id = f"#{a_tag.find_previous('h4').get('id')}-{a_tag_text}"
                            a_tag_id = f"#{a_tag.find_previous('h3').get('id')}-judicialdecisions-{a_tag_text}"

                        anchor = self.soup.new_tag('a', href=a_tag_id)
                        anchor.string = a_tag.text
                        a_tag.string = ''
                        a_tag.append(anchor)

                    elif a_tag.get("class") == [self.tag_type_dict['head4']]:
                        break
            else:
                if analysis_p_tag.find_previous("h4"):
                    if re.search(r'^JUDICIAL DECISIONS', analysis_p_tag.find_previous("h4").text.strip()):
                        if analysis_num_tag_id and re.search(r'^\d+\.\s—\w+', analysis_p_tag.text.strip()):
                            analysis_p_tag.name = "li"
                            a_tag_text = re.sub(r'[\W\s]+', '', analysis_p_tag.text.strip())

                            if analysis_p_tag.find_previous("li") and \
                                    re.search(r'^\d+\.', analysis_p_tag.find_previous("li").text.strip()):
                                text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                analysis_p_tag.wrap(text_ul_tag)
                                analysis_num_tag.append(text_ul_tag)

                            else:
                                text_ul_tag.append(analysis_p_tag)

                            a_tag_id = f'{analysis_num_tag_id}{a_tag_text}'

                        elif re.search(r'^\d+\.', analysis_p_tag.text.strip()):
                            analysis_p_tag.name = "li"
                            analysis_num_tag = analysis_p_tag
                            if re.search(r'^1\.', analysis_p_tag.text.strip()):
                                inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                analysis_p_tag.wrap(inner_ul_tag)
                            else:
                                inner_ul_tag.append(analysis_p_tag)
                            a_tag_text = re.search(r'^(?P<id>\d+)\.', analysis_p_tag.text.strip()).group("id")
                            analysis_num_tag_id = f"#{analysis_p_tag.find_previous('h3').get('id')}-judicialdecision-{a_tag_text}"
                            a_tag_id = analysis_num_tag_id

                        anchor = self.soup.new_tag('a', href=a_tag_id)
                        anchor.string = analysis_p_tag.text
                        analysis_p_tag.string = ''
                        analysis_p_tag.append(anchor)

    def create_case_note_analysis_nav_tag(self):
        """
             - Analysis classes are defined based on the header of the analysis tag.
             -  This method creates Case Notes  analysis nav tag

                """

        digit_tag, s_alpha_ul, digit_id, s_alpha_tag, s_rom_ul, s_alpha_id = None, None, None, None, None, None
        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})

        cap_alpha = 'A'
        s_roman = "i"
        s_alpha = 'a'
        case_count = 1
        case_tag_id = None
        a_tag_id = None
        alpha_id = None
        rom_tag = None
        rom_id = None
        alpha_tag = None
        note_head_id = None
        case_tag_id_list = []

        case_head_id = None
        case_head_tag = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for case_tag in self.soup.find_all(class_='casenote'):
            if re.search(r'^ANNOTATIONS$', case_tag.find_previous().text.strip()):
                rom_tag = None

            case_tag.name = "li"
            if re.search(r'^[IVX]+\.', case_tag.text.strip()):
                rom_tag = case_tag
                cap_alpha = 'A'

                if re.search(r'^I\.', case_tag.text.strip()):
                    if case_tag.find_next(class_='casenote') and re.search(r'^J\.', case_tag.find_next(
                            class_='casenote').text.strip()):
                        alpha_ul.append(case_tag)
                        cap_alpha = 'J'
                        a_tag_id = f'{rom_id}-I'

                    else:
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                        rom_id = f'#{case_tag.find_previous("h3").get("id")}-notetodecisison-I'
                        a_tag_id = rom_id
                else:
                    rom_ul.append(case_tag)

                    rom_num = re.search(r'^(?P<rid>[IVX]+)\.', case_tag.text.strip()).group("rid")
                    rom_id = f'#{case_tag.find_previous("h3").get("id")}-notetodecisison-{rom_num}'
                    a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-notetodecisison-{rom_num}'

            elif re.search(fr'^{cap_alpha}\.', case_tag.text.strip()):
                alpha_tag = case_tag
                if re.search(r'^A\.', case_tag.text.strip()):
                    alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(alpha_ul)
                    rom_tag.append(alpha_ul)
                else:
                    alpha_ul.append(case_tag)

                alpha_id = f"{rom_id}-{cap_alpha}"
                cap_alpha = chr(ord(cap_alpha) + 1)
                a_tag_id = alpha_id

            elif re.search(r'^\d+\.', case_tag.text.strip()):
                digit_tag = case_tag
                s_alpha = 'a'
                if re.search(r'^1\.', case_tag.text.strip()):
                    digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(digit_ul)
                    alpha_tag.append(digit_ul)
                    if alpha_tag:
                        alpha_tag.append(digit_ul)
                else:
                    digit_ul.append(case_tag)

                digit_num = re.search(r'^(?P<nid>\d+)\.', case_tag.text.strip()).group("nid")
                digit_id = f"{alpha_id}-{digit_num}"
                a_tag_id = f"{alpha_id}-{digit_num}"

            elif re.search(r'^—\w+', case_tag.text.strip()):
                inner_tag = case_tag
                inner_tag_text = re.sub(r'[\W\s]+', '', case_tag.text.strip()).lower()
                inner_tag_id = f'{case_head_id}-{inner_tag_text}'

                if not re.search(r'^—\w+', case_tag.find_previous("li").text.strip()):
                    inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(inner_ul_tag)
                    if case_head_tag:
                        case_head_tag.append(inner_ul_tag)
                    else:
                        inner_tag_id = f'#{case_tag.find_previous("h4").get("id")}-{inner_tag_text}'
                else:
                    inner_ul_tag.append(case_tag)

                if inner_tag_id in case_tag_id_list:
                    case_tag_id = f'{inner_tag_id}.{case_count}'
                    case_count += 1
                else:
                    case_tag_id = f'{inner_tag_id}'
                    case_count = 1

                case_tag_id_list.append(case_tag_id)
                a_tag_id = case_tag_id

            elif re.search(rf'^{s_alpha}\.', case_tag.text.strip()):
                s_alpha_tag = case_tag
                s_roman = "i"
                if re.search(r'^a\.', case_tag.text.strip()):
                    s_alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(s_alpha_ul)
                    digit_tag.append(s_alpha_ul)
                else:
                    s_alpha_ul.append(case_tag)

                s_alpha_id = f"{digit_id}-{s_alpha}"
                a_tag_id = f"{digit_id}-{s_alpha}"
                s_alpha = chr(ord(s_alpha) + 1)

            elif re.search(rf'^{s_roman}\.', case_tag.text.strip()):
                s_rom_tag = case_tag
                if re.search(r'^i\.', case_tag.text.strip()):
                    s_rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(s_rom_ul)
                    s_alpha_tag.append(s_rom_ul)
                else:
                    s_rom_ul.append(case_tag)

                a_tag_id = f"{s_alpha_id}-{s_roman}"
                s_roman = roman.toRoman(roman.fromRoman(s_roman.upper()) + 1).lower()
            else:
                if case_tag.find_previous("h4") and \
                        re.search(r'^ANNOTATIONS$', case_tag.find_previous("h4").text.strip(), re.I):
                    case_head_tag = case_tag
                    case_tag_text = re.sub(r'[\W\s]+', '', case_tag.text.strip()).lower()

                    if re.search(r'^ANNOTATIONS|^[IVX]+\.', case_tag.find_previous().text.strip()):
                        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(ul_tag)
                        if rom_tag:
                            rom_tag.append(ul_tag)
                            note_head_id = f'{rom_id}'
                        else:
                            note_head_id = f'#{case_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision'
                    else:
                        ul_tag.append(case_tag)

                    case_head_id = f'{note_head_id}-{case_tag_text}'
                    if case_head_id in case_tag_id_list:
                        case_tag_id = f'{case_head_id}.{case_count}'
                        case_count += 1
                    else:
                        case_tag_id = f'{case_head_id}'
                        case_count = 1

                    a_tag_id = f'{note_head_id}-{case_tag_text}'
                    case_tag_id_list.append(case_head_id)

            anchor = self.soup.new_tag('a', href=a_tag_id)
            anchor.string = case_tag.text
            case_tag.string = ''
            case_tag.append(anchor)

        for p_tag in self.soup.findAll('h4', string=re.compile(r'^Case Notes$')):
            case_note_tag = p_tag.find_next_sibling()
            if not case_note_tag.get("class") == [self.tag_type_dict['ol_p']]:
                case_tag_list = case_note_tag.text.splitlines()
                case_note_tag.clear()
                for tag in case_tag_list:
                    if len(tag) > 0:
                        new_ul_tag = self.soup.new_tag("li")
                        new_ul_tag.string = tag
                        new_ul_tag["class"] = "casenotes"
                        case_note_tag.append(new_ul_tag)
                case_note_tag.unwrap()

        case_count = 1
        case_tag_id_list = []

        for case_tag in self.soup.find_all("li", class_='casenotes'):
            if re.search(r'^—\w+', case_tag.text.strip()):
                inner_tag = case_tag
                inner_tag_text = re.sub(r'[\W\s]+', '', case_tag.text.strip()).lower()
                case_tag_id = f'{case_head_id}-{inner_tag_text}'

                if not re.search(r'^—\w+', case_tag.find_previous("li").text.strip()):
                    inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(inner_ul_tag)
                    case_head_tag.append(inner_ul_tag)
                else:
                    inner_ul_tag.append(case_tag)

            elif re.search(r'^— —\w+', case_tag.text.strip()):
                pass
            elif re.search(r'^— — —\w+', case_tag.text.strip()):
                pass
            elif re.search(r'^— — — —\w+', case_tag.text.strip()):
                pass
            else:
                case_head_tag = case_tag
                case_tag_text = re.sub(r'[\W\s]+', '', case_tag.text.strip()).lower()
                case_head_id = f'#{case_tag.find_previous({"h3", "h2", "h1"}).get("id")}-casenote-{case_tag_text}'

                if case_head_id in case_tag_id_list:
                    case_tag_id = f'{case_head_id}.{case_count}'
                    case_count += 1
                else:
                    case_tag_id = f'{case_head_id}'
                    case_count = 1

                if case_tag.find_previous().name != "a":
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(ul_tag)
                else:
                    ul_tag.append(case_tag)

                case_tag_id_list.append(case_head_id)

            anchor = self.soup.new_tag('a', href=case_tag_id)
            anchor.string = case_tag.text
            case_tag.string = ''
            case_tag.append(anchor)

    def create_annotation_analysis_nav_tag(self):
        """
            - Analysis classes are defined based on the header of the analysis tag.
            -  This method creates ANNOTATION  analysis nav tag

        """

        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})

        rom_tag = None
        alpha_tag = None
        a_tag_id = None
        rom_tag_id = None
        alpha_tag_id = None

        for case_tag in self.soup.find_all("p", class_=self.tag_type_dict['Analysis']):
            if re.search(r'^I\.', case_tag.text.strip()):
                case_tag_list = case_tag.text.splitlines()
                case_tag.clear()
                for tag in case_tag_list:
                    new_ul_tag = self.soup.new_tag("li")
                    new_ul_tag.string = tag
                    new_ul_tag["class"] = "annotation"
                    case_tag.append(new_ul_tag)
                case_tag.unwrap()

        for case_tag in self.soup.find_all("li", class_='annotation'):
            if re.search(rf'^[IVX]+\.', case_tag.text.strip()):
                rom_tag = case_tag
                if re.search(r'^I\.', case_tag.text.strip()):
                    if not re.search(r'^H\.', case_tag.find_previous("li").text.strip()):
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        case_tag.wrap(rom_ul)
                        rom_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-I'
                        a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-I'
                    else:
                        alpha_tag = case_tag
                        alpha_ul.append(case_tag)
                        alpha_tag_id = f'{rom_tag_id}-I'
                        a_tag_id = f'{rom_tag_id}-I'
                else:
                    rom_ul.append(case_tag)
                    rom_num = re.search(r'^(?P<rid>[IVX]+)\.', case_tag.text.strip()).group("rid")
                    rom_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-{rom_num}'
                    a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-{rom_num}'

            elif re.search(r'^[A-Z]\.', case_tag.text.strip()):
                alpha_tag = case_tag
                if re.search(r'^A\.', case_tag.text.strip()):
                    alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(alpha_ul)
                    rom_tag.append(alpha_ul)
                else:
                    alpha_ul.append(case_tag)

                alpha = re.search(r'^(?P<aid>[A-Z])\.', case_tag.text.strip().strip())
                alpha_tag_id = f'{rom_tag_id}-{alpha.group("aid")}'
                a_tag_id = f'{rom_tag_id}-{alpha.group("aid")}'

            elif re.search(r'^\d+\.', case_tag.text.strip().strip()):
                if re.search(r'^1\.', case_tag.text.strip().strip()):
                    digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    case_tag.wrap(digit_ul)
                    alpha_tag.append(digit_ul)
                else:
                    digit_ul.append(case_tag)
                digit = re.search(r'^(?P<nid>\d+)\.', case_tag.text.strip().strip()).group("nid")
                a_tag_id = f'{alpha_tag_id}-{digit}'

            anchor = self.soup.new_tag('a', href=a_tag_id)
            anchor.string = case_tag.text
            case_tag.string = ''
            case_tag.append(anchor)

    def create_Notes_to_decision_analysis_nav_tag_con(self):
        case_tag_id = None
        case_head_id = None
        case_head_tag = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        rom_tag = None

        for note_tag in self.soup.find_all():
            if note_tag.name == "h4":
                case_tag_id = None
                case_head_id = None
                case_head_tag = None
                inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                rom_tag = None

            elif note_tag.name == "li" and note_tag.get("class") == "note":
                if re.search(r'^[IVX]+\.', note_tag.text.strip()):
                    rom_tag = note_tag
                    rom_num = re.search(r'^(?P<id>[IVX]+)\.', note_tag.text.strip()).group("id")
                    if re.search(r'^I\.', note_tag.text.strip()):
                        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(rom_ul)
                    else:
                        rom_ul.append(note_tag)
                    rom_tag_id = f'#{note_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{rom_num}'
                    case_tag_id = f'#{note_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{rom_num}'

                elif re.search(r'^—\w+', note_tag.text.strip()):
                    inner_tag = note_tag
                    inner_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                    inner_tag_id = f'{case_head_id}-{inner_tag_text}'
                    case_tag_id = f'{case_head_id}-{inner_tag_text}'
                    if not re.search(r'^—\w+', note_tag.find_previous("li").text.strip()):
                        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(inner_ul_tag)
                        if case_head_tag:
                            case_head_tag.append(inner_ul_tag)
                    else:
                        inner_ul_tag.append(note_tag)

                elif re.search(r'^— —\w+', note_tag.text.strip()):
                    inner_li_tag = note_tag
                    inner_li_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                    case_tag_id = f'{inner_tag_id}-{inner_li_tag_text}'
                    if not re.search(r'^— —\w+', note_tag.find_previous("li").text.strip()):
                        inner_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(inner_ul_tag1)
                        inner_tag.append(inner_ul_tag1)
                    else:
                        inner_ul_tag1.append(note_tag)
                else:
                    case_head_tag = note_tag
                    case_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()

                    if re.search(r'^Notes to Decisions|^[IVX]+\.', note_tag.find_previous().text.strip()):
                        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(ul_tag)
                        if rom_tag:
                            rom_tag.append(ul_tag)
                            note_head_id = f'{rom_tag_id}'
                        else:
                            note_head_id = f'#{note_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision'
                    else:
                        ul_tag.append(note_tag)

                    case_head_id = f'{note_head_id}-{case_tag_text}'
                    case_tag_id = f'{note_head_id}-{case_tag_text}'

                anchor = self.soup.new_tag('a', href=case_tag_id)
                anchor.string = note_tag.text
                note_tag.string = ''
                note_tag.append(anchor)

    def create_Notes_to_decision_analysis_nav_tag(self):
        """
           - Analysis classes are defined based on the header of the analysis tag.
           -  This method creates NOTES TO DECISION  analysis nav tag

        """
        case_tag_id = None
        case_head_id = None
        case_head_tag = None
        note_head_tag = None
        note_id = None
        note_inner_tag = None
        note_inr_id = None
        inner_tag_id = None
        doubledash_inner_tag_id = None
        inner_tag = None
        doubledash_inner_tag = None
        subsection_tag = None
        doubledash_inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        note_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_inner1_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        tripledash_inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
        note_tag_id: list = []
        count = 1
        inr_count = 1

        for note_tag in self.soup.find_all("li", class_="note"):
            if re.search(r'^—?\d+\.?\s*—\s*(\w+|“)', note_tag.text.strip()):
                inner_tag = note_tag
                inner_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                inner_tag_id = f'{case_head_id}-{inner_tag_text}'

                if not re.search(r'^—?\d+\.?\s*—\s*(\w+|“)', note_tag.find_previous("li").text.strip()):
                    inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(inner_ul_tag)
                    case_head_tag.append(inner_ul_tag)
                else:
                    inner_ul_tag.append(note_tag)

                if inner_tag_id in note_tag_id:
                    inner_tag_id = f'{inner_tag_id}.{inr_count:02}'
                    inr_count += 1
                else:
                    inner_tag_id = f'{inner_tag_id}'
                    inr_count = 1

                case_tag_id = f'{inner_tag_id}'
                note_tag_id.append(case_tag_id)

            elif re.search(r'^—?\d+\.?\s*—\s*—\s*(\w+|“)', note_tag.text.strip()):
                doubledash_inner_tag = note_tag
                doubledash_inner_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                doubledash_inner_tag_id = f'{inner_tag_id}-{doubledash_inner_tag_text}'

                if doubledash_inner_tag_id in note_tag_id:
                    doubledash_inner_tag_id = f'{doubledash_inner_tag_id}.{inr_count:02}'
                    inr_count += 1
                else:
                    doubledash_inner_tag_id = f'{doubledash_inner_tag_id}'
                    inr_count = 1

                case_tag_id = f'{doubledash_inner_tag_id}'
                note_tag_id.append(case_tag_id)

                if not re.search(r'^—?\d+\.?\s*—\s*—\s*(\w+|“)', note_tag.find_previous("li").text.strip()):
                    doubledash_inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(doubledash_inner_ul_tag)
                    inner_tag.append(doubledash_inner_ul_tag)
                else:
                    doubledash_inner_ul_tag.append(note_tag)

            elif re.search(r'^—?\d+\.?\s*—\s*—\s*—\s*(\w+|“)', note_tag.text.strip()):
                tripledash_inner_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                tripledash_inner_tag_id = f'{doubledash_inner_tag_id}-{tripledash_inner_tag_text}'

                if tripledash_inner_tag_id in note_tag_id:
                    tripledash_inner_tag_id = f'{tripledash_inner_tag_id}.{inr_count:02}'
                    inr_count += 1
                else:
                    tripledash_inner_tag_id = f'{tripledash_inner_tag_id}'
                    inr_count = 1
                case_tag_id = f'{tripledash_inner_tag_id}'
                note_tag_id.append(case_tag_id)

                if not re.search(r'^—?\d+\.?\s*—\s*—\s*—\s*(\w+|“)', note_tag.find_previous("li").text.strip()):
                    tripledash_inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(tripledash_inner_ul_tag)
                    doubledash_inner_tag.append(tripledash_inner_ul_tag)
                else:
                    tripledash_inner_ul_tag.append(note_tag)

            elif re.search(r'^\d+\.?\s*—\s*—\s*—\s*—\s*(\w+|“)', note_tag.text.strip()):
                pass

            elif re.search(r'^[IVX]+\.', note_tag.text.strip()):
                rom_tag = note_tag
                rom_num = re.search(r'^(?P<id>[IVX]+)\.', note_tag.text.strip()).group("id")
                if re.search(r'^I\.', note_tag.text.strip()):
                    rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(rom_ul)
                else:
                    rom_ul.append(note_tag)
                case_tag_id = f'#{note_tag.find_previous({"h4", "h3", "h2", "h1"}).get("id")}-notetodecision-{rom_num}'
            else:
                case_head_tag = note_tag
                case_tag_text = re.sub(r'[\W\s]+', '', note_tag.text.strip()).lower()
                if re.search(r'^\d+\.?', note_tag.text.strip()):
                    if re.search(r'^0\.5\.?', note_tag.text.strip()):
                        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(ul_tag)

                    elif re.search(r'^1\.', note_tag.text.strip()):
                        if note_tag.find_previous("li") and \
                                re.search(r'^0\.5\.?', note_tag.find_previous("li").text.strip()):
                            ul_tag.append(note_tag)

                        else:
                            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            note_tag.wrap(ul_tag)
                            if subsection_tag:
                                subsection_tag.append(ul_tag)
                    else:
                        if note_tag.find_previous().name != 'a':
                            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            note_tag.wrap(ul_tag)
                        else:
                            ul_tag.append(note_tag)

                    case_head_id = f'#{note_tag.find_previous({"h4", "h3", "h2", "h1"}).get("id")}-{case_tag_text}'
                    case_tag_id = f'#{note_tag.find_previous({"h4", "h3", "h2", "h1"}).get("id")}-{case_tag_text}'

                elif re.search(r'^(FIRST|SECOND|THIRD) SUBSECTION', note_tag.text.strip()):
                    subsection_tag = note_tag
                    if re.search(r'^FIRST SUBSECTION', note_tag.text.strip()):
                        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(new_ul_tag)
                    else:
                        new_ul_tag.append(note_tag)

                else:
                    if re.search(r'^—\w+', note_tag.text.strip()):
                        if not re.search(r'^—\w+', note_tag.find_previous("li").text.strip()):
                            note_inner_tag = note_tag
                            note_inner_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            note_tag.wrap(note_inner_ul)
                            if note_head_tag:
                                note_head_tag.append(note_inner_ul)
                            else:
                                note_id = f'{note_tag.find_previous("h3").get("id")}-casenote'
                        else:
                            note_inner_ul.append(note_tag)

                        note_inr_id = f'{note_id}-{case_tag_text}'

                        if note_inr_id in note_tag_id:
                            case_tag_id = f'{note_inr_id}.{inr_count:02}'
                            inr_count += 1
                        else:
                            case_tag_id = f'{note_inr_id}'
                            inr_count = 1

                        note_tag_id.append(note_inr_id)

                    elif re.search(r'^— —\w+', note_tag.text.strip()):
                        if not re.search(r'^— —\w+', note_tag.find_previous("li").text.strip()):
                            note_inner1_tag = note_tag
                            note_inner1_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            note_tag.wrap(note_inner1_ul)
                            note_inner_tag.append(note_inner1_ul)
                        else:

                            note_inner1_ul.append(note_tag)

                        note_inr1_id = f'{note_inr_id}-{case_tag_text}'

                        if note_inr1_id in note_tag_id:
                            case_tag_id = f'{note_inr1_id}.{inr_count:02}'
                            inr_count += 1
                        else:
                            case_tag_id = f'{note_inr1_id}'
                            inr_count = 1

                        note_tag_id.append(note_inr1_id)

                    else:
                        note_head_tag = note_tag
                        note_head_id = f'#{note_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{case_tag_text}'

                        if note_head_id in note_tag_id:
                            case_tag_id = f'{note_head_id}.{count:02}'
                            count += 1
                        else:
                            case_tag_id = f'{note_head_id}'
                            count = 1

                        if note_tag.find_previous().name != "a":
                            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            note_tag.wrap(ul_tag)
                        else:
                            ul_tag.append(note_tag)

                        note_id = case_tag_id

                        note_tag_id.append(note_head_id)

            anchor = self.soup.new_tag('a', href=case_tag_id)
            anchor.string = note_tag.text
            note_tag.string = ''
            note_tag.append(anchor)

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
            if sec_header:
                while True:
                    next_sec_tag = sec_header.find_next_sibling()
                    if sec_header.name == 'h3':
                        new_sec_div = self.soup.new_tag('div')
                        tag_to_wrap = sec_header.find_next_sibling()
                        sec_header.wrap(new_sec_div)
                        while True:
                            if tag_to_wrap:
                                next_tag = tag_to_wrap.find_next_sibling()
                            else:
                                break
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
                            if not re.search(r'h\d', str(tag_to_wrap.name)):
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

        logger.info("wrapped inside div tags")

    def wrap_inside_main_tag(self):

        """wrap inside main tag"""

        main_tag = self.soup.new_tag('main')
        chap_nav = self.soup.find('nav')
        ul = self.soup.find("ul")
        if ul:
            if ul.find_previous("p", string=re.compile(r'^[A-Za-z]')):
                ul.find_previous("p", string=re.compile(r'^[A-Za-z]')).wrap(chap_nav)
            self.soup.find("ul").wrap(chap_nav)
        tag_to_wrap = chap_nav.find_next_sibling()
        while True:
            next_tag = tag_to_wrap.find_next_sibling()
            main_tag.append(tag_to_wrap)
            if not next_tag:
                chap_nav.insert_after(main_tag)
                break
            tag_to_wrap = next_tag

        logger.info("wrapped inside main tag")

    def post_process(self):
        """
             adding css file
             wrapping watermark tag and head tag inside nav tag
             clean HTML
        """

        "adding css file"
        stylesheet_link_tag = self.soup.new_tag('link')
        stylesheet_link_tag.attrs = {'rel': 'stylesheet', 'type': 'text/css',
                                     'href': 'https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css'}
        self.soup.style.replace_with(stylesheet_link_tag)
        self.meta_tags.append(copy.copy(stylesheet_link_tag))

        "adding watermark"
        watermark_p = self.soup.new_tag('p', **{"class": "transformation"})
        watermark_p.string = self.watermark_text.format(self.release_number, self.release_date,
                                                        datetime.now().date())
        self.soup.find("nav").insert(0, watermark_p)

        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()

        "adding watermark tag inside meta data"
        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)

        "clean HTML"
        [text_junk.decompose() for text_junk in
         self.soup.find_all("p", class_=self.tag_type_dict['junk1'])]

        [tag.decompose() for tag in self.soup.find_all("p", string=re.compile(r'——————————'))]

        for junk_tag in self.soup.find_all(class_=self.junk_tag_class):
            junk_tag.unwrap()

        for tag in self.soup.findAll():
            if len(tag.contents) == 0:
                if tag.name == 'meta':
                    if tag.attrs.get('http-equiv') == 'Content-Style-Type':
                        tag.decompose()
                        continue
                    self.meta_tags.append(copy.copy(tag))
                elif tag.name == 'br':
                    if not tag.parent or tag in tag.parent.contents:
                        tag.decompose()
                continue

            if tag.name == "ul" and tag.li and re.search(r'p\d+',
                                                         str(tag.li.get("class"))) and tag.parent.name != "nav":
                tag.wrap(self.soup.new_tag("nav"))

        clss = re.compile(r'p\d+')
        for all_tag in self.soup.findAll(class_=clss):
            del all_tag["class"]

        for tag in self.soup.find_all(class_="navhead"):
            del tag["id"]

        for tag in self.soup.find_all(class_="navhead1"):
            del tag["id"]

        logger.info("clean HTML is processed")
        return self.soup

    def write_soup_to_file(self):
        """
            - add the space before self-closing meta tags
            - replace <br/> to <br /> and & to &amp;
            - convert html to str
            - write html str to an output file

        """
        soup_str = str(self.soup.prettify(formatter=None))

        for tag in self.meta_tags:
            cleansed_tag = re.sub(r'/>', ' />', str(tag))
            soup_str = re.sub(rf'{tag}', rf'{cleansed_tag}', soup_str, re.I)

        with open(
                f"/home/mis/PycharmProjects/cic_code_framework/transforms_output/{self.state_key.lower()}/oc{self.state_key.lower()}/r{self.release_number}/{self.input_file_name}",
                "w") as file:
            soup_str = getattr(self.parser_obj, "amp_pattern").sub('&amp;', soup_str)
            soup_str = getattr(self.parser_obj, "br_pattern").sub('<br />', soup_str)
            soup_str = re.sub(r'<span class.*?>\s*</span>|<p>\s*</p>', '', soup_str)
            soup_str = soup_str.replace('=“”>', '=“”&gt;')

            file.write(soup_str)

        logger.info(f"parsing {self.input_file_name} is completed")

    def replace_h3_tags_con(self):
        count = 1
        for header_tag in self.soup.find_all(class_=self.tag_type_dict["head3"]):
            if self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()):
                header_tag.name = "h3"
                chap_no = self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()).group('id')

                if header_tag.find_previous("h4") and \
                        self.regex_pattern_obj.h2_article_pattern_con.search(
                            header_tag.find_previous("h4").text.strip()):
                    header_tag.name = "h5"
                    header_tag_id = f'{header_tag.find_previous("h4").get("id")}-s{chap_no.zfill(2)}'
                elif header_tag.find_previous("h3") and \
                        self.regex_pattern_obj.amend_pattern_con.search(
                            header_tag.find_previous("h3").text.strip()):
                    header_tag.name = "h4"
                    header_tag_id = f'{header_tag.find_previous("h3").get("id")}-s{chap_no.zfill(2)}'
                else:
                    header_tag_id = f'{header_tag.find_previous("h2", class_={"oneh2", "gen"}).get("id")}-s{chap_no.zfill(2)}'

                if header_tag.find_previous({"h3", "h4"}, id=header_tag_id):
                    header_tag["id"] = f'{header_tag_id}.{count:02}'
                    count += 1
                else:
                    header_tag["id"] = f'{header_tag_id}'
                    count = 1

                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def replace_tags_constitution(self):
        h4_count = 1
        h3_id_list = []
        h2_id_list = []
        count = 1
        self.get_h2_order()
        for header_tag in self.soup.find_all("p"):
            if header_tag.get("class") == [self.tag_type_dict["head1"]]:
                if self.regex_pattern_obj.h1_pattern_con.search(header_tag.text.strip()):
                    header_tag.name = "h1"
                    title_no = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    self.title = title_no
                    header_tag["class"] = "title"
                    header_tag["id"] = f't{title_no}'
                    header_tag.wrap(self.soup.new_tag("nav"))
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif header_tag.get("class") == [self.tag_type_dict["head2"]]:
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                header_tag_text = re.sub(r'\W+', '', header_tag.text.strip())
                text = re.search(r'^(\S+)', header_tag.text.strip()).group().lower()
                if text == self.h2_order[0]:
                    pattern = f'h2_{text}_pattern_con'
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(header_tag.text.strip()):
                        header_tag.name = "h2"
                        chap_no = instance.search(header_tag.text.strip()).group('id')
                        header_tag_id = f'{header_tag.find_previous("h1").get("id")}{text[:2]}{chap_no.zfill(2)}'
                        if header_tag_id in self.h2_rep_id:
                            header_tag["id"] = f'{header_tag_id}.{self.h2_id_count:02}'
                            self.h2_id_count += 1
                        else:
                            header_tag["id"] = f'{header_tag_id}'
                            self.h2_id_count = 1

                        header_tag["class"] = "oneh2"
                        self.h2_rep_id.append(header_tag_id)

                elif text == self.h2_order[1]:
                    self.set_id_for_h2_tags_con(header_tag, text, prev="oneh2", cur="twoh2")

                elif text == self.h2_order[2]:
                    self.set_id_for_h2_tags_con(header_tag, text, prev={"twoh2", "oneh2"}, cur="threeh2")

                elif text == self.h2_order[3]:
                    self.set_id_for_h2_tags_con(header_tag, text, prev={"oneh2", "twoh2", "threeh2"}, cur="fourh2")

                if re.search(r'^Amendment (\d+|[IVX]+)', header_tag.text.strip(), re.I):
                    header_tag.name = "h3"
                    tag_num = re.search(r'^(?P<amd_txt>Amendment (?P<id>\d+|[IVX]+))', header_tag.text.strip(), re.I)

                    if re.search(f'{tag_num.group("amd_txt")}', self.soup.find("ul").text.strip()):
                        header_tag.name = "h2"
                        header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}am{tag_num.group('id').zfill(2)}"
                    else:
                        header_tag["id"] = f"{header_tag.find_previous('h2').get('id')}-{tag_num.group('id').zfill(2)}"

                    header_tag["class"] = "gen"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif re.search(r'^PREAMBLE|^AMENDMENTS|^Schedule', header_tag.text.strip(), re.I) or \
                        self.h2_pattern_text and header_tag.text.strip() in self.h2_pattern_text:
                    header_tag.name = "h2"
                    tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}-{tag_text}"
                    header_tag["class"] = "gen"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()):
                    if re.search(r'§ 4\. Power inherent in the', header_tag.text.strip()):
                        print()

                    header_tag.name = "h3"
                    chap_no = self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()).group('id')
                    header_tag_id = f'{header_tag.find_previous("h2", class_={"oneh2", "gen"}).get("id")}-s{chap_no.zfill(2)}'

                    if header_tag.find_previous("h3", id=header_tag_id):
                        header_tag_id = f'{header_tag_id}.{count:02}'
                        header_tag["id"] = f'{header_tag_id}.{count:02}'
                        count += 1
                    else:
                        header_tag["id"] = f'{header_tag_id}'
                        count = 1
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif self.h2_text_con and header_tag_text in self.h2_text_con:
                    header_tag.name = "h2"
                    header_tag["id"] = f'{self.soup.find("h1").get("id")}-{header_tag_text.lower()}'
                    header_tag["class"] = "oneh2"

                elif self.h2_pattern_text_con:
                    for list_pattern in self.h2_pattern_text_con:
                        h2_pattern = re.compile(list_pattern)
                        if h2_tag := h2_pattern.search(header_tag.text.strip()):
                            header_tag.name = "h2"
                            header_tag["class"] = "amd"
                            header_tag[
                                "id"] = f'{header_tag.find_previous("h2", class_="gen").get("id")}-amd{h2_tag.group("id").zfill(2)}'

                elif self.h2_text_con and header_tag_text in self.h2_text_con:
                    header_tag.name = "h2"
                    p_tag_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                    header_tag_id = f'{self.soup.find("h1").get("id")}-{p_tag_text}'

                    if header_tag_id in self.h2_rep_id:
                        header_tag["id"] = f'{header_tag_id}.{self.h2_id_count:02}'
                        self.h2_id_count += 1
                    else:
                        header_tag["id"] = f'{header_tag_id}'
                        self.h2_id_count = 1
                    header_tag["class"] = "oneh2"
                    self.h2_rep_id.append(header_tag['id'])

            elif header_tag.get("class") == [self.tag_type_dict["head3"]]:
                if re.search(r'^PREAMBLE|^AMENDMENTS|^Schedule', header_tag.text.strip(), re.I):
                    header_tag.name = "h2"
                    tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}-{tag_text}"
                    header_tag["class"] = "gen"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()):
                    header_tag.name = "h3"
                    chap_no = self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()).group('id')
                    header_tag[
                        "id"] = f'{header_tag.find_previous({"h2", "h3"}, class_={"oneh2", "gen", "amd"}).get("id")}-s{chap_no.zfill(2)}'
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                if self.h3_pattern_text_con:
                    for list_pattern in self.h3_pattern_text_con:
                        h3_pattern = re.compile(list_pattern)
                        if h3_tag := h3_pattern.search(header_tag.text.strip()):
                            header_tag.name = "h3"
                            sec_id = h3_tag.group("id")
                            if header_tag.find_previous("h2", class_={"oneh2", "twoh2", "threeh2"}):
                                header_tag_id = f'{header_tag.find_previous("h2", class_={"oneh2", "twoh2", "threeh2"}).get("id")}s{sec_id.zfill(2)}'
                                if header_tag_id in h3_id_list:
                                    header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                                    self.h3_count += 1
                                else:
                                    header_tag["id"] = f'{header_tag_id}'
                                    self.h3_count = 1
                            else:
                                header_tag_id = f'{header_tag.find_previous("h1").get("id")}s{sec_id.zfill(2)}'
                                if header_tag_id in h3_id_list:
                                    header_tag["id"] = f'{header_tag_id}.{self.h3_count:02}'
                                    self.h3_count += 1
                                else:
                                    header_tag["id"] = f'{header_tag_id}'
                                    self.h3_count = 1

                            h3_id_list.append(header_tag_id)

            elif header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if header_tag.text.strip() in self.h4_head:
                    self.replace_h4_tag_titles(header_tag, h4_count, None)
                    h4_count += 1
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif header_tag.get("class") == [self.tag_type_dict["ul"]]:
                if not re.search(r'^(Section\.?|Chapter|Sec\.|Article|Amendment)$', header_tag.text.strip()):
                    header_tag.name = "li"
                    header_tag.wrap(self.ul_tag)

    def add_anchor_tags_con(self):
        for li_tag in self.soup.findAll():
            if li_tag.name == "li":
                li_tag_text = re.sub(r'\W+', '', li_tag.text.strip())
                text = re.search(r'^\S+', li_tag.text.strip()).group().lower()
                pattern = f'h2_{text}_pattern_con'
                if text == self.h2_order[0]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.c_nav_count += 1
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag=f"{text[:2]}",
                                                    prev_id=li_tag.find_previous("h1").get("id"),
                                                    cnav=f'cnav{self.c_nav_count:02}')
                elif text == self.h2_order[1]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()) and instance.search(li_tag.text.strip()).group('id'):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.c_nav_count += 1
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag=f"{text[:2]}",
                                                    prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                    cnav=f'cnav{self.c_nav_count:02}')
                elif text == self.h2_order[2]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.c_nav_count += 1
                        if li_tag.find_previous("h2", class_="twoh2"):
                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag=f"{text[0]}",
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'cnav{self.c_nav_count:02}')
                elif text == self.h2_order[3]:
                    instance = getattr(self.parser_obj, pattern)
                    if instance.search(li_tag.text.strip()):
                        chap_num = instance.search(li_tag.text.strip()).group('id')
                        self.c_nav_count += 1

                        if li_tag.find_previous("h2", class_="threeh2"):
                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag=f"{text[0]}",
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'cnav{self.c_nav_count:02}')
                elif self.regex_pattern_obj.h2_article_pattern_con.search(li_tag.text.strip()):
                    chap_num = self.regex_pattern_obj.h2_article_pattern_con.search(li_tag.text.strip()).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-ar",
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

                elif self.regex_pattern_obj.section_pattern_con.search(li_tag.text.strip()):
                    chap_num = self.regex_pattern_obj.section_pattern_con.search(li_tag.text.strip()).group("id")
                    self.s_nav_count += 1
                    if self.regex_pattern_obj.section_pattern_con1.search(li_tag.text.strip()):
                        if li_tag.find_previous("h3", class_={"oneh2", "gen", "amend"}):
                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag="-s",
                                                        prev_id=li_tag.find_previous("h3", class_={"oneh2", "gen",
                                                                                                   "amend"}).get("id"),
                                                        cnav=f'snav{self.s_nav_count:02}')
                        else:

                            self.set_chapter_section_id(li_tag, chap_num,
                                                        sub_tag="-s",
                                                        prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                        cnav=f'snav{self.s_nav_count:02}')

                    elif li_tag.find_previous("h4") and \
                            self.regex_pattern_obj.h2_article_pattern_con.search(
                                li_tag.find_previous("h4").text.strip()):
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag="-s",
                                                    prev_id=li_tag.find_previous("h4").get("id"),
                                                    cnav=f'snav{self.s_nav_count:02}')

                    elif li_tag.find_previous("h3") and \
                            self.regex_pattern_obj.amend_pattern_con.search(
                                li_tag.find_previous("h3").text.strip()):
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag="-s",
                                                    prev_id=li_tag.find_previous("h3").get("id"),
                                                    cnav=f'snav{self.s_nav_count:02}')

                    else:
                        self.set_chapter_section_id(li_tag, chap_num,
                                                    sub_tag="-s",
                                                    prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                    cnav=f'snav{self.s_nav_count:02}')

                elif re.search(r'^PREAMBLE|^AMENDMENTS|^Schedule', li_tag.text.strip(), re.I) or \
                        self.h2_pattern_text and li_tag.text.strip() in self.h2_pattern_text:
                    chap_num = re.sub(r'[\W\s]+', '', li_tag.text.strip()).lower()
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous('h1').get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
                elif self.regex_pattern_obj.amend_pattern_con.search(li_tag.text.strip()):
                    chap_num = self.regex_pattern_obj.amend_pattern_con.search(li_tag.text.strip()).group("id")
                    self.a_nav_count += 1
                    self.set_chapter_section_id(li_tag, chap_num,
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous({"h2", "h1"}).get("id"),
                                                cnav=f'amnav{self.a_nav_count:02}')

                elif self.h2_text_con and li_tag_text in self.h2_text_con:
                    if li_tag.find_previous("li") and li_tag.find_previous("li").get("id"):
                        self.chp_nav_count = int(
                            re.search(r'(c|s|am|a)nav(?P<ncount>\d+)',
                                      li_tag.find_previous("li").get("id").strip()).group(
                                "ncount")) + 1
                    else:
                        self.chp_nav_count += 1
                    self.set_chapter_section_id(li_tag, li_tag_text.lower(),
                                                sub_tag="-",
                                                prev_id=li_tag.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.chp_nav_count:02}')
                elif self.h3_pattern_text_con:
                    for list_pattern in self.h3_pattern_text_con:
                        h3_pattern = re.compile(list_pattern)
                        if h3_tag := h3_pattern.search(li_tag.text.strip()):
                            self.s_nav_count += 1
                            self.set_chapter_section_id(li_tag, h3_tag.group("id"),
                                                        sub_tag='s',
                                                        prev_id=li_tag.find_previous(
                                                            class_={"navhead1", "navhead", "oneh2", "twoh2",
                                                                    "threeh2"}).get(
                                                            "id"),
                                                        cnav=f'snav{self.s_nav_count:02}')
            elif li_tag.name in ['h2', 'h3', 'h4']:
                self.a_nav_count = 0
                self.c_nav_count = 0
                self.p_nav_count = 0
                self.s_nav_count = 0

    def create_analysis_nav_tag_con(self):
        pass

    def run_constitution(self):
        """calling methods to parse the passed constitution htmls"""

        self.set_page_soup()
        self.set_release_date()
        self.pre_process()
        self.generate_class_name_dict()
        self.replace_tags_constitution()
        self.wrap_inside_main_tag()
        self.add_anchor_tags_con()
        self.convert_paragraph_to_alphabetical_ol_tags()
        self.create_analysis_nav_tag()
        self.wrap_div_tags()
        self.post_process()
        self.validating_broken_links()
        self.write_soup_to_file()

    def run_titles(self):

        """calling methods to parse the passed title htmls"""

        self.set_page_soup()
        self.set_release_date()
        self.pre_process()
        self.generate_class_name_dict()
        self.replace_tags_titles()
        self.wrap_inside_main_tag()
        self.add_anchor_tags()
        self.convert_paragraph_to_alphabetical_ol_tags()
        self.create_analysis_nav_tag()
        self.wrap_div_tags()
        self.creating_formatted_table()
        self.post_process()
        self.storing_header_ids()
        self.validating_broken_links()
        self.write_soup_to_file()

    def run(self):
        logger.info(self.meta_data)
        start_time = datetime.now()
        logger.info(start_time)

        if re.search('constitution', self.input_file_name):
            self.run_constitution()
        else:
            self.run_titles()

        logger.info(datetime.now() - start_time)
        return str(self.soup.prettify(formatter=None)), self.meta_tags

    def storing_header_ids(self):
        title_id = re.search(r'(?P<tid>(\d+[A-Z]?\.\d+[A-Z]?)|\d+(\w)*|\d+(\.\w+)*)', self.input_file_name).group("tid")
        if not os.path.exists(f'{self.state_key}_cite_id'):
            os.mkdir(f'{self.state_key}_cite_id')
        if not os.path.exists(f'{self.state_key}_cite_id/{self.state_key}{self.release_number}'):
            os.mkdir(f'{self.state_key}_cite_id/{self.state_key}{self.release_number}')

        with open(
                f'{self.state_key}_cite_id/{self.state_key}{self.release_number}/{self.state_key}{self.release_number}_{title_id}_ids.txt',
                "w") as file:
            list_of_ids = []
            for tag in self.soup.find_all({'h3', "li"}):
                if tag.name == "h3" and tag.get("id"):
                    key = re.search(r'.+(s|c)(?P<sec_id>.+)$', tag.get("id").strip()).group("sec_id")
                    value = tag.get("id")
                    list_of_ids.append(f'{key} {value}\n')
                elif tag.name == "li" and tag.get("id") and tag.parent.name == "ol":
                    if re.search(r'.+s(?P<sec_id>.+)$', tag.get("id").strip()):
                        key = re.search(r'.+s(?P<sec_id>.+)$', tag.get("id").strip()).group("sec_id")
                        value = tag.get("id")
                        list_of_ids.append(f'{key} {value}\n')
            file.writelines(list_of_ids)

    def validating_broken_links(self):
        header_id_list: list = []
        for head_tag in self.soup.find_all({'h2', 'h3', 'h5', 'table'}):
            if head_tag.get("id"):
                header_id_list.append(head_tag.get("id"))

        for li_tag in self.soup.find_all("li"):
            if li_tag.a and li_tag.a.get("href"):
                href_to_id = re.sub(r'#', '', li_tag.a.get("href").strip())
                if href_to_id not in header_id_list:
                    print(li_tag)
                    li_tag.a.unwrap()
                    logger.warning(
                        f"*{li_tag.text.strip()}* is invalid link in r{self.release_number}f{self.input_file_name}")

        logger.info("validated for broken links")

    def creating_formatted_table(self):
        pass

    def format_id(self, sec_id, tag):
        pass

    def h2_set_id(self, header_tag):
        pass

    def get_h2_order(self):
        if len(self.h2_order) < 4:
            self.h2_order += [""] * (abs(4 - len(self.h2_order)))
            logger.warning("appending empty element to h2_order list")
        elif len(self.h2_order) > 4:
            logger.warning("ignoring elements of he_order list after 4 elements")
