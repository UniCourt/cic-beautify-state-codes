# cic-beautify-state-codes

Welcome to the Code Improvement Commission

This repository was created by UniCourt on behalf of [Public.Resource.Org](https://public.resource.org/). All this work is in the public domain and there are NO RIGHTS RESERVED.

This repository contains software that transforms official codes from ugly .rtf files into nice-looking, accessible HTML. We use "textutil" on a Mac to go from .rtf to bad HTML. Then, the code in this repository does the heavy lifting.

Currently this code supports GA  and current quarterly releases that are available include:

* Release 70 dated 2018.12.01.
* Release 71 dated 2019.03.05.
* Release 72 dated 2019.05.01.
* Release 73 dated 2019.08.21.
* Release 74 dated 2020.01.15.
* Release 75 dated 2020.04.20.
* Release 76 dated 2020.06.12.
* Release 77 dated 2020.08.10.

Release are available here: https://github.com/UniCourt/cic-code-ga

Original RTF files can be found here: https://archive.org/download/gov.ga.ocga.2018

In subsequent months, we intend to add two more features:

1. Extend the code to handle the official codes of Mississippi, Arkansas, Kentucky, and Colorado.
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
