# cic-beautify-state-codes-framework

Welcome to the Code Improvement Commission

This repository was created by UniCourt on behalf of [Public.Resource.Org](https://public.resource.org/). All this work is in the public domain and there are NO RIGHTS RESERVED.

This repository contains software that transforms official codes from ugly .rtf files into nice-looking, accessible HTML. We use "textutil" on a Mac to go from .rtf to bad HTML. Then, the code in this repository does the heavy lifting.

Currently this code supports following states:

1. ###Alaska (AK): 
   
   **Code repo:** https://github.com/UniCourt/cic-code-ak
   
   **Code pages:** https://unicourt.github.io/cic-code-ak

   **Original RTF:** https://archive.org/download/gov.ak.code


2. ###Arkansas (AR):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ar
   
   **Code pages:** https://unicourt.github.io/cic-code-ar
   
   **Original RTF:** https://archive.org/download/gov.ar.code


3. ###Colorado (CO):
   
   **Code repo:** https://github.com/UniCourt/cic-code-co
   
   **Code pages:** https://unicourt.github.io/cic-code-co
   
   **Original RTF:** https://archive.org/download/gov.co.crs.bulk


4. ###Georgia (GA):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ga
   
   **Code pages:** https://unicourt.github.io/cic-code-ga
   
   **Original RTF:** https://archive.org/download/gov.ga.ocga.2018


5. ###Idaho (ID):
   
   **Code repo:** https://github.com/UniCourt/cic-code-id
   
   **Code pages:** https://unicourt.github.io/cic-code-id
   
   **Original files can be found here:** https://archive.org/details/govlaw?and%5B%5D=subject%3A%22idaho.gov%22+AND+subject%3A%222020+Code%22&sin=&sort=titleSorter


6. ###Kentucky (KY):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ky
   
   **Code pages:** https://unicourt.github.io/cic-code-ky
   
   **Original RTF:** https://archive.org/details/gov.ky.code


7. ###Mississippi (MS):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ms
   
   **Code pages:** https://unicourt.github.io/cic-code-ms
   
   **Original RTF:** https://archive.org/download/gov.ms.code.ann.2018


8. ###North Carolina (NC):
   
   **Code repo:** https://github.com/UniCourt/cic-code-nc
   
   **Code pages:** https://unicourt.github.io/cic-code-nc
   
   **Original RTF:**  https://archive.org/download/gov.nc.code


9.  ###North Dakota (ND):
   
      **Code repo:** https://github.com/UniCourt/cic-code-nd
      
      **Code pages:** https://unicourt.github.io/cic-code-nd
      
      **Original RTF:**  https://archive.org/details/gov.nd.code


10. ###Tennessee (TN):
   
      **Code repo:** https://github.com/UniCourt/cic-code-tn
      
      **Code pages:** https://unicourt.github.io/cic-code-tn
      
      **Original RTF:** https://archive.org/details/gov.tn.tca


11. ###Vermont (VT):
   
      **Code repo:** https://github.com/UniCourt/cic-code-vt
      
      **Code pages:** https://unicourt.github.io/cic-code-vt
      
      **Original RTF:** https://archive.org/download/gov.vt.code


12. ###Virginia (VA):
   
      **Code repo:** https://github.com/UniCourt/cic-code-va
      
      **Code pages:** https://unicourt.github.io/cic-code-va
      
      **Original RTF:**  https://archive.org/download/gov.va.code/


13. ###Wyoming (WY):
   
      **Code repo:** https://github.com/UniCourt/cic-code-wy
      
      **Code pages:** https://unicourt.github.io/cic-code-wy
      
      **Original RTF:** https://archive.org/details/gov.wy.code/


In subsequent months, we intend to add two more features:

1. Extend the code to handle the official codes Rhode Island and other states.
2. Add a "redline" capability to show diffs.
3. Adding citation to external links.


**REQUIREMENTS AND INSTALLATION**

**BeautifulSoup 4:** https://www.crummy.com/software/BeautifulSoup/

**lxml:** https://lxml.de/

**To setup project :**

1. Create new folder named **transforms**

2. Based on the state create a folder called *transforms/{state_name}*

3.Inside the above folder based on the release create a folder ocga/{release} which will contain raw files (raw files are textutil output files)

4. Example folder structure:

                    ```
                    project
                    │   README.md
                    │   requirements.txt    
                    │
                    └───html_parser
                    │   │   file011.py
                    │   │   file012.py
                    |
                    └───transforms
                    │   └───co
                    │       └───occo
                    │              └───title_01.html 
    

5. Python3.8 should be installed in development environment to run this project  

6. run **pip install -r requirements.txt** to install all the packages required

**Usage:** python html_parser/html_parse_runner.py

         [--state_key (CO)]

         [--path     This argument can be in three different types,
                     To run single file : (/co/occo/r80/gov.co.code.title.01.html) 
                     To run all files from particular release : (/co/occo/r80/) 
                     To run all the release of particular state : (/co/occo/) ]
    
         [--run_after_release (83) This is an optional argument,this helps to run all releases after the mentioned release]


**Additional required files:**
      
      Release_dates.txt :
		             This is a file where all states release dates are stored in the format <state_key>_r<release_number>< ><release_date> 
                     eg: [CO_r71 2020.08.01]

**Implementation of Child class:**

      Child class name format : <state_key>_html_parser eg:co_html_parser.
      Mandatory functions in child :
         Pre_process :
         convert_paragraph_to_alphabetical_ol_tags
