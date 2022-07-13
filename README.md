# Open Bibles

Repository of public domain and freely licensed bibles in some standard XML formats.

## Translation List

| Filename                        | Language     | Format  | Abbrev | Version                                          | License       |
|---------------------------------|--------------|---------|--------|--------------------------------------------------|---------------|
| chr-cherokee.usfx.xml           | Cherokee     | USFX    |        | Cherokee New Testament                           | Public Domain |
| cze-bkr.zefania.xml             | Czech        | Zefania |        | Bible kralická                                   | Public Domain |
| eng-kjv.osis.xml                | English      | OSIS    | KJV    | King James Version                               | Public Domain |
| eng-bbe.usfx.xml                | English      | USFX    | BBE    | Bible in Basic English                           | Public Domain |
| eng-gb-oeb.osis.xml             | English (UK) | OSIS    | OEB-CW | Open English Bible, Commonwealth Edition         | Public Domain |
| eng-gb-webbe.usfx.xml           | English (UK) | USFX    | WEBBE  | World English Bible, British Edition             | Public Domain |
| eng-us-oeb.osis.xml             | English (US) | OSIS    | OEB-US | Open English Bible, US Edition                   | Public Domain |
| eng-web.usfx.xml                | English      | USFX    | WEB    | World English Bible                              | Public Domain |
| heb-leningrad.usfx.xml          | Hebrew       | USFX    |        | Hebrew Leningrad Codex                           | _see below_   |
| lat-clementine.usfx.xml         | Latin        | USFX    |        | Clementine Latin Vulgate                         | Public Domain |
| por-almeida.usfx.xml            | Portuguese   | USFX    |        | João Ferreira de Almeida                         | Public Domain |
| ron-rccv.usfx.xml               | Romanian     | USFX    |        | Protestant Romanian Corrected Cornilescu Version | Public Domain |
| dut-statenvertaling.zefania.xml | Dutch        | Zefania |        | Statenvertaling (1637)                           | Public Domain |
| jpn-kougo.osis.xml              | Japanese     | OSIS    |        | Japanese Kougo (Colloquial)                      | Public Domain |
| spaRV1909_usfx.xml              | Spanish      | USFX    | RV1909 | Reina Valera 1909                                | Public Domain |
| spabes_usfx.xml                 | Spanish      | USFX    | SPNBES | La Biblia en Español Sencillo                    | Creative Commons |
| spapddpt_usfx.xml               | Spanish      | USFX    | SPAPDT | Spanish Bible (God's Word for You)               | Creative Commons |
| spavbl_usfx.xml                 | Spanish      | USFX    | VBL    | Spanish Free Bible Version                       | Creative Commons |


## Translation Details

### Hebrew Leningrad Codex

- Source: http://www.tanach.us/Pages/Technical.html
- License: http://www.tanach.us/License.html

>All biblical Hebrew text, in any format, may be viewed or copied without restriction.
>Citation...is appreciated. Please include the version number, 26.0, as a reference. 

## How to Use

The XML files are in a few different (de facto) standard formats, all marked up with XML. There are various tools on the 'net that will let you parse the files and build something cool.

I use these files along with the [bible_parser](https://github.com/seven1m/bible_parser) Ruby gem to build a MySQL database that backs the service [bible-api.com](https://bible-api.com), which is free for everyone to use.
