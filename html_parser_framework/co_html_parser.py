import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexCO
import roman
from loguru import logger


class COParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.file_no = None

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'ul': '^Article I.|^Preamble', 'head2': '^Article I.',
                                        'head1': '^Declaration of Independence|Constitution of the State of Colorado',
                                        'head3': r'^§ 1.|^Section 1\.', 'junk1': '^Statute text|^Text', 'ol_p': r'^§',
                                        'head4': '^ANNOTATIONS|^ANNOTATION', 'art_head': '^ARTICLE',
                                        'amd': '^AMENDMENTS', 'Analysis': r'^I\.', 'section': '^Section 1.',
                                        }
        else:
            self.file_no = re.search(r'gov\.co\.crs\.title\.(?P<fno>\w+(\.\d)*)\.html', self.input_file_name).group(
                "fno")

            if self.file_no in ['07', '38', '04']:
                self.tag_type_dict: dict = {'ul': '^Art.', 'head2': r'^ARTICLE \d',
                                            'head1': '^(TITLE|Title)|^(CONSTITUTION OF KENTUCKY)',
                                            'head3': r'^\d+(\.\d+)*-\d+-\d+\.',
                                            'part_head': r'^PART 1',
                                            'junk1': '^Annotations', 'ol_p': r'^(\(1\))',
                                            'head4': '^ANNOTATION', 'nd_nav': r'^1\.',
                                            'Analysis': r'^Analysis', 'editor': '^Editor\'s note',
                                            'h4_article': r'^Article I',
                                            'table': r'^Eligible Employers Solvency|20 or younger|^Table \d'}

            else:
                self.tag_type_dict: dict = {'ul': '^Art.', 'head2': '^ARTICLE|^Article|^Part',
                                            'head1': '^(TITLE|Title)|^(CONSTITUTION OF KENTUCKY)',
                                            'head3': r'^\d+(\.\d+)*-\d+-\d+\.',
                                            'junk1': '^Annotations', 'ol_p': r'^(\(1\))',
                                            'head4': '^ANNOTATION', 'nd_nav': r'^1\.', 'part_head': r'^PART\s\d+',
                                            'Analysis': r'^Analysis', 'editor': '^Editor\'s note',
                                            'h4_article': 'Article I', 'h4_article1': 'Article I',
                                            'table': r'^Eligible Employers Solvency|20 or younger|^Table \d'}

            self.h2_text = ['General, Primary, Recall, and Congressional Vacancy Elections', 'Other Election Offenses',
                            'Initiative and Referendum', 'Odd-Year Elections', 'Election Campaign Regulations',
                            'Congressional Districts', 'General Assembly', 'Legislative Services', 'Jurisdiction',
                            'Statutes - Construction and Revision', 'Miscellaneous', 'Consumer Credit Code',
                            'Refund Anticipation Loans', 'Rental Purchase', 'Interest Rates', 'Debt Management',
                            'Fair Trade and Restraint of Trade', 'Energy and Water Conservation', 'Art Transactions',
                            'Agricultural Assistance', 'Assignments in General', 'Patents - Prohibited Communication',
                            'Enforcement of Nondramatic Music Copyrights', 'Charitable Solicitations',
                            'Records Retention', 'Health Care Coverage Cooperatives',
                            'Transactions Involving Licensed Hospitals', 'Hospital Disclosures to Consumers',
                            'Protection Against Exploitation of At-Risk Adults', 'Residential Roofing Services',
                            'Direct Primary Health Care', 'Cemeteries', 'Public Establishments',
                            'Internet Service Providers', 'Corporations', 'Associations', 'Partnerships',
                            'Trademarks and Business Names', 'Trade Secrets', 'Limited Liability Companies',
                            'Corporations and Associations', 'Corporations - Continued', 'Colorado Corporation Code',
                            'Nonprofit Corporations', 'Special Purpose Corporations',
                            'Religious and Benevolent Organizations', 'LABOR I - Department of Labor and Employment',
                            'LABOR II - Workers’ Compensation and Related Provisions',
                            'LABOR III - Employment Security',
                            'Employment and Training', 'Independent Living Services', 'Labor Conditions', 'Wages',
                            'Division of Labor - Industrial Claim Appeals Office', 'Labor Relations',
                            'Workers’ Compensation Cost Containment', 'Apprenticeship and Training',
                            'Public Works', 'Fuel Products', 'Buildings and Equipment', 'Explosives',
                            'Special Safety Provisions', 'General Provisions', 'Licenses',
                            'Regulation of Insurance Companies', 'Property and Casualty Insurance',
                            'Nonadmitted Insurance', 'Captive Insurance Companies',
                            'Life Insurance', 'Covercolorado',
                            'Franchise Insurance', 'Credit Insurance', 'Title Insurance', 'Mutual Insurance',
                            'Interinsurance', 'Fraternal Benefit Societies', 'Preneed Funeral Contracts',
                            'Health Care Coverage', 'Health Maintenance Organizations', 'Medicare Supplement Insurance',
                            'Long - Term Care', 'Life and Health Insurance Protection', 'Health Care',
                            'Cash - Bonding Agents', 'Banks and Industrial Banks', 'Branch Institutions',
                            'Credit Unions', 'Marijuana Financial Services Cooperatives', 'Miscellaneous',
                            'Savings and Loan Associations', 'Securities', 'Public Securities',
                            'Recovery and Reinvestment Finance Act', 'U.S. Agency Obligations',
                            'Hospital and Health Care Trusts', 'Compliance Review Documents', 'Banks', 'Banking Code',
                            'General Financial Provisions', 'Industrial Banks', 'Trust Companies and Trust Funds',
                            'General', 'Division of Real Estate', 'Division of Conservation',
                            'Division of Professions and Occupations', 'Business Professions and Occupations',
                            'Health Care Professions and Occupations', 'Courts of Record',
                            'Municipal Courts', 'Civil Protection Orders', 'Change of Name', 'Costs',
                            'Regulation of Actions and Proceedings', 'Damages and Limitations on Actions',
                            'Contracts and Agreements', 'Evidence', 'Fees and Salaries', 'Forcible Entry and Detainer',
                            'Habeas Corpus', 'Joint Rights and Obligations', 'Judgments and Executions',
                            'Juries and Jurors', 'Limitation of Actions', 'Priority of Actions', 'Witnesses',
                            'Advocates', 'Adoption - Adults', 'Marriage and Rights of Married Persons',
                            'Domestic Abuse', 'Desertion and Nonsupport',
                            'Dissolution of Marriage - Parental Responsibilities',
                            'Child Support', 'Civil Union', 'Fiduciary', 'Powers of Appointment',
                            'Colorado Uniform Trust Code', 'Colorado Probate Code',
                            'Declarations - Future Health Care Treatment', 'Human Bodies After Death',
                            'Community Property Rights', 'Designated Beneficiary Agreements',
                            'Abandoned Estate Planning Documents', 'Code of Criminal Procedure',
                            'Uniform Mandatory Disposition of Detainers Act', 'Wiretapping and Eavesdropping',
                            'Criminal Activity Information', 'Sentencing and Imprisonment', 'Costs - Criminal Actions',
                            'Fugitives and Extradition', 'Offenders - Registration', 'Department of Corrections',
                            'Correctional Facilities and Programs', 'Diagnostic Programs', 'Miscellaneous Provisions',
                            'General and Administrative', 'Compensatory Education', 'School Districts',
                            'Financial Policies and Procedures', 'Financing of Schools', 'Second Chance Program',
                            'Financing of Schools - Continued', 'Teachers', 'Junior Colleges', 'Miscellaneous',
                            'State Universities and Colleges', 'Community Colleges and Occupational Education',
                            'Educational Centers and Local District Colleges', 'Educational Programs',
                            'Administration', 'Vital Statistics', 'Hospitals', 'Disease Control',
                            'Products Control and Safety', 'Family Planning', 'Environmental Control',
                            'Environment - Small Communities', 'Safety - Disabled Persons',
                            'Prevention, Intervention, and Treatment Services', 'Health Care', 'Administration',
                            'Prescription Drugs', 'Indigent Care', 'Colorado Medical Assistance Act',
                            'Children’s Basic Health Plan', 'Administration', 'State Officers', 'Principal Departments',
                            'Governor’s Office', 'Other Agencies', 'State Personnel System and State Employees',
                            'Public Employees’ Retirement Systems', 'Federal Programs - Housing - Relocation',
                            'Interstate Compacts and Agreements', 'Planning - State',
                            'Publication of Legal Notices and Public Printing', 'Electronic Transactions',
                            'Public (Open) Records', 'Governmental Access to News Information',
                            'State Funds', 'Federal Funds', 'Restrictions on Public Benefits',
                            'State Fiscal Policies Relating To Section 20 Of Article X of the State Constitution',
                            'Federal Mandates', 'Internet Regulation', 'State Delinquency Charges',
                            'State History, Archives, and Emblems', 'Allocation for Art', 'State Property',
                            'State Assistance - Denver Convention Center', 'Information Technology Access for Blind',
                            'Libraries', 'Construction', 'Procurement Code',
                            'Government Competition with Private Enterprise',
                            'Financing of Critical State Needs', 'Administration''Vital Statistics', 'Hospitals',
                            'Disease Control', 'Products Control and Safety', 'Family Planning',
                            'Environmental Control', 'Environment - Small Communities', 'Safety - Disabled Persons',
                            'Prevention, Intervention, and Treatment Services', 'Health Care',
                            'Department of Human Services', 'Mental Health', 'Corrections', 'Other Institutions',
                            'Colorado Diagnostic Program', 'Behavioral Health',
                            'Mental Health and Mental Health Disorders',
                            'Alcohol and Substance Use - Alcohol and Substance Use Disorders', 'Institutions',
                            'Emergency Preparedness', 'Military', 'Veterans', 'Division of Aviation',
                            'General Provisions', 'Housing', 'Miscellaneous', 'Energy Conservation',
                            'Property Insurance',
                            'Bond Anticipation Notes', 'Tax Anticipation Notes', 'Land Use Control and Conservation',
                            'Hazardous Substance Incidents', 'Wildland Fire Planning', 'Special Statutory Authorities',
                            'Marketing Districts', 'Affordable Housing Dwelling Unit Advisory Boards',
                            'Competition in Utility and Entertainment Services', 'Medical Provider Fees',
                            'Immigration Status - Cooperation with Federal Officials', 'Compensation - Fees',
                            'County Elected Officials’ Salary Commission', 'Location and Boundaries', 'County Officers',
                            'County Powers and Functions', 'County Planning and Building Codes',
                            'Apportionment of Federal Moneys', 'Flood Control', 'Home Rule',
                            'Corporate Class - Organization and Territory', 'Municipal Elections',
                            'Annexation - Consolidation - Disconnection', 'Powers and Functions of Cities and Towns',
                            'Special District Act', 'Multipurpose Districts', 'Water and Sanitation Districts',
                            'Single Purpose Service Districts', 'Regional Service Authorities',
                            'Special Statutory Districts', 'Wildlife', 'Administration', 'Parks',
                            'Wildlife - Continued',
                            'Outdoor Recreation', 'Colorado Natural Areas', 'Recreational Areas and Ski Safety',
                            'Great Outdoors Program', 'Geological Survey', 'Joint Review Process', 'Mines and Minerals',
                            'Oil and Natural Gas', 'Administration', 'Pest and Weed Control',
                            'Organically Grown Products',
                            'Fertilizers', 'Weights and Measures', 'Central Filing System', 'Poultry and Rabbits',
                            'Agricultural Products - Standards and Regulations', 'Marketing and Sales',
                            'Protection of Livestock', 'Livestock', 'Meat Processing',
                            'Agricultural Products - Standards and Regulations - Continued', 'Fairs',
                            'Soil Conservation', 'Development Authority', 'Produce Safety', 'Pet Animal Care',
                            'Public Lands and Rivers', 'Weather Modification', 'State Lands', 'Forestry',
                            'Natural Areas',
                            'Conservancy Law of Colorado - Flood Control', 'Drainage and Drainage Districts',
                            'Water Conservation and Irrigation Districts', 'Water Conservation Board and Compacts',
                            'Water Rights and Irrigation', 'Water Resources and Power Development',
                            'Water Conservation', 'Eminent Domain', 'Frauds - Statute of Frauds',
                            'Joint Rights and Obligations', 'Tenants and Landlords', 'Unclaimed Property',
                            'Loaned Property', 'Liens', 'Partition', 'Manufactured Homes', 'Real Property',
                            'Survey Plats and Monument Records', 'Property Tax', 'Specific Taxes',
                            'General and Administrative', 'Exemptions', 'Deferrals', 'Valuation and Taxation',
                            'Equalization', 'Collection and Redemption', 'Conveyancing and Evidence of Title',
                            'Public Utilities', 'Railroads', 'Geothermal Heat', 'Energy Impacts', 'Aircraft',
                            'Airports', 'Aerospace', 'General and Administrative', 'Drivers’ Licenses', 'Taxation',
                            'Regulation of Vehicles and Traffic', 'Automobile Theft Law', 'Certificates of Title',
                            'Motor Vehicle Financial Responsibility Law', 'Port of Entry Weigh Stations',
                            'Motor Vehicle Repairs', 'Collector’s Items', 'Disposition of Personal Property',
                            'Idling Standard', 'Highway Safety', 'General and Administrative',
                            'Highways and Highway Systems', 'Special Highway Construction', 'Financing',
                            'Highway Safety',
                            'Aviation Safety and Accessibility', 'General Provisions', 'Alcohol and Tobacco Regulation',
                            'Marijuana Regulation', 'Automobiles', 'Gaming and Racing', 'Lottery',
                            'Generally', 'Airport Revenue Bonds'
                            ]

        self.h4_head: list = ['Editor’s Notes', 'Cross references:', 'NOTES TO DECISIONS', 'JUDICIAL DECISIONS',
                              'RESEARCH REFERENCES', 'ANNOTATION', 'OFFICIAL COMMENT', 'History.']

        self.watermark_text = """Release {0} of the Official Code of Colorado Annotated released {1}.
                       Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                       This document is not subject to copyright and is in the public domain.
                       """
        self.h2_order: list = ['article', 'part', 'subpart', '']

        self.regex_pattern_obj = CustomisedRegexCO()

    def replace_tags_titles(self):
        for p_tag in self.soup.find_all("p", class_=self.tag_type_dict["head1"]):
            if self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()):
                pos = p_tag.attrs['class'].index(self.tag_type_dict["head1"])
                p_tag.attrs['class'][pos] = self.tag_type_dict["head2"]

        super(COParseHtml, self).replace_tags_titles()
        num_p_tag = None
        h4_count = 1
        cap_roman = "I"
        cap_rom_id = None
        alpha_id = None

        for p_tag in self.soup.find_all("p"):
            if p_tag.get("class") == [self.tag_type_dict["head2"]]:
                p_tag.name = "h2"
            if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                if num_p_tag and re.search(r'^\d+\.\s—\w+', p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip())
                    p_tag["id"] = f'{num_p_tag}{p_tag_text}'
                else:
                    if re.search(rf'^{cap_roman}\.', p_tag.text.strip()):
                        p_tag.name = "h5"
                        chap_num = re.search(r'^(?P<id>[IVX]+)\.', p_tag.text.strip()).group("id")

                        cap_rom_id = f'{p_tag.find_previous("h3").get("id")}-annotation-{chap_num}'
                        p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-annotation-{chap_num}'
                        cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                    elif re.search(r'^[A-Z]\.\s"?[A-Z][a-z]+', p_tag.text.strip()) and \
                            p_tag.find_previous(re.compile('^h[1-4]$')).name == "h4":
                        p_tag.name = "h5"
                        prev_id = cap_rom_id
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', p_tag.text.strip()).group("id")
                        alpha_id = f'{prev_id}-{chap_num}'
                        p_tag["id"] = f'{prev_id}-{chap_num}'

                    elif alpha_id and re.search(r'^[1-9]\.', p_tag.text.strip()):
                        p_tag.name = "h5"
                        num_id = alpha_id
                        chap_num = re.search(r'^(?P<id>[0-9])\.', p_tag.text.strip()).group("id")
                        p_tag["id"] = f'{num_id}-{chap_num}'
                    elif re.search(r'^(?P<id>[IVX]+)\.', p_tag.text.strip()) and self.release_number == '76':
                        p_tag.name = "h5"
                        chap_num = re.search(r'^(?P<id>[IVX]+)\.', p_tag.text.strip()).group("id")
                        cap_rom_id = f'{p_tag.find_previous("h3").get("id")}-annotation-{chap_num}'
                        p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-annotation-{chap_num}'

                    if self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                        p_tag["class"] = "navhead1"
                        p_tag[
                            "id"] = f'{p_tag.find_previous("h2").get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                    elif self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()):

                        p_tag["class"] = "navhead"
                        p_tag[
                            "id"] = f'{p_tag.find_previous("p", class_="navhead1").get("id")}s{self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                    if re.search(r'^——————————$', p_tag.text.strip()):
                        p_tag.decompose()

            elif p_tag.get("class") == [self.tag_type_dict["part_head"]]:
                if self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                    p_tag["class"] = "navhead1"
                    p_tag[
                        "id"] = f'{p_tag.find_previous("h2").get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                elif self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()):

                    p_tag["class"] = "navhead"
                    p_tag[
                        "id"] = f'{p_tag.find_previous("p", class_="navhead1").get("id")}s{self.regex_pattern_obj.h2_subpart_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                if re.search(r'^——————————$', p_tag.text.strip()):
                    p_tag.decompose()

            elif p_tag.get("class") == [self.tag_type_dict["h4_article"]] or \
                    "h4_article1" in self.tag_type_dict and p_tag.get("class") == [self.tag_type_dict["h4_article1"]]:
                if re.search(r'^(ARTICLE|Article) ([IVX]+|\d+)', p_tag.text.strip()):
                    p_tag.name = "h4"
                    ar_id = re.search(r"^(ARTICLE|Article) (?P<aid>[IVX]+|\d+)", p_tag.text.strip()).group("aid")
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-' \
                                  f'a{ar_id}'

            elif p_tag.get("class") == [self.tag_type_dict["ol_p"]]:
                if p_tag.text.strip() in self.h4_head:
                    p_tag.name = "h4"
                    header4_tag_text = re.sub(r'[\W.]+', '', p_tag.text.strip()).lower()
                    h4_tag_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'

                    if h4_tag_id in self.h4_cur_id_list:
                        p_tag['id'] = f'{h4_tag_id}.{h4_count}'
                        h4_count += 1
                    else:
                        p_tag['id'] = f'{h4_tag_id}'

                    self.h4_cur_id_list.append(h4_tag_id)

                if self.release_number in ['75', '76'] and self.file_no in ['37', '24']:
                    if re.search(r'^(ARTICLE|Article) ([IVX]+|\d+)', p_tag.text.strip()):
                        p_tag.name = "h4"
                        ar_id = re.search(r"^(ARTICLE|Article) (?P<aid>[IVX]+|\d+)", p_tag.text.strip()).group("aid")
                        p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-' \
                                      f'a{ar_id}'

            if re.search(r'^Analysis$|^ARTICLE \d\.', p_tag.text.strip()):
                cap_roman = "I"
                for tag in p_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]] or \
                            tag.get('class') == [self.tag_type_dict["part_head"]]:
                        break
                    else:
                        tag["class"] = "annotation"
                        tag.name = "li"

            if re.search(r'^History\.', p_tag.text.strip()):
                alpha_id = None

    def add_anchor_tags(self):
        super(COParseHtml, self).add_anchor_tags()

        h2_article_pattern = re.compile(r'^(article|Art\.)\s(?P<id>\d+(\.\d+)*)', re.I)

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if h2_article_pattern.search(li_tag.text.strip()):
                    chap_num = h2_article_pattern.search(li_tag.text.strip()).group("id")
                    sub_tag = "a"
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
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
        if not re.search('constitution', self.input_file_name):
            for tag in self.soup.find_all("p", class_=[self.tag_type_dict['editor']]):
                if re.search(r'^Editor\'s note: \(\d+\)', tag.text.strip()):
                    new_h4_tag = self.soup.new_tag("h4")
                    new_h4_tag.string = tag.find_next("b").text
                    h4_text = re.sub(r'[\W\s]+', '', tag.find_next("b").text.strip()).lower()
                    new_h4_tag['id'] = f'{tag.find_previous({"h3", "h2", "h1"}).get("id")}-{h4_text}'
                    tag.insert_before(new_h4_tag)
                    tag.find_next("b").decompose()

        for p_tag in self.soup.find_all("p", class_=[self.tag_type_dict['ol_p']]):
            current_p_tag = p_tag.text.strip()
            if re.search(r'^\[.+\]\s*\(\d+(\.\d+)*\)', current_p_tag):
                alpha_text = re.sub(r'^\[.+\]\s*', '', current_p_tag)
                num_text = re.sub(r'\(1\).+', '', current_p_tag)
                new_p_tag = self.soup.new_tag("p")
                new_p_tag.string = alpha_text
                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                p_tag.insert_after(new_p_tag)
                p_tag.string = num_text

            if re.search(r'^\(\d+(\.\d+)*\)', current_p_tag):
                if p_tag.find_next().name == "b":
                    if re.search(r'^\[ Editor\'s note:', p_tag.find_next().text.strip()):
                        continue
                    else:
                        alpha_text = re.sub(r'^[^.]+\.', '', current_p_tag)
                        num_text = re.sub(r'\(a\).+', '', current_p_tag)
                        if re.search(r'^\s*\([a-z]\)', alpha_text):
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                        elif re.search(r'^.+\s(?P<alpha>\(a\)+)', current_p_tag):
                            alpha_text = re.search(r'^.+\s(?P<alpha>\(a\).+)', current_p_tag).group("alpha")
                            num_text = re.sub(r'\(a\).+', '', current_p_tag)
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

            if re.search(r'^\(\d+\)\s*\([a-z]+\)\s*.+\s*\([a-z]\)', current_p_tag):
                alpha = re.search(
                    r'^(?P<num_text>\(\d+\)\s*\((?P<alpha1>[a-z]+)\)\s*.+\s*)(?P<alpha_text>\((?P<alpha2>[a-z])\).+)',
                    current_p_tag)
                if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                          p_tag.find_next_sibling().text.strip()).group("alpha3")
                    if ord(alpha.group("alpha2")) == (ord(alpha.group("alpha1"))) + 1:
                        if ord(nxt_alpha) == (ord(alpha.group("alpha2"))) + 1:
                            alpha_text = alpha.group("alpha_text")
                            num_text = alpha.group("num_text")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

            if re.search(r'^\(\d+\)\s*(to|and)\s*\(\d+\)\s*', current_p_tag):
                nxt_tag = p_tag.find_next_sibling(
                    lambda tag: tag.name in ['p'] and re.search(r'^[^\s]', tag.text.strip()))
                alpha = re.search(
                    r'^(?P<text1>\((?P<num1>\d+)\))\s*(to|and)\s*(?P<text2>\((?P<num2>\d+)\)\s*(?P<rpt_text>.+))',
                    current_p_tag)
                if re.search(r'^\(\d+\)', nxt_tag.text.strip()):
                    nxt_alpha = re.search(r'^\((?P<num3>\d+)\)', nxt_tag.text.strip()).group(
                        "num3")
                    if int(nxt_alpha) != int(alpha.group("num1")) + 1:
                        if int(alpha.group("num2")) == int(alpha.group("num1")) + 1:
                            if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                alpha_text = alpha.group("text2")
                                num_text = alpha.group("text1")
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = alpha_text
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag.string = num_text
                        else:
                            if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                alpha_text = alpha.group("text2")
                                num_text = alpha.group("text1") + alpha.group("rpt_text")
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = alpha_text
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag.string = num_text
                                range_from = int(alpha.group("num1"))
                                range_to = int(alpha.group("num2"))
                                count = range_from + 1
                                for new_p_tag in range(range_from + 1, range_to):
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = f'({count}){alpha.group("rpt_text")}'
                                    new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag = new_p_tag
                                    count += 1

            if re.search(r'^\([a-zA-Z]\)\s*(to|and)\s*\([a-zA-Z]\)\s*(Repealed.|\()', current_p_tag):
                alpha = re.search(
                    r'^(?P<text1>\((?P<num1>[a-zA-Z])\))\s*(to|and)\s*(?P<text2>\((?P<num2>[a-zA-Z])\)\s*('
                    r'?P<rpt_text>Repealed.|\(.+))',
                    current_p_tag)
                if re.match(r'^\([a-zA-Z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<num3>[a-zA-Z])\)',
                                          p_tag.find_next_sibling().text.strip()).group(
                        "num3")
                    if ord(alpha.group("num2")) == ord(alpha.group("num1")) + 1:
                        if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

                    else:
                        if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1") + alpha.group("rpt_text")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                            range_from = ord(alpha.group("num1"))
                            range_to = ord(alpha.group("num2"))
                            count = range_from + 1
                            for new_p_tag in range(range_from + 1, range_to):
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = f'({chr(count)}){alpha.group("rpt_text")}'
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag = new_p_tag
                                count += 1

                else:
                    alpha_text = alpha.group("text2")
                    num_text = alpha.group("text1")
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = alpha_text
                    new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                    p_tag.insert_after(new_p_tag)
                    p_tag.string = num_text
                    range_from = ord(alpha.group("num1"))
                    range_to = ord(alpha.group("num2"))
                    count = range_from + 1
                    for new_p_tag in range(range_from + 1, range_to):
                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = f'({chr(count)})'
                        new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                        p_tag.insert_after(new_p_tag)
                        p_tag = new_p_tag
                        count += 1

            if re.search(r'^\([a-z]\).+\([a-z]\)\s*', current_p_tag):
                alpha = re.search(r'^(?P<text1>\((?P<alpha1>[a-z])\).+)(?P<text2>\((?P<alpha2>[a-z])\)\s*.+)',
                                  current_p_tag)
                if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                          p_tag.find_next_sibling().text.strip()).group(
                        "alpha3")
                    if ord(alpha.group("alpha2")) == ord(alpha.group("alpha1")) + 1:
                        if ord(nxt_alpha) == ord(alpha.group("alpha2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

        main_sec_alpha = 'a'
        sec_alpha = 'a'
        cap_alpha = 'A'
        inr_cap_alpha = 'A'
        cap_roman = 'I'
        ol_head = 1
        roman_count = 1
        ol_count = 1
        inner_num_head = 1

        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")

        dup_id_list = []
        inner_roman_ol = None
        num_tag = None
        inr_cap_alpha_cur_tag = None
        alpha_cur_tag = None
        prev_alpha_id = None
        prev_head_id = None
        article_alpha_tag = None
        inner_alpha_tag = None
        num_cur_tag = None
        cap_alpha_cur_tag = None
        sec_alpha_cur_tag = None
        previous_li_tag = None
        prev_num_id = None
        rom_id = None
        prev_id = None
        prev_alpha = None
        sec_alpha_id = None
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        inr_cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol1 = self.soup.new_tag("ol")

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^\({ol_head}\)|^\[.+]\s*\({ol_head}\)|^\(\d+\.\d+\)', current_tag_text):
                previous_li_tag = p_tag
                if re.search(rf'^\({ol_head}\)|^\[.+]\s*\({ol_head}\) ', current_tag_text):
                    p_tag.name = "li"
                    num_cur_tag = p_tag

                    if re.search(r'^\(1\)|^\[.+]\s*\(1\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)

                        if article_alpha_tag:
                            alpha_cur_tag.append(num_ol)
                            prev_head_id = alpha_cur_tag.get("id")
                        elif cap_alpha_cur_tag:
                            cap_alpha_cur_tag.append(num_ol)
                            prev_head_id = cap_alpha_cur_tag.get("id")
                        elif inner_alpha_tag:
                            inner_alpha_tag.append(num_ol)
                            prev_head_id = inner_alpha_tag.get("id")
                        else:
                            prev_head_id = p_tag.find_previous(["h4", "h3", "h2", "h1"]).get("id")
                            main_sec_alpha = 'a'
                    else:
                        num_ol.append(p_tag)

                    if inr_cap_alpha_cur_tag:
                        p_tag["id"] = f'{inr_cap_alpha_cur_tag.get("id")}{ol_head}'
                    elif article_alpha_tag:
                        p_tag["id"] = f'{alpha_cur_tag.get("id")}{ol_head}'
                    else:
                        prev_num_id = f'{prev_head_id}ol{ol_count}{ol_head}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
                        main_sec_alpha = 'a'

                    p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
                    ol_head += 1

                    if re.search(r'^\(\d+\)\s\(a\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s\(a\)', '', current_tag_text)
                        previous_li_tag = li_tag
                        alpha_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>a)\)', current_tag_text)
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(alpha_ol)
                        main_sec_alpha = "b"

                        if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="I")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            rom_cur_tag = li_tag
                            cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[IVX]+)\)',
                                                current_tag_text)
                            rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}'
                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            roman_ol.append(inner_li_tag)
                            alpha_cur_tag.string = ""
                            alpha_cur_tag.insert(0, roman_ol)
                            cap_roman = "II"

                            if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                                cap_alpha_ol = self.soup.new_tag("ol", type="A")
                                inner_li_tag = self.soup.new_tag("li")
                                inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '',
                                                             current_tag_text)
                                li_tag["class"] = self.tag_type_dict['ol_p']
                                cur_tag = re.search(
                                    r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                    current_tag_text)
                                prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                                inner_li_tag[
                                    "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'
                                cap_alpha_ol.append(inner_li_tag)
                                rom_cur_tag.string = ""
                                rom_cur_tag.append(cap_alpha_ol)
                                cap_alpha = "B"

                    if re.search(r'^\(\d+\)\s\(i\)', current_tag_text):
                        inner_roman_ol = self.soup.new_tag("ol", type="i")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s\(i\)', '', current_tag_text)
                        prev_alpha = p_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>i)\)', current_tag_text)
                        prev_num_id = f'{prev_head_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        inner_roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(inner_roman_ol)

                elif re.search(r'^\(\d+\.\d+\)', current_tag_text):
                    cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)', current_tag_text).group("cid")
                    tag_id = f'{prev_num_id}-{cur_tag}'
                    prev_num_id = f'{prev_num_id}-{cur_tag}'
                    if tag_id in dup_id_list:
                        p_tag["id"] = f'{tag_id}-{cur_tag}.1'
                    else:
                        p_tag["id"] = f'{tag_id}-{cur_tag}'

                    dup_id_list.append(tag_id)
                    if num_cur_tag:
                        num_cur_tag.append(p_tag)
                    else:
                        p_tag.find_previous("li").append(p_tag)
                    main_sec_alpha = "a"
                    num_cur_tag = p_tag

                    if re.search(r'^\(\d+\.\d+\)\s\(\w\)|^\(\d+\.\d+\)\s*\[.+\]\s*\(\w\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.append(current_tag_text)
                        alpha_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\).+\((?P<pid>\w)\)', current_tag_text)
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        if prev_alpha_id in dup_id_list:
                            li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}.1'
                        else:
                            li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(alpha_ol)
                        main_sec_alpha = "b"
                        cap_roman = "I"
                        dup_id_list.append(prev_alpha_id)
                        if re.search(r'^\(\d+\.\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="I")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            rom_cur_tag = li_tag
                            cur_tag = re.search(r'^\((?P<id1>\d+\.\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
                                                current_tag_text)
                            rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            roman_ol.append(inner_li_tag)
                            p_tag.insert(1, roman_ol)
                            roman_ol.find_previous().string.replace_with(roman_ol)
                            cap_roman = "II"

            elif re.search(rf'^\({main_sec_alpha}\)|^\([a-z]\.\d+\)', current_tag_text):
                previous_li_tag = p_tag
                if re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                    p_tag.name = "li"
                    alpha_cur_tag = p_tag
                    cap_roman = "I"
                    if re.search(r'^\(a\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(alpha_ol)

                        if p_tag.find_previous("h4") and re.search(r'^(ARTICLE|Article) [IVX]+',
                                                                   p_tag.find_previous("h4").text.strip()):
                            if num_tag:
                                num_tag.append(alpha_ol)
                                prev_alpha_id = f'{num_tag.get("id")}'
                            elif num_cur_tag:
                                num_cur_tag.append(alpha_ol)
                                prev_alpha_id = f'{prev_num_id}'
                            else:
                                prev_alpha_id = f'{p_tag.find_previous("h4").get("id")}ol{ol_count}'
                                article_alpha_tag = p_tag
                        elif num_cur_tag:
                            article_alpha_tag = None
                            num_cur_tag.append(alpha_ol)
                            prev_alpha_id = f'{prev_num_id}'
                        else:
                            article_alpha_tag = p_tag
                            prev_alpha_id = f'{p_tag.find_previous(["h4", "h3", "h2", "h1"]).get("id")}ol{ol_count}'

                    else:
                        alpha_ol.append(p_tag)

                    if p_tag.find_previous("h4") and re.search(r'^(ARTICLE|Article) [IVX]+',
                                                               p_tag.find_previous("h4").text.strip()):
                        ol_head = 1

                    p_tag["id"] = f'{prev_alpha_id}{main_sec_alpha}'
                    p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                    if re.search(r'^\(\w\)(\s*\[.+])*\s*\([I,V,X]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)

                        li_tag["class"] = self.tag_type_dict['ol_p']
                        rom_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w+)\)(\s*\[.+\])*\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                        rom_id = f'{prev_num_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(roman_ol)
                        cap_roman = "II"

                        if re.search(r'^\(\w\)\s*\([IVX]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\w\)\s*\([IVX]+\)\s*\(\w\)', '', current_tag_text)
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            cur_tag = re.search(
                                r'^\((?P<cid>\w)\)\s*\((?P<id2>[IVX]+)\)\s*\((?P<id3>\w)\)',
                                current_tag_text)
                            prev_id = rom_cur_tag.get("id")
                            inner_li_tag[
                                "id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("id3")}'
                            cap_alpha_ol.append(inner_li_tag)
                            p_tag.insert(1, cap_alpha_ol)
                            rom_cur_tag.string = ""
                            rom_cur_tag.string.replace_with(cap_alpha_ol)
                            cap_alpha = "B"

                    if re.search(r'^\(\w\)\s*\(\d+\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\)\s*\(\d+\)', '', current_tag_text)
                        li_tag["class"] = self.tag_type_dict['ol_p']
                        cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>\d+)\)', current_tag_text)
                        li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                        num_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(num_ol)
                        ol_head = 2
                        cap_alpha = "A"

                    if re.search(r'^\(\w\)\s*\([ivx]+\)', current_tag_text):
                        inner_roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\w\)\s*\([ivx]+\)', '', current_tag_text)
                        inner_li_tag["class"] = self.tag_type_dict['ol_p']
                        prev_alpha = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                        inner_li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                        inner_roman_ol.append(inner_li_tag)
                        p_tag.contents = []
                        p_tag.append(inner_roman_ol)
                elif re.search(r'^\(\w+\.\d+\)', current_tag_text):
                    p_tag.name = "li"
                    roman_count = 1
                    cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)', current_tag_text).group("cid")
                    p_tag.string = re.sub(r'^\(\w+\.\d+\)', '', current_tag_text)
                    p_tag_id = f'{prev_alpha_id}-{cur_tag}'
                    if p_tag_id in dup_id_list:
                        p_tag["id"] = f'{prev_alpha_id}-{cur_tag}.1'
                    else:
                        p_tag["id"] = f'{prev_alpha_id}-{cur_tag}'

                    dup_id_list.append(p_tag_id)
                    prev_alpha_id = f'{prev_alpha_id}'

                    if not re.search(r'^\(\w+\.\d+\)', p_tag.find_next().text.strip()) and re.search(r'^\([A-Z]\)',
                                                                                                     p_tag.find_next().text.strip()):
                        prev_alpha_id = f'{prev_alpha_id}-{cur_tag}'

                    alpha_ol.append(p_tag)
                    alpha_cur_tag = p_tag

                    if re.search(r'^\(\w\.\d+\)\s*\([IVX]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\.\d+\)\s*\([IVX]+\)', '', current_tag_text)

                        li_tag["class"] = self.tag_type_dict['ol_p']
                        cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)\s*\((?P<pid>[IVX]+)\)', current_tag_text)
                        rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(roman_ol)
                        cap_roman = "II"

                        if re.search(r'^\(\w\.\d+\)\s*\([IVX]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.append(current_tag_text)
                            inner_li_tag["class"] = self.tag_type_dict['ol_p']
                            cur_tag = re.search(
                                r'^\((?P<cid>\w\.\d+)\)\s*\((?P<id2>[IVX]+)\)\s*\((?P<id3>\w)\)',
                                current_tag_text)
                            prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'

                            cap_alpha_ol.append(inner_li_tag)
                            p_tag.insert(1, cap_alpha_ol)
                            cap_alpha_ol.find_previous().string.replace_with(cap_alpha_ol)
                            cap_alpha = "B"

            elif re.search(rf'^\({cap_roman}\)', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                rom_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(I\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(roman_ol)
                    if alpha_cur_tag:
                        alpha_cur_tag.append(roman_ol)
                        rom_id = f'{alpha_cur_tag.get("id")}'
                        p_tag["id"] = f'{alpha_cur_tag.get("id")}I'
                    else:
                        rom_id = f'{p_tag.find_previous("li").get("id")}'
                        p_tag["id"] = f'{p_tag.find_previous("li").get("id")}I'
                        p_tag.find_previous("li").append(roman_ol)
                else:
                    roman_ol.append(p_tag)
                    p_tag["id"] = f'{rom_id}{cap_roman}'

                p_tag.string = re.sub(rf'^\({cap_roman}\)', '', current_tag_text)
                cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                if re.search(r'^\([IVX]+\)\s*\([A-Z]\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([IVX]+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[IVX]+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
                    prev_id = f'{rom_cur_tag.get("id")}'
                    li_tag["id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("pid")}'

                    if not re.search(r'^\(I\)', current_tag_text):
                        prev_tag_id = p_tag.find_previous("li").get("id")
                        cur_tag_id = re.search(r'^[^IVX]+', prev_tag_id).group()
                        li_tag["id"] = f'{cur_tag_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    roman_count += 1
                    cap_alpha = "B"

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    prev_id = p_tag.find_previous("li").get("id")
                    p_tag.find_previous("li").append(cap_alpha_ol)

                else:
                    cap_alpha_ol.append(p_tag)

                if cap_alpha in ['I', 'V', 'X', 'L']:
                    p_tag["id"] = f'{prev_id}{ord(cap_alpha)}'
                else:
                    p_tag["id"] = f'{prev_id}{cap_alpha}'

                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                if cap_alpha == 'Z':
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

            elif re.search(r'^\([ivx]+\)', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                cap_alpha = "A"
                if re.search(r'^\(i\)', current_tag_text):
                    inner_roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(inner_roman_ol)
                    p_tag.find_previous("li").append(inner_roman_ol)
                    prev_alpha = p_tag.find_previous("li")
                    p_tag["id"] = f'{prev_alpha.get("id")}i'
                else:
                    cur_tag = re.search(r'^\((?P<cid>[ivx]+)\)', current_tag_text).group("cid")
                    if inner_roman_ol:
                        inner_roman_ol.append(p_tag)
                        p_tag["id"] = f'{prev_alpha.get("id")}{cur_tag}'

                    else:
                        alpha_ol.append(p_tag)
                        alpha_cur_tag = p_tag
                        p_tag["id"] = f'{prev_num_id}{cur_tag}'
                p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)', '', current_tag_text)

            elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_tag:
                        num_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_tag.get("id")
                    else:
                        sec_alpha_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count}{sec_alpha}'
                        inner_num_head = 1
                else:
                    sec_alpha_ol.append(p_tag)
                    if not num_tag:
                        inner_num_head = 1

                p_tag["id"] = f'{sec_alpha_id}{sec_alpha}'
                p_tag.string = re.sub(rf'^{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

            elif re.search(rf'^{inr_cap_alpha}\.', current_tag_text) and p_tag.name == "p":
                inner_alpha_tag = p_tag
                p_tag.name = "li"
                inr_cap_alpha_cur_tag = p_tag
                inner_num_head = 1
                ol_head = 1

                if re.search(r'^A\.', current_tag_text):
                    inr_cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inr_cap_alpha_ol)
                    prev_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count}'

                else:
                    inr_cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_id}{inr_cap_alpha}'
                p_tag.string = re.sub(rf'^{inr_cap_alpha}\.', '', current_tag_text)
                if inr_cap_alpha == 'Z':
                    inr_cap_alpha = 'A'
                else:
                    inr_cap_alpha = chr(ord(inr_cap_alpha) + 1)

                if re.search(r'^[A-Z]\.\s\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[A-Z]\.\s\(1\)', '', current_tag_text)
                    li_tag["class"] = self.tag_type_dict['ol_p']
                    inner_alpha_id = f'{inr_cap_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inr_cap_alpha_cur_tag.get("id")}1'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    ol_head = 2

            elif re.search(rf'^{inner_num_head}\.', current_tag_text) and p_tag.name == "p":
                inner_num_tag = p_tag
                p_tag.name = "li"
                num_tag = p_tag
                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(num_ol1)
                        prev_head_id = sec_alpha_cur_tag.get('id')
                        sec_alpha = 'a'
                    elif inr_cap_alpha_cur_tag:
                        inr_cap_alpha_cur_tag.append(num_ol1)
                        prev_head_id = inr_cap_alpha_cur_tag.get('id')
                    elif alpha_cur_tag:
                        alpha_cur_tag.append(num_ol1)
                        prev_head_id = alpha_cur_tag.get('id')
                    else:
                        prev_head_id = p_tag.find_previous({"h5", "h4", "h3", "h2"}).get("id")
                else:
                    num_ol1.append(p_tag)

                    if sec_alpha_cur_tag:
                        sec_alpha = 'a'
                    if p_tag.find_previous("h4") and re.search(r'^(ARTICLE|Article) [IVX]+',
                                                               p_tag.find_previous("h4").text.strip()):
                        main_sec_alpha = 'a'

                p_tag["id"] = f'{prev_head_id}ol{ol_count}{inner_num_head}'
                p_tag.string = re.sub(rf'^{inner_num_head}\.', '', current_tag_text)
                inner_num_head += 1

                if re.search(r'^\d+\.\s*?a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\d+\.\s*?a\.', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^(?P<cid>\d+)\.\s*?a\.', current_tag_text)
                    prev_id = f'{num_tag.get("id")}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{num_tag.get("id")}{cur_tag.group("cid")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol)
                    sec_alpha = "b"

            elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
                previous_li_tag = p_tag
                curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                alpha_ol.append(p_tag)
                prev_alpha_id = f'{prev_num_id}{curr_id}'
                p_tag["id"] = f'{prev_num_id}{curr_id}'
                roman_count = 1
                p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)

            elif p_tag.get("class") == [self.tag_type_dict['ol_p']] and not re.search(r'^History|^Source',
                                                                                      current_tag_text):
                if previous_li_tag:
                    previous_li_tag.append(p_tag)

            elif "table" in self.tag_type_dict and p_tag.get("class") == [self.tag_type_dict["table"]] and p_tag.span:
                if previous_li_tag:
                    previous_li_tag.append(p_tag)
                    p_tag["class"] = 'table'

            if re.search(r'^Source|^Cross references:|^OFFICIAL COMMENT|^(ARTICLE|Article) ([IVX]+|\d+)',
                         current_tag_text, re.I) or p_tag.name in ['h3', 'h4', 'h2']:
                main_sec_alpha = 'a'
                sec_alpha = 'a'
                cap_alpha = 'A'
                inr_cap_alpha = 'A'
                cap_roman = 'I'
                ol_head = 1
                roman_count = 1
                ol_count = 1
                inner_roman_ol = None
                num_tag = None
                inr_cap_alpha_cur_tag = None
                alpha_cur_tag = None
                prev_alpha_id = None
                article_alpha_tag = None
                inner_alpha_tag = None
                num_cur_tag = None
                cap_alpha_cur_tag = None
                sec_alpha_cur_tag = None
                previous_li_tag = None
                prev_id = None
                inner_num_head = 1

        logger.info("ol tags added")

    def create_analysis_nav_tag(self):
        if self.release_number == '76':
            rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
            alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
            digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
            rom_tag_id = None
            rom_tag = None
            alpha_tag = None
            alpha_tag_id, a_tag_id = None, None
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
                    elif re.search(r'^II\.', case_tag.text.strip()):
                        if case_tag.find_previous().name == 'a':
                            rom_ul.append(case_tag)
                            rom_num = re.search(r'^(?P<rid>[IVX]+)\.', case_tag.text.strip()).group("rid")
                            rom_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-{rom_num}'
                            a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-{rom_num}'
                        else:
                            rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            case_tag.wrap(rom_ul)
                            rom_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-II'
                            a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-annotation-II'

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

        else:
            super(COParseHtml, self).create_annotation_analysis_nav_tag()
            logger.info("Annotation analysis nav created")

    def wrap_inside_main_tag(self):

        """wrap inside main tag"""

        main_tag = self.soup.new_tag('main')
        chap_nav = self.soup.find('nav')

        h2_tag = self.soup.find("h2")
        tag_to_wrap = h2_tag.find_previous_sibling()

        for tag in tag_to_wrap.find_next_siblings():
            tag.wrap(main_tag)

        for nav_tag in chap_nav.find_next_siblings():
            if nav_tag.name != "main":
                nav_tag.wrap(chap_nav)

    def replace_tags_constitution(self):
        for p_tag in self.soup.find_all(class_=self.tag_type_dict['head3']):
            current_p_tag = p_tag.text.strip()
            next_sibling = p_tag.find_next_sibling()
            if re.search('^§', current_p_tag):
                if p_tag.b and re.search('^§', p_tag.b.text.strip()):
                    new_h3_tag = self.soup.new_tag("p")
                    new_h3_tag.attrs["class"] = self.tag_type_dict['head3']
                    h3_text = p_tag.b.text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    p_tag["class"] = self.tag_type_dict['head3']
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()

                else:
                    new_h3_tag = self.soup.new_tag("p")
                    new_h3_tag["class"] = self.tag_type_dict['head3']
                    h3_text = "§ " + p_tag.find_next("b").text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()
                    if re.search(r'^§', p_tag.text.strip()):
                        p_tag.string = re.sub(r'^§', '', p_tag.text.strip())

        super(COParseHtml, self).replace_tags_constitution()
        cap_roman = "I"
        rom_id = None
        for header_tag in self.soup.find_all("p"):
            if header_tag.get("class") == [self.tag_type_dict["head2"]] or \
                    header_tag.get("class") == [self.tag_type_dict["amd"]]:
                if re.search(r'^PREAMBLE|^AMENDMENTS|^Schedule', header_tag.text.strip(), re.I):
                    header_tag.name = "h2"
                    tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}-{tag_text}"
                    header_tag["class"] = "gen"
            elif header_tag.get("class") == [self.tag_type_dict["art_head"]]:
                if self.regex_pattern_obj.h2_article_pattern_con.search(header_tag.text.strip()):
                    header_tag.name = "h3"
                    chap_no = self.regex_pattern_obj.h2_article_pattern_con.search(header_tag.text.strip()).group('id')
                    header_tag["id"] = f'{header_tag.find_previous("h2").get("id")}-am{chap_no.zfill(2)}'
                    header_tag["class"] = "amend"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            elif header_tag.get("class") == [self.tag_type_dict["section"]]:
                if re.search(r'^Section \d+(\.?\w)*\.', header_tag.text.strip()):
                    chap_num = re.search(r'^Section (?P<id>\d+(\.?\w)*)\.', header_tag.text.strip()).group("id")
                    header_tag.name = "h3"
                    header_tag[
                        "id"] = f"{header_tag.find_previous('h2', class_={'oneh2', 'twoh2', 'threeh2', 'gen'}).get('id')}-sec{chap_num.zfill(2)}"
                    header_tag["class"] = "sec"

            elif header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    chap_num = re.search(r'^(?P<id>[IVX]+)\.', header_tag.text.strip()).group("id")
                    rom_id = f'{header_tag.find_previous("h3").get("id")}-annotation-{chap_num}'
                    header_tag["id"] = f'{header_tag.find_previous("h3").get("id")}-annotation-{chap_num}'
                    cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                elif re.search(r'^[A-Z]\.\s"?[A-Z][a-z]+', header_tag.text.strip()):
                    header_tag.name = "h5"
                    prev_id = rom_id
                    chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                    header_tag["id"] = f'{prev_id}-{chap_num}'

                elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    if header_tag.find_previous(
                            lambda tag: tag.name in ['h5'] and re.search(r'^[A-Z]\.',
                                                                         tag.text.strip())):

                        prev_id = header_tag.find_previous(
                            lambda tag: tag.name in ['h5'] and re.search(r'^[A-Z]\.',
                                                                         tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'
                    else:
                        header_tag["class"] = [self.tag_type_dict['ol_p']]

            if re.search(r'^Analysis$', header_tag.text.strip()):
                cap_roman = "I"

            if self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()):
                header_tag.name = "h3"
                chap_no = self.regex_pattern_obj.section_pattern_con.search(header_tag.text.strip()).group('id')
                if header_tag.find_previous("h3", class_={"oneh2", "gen", "amend"}):
                    header_tag[
                        "id"] = f'{header_tag.find_previous("h3", class_={"oneh2", "gen", "amend"}).get("id")}-s{chap_no.zfill(2)}'
                else:
                    header_tag[
                        "id"] = f'{header_tag.find_previous("h2", class_={"oneh2", "gen", "amd"}).get("id")}-s{chap_no.zfill(2)}'

                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def add_anchor_tags_con(self):
        super(COParseHtml, self).add_anchor_tags_con()
        for li in self.soup.find_all("li"):
            if not li.get("id"):
                if re.search(r'^[IVX]+', li.text.strip()):
                    chap_num = re.search(r'^(?P<id>[IVX]+)', li.text.strip()).group("id")
                    self.c_nav_count += 1

                    if self.release_number in ['71', '74']:
                        if li.find_previous({"h1", "h2"}) and \
                                re.search(r'^AMENDMENTS$', li.find_previous({"h1", "h2"}).text.strip()):
                            tag = "-am"
                        else:
                            tag = 'ar'
                        self.set_chapter_section_id(li, chap_num,
                                                    sub_tag=tag,
                                                    prev_id=li.find_previous({"h1", "h2"}).get("id"),
                                                    cnav=f'cnav{self.c_nav_count:02}')

                    else:
                        self.set_chapter_section_id(li, chap_num,
                                                    sub_tag="ar",
                                                    prev_id=li.find_previous({"h1", "h2"}).get("id"),
                                                    cnav=f'cnav{self.c_nav_count:02}')

                elif re.search(r'^Section \d+(\.?\w)*\.', li.text.strip()):
                    chap_num = re.search(r'^Section (?P<id>\d+(\.?\w)*)\.', li.text.strip()).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li, chap_num.zfill(2),
                                                sub_tag="-sec",
                                                prev_id=li.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
                elif re.search(r'^\d+(\.?\w)*\.', li.text.strip()):
                    chap_num = re.search(r'^(?P<id>\d+(\.?\w)*)\.', li.text.strip()).group("id")
                    self.c_nav_count += 1
                    if self.release_number in ['74']:
                        tag = "-sec"
                    else:
                        tag = "-s"
                    self.set_chapter_section_id(li, chap_num.zfill(2),
                                                sub_tag=tag,
                                                prev_id=li.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

    def creating_formatted_table(self):
        tbl_head = []
        count = 1
        tbl_text = None
        new_row_tag = self.soup.new_tag('div', style="flex-basis: 10%;")

        if self.file_no == '06':
            tbl_text = ['Table 1', 'Table 2']

        for tag in self.soup.find_all(class_="table"):
            if self.file_no == '06' and re.search(r'^Table 2', tag.text.strip()):
                colum_count = len(tag.find_all("b"))
                newRow = self.soup.new_tag('li', style="border-radius: 3px;padding: 20px 25px;"
                                                       "display: flex;justify-content:space-evenly;margin-bottom: 05px;")
                newTable = self.soup.new_tag('ul')
                new_p_tag = self.soup.new_tag('p')
                new_p_tag.string = re.search(r'^Table 2', tag.text.strip()).group()
                tag.insert_before(new_p_tag)
                tag.string = re.sub(r'^Table 2', '', tag.text.strip())

                tbl_data = tag.text.split('\n')

                count = 1
                for data in tbl_data:
                    if len(data.strip()) > 0 and data.strip() not in tbl_text:
                        if data.strip() not in ['w', 'r', 'f']:
                            if 0 < count <= colum_count:
                                count += 1
                            else:
                                newRow = self.soup.new_tag('li', style="border-radius: 3px;padding: 20px 25px;"
                                                                       "display: flex;justify-content:space-evenly"
                                                                       ";margin-bottom: 05px;")
                                count = 2

                            new_row_tag = self.soup.new_tag('div', style="flex-basis: 10%;")
                            new_row_tag.append(data)
                            newRow.append(new_row_tag)
                            newTable.append(newRow)
                        else:
                            new_sub_tag = self.soup.new_tag('sub')
                            new_sub_tag.string = data
                            new_row_tag.append(new_sub_tag)

                tag.replace_with(newTable)

            elif self.file_no not in ['06'] and tag.span and re.search(r's\d', str(tag.span.get("class"))):
                colum_count = len(tag.find_all("b"))
                newRow = self.soup.new_tag('li', style="border-radius: 3px;padding: 20px 25px;"
                                                       "display: flex;justify-content:space-evenly;margin-bottom: 05px;")
                newTable = self.soup.new_tag('ul')
                tbl_head_row = self.soup.new_tag('li', style="border-radius: 1px;padding: 10px 15px;"
                                                             "display: flex;justify-content:space-evenly;")

                for head_tag in tag.find_all("b"):
                    new_head_tag = self.soup.new_tag('div', style="flex-basis: 10%;color: #000000;")
                    new_head_tag.append(head_tag.text.strip())
                    tbl_head_row.append(new_head_tag)
                    newTable.append(tbl_head_row)
                    tbl_head.append(head_tag.text.strip())

                tbl_data = tag.text.split('\n')
                tbl_data = [i for i in tbl_data if i]
                for data in tbl_data:
                    if len(data.strip()) > 0:
                        if 0 < count <= colum_count:
                            count += 1
                        else:
                            newRow = self.soup.new_tag('li', style="border-radius: 3px;padding: 20px 25px;display:flex;"
                                                                   "justify-content:space-evenly;margin-bottom: 05px;")
                            count = 2

                        new_row_tag = self.soup.new_tag('div', style="flex-basis: 10%;")
                        new_row_tag.append(data)
                        newRow.append(new_row_tag)
                        newTable.append(newRow)

                tag.replace_with(newTable)
