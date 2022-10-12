import re


class RegexPatterns:
    """ BASE PATTERNS"""
    h1_pattern = re.compile(r'title (?P<id>\d+(\.\d+)*)', re.I)
    h2_chapter_pattern = re.compile(r'^chapter\s(?P<id>\d+([a-zA-Z])*)', re.I)
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+([a-zA-Z])*)', re.I)
    h2_part_pattern = re.compile(r'^part\s(?P<id>(\d+([a-zA-Z])*)|([IVX]+)*)', re.I)
    h2_subtitle_pattern = re.compile(r'^Subtitle\s*(?P<id>\d+)', re.I)
    section_pattern_con1 = re.compile(r'^Section (?P<id>\d+)')
    amend_pattern_con = re.compile(r'^AMENDMENT (?P<id>\d+)', re.I)
    amp_pattern = re.compile(r'&(?!amp;)')
    br_pattern = re.compile(r'<br/>')
    cite_pattern = None
    code_pattern = None
    h1_pattern_con = None
    h2_article_pattern_con = None
    section_pattern_con = None
    article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+(\w)?)')
    section_pattern_1 = None


class CustomisedRegexGA(RegexPatterns):
    """ Customised regex patterns for GA code"""

    section_pattern = re.compile(r'^(?P<id>\d+-\d+([a-z])?-\d+(\.\d+)?)', re.I)
    ul_pattern = re.compile(r'^(?P<id>\d+([A-Z])?)', re.I)
    rule_pattern = re.compile(r'^Rule (?P<id>\d+(-\d+-\.\d+)*(\s\(\d+\))*)\.', re.I)

    h1_pattern_con = re.compile(r'^Constitution of the United States|'
                                r'^CONSTITUTION OF THE STATE OF VERMONT', re.I)
    h2_chapter_pattern_con = re.compile(r'^chapter\s*(?P<id>[IVX]+)', re.I)
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+)\.*', re.I)
    section_pattern_con = re.compile(r'^(Article|§)\s*(?P<id>\d+(-[A-Z])*)\.')
    h2_amendment_pattern_con = re.compile(r'^AMENDMENT (?P<id>[IVX]+)\.*', re.I)

    cite_pattern = re.compile(r'\b((?P<cite>(?P<title>\d{1,2})-(?P<chap>\d(\w+)?)-(?P<sec>\d+(\.\d+)?))(\s?(\(('
                              r'?P<ol>\w+)\))+)?)')

    code_pattern = re.compile(r"|\d+ Ga.( App.)? \d+"
                              r"|\d+ S.E.(2d)? \d+"
                              r"|\d+ U.S.C. § \d+(\(\w\))?"
                              r"|\d+ S\. (Ct\.) \d+"
                              r"|\d+ L\. (Ed\.) \d+"
                              r"|\d+ L\.R\.(A\.)? \d+"
                              r"|\d+ Am\. St\.( R\.)? \d+"
                              r"|\d+ A\.L\.(R\.)? \d+")

    cite_tag_pattern = re.compile(r"§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                  r"|\d+ Ga.( App.)? \d+"
                                  r"|\d+ S.E.(2d)? \d+"
                                  r"|\d+ U.S.C. § \d+(\(\w\))?"
                                  r"|\d+ S\. (Ct\.) \d+"
                                  r"|\d+ L\. (Ed\.) \d+"
                                  r"|\d+ L\.R\.(A\.)? \d+"
                                  r"|\d+ Am\. St\.( R\.)? \d+"
                                  r"|\d+ A\.L\.(R\.)? \d+")


class CustomisedRegexVA(RegexPatterns):
    """ Customised regex patterns for VA code"""

    h2_subtitle_pattern = re.compile(r'^subtitle\s(?P<id>[IVX]+([a-zA-Z])*)', re.I)
    h2_part_pattern = re.compile(r'^part\s(?P<id>([A-Z]))', re.I)
    h2_chapter_pattern = re.compile(r'^chapter\s(?P<id>\d+(\.\d+(:1\.)*?)*)', re.I)
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+((\.\d+)*?[a-zA-Z])*)', re.I)

    section_pattern = re.compile(
        r'^§+\s(?P<id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*(:\d+)*(\.\d+)*(\.\d+)*)\.*\s*', re.I)

    cite_pattern = re.compile(
        r'(?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*(\.\s:\d+)*(?P<ol>(\([a-z]\))(\(\d+\))*)*)')
    code_pattern = re.compile(r'(\d+\sVa.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*))')


class CustomisedRegexAK(RegexPatterns):
    """ Customised regex patterns for AK code"""

    section_pattern = re.compile(r'^Sec\.\s*?(?P<id>\d+\.\d+\.\d+)\.')
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)\.\d+\.\d+)(?P<ol>(\([a-z]\))(\(\d+\))*(\(\w+\))*)*)')
    code_pattern = re.compile(r'\d+ AAC \d+, art\. \d+\.|State v\. Yi, \d+ P\.\d+d \d+')

    h1_pattern_con = re.compile(r'The Constitution of the State')
    h2_article_pattern_con = re.compile(r'^Article (?P<id>[IVX]+)', re.I)
    section_pattern_con = re.compile(r'^Section (?P<id>\d+)\.')

    cite_tag_pattern = re.compile(r'AS\s\d+\.\d+\.\d+((\([a-z]\))(\(\d+\))*(\(\w+\))*)*|'
                                  r'\d+ AAC \d+, art\. \d+\.|State v\. Yi, \d+ P\.\d+d \d+')


class CustomisedRegexCO(RegexPatterns):
    """ Customised regex patterns for CO code"""

    h2_article_pattern = re.compile(r'^(article|Art\.)\s(?P<id>\d+(\.\d+)*)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)', re.I)
    h2_subpart_pattern = re.compile(r'^(subpart|SUBPART|Subpart)\s(?P<id>(\d+([a-zA-Z])*)|([A-Z]))')

    cite_pattern = re.compile(
        r'((?P<cite>(?P<title>\d+)(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)\s?(?P<ol>(\(\w\))(\(\w\))?(\(\w\))?)*)')
    code_pattern = re.compile(r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                              r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                              r"\d{4}\s*COA\s*\d+|"
                              r"L\.\s*\d+,\s*p\.\s*\d+|"
                              r"Colo\.+P\.\d\w\s\d+")

    h1_pattern_con = re.compile(r'^Declaration of Independence|'
                                r'^Constitution of the United States of America of 1787|'
                                r'^Constitution of the State of Colorado')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+)', re.I)
    section_pattern_con = re.compile(r'^(§)\s*(?P<id>\d+(\d+)*(\.?\w)*)\.')

    cite_tag_pattern = re.compile(r"\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*"
                                  r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                                  r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                                  r"\d{4}\s*COA\s*\d+|"
                                  r"L\.\s*\d+,\s*p\.\s*\d+|"
                                  r"Colo\.+P\.\d\w\s\d+")


class CustomisedRegexVT(RegexPatterns):
    """ Customised regex patterns for VT code"""
    h1_pattern = re.compile(r'title (?P<id>\d+(\w+)*)', re.I)
    h2_chapter_pattern = re.compile(r'^chapter\s*(?P<id>([IVX]+|\d+([A-Z])*))', re.I)
    h2_article_pattern = re.compile(r'^article\s*(?P<id>([IVX]+|\d+([a-zA-Z])*))', re.I)
    section_pattern = re.compile(
        r'^§*\s*(?P<id>\d+([a-z]{0,2})*([A-Z])*(\.\d+)*(\.*?\s*?(-|—)\d+([a-z])*)*(\.\d+)*)\.*\s*')
    rename_class_section_pattern = re.compile(
        r'^§+\s*(?P<id>\d+([a-z]{0,2})*([A-Z])*)(\.\d+)*(\.*?\s*?-\d+([a-z])*)*(\.\d+)*\.*\s*')
    section_pattern_1 = re.compile(r'^Executive Order No\. (?P<id>\d+-\d+)')
    h2_subchapter_pattern = re.compile(r'^Subchapter (?P<id>\d+([A-Z]+)?)', re.I)

    h1_pattern_con = re.compile(r'^Constitution of the United States|'
                                r'^CONSTITUTION OF THE STATE OF VERMONT', re.I)
    h2_chapter_pattern_con = re.compile(r'^chapter\s*(?P<id>[IVX]+)', re.I)
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+)\.*', re.I)
    section_pattern_con = re.compile(r'^(Article)\s*(?P<id>\d+(-[A-Z])*)\.')
    h2_amendment_pattern_con = re.compile(r'^AMENDMENT (?P<id>[IVX]+)\.*', re.I)

    cite_pattern = re.compile(r'\b((?P<cite>(?P<title>\d{1,2})-(?P<chap>\d(\w+)?)-(?P<sec>\d+(\.\d+)?))(\s?(\(('
                              r'?P<ol>\w+)\))+)?)')

    code_pattern = re.compile(r"(\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*"
                              r"|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*"
                              r"|\d+,\sNo\.\s\d+)")

    cite_tag_pattern = re.compile(r"\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*"
                                  r"|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*"
                                  r"|\d+,\sNo\.\s\d+")


class CustomisedRegexAR(RegexPatterns):
    """ Customised regex patterns for AR code"""

    section_pattern = re.compile(r'^(?P<id>(\d+-\d+([a-zA-Z])?-\d+(\.\d+)?)|\d\. Acts)')
    h2_subtitle_pattern = re.compile(r'^Subtitle (?P<id>\d+)\.')
    h2_chapters_pattern = re.compile(r'^Chapters (?P<id>\d+-\d+)')
    h2_subchapter_pattern = re.compile(r'^Subchapter (?P<id>\d+)')

    h1_pattern_con = re.compile(r'^Constitution\s+Of\s+The', re.I)
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+)', re.I)
    section_pattern_con = re.compile(r'^\[*§+\s*(?P<id>\d+)')
    amend_pattern_con = re.compile(r'^AMENDMENT (?P<id>\d+)', re.I)

    cite_pattern = re.compile(r'\b((?P<cite>(?P<title>\d{1,2})-(?P<chap>\d(\w+)?)-(?P<sec>\d+(\.\d+)?))(\s?(\(('
                              r'?P<ol>\w+)\))+)?)')
    code_pattern = re.compile(r"(\d+ Ga\.( App\.)? \d+"
                              r"|\d+ S\.E\.(2d)? \d+"
                              r"|\d+ U\.S\.C\. § \d+(\(\w\))?"
                              r"|\d+ S\. (Ct\.) \d+"
                              r"|\d+ L\. (Ed\.) \d+"
                              r"|\d+ L\.R\.(A\.)? \d+"
                              r"|\d+ Am\. St\.( R\.)? \d+"
                              r"|\d+ A\.L\.(R\.)? \d+)")

    cite_tag_pattern = re.compile(r"§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                  r"|\d+ Ga\.( App\.)? \d+"
                                  r"|\d+ S\.E\.(2d)? \d+"
                                  r"|\d+ U\.S\.C\. § \d+(\(\w\))?"
                                  r"|\d+ S\. (Ct\.) \d+"
                                  r"|\d+ L\. (Ed\.) \d+"
                                  r"|\d+ L\.R\.(A\.)? \d+"
                                  r"|\d+ Am\. St\.( R\.)? \d+"
                                  r"|\d+ A\.L\.(R\.)? \d+")


class CustomisedRegexND(RegexPatterns):
    """ Customised regex patterns for ND code"""

    h2_part_pattern = re.compile(r'^Part\s(?P<id>([IVX]+)*(\d+([a-zA-Z])*)*)')
    h2_chapter_pattern = re.compile(r'^CHAPTER\s(?P<id>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)')
    h2_article_pattern = re.compile(r'^article\s(?P<id>(\d+([a-zA-Z])*)|[IVX]+)', re.I)

    cite_pattern = re.compile(
        r'((?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*-\d+(\.\d+)*)(?P<ol>(\(\w\))(\(\w\))?(\(\w\))?)*)')
    code_pattern = re.compile(r'N\.D\. LEXIS \d+')

    cite_tag_pattern = re.compile(r"\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*"
                                  r"|Chapter\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)"
                                  r"|N\.D\. LEXIS \d+")

    h1_pattern_con = re.compile(r'^CONSTITUTION OF NORTH DAKOTA|CONSTITUTION OF THE UNITED STATES OF AMERICA')
    section_pattern_con = re.compile(r'^(Section(s)?|§) (?P<id>\d+(\.\d+)*)(\.| and| to)')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+|\d+)')
    article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+(\w)?)')


class CustomisedRegexID(RegexPatterns):
    """ Customised regex patterns for ID code"""

    h2_article_pattern = re.compile(r'^(article)\s(?P<id>\d+([a-zA-Z])*)', re.I)
    section_pattern = re.compile(r'^§?(\s?)(?P<id>\d+-\d+[a-zA-Z]?(-\d+)?)\.?', re.I)
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)\.\d+\.\d+)(?P<ol>(\([a-z]\))(\(\d+\))*)*)')
    code_pattern = re.compile(r'N\.D\. LEXIS \d+')


class CustomisedRegexWY(RegexPatterns):
    """ Customised regex patterns for WY code"""

    section_pattern = re.compile(r'^§*\s*(?P<id>\d+(\.\d+)*-\d+(\.[A-Z]+)*-\d+(\.\d+)*)', re.I)
    h2_division_pattern = re.compile(r'^Division (?P<id>\d+)\.')
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+(\.*[a-zA-Z])*)', re.I)
    h2_subpart_pattern = re.compile(r'^subpart\s(?P<id>\d+(\.*[a-zA-Z])*)', re.I)

    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)-\d+-\d+)(?P<ol>(\([a-z]\))(\([ivxl]+\))*(\(\w+\))*)*)')
    code_pattern = re.compile(r'\d+ Wyo\. LEXIS \d+')

    h1_pattern_con = re.compile(r'^THE CONSTITUTION OF THE UNITED STATES OF AMERICA|'
                                r'^Constitution of the State of Wyoming')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+)', re.I)
    section_pattern_con = re.compile(r'^(Section|§) (?P<id>\d+)')
    section_pattern_con1 = re.compile(r'^Section (?P<id>\d+)')

    cite_tag_pattern = re.compile(r"\d+-\d+-\d+((\([a-z]\))(\([ivxl]+\))*(\(\w+\))*)*|\d+ Wyo\. LEXIS \d+")


class CustomisedRegexTN(RegexPatterns):
    """ Customised regex patterns for TN code"""

    section_pattern = re.compile(r'^(?P<id>\d+-\d+([a-z])?-\d+(\.\d+)?)', re.I)
    cite_pattern = re.compile(r'\b(?P<cite>(?P<title>\d{1,2})-\d(\w+)?-\d+(\.\d+)?)(\s*(?P<ol>(\(\w+\))+))?')
    code_pattern = re.compile(r'(\d+ (Ga\.) \d+)|(\d+ Ga\.( App\.) \d+)'
                              r'(\d+ S\.E\.(2d)? \d+)|(\d+ U\.S\.(C\. §)? \d+(\(\w\))?)'
                              r'(\d+ S\. (Ct\.) \d+)|(\d+ L\. (Ed\.) \d+)|'
                              r'(\d+ L\.R\.(A\.)? \d+)|(\d+ Am\. St\.( R\.)? \d+)'
                              r'(\d+ A\.L\.R\.(2d)? \d+)')


class CustomisedRegexKY(RegexPatterns):
    h1_pattern = re.compile(r'title (?P<id>[IVXL]+)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+([A-Z]*?)\.\d+(-\d+)*?)\.', re.I)

    cite_pattern = re.compile(r'(?P<cite>(?P<title>\d+[a-zA-Z]*)\.\d+(\(\d+\))*(-\d+)*)(\s*(?P<ol>(\(\w+\))+))?')
    code_pattern = re.compile(r'((Ky\.\s*(L\. Rptr\.\s*)*\d+)|'
                              r'(Ky\.\s?(App\.)?\s?LEXIS\s?\d+)|'
                              r'(U\.S\.C\.\s*secs*\.\s*\d+(\([a-zA-Z]\))*(\(\d+\))*)|'
                              r'(OAG \d+-\d+))')

    cite_tag_pattern = re.compile(r"(KRS)*\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*(-\d+)*|"
                                  r"(KRS Chapter \d+[a-zA-Z]*)|"
                                  r"(KRS Title \D+, Chapter \D+?,)|"
                                  r"KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                                  r"(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                                  r"(U.S.C.\s*secs*\.\s*\d+)|"
                                  r"(Ky.\s?(App\.)?\s?LEXIS\s?\d+)|"
                                  r"(Ky.\s*(L. Rptr.\s*)*\d+)|"
                                  r"(OAG \d+-\d+))")


class CustomisedRegexNC(RegexPatterns):
    """ Customised regex patterns for NC code"""

    h1_pattern = re.compile(r'^Chapter\s(?P<id>\d+([A-Z])*)')

    section_pattern = re.compile(
        r'^§§*?\s*(?P<id>(\d+([A-Z])*-\d+([A-Z])*(\.\d+[A-Z]*)*(-\d+)*)|\d+([A-Z])*)[.:, ]')

    section_pattern_1 = re.compile(
        r'^Rule(s)*\s*(?P<id>(\d+(\.\d+)*))[:., throug]')

    h2_subchapter_pattern = re.compile(r'^(Subchapter|SUBCHAPTER) (?P<id>[IVX]+-*?([A-Z])*)\.')

    h1_pattern_con = re.compile(r'^Constitution of the United States|'
                                r'^Constitution of North Carolina', re.I)
    h2_chapter_pattern_con = re.compile(r'^chapter\s*(?P<id>[IVX]+)', re.I)
    h2_article_pattern_con = re.compile(r'^Article (?P<id>[IVX]+)', re.I)
    section_pattern_con = re.compile(r'^(Article|§)\s*(?P<id>\d+(-[A-Z])*)\.')
    h2_amendment_pattern_con = re.compile(r'^AMENDMENT (?P<id>[IVX]+)\.*', re.I)

    cite_pattern = re.compile(r'(G\.S\.\s(?P<cite>(?P<title>\d+[A-Z]*)-\d+(\.\d+)*(-\d+)*)(\s?(\((?P<ol>\w+)\))+)?)')

    code_pattern = re.compile(r"(\d+ N\.C\. \d+|"
                              r"\d+ N\.C\. App\. LEXIS \d+|N\.C\. LEXIS \d+)")

    cite_tag_pattern = re.compile(r"G\.S\.\s\d+[A-Z]*-\d+(\.\d+)*(\([a-z0-9]+\))*|Chapter \d+[A-Z]*|"
                                  r"\d+ N\.C\. \d+|"
                                  r"\d+ N\.C\. App\.")
