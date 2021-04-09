# cic-beautify-state-codes

Welcome to the Code Improvement Commission

This repository was created by UniCourt on behalf of [Public.Resource.Org](https://public.resource.org/). All this work is in the public domain and there are NO RIGHTS RESERVED.

This repository contains software that transforms official codes from ugly .rtf files into nice-looking, accessible HTML. We use "textutil" on a Mac to go from .rtf to bad HTML. Then, the code in this repository does the heavy lifting.

Currently this code supports following states:

1. ###Georgia (GA): 
   
   **Code repo:** https://github.com/UniCourt/cic-code-ga
   
   **Code pages:** https://unicourt.github.io/cic-code-ga

   **Original RTF:** https://archive.org/download/gov.ga.ocga.2018

   

2. ###Arkansas (AR):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ar
   
   **Code pages:** https://unicourt.github.io/cic-code-ar
   
   **Original RTF:** https://archive.org/download/gov.ar.code


3. ###Mississippi (MS):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ms
   
   **Code pages:** https://unicourt.github.io/cic-code-ms
   
   **Original RTF:** https://archive.org/download/gov.ms.code.ann.2018


4. ###Tennessee (TN):
   
   **Code repo:** https://github.com/UniCourt/cic-code-tn
   
   **Code pages:** https://unicourt.github.io/cic-code-tn
   
   **Original RTF:** https://archive.org/details/gov.tn.tca

5. ###Kentucky (KY):
   
   **Code repo:** https://github.com/UniCourt/cic-code-ky
   
   **Code pages:** https://unicourt.github.io/cic-code-ky
   
   **Original RTF:** https://archive.org/details/gov.ky.code


In subsequent months, we intend to add two more features:

1. Extend the code to handle the official codes Colorado and Idaho.
2. Add a "redline" capability to show diffs. 

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
                    │   └───ga
                    │       └───ocga
                    │              └───raw
                    │                     title_01.html
    

5. Python3.8 should be installed in development environment to run this project  

6. run **pip install -r requirements.txt** to install all the packages required

**Usage:** python html_parser/html_parse_runner.py

        [--state_key (GA)]
        
        [--release_label (Release-75)]
        
        [--release_date (DD-MM-YYYY)]
        
        [--input_file_name (gov.ga.ocga.title.01.html) This is an optional argument,
        
        if this argument is not passed all the files for provided release label will be parsed]
