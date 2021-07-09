#!/usr/bin/python3
# -*- coding: utf-8 -*-

r"""
Convert usfm bibles to osis.

Notes:
   * better handling of osisID's is probably needed.

   * no attempt has been made to process any x- attributes in this script
     other than x-morph as found in bibles located on the ebible.org website.

   * I can think of scenarios where this script may not work properly. However,
     it works fine for all of the usfm bibles that I have access to at this
     time.

   * jmp, xop, and sd# need better handling.

   * There may be better ways to handle lh and lf

   * table cell column spanning is not implemented

Alternative Book Ordering:
    To have the books output in an order different from the built in canonical
    book order you will have to create a simple text file.

    FIRST, put the OSIS ID's for the books in the order you want, one per line,
    in a plain text file. Example:
        Gen
        Exod
        Lev
        ...
        Rev

    SECOND, name the file as follows:   order-SomeOrderYouWant.txt

    THIRD, place that file in the directory where you will be running
    the script. This new book order will be automatically detected and
    available.

    Examples can be provided. Simple send me an email and ask me for them.

    NOTE: I should probably change this so that there's a more central
          location for these alternative book orderings.

This script has been tested and is known to work with CPython 3.4.0,
CPython 2.7.6, jython 2.7.0, pypy 2.5.0, and pypy3 2.4.0.

Neither jython nor pypy are recomended as they are quite a bit slower at
running this script than CPython.

This script is public domain. You may do whatever you want with it.

"""

#
#    uFDD0     - used to mark line breaks during processing
#    uFDD1     - used to preserve line breaks during wj processing
#
#    uFDD2     - used at start of footnotes to help process \fp markers
#    uFDD3     - used at end of footnotes to help process \fp markers
#
#    uFDD4     - mark end of cl and sp tags
#    uFDD5     - mark end of cp tags
#
#    uFDE0     - used to mark the start of introductions
#    uFDE1     - used to mark the end of introductions
#
#    uFDE2     - used to separate attributes in usfm tags
#

# make pylint happier..
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
# pylint: disable=too-many-branches
# pylint: disable=too-many-locals


from __future__ import print_function, unicode_literals
import sys
import argparse
import os
import os.path
import glob
import re
import codecs
import datetime
import unicodedata
import logging
from collections import OrderedDict
from contextlib import closing

# try to import multiprocessing
# (jython 2.7.0 doesn't have this module.)
HAVEMULTIPROCESSING = False
try:
    import multiprocessing

    HAVEMULTIPROCESSING = True
except ImportError:
    pass

# try to import lxml so that we can validate
# our output against the OSIS schema.
HAVELXML = False
try:
    import lxml.etree as et

    HAVELXML = True
except ImportError:
    pass

# -------------------------------------------------------------------------- #

META = {
    "USFM": "3.0",  # Targeted USFM version
    "OSIS": "2.1.1",  # Targeted OSIS version
    "VERSION": "0.6",  # THIS SCRIPT version
    "DATE": "2021-06-30",  # THIS SCRIPT revision date
}

# -------------------------------------------------------------------------- #

OSISHEADER = """<?xml version="1.0" encoding="utf-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.bibletechnologies.net/2003/OSIS/namespace
        http://www.bibletechnologies.net/osisCore.2.1.1.xsd">
    <osisText osisIDWork="{}" osisRefWork="Bible" xml:lang="{}">
        <header>
            <revisionDesc resp="{}">
                <date>{}</date>
                <p>Converted from USFM source using u2o.py</p>
            </revisionDesc>
            <work osisWork="{}">
                <title>{}</title>
                {}
                <type type="OSIS">Bible</type>
                <identifier type="OSIS">Bible.{}.{}</identifier>
                <refSystem>Bible</refSystem>
            </work>{}
        </header>\n"""

STRONGSWORK = """
            <work osisWork="strong">
                <refSystem>Dict.Strongs</refSystem>
            </work>"""

OSISFOOTER = """
    </osisText>
</osis>\n"""

# -------------------------------------------------------------------------- #

CANONICALORDER = [
    # Canonical order used by the usfm2osis.py script...
    # minus the extra books that aren't part of usfm at this time.
    "FRONT",
    "INTRODUCTION",
    "Gen",
    "Exod",
    "Lev",
    "Num",
    "Deut",
    "Josh",
    "Judg",
    "Ruth",
    "1Sam",
    "2Sam",
    "1Kgs",
    "2Kgs",
    "1Chr",
    "2Chr",
    "PrMan",
    "Jub",
    "1En",
    "Ezra",
    "Neh",
    "Tob",
    "Jdt",
    "Esth",
    "EsthGr",
    "1Meq",
    "2Meq",
    "3Meq",
    "Job",
    "Ps",
    "AddPs",
    "5ApocSyrPss",
    "Odes",
    "Prov",
    "Reproof",
    "Eccl",
    "Song",
    "Wis",
    "Sir",
    "PssSol",
    "Isa",
    "Jer",
    "Lam",
    "Bar",
    "EpJer",
    "2Bar",
    "EpBar",
    "4Bar",
    "Ezek",
    "Dan",
    "DanGr",
    "PrAzar",
    "Sus",
    "Bel",
    "Hos",
    "Joel",
    "Amos",
    "Obad",
    "Jonah",
    "Mic",
    "Nah",
    "Hab",
    "Zeph",
    "Hag",
    "Zech",
    "Mal",
    "1Esd",
    "2Esd",
    "4Ezra",
    "5Ezra",
    "6Ezra",
    "1Macc",
    "2Macc",
    "3Macc",
    "4Macc",
    "Matt",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Rom",
    "1Cor",
    "2Cor",
    "Gal",
    "Eph",
    "Phil",
    "Col",
    "1Thess",
    "2Thess",
    "1Tim",
    "2Tim",
    "Titus",
    "Phlm",
    "Heb",
    "Jas",
    "1Pet",
    "2Pet",
    "1John",
    "2John",
    "3John",
    "Jude",
    "Rev",
    "EpLao",
    "XXA",
    "XXB",
    "XXC",
    "XXD",
    "XXE",
    "XXF",
    "XXG",
    "BACK",
    "CONCORDANCE",
    "GLOSSARY",
    "INDEX",
    "GAZETTEER",
    "X-OTHER",
]
# get list of book orders available from external files in the current
# working directory.  Each order file has the following naming pattern:
#    order-SOMEORDER.txt
BOOKORDERS = sorted(
    [
        _.replace("order-", "").replace(".txt", "")
        for _ in glob.glob("order-*.txt")
    ]
)
BOOKORDERS.append("none")
BOOKORDERS.insert(0, "canonical")

# -------------------------------------------------------------------------- #

# convert usfm book names
BOOKNAMES = {
    # old testament books
    "GEN": "Gen",
    "EXO": "Exod",
    "LEV": "Lev",
    "NUM": "Num",
    "DEU": "Deut",
    "JOS": "Josh",
    "JDG": "Judg",
    "RUT": "Ruth",
    "1SA": "1Sam",
    "2SA": "2Sam",
    "1KI": "1Kgs",
    "2KI": "2Kgs",
    "1CH": "1Chr",
    "2CH": "2Chr",
    "EZR": "Ezra",
    "NEH": "Neh",
    "EST": "Esth",
    "JOB": "Job",
    "PSA": "Ps",
    "PRO": "Prov",
    "ECC": "Eccl",
    "SNG": "Song",
    "ISA": "Isa",
    "JER": "Jer",
    "LAM": "Lam",
    "EZK": "Ezek",
    "DAN": "Dan",
    "HOS": "Hos",
    "JOL": "Joel",
    "AMO": "Amos",
    "OBA": "Obad",
    "JON": "Jonah",
    "MIC": "Mic",
    "NAM": "Nah",
    "HAB": "Hab",
    "ZEP": "Zeph",
    "HAG": "Hag",
    "ZEC": "Zech",
    "MAL": "Mal",
    # new testament books
    "MAT": "Matt",
    "MRK": "Mark",
    "LUK": "Luke",
    "JHN": "John",
    "ACT": "Acts",
    "ROM": "Rom",
    "1CO": "1Cor",
    "2CO": "2Cor",
    "GAL": "Gal",
    "EPH": "Eph",
    "PHP": "Phil",
    "COL": "Col",
    "1TH": "1Thess",
    "2TH": "2Thess",
    "1TI": "1Tim",
    "2TI": "2Tim",
    "TIT": "Titus",
    "PHM": "Phlm",
    "HEB": "Heb",
    "JAS": "Jas",
    "1PE": "1Pet",
    "2PE": "2Pet",
    "1JN": "1John",
    "2JN": "2John",
    "3JN": "3John",
    "JUD": "Jude",
    "REV": "Rev",
    # other books
    "TOB": "Tob",
    "JDT": "Jdt",
    "ESG": "EsthGr",
    "WIS": "Wis",
    "SIR": "Sir",
    "BAR": "Bar",
    "LJE": "EpJer",
    "S3Y": "PrAzar",
    "SUS": "Sus",
    "BEL": "Bel",
    "1MA": "1Macc",
    "2MA": "2Macc",
    "3MA": "3Macc",
    "4MA": "4Macc",
    "1ES": "1Esd",
    "2ES": "2Esd",
    "MAN": "PrMan",
    "PS2": "AddPs",
    "ODA": "Odes",
    "PSS": "PssSol",
    "EZA": "4Ezra",
    "5EZ": "5Ezra",
    "6EZ": "6Ezra",
    "DAG": "DanGr",
    "PS3": "5ApocSyrPss",
    "2BA": "2Bar",
    "LBA": "EpBar",
    "JUB": "Jub",
    "ENO": "1En",
    "1MQ": "1Meq",
    "2MQ": "2Meq",
    "3MQ": "3Meq",
    "REP": "Reproof",
    "4BA": "4Bar",
    "LAO": "EpLao",
    # private use
    "XXA": "XXA",
    "XXB": "XXB",
    "XXC": "XXC",
    "XXD": "XXD",
    "XXE": "XXE",
    "XXF": "XXF",
    "XXG": "XXG",
    # Peripheral books
    "FRT": "FRONT",
    "INT": "INTRODUCTION",
    "BAK": "BACK",
    "CNC": "CONCORDANCE",
    "GLO": "GLOSSARY",
    "TDX": "INDEX",
    "NDX": "GAZETTEER",
    "OTH": "X-OTHER",
}

# noncanonical book id's
NONCANONICAL = {
    "FRONT": "front",
    "INTRODUCTION": "introduction",
    "XXA": "x-other-a",
    "XXB": "x-other-b",
    "XXC": "x-other-c",
    "XXD": "x-other-d",
    "XXE": "x-other-e",
    "XXF": "x-other-f",
    "XXG": "x-other-g",
    "BACK": "back",
    "CONCORDANCE": "concordance",
    "GLOSSARY": "glossary",
    "INDEX": "index",
    "GAZETTEER": "gazetteer",
    "X-OTHER": "x-other",
}

# list of books with one chapter
ONECHAP = ["Obad", "Phlm", "2John", "3John", "Jude"]


# -------------------------------------------------------------------------- #
# TAG MAPPINGS

# identification tags
IDTAGS = {
    r"\sts": ("", '<milestone type="x-usfm-sts" n="{}" />'),
    r"\toc1": ("", '<milestone type="x-usfm-toc1" n="{}" />'),
    r"\toc2": ("", '<milestone type="x-usfm-toc2" n="{}" />'),
    r"\toc3": ("", '<milestone type="x-usfm-toc3" n="{}" />'),
    # ebible.org bibles sometimes use a ztoc4 tag. If it's desired to process
    # this tag then simply uncomment the ztoc4 line here.
    # (No other ztags are even attempted in this converter.)
    # r'\ztoc4': ('', '<milestone type=x-usfm-ztoc4 n="{}" />'),
    r"\restore": ("<!-- restore - ", " -->"),
    # the osis 2.1.1 user manual says the value of h h1 h2 and h3 tags should
    # be in the short attribute of a title.
    # ************************************************************************
    # NOTE: These types of titles seem to be problematic when trying to import
    #       bibles for The SWORD Project. So alternative conversions have been
    #       implemented to work around the issue.
    # ************************************************************************
    # r'\h': ('', '<title type="runningHead" short="{}" />'),
    # r'\h1': ('', '<title type="runningHead" n="1" short="{}" />'),
    # r'\h2': ('', '<title type="runningHead" n="2" short="{}" />'),
    # r'\h3': ('', '<title type="runningHead" n="3" short="{}" />')
    # ************************************************************************
    r"\h": ("", '<milestone type="x-usfm-h" n="{}" />'),
    r"\h1": ("", '<milestone type="x-usfm-h1" n="{}" />'),
    r"\h2": ("", '<milestone type="x-usfm-h2" n="{}" />'),
    r"\h3": ("", '<milestone type="x-usfm-h3" n="{}" />'),
}

# the osis 2.1.1 user manual says the value of id, ide, and rem should be
# placed in description tags in the header. That's why they are in a separate
# list instead of the dict above.
IDTAGS2 = [r"\id", r"\ide", r"\rem"]

# title tags
TITLETAGS = {
    # ---------------------------------------------------------
    # ##### SECTION TAGS get special handling elsewhere ##### #
    r"\is": ('<title type="x-introduction">', "</title>"),
    r"\is1": ('<title type="x-introduction">', "</title>"),
    r"\is2": ('<title type="x-introduction">', "</title>"),
    # \is3 and \is4 are not currently handled in this script.
    # r'\is3': ('<title type="x-introduction">', '</title>'),
    # r'\is4': ('<title type="x-introduction">', '</title>'),
    #
    r"\ms": ("<title>", "</title>"),
    r"\ms1": ("<title>", "</title>"),
    r"\ms2": ("<title>", "</title>"),
    r"\ms3": ("<title>", "</title>"),
    # \ms4 is not currently handled by this script.
    # r'\ms4': ('<title>', '</title>'),
    #
    r"\s": ("<title>", "</title>"),
    r"\s1": ("<title>", "</title>"),
    r"\s2": ("<title>", "</title>"),
    r"\s3": ("<title>", "</title>"),
    r"\s4": ("<title>", "</title>"),
    # ##### Semantic Whitespace ##### #
    r"\sd": ('<milestone type="x-usfm-sd" />', ""),
    r"\sd1": ('<milestone type="x-usfm-sd1" />', ""),
    r"\sd2": ('<milestone type="x-usfm-sd2" />', ""),
    r"\sd3": ('<milestone type="x-usfm-sd3" />', ""),
    r"\sd4": ('<milestone type="x-usfm-sd4" />', ""),
    # ---------------------------------------------------------
    # ##### INTRODUCTIONS ##### #
    r"\imt": ('<title type="main" subType="x-introduction">', "</title>"),
    r"\imt1": (
        '<title level="1" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imt2": (
        '<title level="2" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imt3": (
        '<title level="3" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imt4": (
        '<title level="4" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imt5": (
        '<title level="5" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imte": ('<title type="main" subType="x-introduction">', "</title>"),
    r"\imte1": (
        '<title level="1" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imte2": (
        '<title level="2" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imte3": (
        '<title level="3" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imte4": (
        '<title level="4" type="main" subType="x-introduction">',
        "</title>",
    ),
    r"\imte5": (
        '<title level="5" type="main" subType="x-introduction">',
        "</title>",
    ),
    # r'\ib': ('', ''),
    # ##### Normal Title Section ##### #
    r"\mt": ('<title type="main">', "</title>"),
    r"\mt1": ('<title level="1" type="main">', "</title>"),
    r"\mt2": ('<title level="2" type="main">', "</title>"),
    r"\mt3": ('<title level="3" type="main">', "</title>"),
    r"\mt4": ('<title level="4" type="main">', "</title>"),
    r"\mt5": ('<title level="5" type="main">', "</title>"),
    r"\mte": ('<title type="main">', "</title>"),
    r"\mte1": ('<title level="1" type="main">', "</title>"),
    r"\mte2": ('<title level="2" type="main">', "</title>"),
    r"\mte3": ('<title level="3" type="main">', "</title>"),
    r"\mte4": ('<title level="4" type="main">', "</title>"),
    r"\mte5": ('<title level="5" type="main">', "</title>"),
    #
    r"\mr": ('<title type="scope"><reference>', "</reference></title>"),
    r"\sr": ('<title type="scope"><reference>', "</reference></title>"),
    r"\r": (
        '<title type="parallel"><reference type="parallel">',
        "</reference></title>",
    ),
    r"\d": ('<title type="psalm" canonical="true">', "</title>"),
    r"\sp": ("<speaker>", "</speaker>"),
    # ##### chapter cl tags ##### #
    #
    # This is the best way I know how to convert these tags.
    #
    # The osis user manual says to convert these to titles and use chapterLabel
    # for type in the title tag. That type is not allowed according to the osis
    # 2.1.1 schema though. So I use x-chapterLabel for the type instead.
    # NOTE: titles created in this manner don't work with The SWORD Project
    #       sofware and create problems with displaying other titles as well.
    #       So the conversion to titles is disabled for now and milestone
    #       markers are inserted instead.
    # r'\cl': ('<title type="x-chapterLabel" short="', '" />'),
    r"\cl": ('<milestone type="x-chapterLabel" n="', '" />'),
    # ##### chapter cd tags ##### #
    # the osis user manual says cd titles should be in an introduction div.
    r"\cd": (
        '<div type="introduction">\ufdd0<title type="x-description">',
        "</title>\ufdd0</div>",
    ),
    # ##### special features ##### #
    # the osis user manual says this should be in an lg tag of type doxology
    # with an l tag of type refrain.
    r"\lit": (
        '<lg type="doxology">\ufdd0<l type="refrain">',
        "</l>\ufdd0</lg>",
    ),
}

# paragraph and poetry/prose tags
PARTAGS = {
    # INTRODUCTIONS
    r"\iot": (r'<item type="x-head" subType="x-introduction">', r"</item>"),
    r"\io": (r'<item type="x-indent-1" subType="x-introduction">', r"</item>"),
    r"\io1": (
        r'<item type="x-indent-1" subType="x-introduction">',
        r"</item>",
    ),
    r"\io2": (
        r'<item type="x-indent-2" subType="x-introduction">',
        r"</item>",
    ),
    r"\io3": (
        r'<item type="x-indent-3" subType="x-introduction">',
        r"</item>",
    ),
    r"\io4": (
        r'<item type="x-indent-4" subType="x-introduction">',
        r"</item>",
    ),
    r"\ip": (r'<p subType="x-introduction">', r" </p>"),
    r"\im": (r'<p type="x-noindent" subType="x-introduction">', r" </p>"),
    r"\ipq": (r'<p type="x-quote" subType="x-introduction">', r" </p>"),
    r"\imq": (
        r'<p type="x-noindent-quote" subType="x-introduction">',
        r" </p>",
    ),
    r"\ipi": (r'<p type="x-indented" subType="x-introduction">', r" </p>"),
    r"\imi": (
        r'<p type="x-noindent-indented" subType="x-introduction">',
        r" </p>",
    ),
    r"\ili": (
        r'<item type="x-indent-1" subType="x-introduction">',
        r" </item>",
    ),
    r"\ili1": (
        r'<item type="x-indent-1" subType="x-introduction">',
        r" </item>",
    ),
    r"\ili2": (
        r'<item type="x-indent-2" subType="x-introduction">',
        r" </item>",
    ),
    r"\ipr": (r'<p type="x-right" subType="x-introduction">', r" </p>"),
    r"\iq": (r'<l level="1" subType="x-introduction">', r" </l>"),
    r"\iq1": (r'<l level="1" subType="x-introduction">', r" </l>"),
    r"\iq2": (r'<l level="2" subType="x-introduction">', r" </l>"),
    r"\iq3": (r'<l level="3" subType="x-introduction">', r" </l>"),
    r"\iex": (r'<div type="bridge" subType="x-introduction">', r"</div>"),
    r"\ie": (r"<!-- ie -->", r""),
    # ##### PARAGRAPH/POETRY
    r"\p": (r"<p>", r" </p>"),
    r"\m": (r'<p type="x-noindent">', r" </p>"),
    r"\po": (r'<p type="x-usfm-po">', r" </p>"),
    r"\pmo": (r'<p type="x-embedded-opening">', r" </p>"),
    r"\pm": (r'<p type="x-embedded">', r" </p>"),
    r"\pmc": (r'<p type="x-embedded-closing">', r" </p>"),
    r"\pmr": (r'<p type="x-right">', r" </p>"),
    r"\pi": (r'<p type="x-indented">', r" </p>"),
    r"\pi1": (r'<p type="x-indented-1">', r" </p>"),
    r"\pi2": (r'<p type="x-indented-2">', r" </p>"),
    r"\pi3": (r'<p type="x-indented-3">', r" </p>"),
    r"\pi4": (r'<p type="x-indented-4">', r" </p>"),
    r"\mi": (r'<p type="x-noindent-indented">', r" </p>"),
    r"\cls": (r"<closer>", r"</closer>"),
    r"\lh": (r'<p type="x-usfm-lh">', r"</p>"),
    r"\lf": (r'<p type="x-usfm-lf">', r"</p>"),
    r"\li": (r'<item type="x-indent-1">', r" </item>"),
    r"\li1": (r'<item type="x-indent-1">', r" </item>"),
    r"\li2": (r'<item type="x-indent-2">', r" </item>"),
    r"\li3": (r'<item type="x-indent-3">', r" </item>"),
    r"\li4": (r'<item type="x-indent-4">', r" </item>"),
    r"\lim": (r'<item type="x-usfm-lim">', r" </item>"),
    r"\lim1": (r'<item type="x-usfm-lim1">', r" </item>"),
    r"\lim2": (r'<item type="x-usfm-lim2">', r" </item>"),
    r"\lim3": (r'<item type="x-usfm-lim3">', r" </item>"),
    r"\lim4": (r'<item type="x-usfm-lim4">', r" </item>"),
    r"\pc": (r'<p type="x-center">', r" </p>"),
    r"\pr": (r'<p type="x-right">', r" </p>"),
    r"\ph": (r'<item type="x-indent-1">', r" </item>"),
    r"\ph1": (r'<item type="x-indent-1">', r" </item>"),
    r"\ph2": (r'<item type="x-indent-2">', r" </item>"),
    r"\ph3": (r'<item type="x-indent-3">', r" </item>"),
    # POETRY Markers
    r"\q": (r'<l level="1">', r" </l>"),
    r"\q1": (r'<l level="1">', r" </l>"),
    r"\q2": (r'<l level="2">', r" </l>"),
    r"\q3": (r'<l level="3">', r" </l>"),
    r"\q4": (r'<l level="4">', r" </l>"),
    r"\qr": (r'<l type="x-right">', r" </l>"),
    r"\qc": (r'<l type="x-center">', r" </l>"),
    r"\qa": (r'<title type="acrostic">', r"</title>"),
    r"\qd": (r'<l type="x-usfm-qd">', r"</l>"),
    r"\qm": (r'<l type="x-embedded" level="1">', r" </l>"),
    r"\qm1": (r'<l type="x-embedded" level="1">', r" </l>"),
    r"\qm2": (r'<l type="x-embedded" level="2">', r" </l>"),
    r"\qm3": (r'<l type="x-embedded" level="3">', r" </l>"),
    r"\qm4": (r'<l type="x-embedded" level="4">', r" </l>"),
    # sidebar markers... FIXED ELSEWHERE
    r"\esb": (r"<SIDEBAR>", ""),
    r"\esbe": (r"</SIDEBAR>", ""),
}

# other introduction and poetry tags
OTHERTAGS = OrderedDict()
for _ in [
    # selah is handled in a special manner…
    (r"\qs ", "<selah>"),
    (r"\qs*", "</selah>"),
    # these tags get special handling…
    (r"\ie", "<!-- ie -->"),  # handled with partags… may not need here…
    (r"\ib ", "<!-- b -->"),  # handled exactly like \b
    (r"\b ", "<!-- b -->"),
    (r"\nb ", "<!-- nb -->"),
    (r"\nb", "<!-- nb -->"),
    # translators chunk marker…
    (r"\ts", "<!-- ts -->"),
]:
    OTHERTAGS[_[0]] = _[1]

# table cell tags
CELLTAGS = {
    # header cells
    r"\th": ('<cell role="label">', "</cell>"),
    r"\th1": ('<cell role="label">', "</cell>"),
    r"\th2": ('<cell role="label">', "</cell>"),
    r"\th3": ('<cell role="label">', "</cell>"),
    r"\th4": ('<cell role="label">', "</cell>"),
    r"\th5": ('<cell role="label">', "</cell>"),
    r"\thr": ('<cell role="label" type="x-right">', "</cell>"),
    r"\thr1": ('<cell role="label" type="x-right">', "</cell>"),
    r"\thr2": ('<cell role="label" type="x-right">', "</cell>"),
    r"\thr3": ('<cell role="label" type="x-right">', "</cell>"),
    r"\thr4": ('<cell role="label" type="x-right">', "</cell>"),
    r"\thr5": ('<cell role="label" type="x-right">', "</cell>"),
    # normal cells
    r"\tc": ("<cell>", "</cell>"),
    r"\tc1": ("<cell>", "</cell>"),
    r"\tc2": ("<cell>", "</cell>"),
    r"\tc3": ("<cell>", "</cell>"),
    r"\tc4": ("<cell>", "</cell>"),
    r"\tc5": ("<cell>", "</cell>"),
    r"\tcr": ('<cell type="x-right">', "</cell>"),
    r"\tcr1": ('<cell type="x-right">', "</cell>"),
    r"\tcr2": ('<cell type="x-right">', "</cell>"),
    r"\tcr3": ('<cell type="x-right">', "</cell>"),
    r"\tcr4": ('<cell type="x-right">', "</cell>"),
    r"\tcr5": ('<cell type="x-right">', "</cell>"),
}

# special text and character style tags.
# \wj tags are handled with a special function. Don't add it here.
SPECIALTEXT = {
    # tags for special text
    r"\add": ('<transChange type="added">', "</transChange>"),
    r"\addpn": (
        '<transChange type="added" subType="x-usfm-addpn">',
        "</transChange>",
    ),
    r"\nd": ("<divineName>", "</divineName>"),
    r"\pn": ("<name>", "</name>"),
    r"\qt": ('<seg type="otPassage">', "</seg>"),
    r"\sig": ("<signed>", "</signed>"),
    r"\ord": ('<hi type="super">', "</hi>"),
    r"\tl": ("<foreign>", "</foreign>"),
    r"\bk": ('<name type="x-usfm-bk">', "</name>"),
    r"\k": ('<seg type="keyword">', "</seg>"),
    r"\dc": ('<transChange type="added" editions="dc">', "</transChange>"),
    r"\sls": ('<foreign type="x-secondaryLanguage">', "</foreign>"),
    r"\+add": (
        '<seg type="x-nested"><transChange type="added">',
        "</transChange></seg>",
    ),
    r"\+addpn": (
        '<seg type="x-nested"><transChange type="added" subType="x-usfm-addpn">',
        "</transChange></seg>",
    ),
    r"\+nd": ('<seg type="x-nested"><divineName>', "</divineName></seg>"),
    r"\+pn": ('<seg type="x-nested"><name>', "</name></seg>"),
    r"\+qt": ('<seg type="x-nested"><seg type="otPassage">', "</seg></seg>"),
    r"\+sig": ('<seg type="x-nested"><signed>', "</signed></seg>"),
    r"\+ord": ('<seg type="x-nested"><hi type="super">', "</hi></seg>"),
    r"\+tl": ('<seg type="x-nested"><foreign>', "</foreign></seg>"),
    r"\+bk": ('<seg type="x-nested"><name type="x-usfm-bk">', "</name></seg>"),
    r"\+k": ('<seg type="x-nested"><seg type="keyword">', "</seg></seg>"),
    r"\+dc": (
        '<seg type="x-nested"><transChange type="added" editions="dc">',
        "</transChange></seg>",
    ),
    r"\+sls": (
        '<seg type="x-nested"><foreign type="x-secondaryLanguage">',
        "</foreign></seg>",
    ),
    # tags for character styles
    r"\em": ('<hi type="emphasis">', "</hi>"),
    r"\bd": ('<hi type="bold">', "</hi>"),
    r"\it": ('<hi type="italic">', "</hi>"),
    r"\bdit": ('<hi type="bold"><hi type="italic">', "</hi></hi>"),
    r"\no": ('<hi type="normal">', "</hi>"),
    r"\sc": ('<hi type="small-caps">', "</hi>"),
    r"\+em": ('<seg type="x-nested"><hi type="emphasis">', "</hi></seg>"),
    r"\+bd": ('<seg type="x-nested"><hi type="bold">', "</hi></seg>"),
    r"\+it": ('<seg type="x-nested"><hi type="italic">', "</hi></seg>"),
    r"\+bdit": (
        '<seg type="x-nested"><hi type="bold"><hi type="italic">',
        "</hi></hi></seg>",
    ),
    r"\+no": ('<seg type="x-nested"><hi type="normal">', "</hi></seg>"),
    r"\+sc": ('<seg type="x-nested"><hi type="small-caps">', "</hi></seg>"),
    # a few stray list tags that work well being handled in this section.
    r"\lik": ('<seg type="x-usfm-lik">', "</seg>"),
    r"\liv": ('<seg type="x-usfm-liv">', "</seg>"),
    r"\liv1": ('<seg type="x-usfm-liv1">', "</seg>"),
    r"\liv2": ('<seg type="x-usfm-liv2">', "</seg>"),
    r"\liv3": ('<seg type="x-usfm-liv3">', "</seg>"),
    r"\liv4": ('<seg type="x-usfm-liv4">', "</seg>"),
    r"\litl": ('<seg type="x-usfm-litl">', "</seg>"),
    # a few stray introduction and poetry tags that
    # work well being handled in this section.
    r"\ior": ('<reference subType="x-introduction">', "</reference>"),
    r"\iqt": ('<q subType="x-introduction">', "</q>"),
    r"\rq": ('<reference type="source">', "</reference>"),
    r"\qac": ('<hi type="acrostic">', "</hi>"),
    r"\+ior": (
        '<seg type="x-nested"><reference subType="x-introduction">',
        "</reference></seg>",
    ),
    r"\+iqt": (
        '<seg type="x-nested"><q subType="x-introduction">',
        "</q></seg>",
    ),
    r"\+rq": (
        '<seg type="x-nested"><reference type="source">',
        "</reference></seg>",
    ),
    r"\+qac": ('<seg type="x-nested"><hi type="acrostic">', "</hi></seg>"),
    # ca and va tags... because simpler handling was needed...
    r"\ca": ('<milestone type="x-usfm-ca" n="', '" />'),
    r"\va": ('<milestone type="x-usfm-va" n="', '" />'),
    # cp and vp tags... because simpler handling was needed...
    r"\cp": ('<milestone type="x-usfm-cp" n="', '" />'),
    r"\vp": ('<milestone type="x-usfm-vp" n="', '" />'),
}

# special features
# do not add \lit here... that is handled with TITLETAGS.
FEATURETAGS = {
    r"\pro": ('<milestone type="x-usfm-pro" n="', '" /> '),
    r"\rb": ('<milestone type="x-usfm-rb" n="', '" /> '),
    r"\rt": ('<milestone type="x-usfm-rt" n="', '" /> '),
    r"\ndx": ("", '<index index="Index" level1="{}" /> '),
    r"\png": ("", '<index index="Geography" level1="{}" />'),
    r"\w": ("", '<index index="Glossary" level1="{}" />'),
    r"\wa": ("", '<index index="Aramaic" level1="{}" />'),
    r"\wg": ("", '<index index="Greek" level1="{}" />'),
    r"\wh": ("", '<index index="Hebrew" level1="{}" />'),
    r"\+pro": ('<milestone type="x-usfm-pro" n="', '" /> '),
    r"\+rb": ('<milestone type="x-usfm-rb" n="', '" /> '),
    r"\+rt": ('<milestone type="x-usfm-rt" n="', '" /> '),
    r"\+ndx": ("", '<index index="Index" level1="{}" /> '),
    r"\+png": ("", '<index index="Geography" level1="{}" />'),
    r"\+w": ("", '<index index="Glossary" level1="{}" />'),
    r"\+wa": ("", '<index index="Aramaic" level1="{}" />'),
    r"\+wg": ("", '<index index="Greek" level1="{}" />'),
    r"\+wh": ("", '<index index="Hebrew" level1="{}" />'),
    # stray xt tags are handled here
    r"\xt": ("<reference>", "</reference>"),
    r"\+xt": ('<seg type="x-nested"><reference>', "</reference></seg>"),
    # This should be converted to an 'a' tag. More work needs
    # to be done before that can happen though.
    r"\jmp": ('<seg type="x-usfm-jmp">', "</seg>"),
}

# special strongs feature tag...
STRONGSTAG = ("<w {}{}>", "</w>")

# footnote and cross reference tags
NOTETAGS = {
    r"\f": ('<note placement="foot">\uFDD2', "\uFDD3</note>"),
    r"\fe": ('<note placement="end">\uFDD2', "\uFDD3</note>"),
    r"\x": ('<note type="crossReference">', "</note>"),
    r"\ef": (
        '<note placement="foot" subType="x-extended">\uFDD2',
        "\uFDD3</note>",
    ),
    r"\ex": ('<note type="crossReference" subType="x-extended">', "</note>"),
}

# tags internal to footnotes and cross references
# * If any of these ever start with anything other than \f or \x *
# * then the NOTEFIXRE regex will need to be modified.           *
NOTETAGS2 = {
    r"\fm": ('<hi type="super">', "</hi>"),
    r"\fdc": ('<seg editions="dc">', "</seg>"),
    r"\fr": ('<reference type="annotateRef">', "</reference>"),
    r"\fk": ("<catchWord>", "</catchWord>"),
    r"\fq": ("<catchWord>", "</catchWord>"),
    r"\fqa": ('<rdg type="alternate">', "</rdg>"),
    # I think this should be label... but that doesn't validate.
    # r'\fl': ('<label>', '</label>'),
    r"\fl": ('<seg type="x-usfm-fl">', "</seg>"),
    r"\fv": ('<hi type="super">', "</hi>"),
    r"\ft": ("", ""),
    r"\xot": ('<seg editions="ot">', "</seg>"),
    r"\xnt": ('<seg editions="nt">', "</seg>"),
    r"\xdc": ('<seg editions="dc">', "</seg>"),
    r"\xk": ("<catchWord>", "</catchWord>"),
    r"\xq": ("<catchWord>", "</catchWord>"),
    # there is no mapping in the osis manual for the xo usfm tag
    r"\xo": (
        '<reference type="annotateRef" subType="x-origin">',
        "</reference>",
    ),
    r"\xop": ('<seg type="x-usfm-xop">', "</seg>"),
    r"\xta": ('<seg type="x-usfm-xta">', "</seg>"),
    r"\xt": ("<reference>", "</reference>"),
    # nested versions of internal footnote tags
    r"\+fm": ('<seg type="x-nested"><hi type="super">', "</hi></seg>"),
    r"\+fdc": ('<seg type="x-nested"><seg editions="dc">', "</seg></seg>"),
    r"\+fr": (
        '<seg type="x-nested"><reference type="annotateRef">',
        "</reference></seg>",
    ),
    r"\+fk": ('<seg type="x-nested"><catchWord>', "</catchWord></seg>"),
    r"\+fq": ('<seg type="x-nested"><catchWord>', "</catchWord></seg>"),
    r"\+fqa": ('<seg type="x-nested"><rdg type="alternate">', "</rdg></seg>"),
    r"\+fl": ('<seg type="x-nested"><seg type="x-usfm-fl">', "</seg></seg>"),
    r"\+fv": ('<seg type="x-nested"><hi type="super">', "</hi></seg>"),
    r"\+ft": ("", ""),
    r"\+xot": ('<seg type="x-nested"><seg editions="ot">', "</seg></seg>"),
    r"\+xnt": ('<seg type="x-nested"><seg editions="nt">', "</seg></seg>"),
    r"\+xdc": ('<seg type="x-nested"><seg editions="dc">', "</seg></seg>"),
    r"\+xk": ('<seg type="x-nested"><catchWord>', "</catchWord></seg>"),
    r"\+xq": ('<seg type="x-nested"><catchWord>', "</catchWord></seg>"),
    r"\+xo": (
        '<seg type="x-nested"><reference type="annotateRef" subType="x-origin">',
        "</reference></seg>",
    ),
    r"\+xop": ('<seg type="x-nested"><seg type="x-usfm-xop">', "</seg></seg>"),
    r"\+xta": ('<seg type="x-nested"><seg type="x-usfm-xta">', "</seg></seg>"),
    r"\+xt": ('<seg type="x-nested"><reference>', "</reference></seg>"),
}

# -------------------------------------------------------------------------- #

# defined attributes for tags
DEFINEDATTRIBUTES = {
    r"\w": ["lemma", "strong", "srcloc"],
    r"\xt": ["link-ref"],
    r"\fig": ["alt", "src", "size", "loc", "copy", "ref"],
    r"\jmp": ["link-href", "link-title", "link-name"],
    r"\qt-s": ["id", "who"],
    r"\qt-e": ["id"],
    r"\periph": ["id"],
}

# defaultattributes for tags
# x-default will be used as the default for undefined default attributes
DEFAULTATTRIBUTES = {r"\w": "lemma", r"\xt": "link-ref"}

# -------------------------------------------------------------------------- #
# REGULAR EXPRESSIONS

# squeeze all regular spaces, carriage returns, and newlines
# into a single space.
SQUEEZE = re.compile(r"[ \t\n\r]+", re.U + re.M + re.DOTALL)

# matches special text and character styles
# Automatically build SPECIALTEXTRE regex string from SPECIALTEXT dict.
SPECIALTEXTRE_S = r"""
        # put special text tags into a named group called 'tag'
        (?P<tag>

            # tags always start with a backslash and may have a + symbol which
            # indicates that it's a nested character style.
            \\\+?

            # match the tags we want to match.
            (?:{})
        )

        # there is always at least one space separating the tag and the content
        \s+

        # put the tag content into a named group called 'osis'
        (?P<osis>.*?)

        # tag end marker
        (?P=tag)\*
    """.format(
    "|".join(
        [_.replace("\\", "") for _ in SPECIALTEXT if not _.startswith(r"\+")]
    )
)
SPECIALTEXTRE = re.compile(SPECIALTEXTRE_S, re.U + re.VERBOSE)
del SPECIALTEXTRE_S

# match z tags that have both a start and end marker
ZTAGS_S = r"""
        # put z tags that have a start and end marker into named group 'tag'
        (?P<tag>

            # tags always start with a backslash
            \\

            # match alphanumeric characters
            z(?:[A-Za-z0-9]+)
        )

        # there is always at least one space separating the tag and the content
        \s+

        # put the tag content into a named group called 'osis'
        (?P<osis>.*?)

        # tag end marker
        (?P=tag)\*
    """
ZTAGSRE = re.compile(ZTAGS_S, re.U + re.VERBOSE)
del ZTAGS_S

# matches special feature tags
# Automatically build SPECIALFEATURESRE regex string from FEATURETAGS dict.
SPECIALFEATURESRE_S = r"""
        # put the special features tags into a named group called 'tag'
        (?P<tag>

            # tags always start with a backslash and may have a + symbol which
            # indicates that it's a nested character style.
            \\\+?

            # this matches all of the known usfm special features except
            # for fig which is handled in a different manner.
            (?:{})
        )

        # there is always at least one space separating the tag and the content
        \s+

        # put the tag content into a named group called 'osis'
        (?P<osis>.*?)

        # tag end marker
        (?P=tag)\*
    """.format(
    "|".join(
        [_.replace("\\", "") for _ in FEATURETAGS if not _.startswith(r"\+")]
    )
)
SPECIALFEATURESRE = re.compile(SPECIALFEATURESRE_S, re.U + re.VERBOSE)
del SPECIALFEATURESRE_S

# regex used in footnote/crossref functions
# Automatically build NOTERE regex string from NOTETAGS dict.
NOTERE_S = r"""
        # put the footnote and cross reference markers into a named group
        # called 'tag'
        (?P<tag>

            # tags always start with a backslash
            \\

            # this matches the usfm footnote and cross reference markers.
            (?:{})
        )

        # there is always at least one space following the tag.
        \s+

        # footnote caller (currently ignored by this script)
        \S

        # there is always at least one space following the caller
        \s+

        # put the tag content into a named group called 'osis'
        (?P<osis>.*?)

        # footnote / cross reference end tag
        (?P=tag)\*
    """.format(
    "|".join(
        [_.replace("\\", "") for _ in NOTETAGS if not _.startswith(r"\+")]
    )
)
NOTERE = re.compile(NOTERE_S, re.U + re.VERBOSE)
del NOTERE_S
# ---
# Automatically build NOTEFIXRE regex string from NOTETAGS2 dict.
NOTEFIXRE_S = r"""
        (
            # tags always start with a backslash and may have a + symbol which
            # indicates that it's a nested character style.
            \\\+?

            # this matches all of the footnote/crossref specific usfm tags that
            # appear inside footnotes and cross references.
            (?:{})
        )

        # there is always at least one space following the tag.
        \s+

        # This matches the content of the tag
        (.*?)

        # This marks the end of the tag. It matches against either the
        # start of an additional tag or the end of the note.
        (?=\\\+?[fx]|</note)
    """.format(
    "|".join(
        [_.replace("\\", "") for _ in NOTETAGS2 if not _.startswith(r"\+")]
    )
)
NOTEFIXRE = re.compile(NOTEFIXRE_S, re.U + re.VERBOSE)
del NOTEFIXRE_S

# match \cp and \vp tags
CPRE = re.compile(
    r"""
        \\(?:cp)
        \s+
        (?P<num>\S+)\b
        \s*
    """,
    re.U + re.VERBOSE,
)
VPRE = re.compile(
    r"""
        \\(?:vp)
        \s+
        (?P<num>\S+)
        \s*
        \\vp\*
        \s*
    """,
    re.U + re.VERBOSE,
)

# regex for matching against \ca or \va usfm tags.
CVARE = re.compile(
    r"""
        # put the tag we match into a named group called tag
        (?P<tag>

            # tags always start with a backslash
            \\

            # match against either ca or va
            (?:ca|va)
        )

        # there is always at least one space following the tag
        \s+

        # put the number into a named group called num
        (?P<num>\S+)

        # make sure the end tag matched the start tag...
        (?P=tag)\*

        # there may or may not be space following this tag.
        \s*
    """,
    re.U + re.VERBOSE,
)

# regex for finding usfm tags
USFMRE = re.compile(
    r"""
    # the first character of a usfm tag is always a backslash
    \\

    # a plus symbol marks the start of a nested character style.
    # this may or may not be present.
    \+?

    # tag names are ascii letters
    [A-Za-z]+

    # tags may or may not be numbered
    [0-9]?

    # a word boundary to mark the end of our tags.
    \b

    # character style closing tags ends with an asterisk.
    \*?

""",
    re.U + re.VERBOSE,
)


ATTRIBRE = re.compile(r' +(\S+=[\'"])', re.U + re.DOTALL)


# -------------------------------------------------------------------------- #
# VARIABLES USED BY REFLOW ROUTINE

# set of paragraph style tags built MOSTLY from other lists above...
# this is used by reflow to reformat the input for processing
# * chapter paragraph tags are omitted because we handle them differently
PARFLOW = set(IDTAGS.keys())
PARFLOW.update(TITLETAGS.keys())
PARFLOW.update(PARTAGS.keys())
PARFLOW.update([r"\ide", r"\rem", r"\tr", r"\pb", r"\periph"])

# poetry/prose tags... used by reflow subroutine below.
# this is used by reflow to test if we have paragraph markup.
PARCHECK = set(PARTAGS.keys())
for _ in [r"\iex", r"\ie", r"\qa"]:
    try:
        PARCHECK.remove(_)
    except KeyError:
        pass

# title tags... used by reflow subroutine below.
# use TITLETAGS keys to eliminate unnecessary duplication
TITLEFLOW = set(TITLETAGS.keys())

# -------------------------------------------------------------------------- #
# VARIABLES USED BY POSTPROCESS ROUTINE

OSISITEM = set()
OSISL = set()

for _ in PARTAGS:
    if PARTAGS[_][0].startswith("<item "):
        OSISITEM.add(PARTAGS[_][0])
    elif PARTAGS[_][0].startswith("<l "):
        OSISL.add(PARTAGS[_][0])
OSISL.add("<l>")
OSISITEM.add("<item>")

# -------------------------------------------------------------------------- #

# osis 2.1.1 schema...
# compressed with bzip2 and base64 encoded.
SCHEMA = b"""
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
OFCQJyEEPw==
"""

# -------------------------------------------------------------------------- #

# logging.basicConfig(format="%(levelname)s: %(message)s")
logging.basicConfig(format="%(message)s")
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARNING)

# -------------------------------------------------------------------------- #


def convertcl(text):
    """
    CL tag format conversion.

    Convert cl tags that appear only before chapter one to
    the form that appears after each chapter marker.

    """
    lines = text.split("\n")

    # count number of cl tags in text
    clcount = len([_ for _ in lines if _.startswith(r"\cl ")])

    # test for presence of only 1 cl marker.
    if clcount == 1:
        chaplines = [
            _ for _ in range(len(lines)) if lines[_].startswith(r"\c ")
        ]

        # get cl marker line if it precedes chapter 1 and add this after
        # each chapter marker in the book.
        if lines[chaplines[0] - 1].startswith(r"\cl "):
            clmarker = lines[chaplines[0] - 1]
            lines[chaplines[0] - 1] = ""
            for i in reversed(chaplines):
                cnumber = lines[i].split(" ")[1]
                lines.insert(i + 1, " ".join([clmarker, cnumber]))

    # return our lines with converted cl tags.
    return "\n".join(lines)


def reflow(text):
    """
    Reflow text for Processing.

    Place all paragraph style tags on their own line.
    This makes it significantly easier to handle paragraph markup.

    """
    # ####################################################################### #
    # The titlepar function depends on how this routine was written in order  #
    # to function properly. Don't make changes here unless you know what      #
    # you're doing and understand the ramifications in relation to how the    #
    # titlepar function operates!                                             #
    # ####################################################################### #

    def manglecheck(text):
        """Check to see if we have paragraph markup."""
        retval = False
        for _ in PARCHECK:
            if re.search(
                r"\\{}\b".format(_.lstrip(r"\\")),
                text,
                re.U + re.M + re.DOTALL,
            ):
                retval = True
                break
        return retval

    def endmark(text):
        """Mark end of cl, sp, and qa tags."""
        textlines = text.split("\n")
        for _ in enumerate(textlines):
            if textlines[_[0]][0:4] in [r"\cl ", r"\sp ", r"\qa "]:
                textlines[_[0]] = "{}\uFDD4".format(textlines[_[0]])
            elif textlines[_[0]][0:4] == r"\cp ":
                textlines[_[0]] = "{}\uFDD5".format(textlines[_[0]])
        return "\n".join(textlines)

    def reflowpar(text):
        """Put (almost) all paragraph tags on separate lines."""
        for _ in PARFLOW:
            if _ in text:
                text = text.replace(r"{} ".format(_), "\n{} ".format(_))
        return text

    def fixlines(text):
        """Fix various potential issues with lines of text."""
        textlines = text.split("\n")

        # always make sure chapter markers are on a separate line from titles.
        for _ in enumerate(textlines):
            if (
                textlines[_[0]].partition(" ")[0] in TITLEFLOW
                and r"\c " in textlines[_[0]]
            ):
                textlines[_[0]] = textlines[_[0]].replace("\\c ", "\n\\c ")

        # fix placement of chapter markers with regards to lists...
        # this probably needs more work.
        for _ in enumerate(textlines):
            if (
                textlines[_[0]].partition(" ")[0].startswith(r"\li")
                and r"\c " in textlines[_[0]]
            ):
                if (
                    textlines[_[0] + 1].startswith(r"\s")
                    or textlines[_[0] + 1].startswith(r"\ms")
                    or textlines[_[0] + 1].startswith(r"\p")
                ):
                    textlines[_[0]] = textlines[_[0]].replace("\\c ", "\n\\c ")

        # fix placement of chapter markers with regards to tables...
        # this probably needs more work.
        for _ in enumerate(textlines):
            if (
                textlines[_[0]].partition(" ")[0].startswith(r"\tr")
                and r"\c " in textlines[_[0]]
            ):
                textlines[_[0]] = textlines[_[0]].replace("\\c ", "\n\\c ")

        for _ in enumerate(textlines):
            # make sure some lines don't contain chapter or verse markers
            for i in [
                r"\rem ",
                r"\is",
                r"\ms",
                r"\s ",
                r"\s1 ",
                r"\s2 ",
                r"\s3 ",
                r"\s4 ",
                r"\th",
                r"\tc",
            ]:
                if textlines[_[0]].startswith(i):
                    textlines[_[0]] = textlines[_[0]].replace("\\c ", "\n\\c ")
                    textlines[_[0]] = textlines[_[0]].replace("\\v ", "\n\\v ")
            # make sure some lines don't contain chapter markers
            for i in [r"\li", r"\ph", r"\io", "ili"]:
                if textlines[_[0]].startswith(i):
                    textlines[_[0]] = textlines[_[0]].replace("\\c ", "\n\\c ")

        return "\n".join(textlines)

    # test for paragraph markup before mangling the text
    mangletext = manglecheck(text)

    # mark end of cl, sp, and qa tags
    text = endmark(text)

    # process text with paragraph formatting
    text = SQUEEZE.sub(" ", text)

    # put (almost) all paragraph style tags on separate lines.
    text = reflowpar(text)

    for _ in (
        # always put \cl and \cd on newlines
        (r"\cl ", "\n\\cl "),
        (r"\cd ", "\n\\cd "),
        # always add newline after \ie
        (r"\ie ", "\\ie\n"),
        # always put a space before \cp and \ca tags
        (r"\cp", r" \cp"),
        (r"\ca", r" \ca"),
    ):
        if _[0] in text:
            text = text.replace(_[0], _[1])

    # always make sure chapter 1 marker is on a new line.
    text = text.replace(r"\c 1 ", "\n\\c 1")

    # fix various possible issues in text lines.
    text = fixlines(text)

    # process text without paragraph markup (may not work. needs testing.)
    if not mangletext:
        # force some things  onto newlines.
        for _ in (
            (r"\c ", "\n\\c "),
            (r"\v ", "\n\\v "),
            (r"\ide ", "\n\\ide "),
        ):
            text = text.replace(_[0], _[1])

        # make sure all lines start with a usfm tag...
        lines = text.split("\n")
        for _ in range(len(lines) - 1, 0, -1):
            if not lines[_].startswith("\\"):
                lines[_ - 1] = "{} {}".format(lines[_ - 1], lines[1])
                lines.pop(_)
        text = "\n".join(lines)
        # remove some newlines that we don't want...
        for _ in [r"\ca", r"\cp", r"\va", r"\vp"]:
            text = text.replace("\n{}".format(_), " {}".format(_))

    # fix newline issue
    if "\uFDD4" in text:
        text = text.replace("\uFDD4", "\n")

    # add custom end marker for cp tags for easier processing
    if "\uFDD5" in text:
        text = text.replace("\uFDD5", r"\cp*")

    # done
    return text


def getbookid(text):
    """Get book id from file text."""
    bookid = None
    lines = [_ for _ in text.split("\n") if _.startswith("\\id ")]
    if lines:
        bookid = lines[0].split()[1].strip()

    return {
        True: {True: BOOKNAMES[bookid], False: "* {}".format(bookid)}[
            bookid in BOOKNAMES
        ],
        False: None,
    }[bookid is not None]


def getencoding(text):
    """Get encoding from file text."""
    lines = [
        _.decode("utf8") for _ in text.split(b"\n") if _.startswith(b"\\ide")
    ]
    if lines:
        encoding = lines[0].partition(" ")[2].lower().strip()
    else:
        encoding = None
    return encoding


def markintroend(lines):
    """
    Mark end of introductions.

    Loop through lines of text and mark start and end of introductions
    to aid in adding div's to introduction sections.

    """
    i = 0
    j = len(lines)
    intro = False
    while i < j:
        tmp = lines[i].partition(" ")
        if tmp[0:3] == r"\ie":
            intro = False
            lines.insert(i, "\ufde0")
        elif tmp[0][:3] in [
            r"\ib",
            r"\il",
            r"\im",
            r"\io",
            r"\ip",
            r"\iq",
            r"\is",
            r"\ie",
        ]:
            if not intro:
                lines.insert(i, "\ufde0")
                intro = True
        else:
            if intro:
                intro = False
                lines.insert(i, "\ufde1")
                j += 1
        i += 1

    if intro:
        lines.append("\ufde1")

    return lines


def parseattributes(tag, tagtext):
    """Separate attributes from text in usfm."""
    # split attributes from text
    text, _, attributestring = tagtext.partition("|")
    attribs = {}

    # extract attributes
    attribs = {}
    if "=" not in attributestring:
        attribs[DEFAULTATTRIBUTES.get(tag, "x-default")] = attributestring
    else:
        tmp = ATTRIBRE.sub("\uFDE2\\1", attributestring)
        for _ in tmp.split("\uFDE2"):
            attr = _.partition("=")
            attribs[attr[0]] = attr[2].strip('"')

    # attribute validity check
    isinvalid = False
    if tag in DEFINEDATTRIBUTES:
        attribtest = DEFINEDATTRIBUTES[tag]
        for _ in attribs:
            if _ not in attribtest and not _.startswith("x-"):
                isinvalid = True
    else:
        for _ in attribs:
            if not _.startswith("x-"):
                isinvalid = True

    return (text, attributestring, attribs, isinvalid)


# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #


def c2o_preprocess(text):
    """Preprocess text."""
    # preprocessing...
    for _ in (
        # special xml characters
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        # special spacing characters
        ("~", "\u00a0"),
        (r"//", '<lb type="x-optional" />'),
        (r"\pb ", '<milestone type="pb" />'),
        (r"\pb", '<milestone type="pb" />'),
    ):
        if _[0] in text:
            text = text.replace(_[0], _[1])

    return text.strip()


def c2o_identification(text, description):
    """
    Process identification tags.

    id, ide, sts, rem, h, h1, h2, h3, toc1, toc2, toc3, restore.

    """
    line = text.partition(" ")
    if line[0] in IDTAGS.keys():
        text = {
            True: "{}\ufdd0".format(
                IDTAGS[line[0]][1].format(line[2].strip())
            ),
            False: "{}{}{}\ufdd0".format(
                IDTAGS[line[0]][0], line[2].strip(), IDTAGS[line[0]][1]
            ),
        }[IDTAGS[line[0]][0] == ""]
    elif line[0] in IDTAGS2:
        description.append(
            '<description {} subType="x-{}">{}</description>'.format(
                'type="usfm"', line[0][1:], line[2].strip()
            )
        )
        text = ""
        # fix problems with url's in rem lines resulting from processing
        # of special spacing in preprocessing section.
        if '<lb type="x-optional" />' in description[-1]:
            description[-1] = description[-1].replace(
                '<lb type="x-optional" />', "//"
            )
    return text, description


def c2o_titlepar(text, bookid):
    """Process title and paragraph tags."""
    # local copies of global variables.
    partags = PARTAGS
    othertags = OTHERTAGS
    celltags = CELLTAGS
    titletags = TITLETAGS

    def titles_and_sections(line):
        """Process titles and sections."""
        # make sure titles don't end with a \b or an \ib tag
        line[2] = line[2].strip()
        if line[2].endswith(r"\b"):
            line[2] = line[2][:-2]
        elif line[2].endswith(r"\ib"):
            line[2] = line[2][:-3]

        # is there ever a reason for a \b tag to appear in a title?
        # if there is, I will have to add \b processing here.

        if line[0] == r"\periph":
            # handle usfm attributes if present
            osis, attributetext, attributes, isvalid = {
                True: parseattributes(r"periph", line[2]),
                False: (line[2], None, dict(), True),
            }["|" in line[2]]
            del isvalid  # make pylint happy
            if attributetext is not None:
                attributetext = "{}{}{}".format(
                    "<!-- USFM Attributes - ", attributetext, " -->"
                )
            starttag = titletags[line[0]][0]
            endtag = titletags[line[0]][1]

            # process id attribute
            if "id" in attributes:
                idattribute = ' n="{}">'.format(attributes["id"])
                starttag = starttag.replace(">", idattribute)

            # finished processing periph now...
            text = "\ufdd0<!-- {} -->{}{}{}{}\ufdd0".format(
                line[0].replace("\\", ""),
                starttag,
                osis.strip(),
                endtag,
                attributetext,
            )
        else:
            text = "\ufdd0<!-- {} -->{}{}{}\ufdd0".format(
                line[0].replace("\\", ""),
                titletags[line[0]][0],
                line[2].strip(),
                titletags[line[0]][1],
            )
        return text

    def paragraphs(line):
        """Process paragraph tags."""
        pstart, pend = partags[line[0]]
        btag = ""
        if pstart.startswith("<p"):
            pstart = "{}\ufdd0".format(pstart)
            pend = "\ufdd0{}\ufdd0".format(pend)

        text = "{}{}".format(pstart, line[2].strip())
        # handle b  and ib tags in paragraphs and poetry...
        if text.endswith("\\b") or text.endswith("\\ib"):
            text = text.rstrip("\\b")
            text = text.rstrip("\\ib")
            btag = "<!-- b -->"
        elif r"\b " in text or r"\ib" in text:
            text = text.replace("\\b ", "<!-- b -->")
            text = text.replace("\\ib ", "<!-- b -->")

        # finish paragraphs.
        return "{}{}{}\ufdd0".format(text, pend, btag)

    def tables(line):
        """Process tables."""
        # make sure table rows don't end with b tags...
        line[2] = line[2].strip().rstrip("\\b").strip()

        line[2] = line[2].replace(r"\th", "\n\\th")
        line[2] = line[2].replace(r"\tc", "\n\\tc")
        cells = line[2].split("\n")
        for i in enumerate(cells):
            tmp = list(cells[i[0]].partition(" "))
            if tmp[0] in celltags.keys():
                cells[i[0]] = "{}{}{}".format(
                    celltags[tmp[0]][0],
                    tmp[2].strip(),
                    celltags[tmp[0]][1],
                )
        return "<row>{}</row>\ufdd0".format("".join(cells))

    def selah(text):
        """Handle selah."""
        tmp = text.replace("<l", "\n<l").replace("</l>", "</l>\n")
        selahfix = [_ for _ in tmp.split("\n") if _ != ""]
        for _ in enumerate(selahfix):
            if (
                selahfix[_[0]].startswith(r"<l")
                and "<selah>" in selahfix[_[0]]
            ):
                selahfix[_[0]] = selahfix[_[0]].replace(
                    "<selah>", '</l><l type="selah">'
                )
                selahfix[_[0]] = selahfix[_[0]].replace("</selah>", "</l><l>")
                if "<l> </l>" in selahfix[_[0]]:
                    selahfix[_[0]] = selahfix[_[0]].replace("<l> </l>", "")
                if "<l>  </l>" in selahfix[_[0]]:
                    selahfix[_[0]] = selahfix[_[0]].replace("<l>  </l>", "")
        for _ in enumerate(selahfix):
            if "<selah>" in selahfix[_[0]] or "</selah>" in selahfix[_[0]]:
                selahfix[_[0]] = selahfix[_[0]].replace(
                    "<selah>", '<lg><l type="selah">'
                )
                selahfix[_[0]] = selahfix[_[0]].replace(
                    "</selah>", "</l></lg>"
                )
        return " ".join(selahfix)

    # add periph tag to titletags if book being processed
    # is a  peripheral or private use book.
    if bookid in [
        "FRONT",
        "INTRODUCTION",
        "BACK",
        "X-OTHER",
        "XXA",
        "XXB",
        "XXC",
        "XXD",
        "XXE",
        "XXF",
        "XXG",
    ]:
        titletags[r"\periph"] = ('<title type="main">', "</title>")

    # ################################################################### #
    # NOTE: I've not seen any kind of documentation to suggest that usage
    #       of the usfm \d tag outside of psalms is valid.
    #
    #       Additionally every other converter that I've looked at does not
    #       make a special exception for \d tags outside of psalms.
    #       Neither the deprecated perl script nor the currently preferred
    #       python script hosted by crosswire.org do this. Haiola does not
    #       do this. Bibledit does not do this.
    #
    #       Anyway, it takes 2 lines. It was trivial. So, against my better
    #       judgment I've provided an implementation of this change as was
    #       requested.
    #
    #       Uncomment the next 2 lines of code to enable handling of
    #       incorrect use of this tag.
    #
    # if bookid != "Ps":
    #     titletags[r'\d'] = ('<title canonical="true">', '</title>')
    # ################################################################### #

    line = list(text.partition(" "))

    # process titles and sections
    if line[0] in titletags:
        text = titles_and_sections(line)

    # process paragraphs
    elif line[0] in partags:
        text = paragraphs(line)

    # process tables
    elif line[0] == r"\tr":
        text = tables(line)

    # other title, paragraph, intro tags
    for _ in othertags.keys():
        text = text.replace(_, othertags[_])

    # fix selah
    if "<selah>" in text:
        text = selah(text)

    return text


def c2o_fixgroupings(lines):
    """Fix linegroups in poetry, lists, etc."""
    # append a blank line. (needed in some cases)
    lines.append("")

    def btags(lines):
        """Handle b tags."""
        for _ in enumerate(lines):
            if "<!-- b -->" in lines[_[0]]:
                if lines[_[0]][:2] in ["<l", "<p"]:
                    lines[_[0]] = lines[_[0]].replace(
                        "<!-- b -->", '<lb type="x-p" />'
                    )
                else:
                    lines[_[0]] = lines[_[0]].replace("<!-- b -->", "")
        return lines

    def lgtags(lines):
        """Handle lg tag groupings."""
        inlg = False
        for _ in enumerate(lines):
            if lines[_[0]].startswith("<l "):
                if not inlg:
                    lines[_[0]] = "<lg>\ufdd0{}".format(lines[_[0]])
                    inlg = True
            else:
                if inlg:
                    lines[_[0] - 1] = "{}\ufdd0</lg>\ufdd0".format(
                        lines[_[0] - 1]
                    )
                    inlg = False
        return lines

    def listtags(lines):
        """Handle list tag groupings."""
        inlist = False
        for _ in enumerate(lines):
            if lines[_[0]].startswith("<item "):
                if not inlist:
                    lines[_[0]] = "<list>\ufdd0{}".format(lines[_[0]])
                    inlist = True
            else:
                if inlist:
                    lines[_[0] - 1] = "{}\ufdd0</list>\ufdd0".format(
                        lines[_[0] - 1]
                    )
                    inlist = False
        return lines

    def tabletags(lines):
        """Handle table tag groupings."""
        intable = False
        for _ in enumerate(lines):
            if lines[_[0]].startswith("<row"):
                if not intable:
                    lines[_[0]] = "\ufdd0<table>\ufdd0{}".format(lines[_[0]])
                    intable = True
            else:
                if intable:
                    lines[_[0] - 1] = "{}\ufdd0</table>\ufdd0".format(
                        lines[_[0] - 1]
                    )
                    intable = False
        return lines

    def introductions(lines):
        """Encapsulate introductions in divs."""
        for _ in enumerate(lines):
            if lines[_[0]] == "\ufde0":
                lines[_[0]] = '<div type="introduction">\ufdd0'
            elif lines[_[0]] == "\ufde1":
                lines[_[0]] = "</div>\ufdd0"
            elif lines[_[0]].endswith("\ufde1"):
                lines[_[0]] = "{}</div>\ufdd0".format(
                    lines[_[0]].replace("\ufde1", "")
                )
        return lines

    # process b tags...
    lines = btags(lines)

    # add breaks before chapter and verse tags
    for _ in enumerate(lines):
        lines[_[0]] = lines[_[0]].replace(r"\c ", "\ufdd0\\c ")
        lines[_[0]] = lines[_[0]].replace(r"\v ", "\ufdd0\\v ")

    # add missing lg tags
    lines = lgtags(lines)

    # add missing list tags
    lines = listtags(lines)

    # add missing table tags
    lines = tabletags(lines)

    # encapsulate introductions inside div's
    lines = introductions(lines)

    return lines


def c2o_specialtext(text):
    """
    Process special text and character styles.

    add, add*, bk, bk*, dc, dc*, k, k*, lit, nd, nd*, ord, ord*, pn, pn*,
    qt, qt*, sig, sig*, sls, sls*, tl, tl*, wj, wj*

    em, em*, bd, bd*, it, it*, bdit, bdit*, no, no*, sc, sc*


    * lit tags are handled in the titlepar function

    """

    def simplerepl(match):
        """Simple regex replacement helper function."""
        tag = SPECIALTEXT[match.group("tag")]
        return "{}{}{}".format(tag[0], match.group("osis"), tag[1])

    text = SPECIALTEXTRE.sub(simplerepl, text, 0)
    # Make sure all nested tags are processed.
    # In order to avoid getting stuck here we abort
    # after a maximum of 5 attempts. (5 was chosen arbitrarily)
    nestcount = 0
    while "\\" in text:
        nestcount += 1
        text = SPECIALTEXTRE.sub(simplerepl, text, 0)
        if nestcount > 5:
            break

    return text


def c2o_noterefmarkers(text):
    """Process footnote and cross reference markers."""

    def notefix(notetext):
        """Additional footnote and cross reference tag processing."""

        def notefixsub(fnmatch):
            """Simple regex replacement helper function."""
            tag = NOTETAGS2[fnmatch.groups()[0]]
            if "<reference>" in tag:
                txt, _, attrtxt = fnmatch.groups()[1].partition("|")
            else:
                txt = fnmatch.groups()[1]
                attrtxt = None
            if attrtxt is not None:
                txt = "<!-- USFM Attributes: {} -->{}".format(attrtxt, txt)
            return "".join([tag[0], txt, tag[1]])

        notetext = NOTEFIXRE.sub(notefixsub, notetext, 0)
        for _ in [
            r"\fm*",
            r"\fdc*",
            r"\fr*",
            r"\fk*",
            r"\fq*",
            r"\fqa*",
            r"\fl*",
            r"\fv*",
            r"\ft*",
            r"\xo*",
            r"\xk*",
            r"\xq*",
            r"\xt*",
            r"\xot*",
            r"\xnt*",
            r"\xdc*",
            r"\+fm*",
            r"\+fdc*",
            r"\+fr*",
            r"\+fk*",
            r"\+fq*",
            r"\+fqa*",
            r"\+fl*",
            r"\+fv*",
            r"\+ft*",
            r"\+xo*",
            r"\+xk*",
            r"\+xq*",
            r"\+xt*",
            r"\+xot*",
            r"\+xnt*",
            r"\+xdc*",
        ]:
            if _ in notetext:
                notetext = notetext.replace(_, "")
        return notetext

    def simplerepl(match):
        """Simple regex replacement helper function."""
        tag = NOTETAGS[match.group("tag")]
        notetext = match.group("osis").replace("\n", " ")
        if "<transChange" in notetext:
            notetext = notetext.replace(
                '<transChange type="added">',
                '<seg><transChange type="added">',
            )
            notetext = notetext.replace(
                "</transChange>", "</transChange></seg>"
            )
        return "{}{}{}".format(tag[0], notetext, tag[1])

    text = NOTERE.sub(simplerepl, text, 0)

    # process additional footnote tags if present
    for _ in [r"\f", r"\x", r"\+f", r"\+x"]:
        if _ in text:
            text = notefix(text)

    # handle fp tags
    if r"\fp " in text:
        # xmllint says this works and validates.
        text = text.replace("\uFDD2", "<p>")
        text = text.replace("\uFDD3", "</p>")
        text = text.replace(r"\fp ", r"</p><p>")
    else:
        text = text.replace("\uFDD2", "").replace("\uFDD3", "")

    # study bible index categories
    if r"\cat " in text:
        text = text.replace(r"\cat ", r'<index index="category" level1="')
        text = text.replace(r"\cat*", r'" />')

    # return our processed text
    return text


def c2o_specialfeatures(text):
    """Process special features."""

    def simplerepl(match):
        """Simple regex replacement helper function."""
        matchtag = match.group("tag")
        tag = FEATURETAGS[matchtag]
        rawosis = match.group("osis")
        attributetext = None

        osis, attributetext, attributes, isvalid = {
            True: parseattributes(matchtag, rawosis),
            False: (rawosis, None, dict(), True),
        }["|" in rawosis]
        del isvalid  # make pylint happy
        osis2 = osis

        # handle w tag attributes
        tag2 = None
        if matchtag in [r"\w", r"\+w"]:
            if "lemma" in attributes.keys():
                osis2 = attributes["lemma"]
            if "strong" in attributes.keys():
                tag2 = STRONGSTAG
                tmp = " ".join(
                    [
                        "strong:{}".format(_.strip())
                        for _ in attributes["strong"].split(",")
                    ]
                )
                strong1 = 'lemma="{}"'.format(tmp)
                strong2 = ""
            if "x-morph" in attributes.keys():
                if tag2 is not None:
                    strong2 = ' morph="{}"'.format(attributes["x-morph"])

        # TODO: improve processing of tag attributes

        if tag[0] == "" and tag2 is None:
            # limited filtering of index entry contents...
            if '<seg type="x-nested"><transChange type="added">' in osis2:
                osis2 = osis2.replace(
                    '<seg type="x-nested"><transChange type="added">', ""
                )
                osis2 = osis2.replace("</transChange></seg>", "")
            outtext = "{}{}".format(osis, tag[1].format(osis2))
        elif tag2 is not None:
            # process strongs
            outtext = "{}{}{}".format(
                tag2[0].format(strong1, strong2), osis, tag2[1]
            )
        else:
            outtext = "{}{}{}".format(tag[0], osis, tag[1])

        if attributetext is not None:
            # problems can occur when strongs numbers are present...
            # this avoids those problems.
            if matchtag not in [r"\w", r"\+w"]:
                outtext = "{}{}".format(
                    outtext,
                    "<!-- USFM Attributes: {} -->".format(attributetext),
                )

        return outtext

    def figtags(text):
        """Process fig tags."""
        text = text.replace(r"\fig ", "\n\\fig ")
        text = text.replace(r"\fig*", "\\fig*\n")
        tlines = text.split("\n")
        for i in enumerate(tlines):
            if tlines[i[0]].startswith(r"\fig "):
                # old style \fig handling
                # \fig DESC|FILE|SIZE|LOC|COPY|CAP|REF\fig*
                if len(tlines[i[0]][5:-5].split("|")) > 2:
                    fig = tlines[i[0]][5:-5].split("|")
                    figref = ""
                    fig[0] = {
                        False: "<!-- fig DESC - {} -->\n".format(fig[0]),
                        True: fig[0],
                    }[not fig[0]]
                    fig[1] = {
                        False: ' src="{}"'.format(fig[1]),
                        True: fig[1],
                    }[not fig[1]]
                    fig[2] = {
                        False: ' size="{}"'.format(fig[2]),
                        True: fig[2],
                    }[not fig[2]]
                    fig[3] = {
                        False: "<!-- fig LOC - {} -->\n".format(fig[3]),
                        True: fig[3],
                    }[not fig[3]]
                    fig[4] = {
                        False: ' rights="{}"'.format(fig[4]),
                        True: fig[4],
                    }[not fig[4]]
                    fig[5] = {
                        False: "<caption>{}</caption>\n".format(fig[5]),
                        True: fig[5],
                    }[not fig[5]]
                    # this is likely going to be very broken without
                    # further processing of the references.
                    if fig[6]:
                        figref = "<reference {}>{}</reference>\n".format(
                            'type="annotateRef"', fig[6]
                        )
                        fig[6] = ' annotateRef="{}"'.format(fig[6])

                # new style \fig handling
                else:
                    figattr = parseattributes(r"\fig", tlines[i[0]][5:-5])
                    fig = []
                    figparts = {
                        "alt": "<!-- fig ALT - {} -->\n",
                        "src": ' src="{}"',
                        "size": ' size="{}"',
                        "loc": "<!-- fig LOC - {} -->\n",
                        "copy": ' rights="{}"',
                    }
                    for _ in ["alt", "src", "size", "loc", "copy"]:
                        fig.append(
                            {
                                True: figparts[_].format(figattr[2][_]),
                                False: "",
                            }[_ in figattr[2]]
                        )
                        # caption absent in new style fig attributes
                        fig.append("")
                        # this is likely going to be very broken without
                        # further processing of the references.
                        if "ref" in figattr[2]:
                            figref = "{}{}{}\n".format(
                                '<reference type="annotateRef">',
                                figattr[2]["ref"],
                                "</reference>\n",
                            )
                            fig.append(
                                ' annotateRef="{}"'.format(figattr[2]["ref"])
                            )
                        else:
                            figref = ""
                            fig.append("")
                # build our osis figure tag
                tlines[i[0]] = "".join(
                    [
                        fig[0],
                        fig[3],
                        "<figure",
                        fig[1],
                        fig[2],
                        fig[4],
                        fig[6],
                        ">\n",
                        figref,
                        fig[5],
                        "</figure>",
                    ]
                )

        return "".join(tlines)

    def milestonequotes(text):
        """Handle usfm milestone quotations."""
        for _ in [
            r"\qt-",
            r"\qt1-",
            r"\qt2-",
            r"\qt3-",
            r"\qt4-",
            r"\qt5-",
        ]:
            if _ in text:
                text = text.replace(_, "\n{}".format(_))
        text = text.replace(r"\*", "\\*\n")
        tlines = text.split("\n")

        for i in enumerate(tlines):
            # make sure we're processing milestone \qt tags
            if tlines[i[0]].endswith(r"\*"):
                for j in (
                    r"\qt-",
                    r"\qt1-",
                    r"\qt2-",
                    r"\qt3-",
                    r"\qt4-",
                    r"\qt5-",
                ):
                    if tlines[i[0]].startswith(j):
                        # replace with milestone osis tags
                        newline = ""
                        tlines[i[0]] = tlines[i[0]].strip().replace(r"\*", "")
                        tag, _, qttext = tlines[i[0]].partition(" ")
                        # milestone start tag
                        if tag.endswith(r"-s"):
                            (
                                _,
                                attributetext,
                                attributes,
                                isvalid,
                            ) = parseattributes(r"\qt-s", qttext)
                            del isvalid, attributetext  # make pylint happy
                            newline = r"<q"
                            newline = {
                                True: "{}{}".format(
                                    newline,
                                    r' sID="{}"'.format(attributes["id"]),
                                ),
                                False: newline,
                            }["id" in attributes]
                            newline = {
                                True: "{}{}".format(
                                    newline,
                                    r' who="{}"'.format(attributes["who"]),
                                ),
                                False: newline,
                            }["who" in attributes]
                            qlevel = {True: tag[3], False: "1"}[
                                tag[3] in ["2", "3", "4", "5"]
                            ]

                            newline = "{}{}{}".format(
                                newline,
                                ' level="{}"'.format(qlevel),
                                r" />",
                            )
                        # milestone end tag
                        elif tag.endswith(r"-e"):
                            (
                                _,
                                attributetext,
                                attributes,
                                isvalid,
                            ) = parseattributes(r"\qt-e", qttext)
                            newline = r"<q"
                            newline = {
                                True: "{}{}".format(
                                    newline,
                                    r' eID="{}"'.format(attributes["id"]),
                                ),
                                False: newline,
                            }["id" in attributes]
                            qlevel = {True: tag[3], False: "1"}[
                                tag[3] in ["2", "3", "4", "5"]
                            ]

                            # I don't know if I need the level attribute
                            # on the milestone end tag. I put it here
                            # just to be sure though. I will remove it
                            # later if it doesn't belong here.
                            newline = "{}{}{}".format(
                                newline,
                                ' level="{}"'.format(qlevel),
                                r" />",
                            )
                        # replace line with osis milestone tag
                        if newline != "":
                            tlines[i[0]] = newline
        # rejoin lines
        return "".join(tlines)

    text = SPECIALFEATURESRE.sub(simplerepl, text, 0)

    if r"\fig" in text:
        text = figtags(text)

    # Process usfm milestone quotation tags... up to 5 levels.
    for _ in [r"\qt-", r"\qt1-", r"\qt2-", r"\qt3-", r"\qt4-", r"\qt5-"]:
        if _ in text:
            text = milestonequotes(text)

    return text


def c2o_ztags(text):
    """Process z tags that have both a start and end marker."""

    def simplerepl(match):
        """Simple regex replacement helper function."""
        return '<seg type="x-usfm-z{}">{}</seg>'.format(
            match.group("tag").replace(r"\z", ""), match.group("osis")
        )

    text = ZTAGSRE.sub(simplerepl, text, 0)
    # milestone z tags… this may need more work…
    if r"\z" in text:
        words = text.split(" ")
        for i in enumerate(words):
            if i[1].startswith(r"\z"):
                words[i[0]] = '<milestone type="x-usfm-z{}" />'.format(
                    i[1].replace(r"\z", "")
                )
        text = " ".join(words)
    return text


def c2o_chapverse(lines, bookid):
    """Process chapter and verse tags."""

    def verserange(text):
        """Generate list for verse ranges."""
        low, high = text.split("-")
        retval = ""
        try:
            retval = [str(_) for _ in range(int(low), int(high) + 1)]
        except ValueError:
            end1 = ""
            end2 = ""
            if low[-1] in ["a", "b", "A", "B"]:
                end1 = low[-1]
                low = "".join(low[:-1])
            if high[-1] in ["a", "b", "A", "B"]:
                end2 = high[-1]
                high = "".join(high[:-1])
            retval = [str(_) for _ in range(int(low), int(high) + 1)]
            if end1 != "":
                retval[0] = "!".join([retval[0], end1])
            if end2 != "":
                retval[-1] = "!".join([retval[-1], end2])
        return retval

    # chapter and verse numbers
    closerlist = [
        _ for _ in range(len(lines)) if lines[_].startswith(r"<closer")
    ]
    for i in reversed(closerlist):
        lines[i - 1] = " ".join([lines[i - 1], lines[i]])
        del lines[i]

    chap = ""
    verse = ""
    caid = ""
    haschap = False
    hasverse = False
    cvlist = [
        _
        for _ in range(len(lines))
        if lines[_].startswith(r"\c ") or lines[_].startswith(r"\v ")
    ]
    for i in cvlist:
        # ## chapter numbers
        if lines[i].startswith(r"\c "):
            haschap = True
            tmp = list(lines[i].split(" ", 2))
            if len(tmp) < 3:
                tmp.append("")
            cnum = tmp[1]

            # nb fix...
            if "<!--" in cnum and "nb -->" in tmp[2]:
                cnum = cnum.replace("<!--", "").strip()
                tmp[2] = "<!-- {}".format(tmp[2])

            caid = ""

            # generate chapter number
            if chap == "":
                lines[i] = "<chapter {} {} {} />{}".format(
                    'sID="{}.{}"'.format(bookid, cnum),
                    'osisID="{}.{}{}"'.format(bookid, cnum, caid),
                    'n="{}"'.format(cnum),
                    tmp[2],
                )
                chap = cnum
            else:
                if hasverse:
                    lines[i] = "{}\n{}\n<chapter {} {} {} />{}".format(
                        '<verse eID="{}.{}.{}" />'.format(bookid, chap, verse),
                        '<chapter eID="{}.{}" />'.format(bookid, chap),
                        'sID="{}.{}"'.format(bookid, cnum),
                        'osisID="{}.{}{}"'.format(bookid, cnum, caid),
                        'n="{}"'.format(cnum),
                        tmp[2],
                    )
                    hasverse = False
                else:
                    lines[i] = "{}\n<chapter {} {} {} />{}".format(
                        '<chapter eID="{}.{}" />'.format(bookid, chap),
                        'sID="{}.{}"'.format(bookid, cnum),
                        'osisID="{}.{}{}"'.format(bookid, cnum, caid),
                        'n="{}"'.format(cnum),
                        tmp[2],
                    )

                chap = cnum
                verse = ""

        # ## verse numbers
        # BUG?: \va tags won't be handled unless lines start with a \v tag
        elif lines[i].startswith(r"\v "):

            # test for books with only one chapter
            if bookid in ONECHAP and haschap is False:
                chap = "1"

            hasverse = True
            tmp = list(lines[i].split(" ", 2))
            if len(tmp) < 3:
                tmp.append("")
            vnum = tmp[1]

            vaid = ""

            # handle verse ranges
            if "-" in vnum:
                try:
                    vlist = verserange(vnum)
                    for j in enumerate(vlist):
                        vlist[j[0]] = "{}.{}.{}".format(
                            bookid, chap, vlist[j[0]]
                        )
                    osisid = 'osisID="{}{}"'.format(" ".join(vlist), vaid)
                except TypeError:
                    vnum = vnum.strip("-")
                    osisid = 'osisID="{}.{}.{}{}"'.format(
                        bookid, chap, vnum, vaid
                    )
            else:
                osisid = 'osisID="{}.{}.{}{}"'.format(bookid, chap, vnum, vaid)

            # generate verse tag
            if verse == "":
                # handle single chapter books without chapter marker
                if chap == "1" and haschap is False:
                    chapmark = "<chapter {} {} {} />\n".format(
                        'sID="{}.1"'.format(bookid),
                        'osisID="{}.1{}"'.format(bookid, caid),
                        'n="1"',
                    )
                    haschap = True
                else:
                    chapmark = ""

                lines[i] = "{}<verse {} {} {} />{}".format(
                    chapmark,
                    'sID="{}.{}.{}"'.format(bookid, chap, vnum),
                    osisid,
                    'n="{}"'.format(vnum),
                    tmp[2],
                )
                verse = vnum
                hasverse = True
            else:
                lines[i] = "<verse {} />\n<verse {} {} {} />{}".format(
                    'eID="{}.{}.{}"'.format(bookid, chap, verse),
                    'sID="{}.{}.{}"'.format(bookid, chap, vnum),
                    osisid,
                    'n="{}"'.format(vnum),
                    tmp[2],
                )
                verse = vnum
                hasverse = True

        elif lines[i].startswith(r"<closer"):
            lines[i] = "<verse {} />\n{}".format(
                'eID="{}.{}.{}"'.format(bookid, chap, verse), tmp[2]
            )
            verse = vnum
            hasverse = False
            # hascloser = True # apparently we're not using this?

    if hasverse:
        lines.append('<verse eID="{}.{}.{}" />'.format(bookid, chap, verse))
    if haschap:
        lines.append('<chapter eID="{}.{}" />'.format(bookid, chap))

    return lines


def c2o_processwj2(lines):
    """
    Alternate processing of wj tags.

    This attempts to insert q start and end tags in appropriate locations
    in order to avoid crossing container boundaries.

    """
    # get lists of tags where lines need to be broken for processing
    wjstarttags = set()
    wjendtags = set()
    for _ in TITLETAGS:
        if TITLETAGS[_][0] != "" and TITLETAGS[_][1] != "":
            wjstarttags.add(TITLETAGS[_][0].strip())
            wjendtags.add(TITLETAGS[_][1].strip())
    for _ in PARTAGS:
        if PARTAGS[_][0] != "" and PARTAGS[_][1] != "":
            wjstarttags.add(PARTAGS[_][0].strip())
            wjendtags.add(PARTAGS[_][1].strip())

    # prepare for processing by joining lines together
    text = "\ufdd1".join(lines)

    # split words of jesus from the rest of the text.
    text = text.replace("\\wj ", "\n\\wj ")
    text = text.replace("\\wj*", "\\wj*\n ")
    lines = text.split("\n")

    # process words of Jesus.
    for i in enumerate(lines):
        if lines[i[0]].startswith(r"\wj "):
            # Add initial start and end q tags
            lines[i[0]] = lines[i[0]].replace(
                r"\wj ", '<q who="Jesus" marker="">'
            )
            lines[i[0]] = lines[i[0]].replace(r"\wj*", "</q>")

            # add additional closing and opening q tags
            for _ in wjstarttags:
                lines[i[0]] = lines[i[0]].replace(
                    _, '{}<q who="Jesus" marker="">'.format(_)
                )
            for _ in wjendtags:
                lines[i[0]] = lines[i[0]].replace(_, "</q>{}".format(_))

    # rejoin lines, then resplit and return processed lines...
    text = "".join(lines)
    return text.split("\ufdd1")


def c2o_postprocess(lines):
    """Attempt to fix some formatting issues."""
    # resplit lines for post processing,
    # removing leading and trailing whitespace, and b comments
    lines = [
        _.strip()
        for _ in "\n".join(lines).split("\n")
        if _.strip() != "" and _.strip() != "<!-- b -->"
    ]

    for _ in enumerate(lines):
        # fix SIDEBAR
        if "SIDEBAR" in lines[_[0]]:
            lines[_[0]] = lines[_[0]].replace(
                "<SIDEBAR>", '<div type="x-sidebar">'
            )
            lines[_[0]] = lines[_[0]].replace("</SIDEBAR>", "</div>")
        # Convert unhandled vp tags, to milestones...
        while r"\vp " in lines[_[0]]:
            vpnum = VPRE.search(lines[_[0]]).group("num")
            lines[_[0]] = VPRE.sub(
                '<milestone type="x-usfm-vp" n="{}" />'.format(vpnum),
                lines[_[0]],
                1,
            )

    # adjust some tags for postprocessing purposes.
    i = len(lines)
    while i > 0:
        i -= 1
        # remove empty l tags if present.
        if lines[i] == '<l level="1"> </l>':
            del lines[i]
            continue
        # move lb to it's own line
        if lines[i].endswith('<lb type="x-p" />'):
            lines.insert(i + 1, '<lb type="x-p" />')
            lines[i] = lines[i].rpartition('<lb type="x-p" />')[0].strip()
        # move lg to it's own line
        if lines[i].endswith("<lg>"):
            lines.insert(i + 1, "<lg>")
            lines[i] = lines[i].rpartition("<lg>")[0].strip()

    # swap lb and lg end tag when lg end tag follows lb.
    i = len(lines)
    while i > 0:
        i -= 1
        try:
            if lines[i] == '<lb type="x-p" />' and lines[i + 1] == "</lg>":
                lines[i], lines[i + 1] = (lines[i + 1], lines[i])
        except IndexError:
            pass

    # adjust placement of some verse end tags...
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
    ]:
        if lines[i - 1].strip() in OSISL or lines[i - 1].strip() in OSISITEM:
            lines.insert(i - 1, lines.pop(i))
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
    ]:
        if lines[i - 1] == "<row><cell>" and lines[i - 2] == "<table>":
            lines.insert(i - 2, lines.pop(i))

    for i, j in [
        (x, y)
        for x in [
            "<p",
            "<lb ",
            "</p>",
            "<lg",
            "<lb ",
            "</lg>",
            "<list",
            "<lb",
            "</list>",
            "<title",
            "<title",
            "<title",
            "<title",
            "<title",
            "<div",
            "</div>",
        ]
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
        ]
    ]:
        if lines[j - 1].startswith(i):
            lines.insert(j - 1, lines.pop(j))
        elif i == "<title":
            if lines[j - 1].startswith("<!-- ") and i in lines[j - 1]:
                lines.insert(j - 1, lines.pop(j))

    for i, j in [
        (x, y)
        for x in [
            "<lb ",
            "</p>",
            "</lg>",
            "<lb",
            "</list>",
            "<lb",
            "</p>",
            "</div>",
        ]
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
        ]
    ]:
        if lines[j - 1].startswith(i):
            lines.insert(j - 1, lines.pop(j))

    for i, j in [
        (x, y)
        for x in ["</l>", "</item>"]
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
        ]
    ]:
        if lines[j - 1].endswith(i):
            tmp = lines[j - 1].rpartition("<")
            lines[j - 1] = "{}{}{}{}".format(tmp[0], lines[j], tmp[1], tmp[2])
            lines[j] = ""

    lines = [_ for _ in lines if _ != ""]

    # special fix for verse end markers following "acrostic" titles...
    # because I can't figure out why my other fixes aren't working.
    for i, j in [
        (x, y)
        for x in ['<title type="acrostic"', "</lg"]
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
        ]
    ]:
        if lines[j - 1].startswith(i):
            lines.insert(j - 1, lines.pop(j))

    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
    ]:
        if lines[i - 1].endswith("</l>"):
            lines[i - 1] = "{}{}</l>".format(
                lines[i - 1].rpartition("<")[0], lines[i]
            )
            lines[i] = ""

    for i, j in [
        (x, y)
        for x in ["<!-- ", "</p>"]
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<verse eID")
        ]
    ]:
        if lines[j - 1].startswith(i):
            lines.insert(j - 1, lines.pop(j))

    # adjust placement of verse tags in relation
    # to d titles that contain verses.
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<!-- d -->")
    ]:
        if (
            lines[i + 1].startswith("<verse sID")
            and lines[i + 1].endswith("</title>")
            and lines[i + 2].startswith("<verse eID")
        ):
            tmp1 = lines[i + 1].rpartition("<")
            lines[i] = "{}{}{}</title>".format(lines[i], tmp1[0], lines[i + 2])
            lines[i + 1] = ""
            lines[i + 2] = ""
    lines = [_ for _ in lines if _ != ""]

    # -- # -- # -- #

    # adjust placement of some chapter end tags
    for i, j in [
        (x, y)
        for x in range(3)
        for y in [
            _ for _ in range(len(lines)) if lines[_].startswith("<chapter eID")
        ]
    ]:
        try:
            if "<title" in lines[j - 1]:
                lines.insert(j - 1, lines.pop(j))
            elif "chapterLabel" in lines[j - 1]:
                lines.insert(j - 1, lines.pop(j))
            elif lines[j - 1] == "</p>":
                lines.insert(j - 1, lines.pop(j))
        except IndexError:
            pass

    # adjust placement of some chapter start tags
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<chapter sID")
    ]:
        try:
            if lines[i + 1] == "</p>" and lines[i + 2].startswith("<p"):
                lines.insert(i + 2, lines.pop(i))
            elif (
                lines[i + 1] == "</p>"
                and "chapterLabel" in lines[i + 2]
                and lines[i + 3].startswith("<p")
            ):
                lines.insert(i + 3, lines.pop(i))
        except IndexError:
            pass
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<chapter sID")
    ]:
        try:
            if (
                lines[i + 1] == "</p>"
                and lines[i + 2] == "</div>"
                and lines[i + 3].startswith("<div")
            ):
                lines.insert(i + 3, lines.pop(i))
        except IndexError:
            pass

    # some chapter start tags have had div's or p's appended to the end...
    # fix that.
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<chapter sID")
    ]:
        try:
            if re.match("<chapter sID[^>]+> ?</div>", lines[i]) and lines[
                i + 1
            ].startswith("<div"):
                lines.insert(i + 2, lines[i].replace("</div>", ""))
                lines[i] = "</div>"
            elif re.match("<chapter sID[^>]+> ?<div", lines[i]):
                tmp = lines[i].replace("<div", "\n<div").split("\n", 1)
                lines[i] = tmp[0]
                lines.insert(i + 1, tmp[1])
            elif re.match("<chapter sID[^>]+> ?<p>", lines[i]):
                lines.insert(i + 1, lines[i].replace("<p>", ""))
                lines[i] = "<p>"
        except IndexError:
            pass
    lines = [_ for _ in lines if _ != ""]

    # -- # -- # -- #

    # selah processing sometimes does weird things with l and lg tags
    # that needs to be fixed.
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<chapter sID")
    ]:
        if (
            lines[i].endswith("</l>")
            and lines[i + 1] == "</lg>"
            and lines[i - 1].startswith("<chapter eID")
            and lines[i - 2].startswith("<verse eID")
            and lines[i - 3].endswith("</l><l>")
        ):
            lines[i - 3] = lines[i - 3][:-3]
            lines[i - 2] = "{}{}".format(lines[i - 2], "</lg>")
            lines[i] = lines[i][:-4]
            lines[i + 1] = ""

    # additional postprocessing for l and lg tags
    for i in [
        _ for _ in range(len(lines)) if lines[_].startswith("<chapter sID")
    ]:
        if (
            lines[i].endswith("</l>")
            and lines[i - 1].startswith("<chapter eID")
            and lines[i + 1] == "</lg>"
        ):
            lines[i - 2] = "{}</l></lg>".format(lines[i - 2])
            lines[i] = lines[i][:-4]
            lines[i + 1] = ""

    # done postprocessing of lines
    return lines


def convert_to_osis(text, bookid="TEST"):
    """Convert usfm file to osis."""
    # ---------------------------------------------------------------------- #

    description = []

    # ---------------------------------------------------------------------- #

    # split text into lines for processing
    lines = text.split("\n")

    # mark introduction endings...
    for _ in [r"\ib", r"\ie", r"\il", r"\im", r"\io", r"\ip", r"\iq", r"\is"]:
        if _ in text:
            lines = markintroend(lines)
            break

    for i in enumerate(lines):

        # preprocessing and special spacing... if necessary
        for _ in ["&", "<", ">", "~", r"//", r"\pb"]:
            if _ in lines[i[0]]:
                lines[i[0]] = c2o_preprocess(lines[i[0]])
                break

        # identification
        lines[i[0]], description = c2o_identification(lines[i[0]], description)

        # character style formatting
        lines[i[0]] = c2o_noterefmarkers(lines[i[0]])
        lines[i[0]] = c2o_specialtext(lines[i[0]])

        # special features if present, and stray \xt tags that were missed.
        for _ in [r"\ndx", r"\pro", r"\w", r"\+w", r"\fig", r"\xt", r"\+xt"]:
            if _ in lines[i[0]]:
                lines[i[0]] = c2o_specialfeatures(lines[i[0]])
                break
        for _ in [r"\qt-", r"\qt1-", r"\qt2-", r"\qt3-", r"\qt4-", r"\qt5-"]:
            if _ in lines[i[0]]:
                lines[i[0]] = c2o_specialfeatures(lines[i[0]])
                break

        # z tags if present
        if r"\z" in lines[i[0]]:
            lines[i[0]] = c2o_ztags(lines[i[0]])

        # paragraph style formatting.
        lines[i[0]] = c2o_titlepar(lines[i[0]], bookid)

    # process words of Jesus
    if r"\wj" in text:
        lines = c2o_processwj2(lines)

    # postprocessing of poetry, lists, tables, and sections
    # to add missing tags and div's.
    lines = c2o_fixgroupings(lines)

    # process chapter/verse markers
    lines = [_.strip() for _ in " ".join(lines).split("\ufdd0")]
    lines = c2o_chapverse(lines, bookid)

    # postprocessing to fix some issues that may be present
    lines = c2o_postprocess(lines)

    descriptiontext = "\n".join(description)

    # rejoin lines after processing
    return ("\n".join([_ for _ in lines if _ != ""]), descriptiontext)


# -------------------------------------------------------------------------- #


def doconvert(args):
    """Convert our text and return our results."""
    text = args

    # convert cl lines to form that follows each chapter marker instead of
    # form that precedes first chapter.
    if r"\cl " in text:
        text = convertcl(text)

    # decode and reflow our text
    newtext = reflow(text)

    # get book id. use TEST if none present.
    bookid = getbookid(newtext)
    if bookid is not None:
        if bookid.startswith("* "):
            LOG.error("Book id naming issue - %s", bookid.replace("* ", ""))
    else:
        bookid = "TEST"

    # convert file to osis
    LOG.info("... Processing %s ...", bookid)
    newtext, descriptiontext = convert_to_osis(newtext, bookid)
    return (bookid, descriptiontext, newtext)


def processfiles(args):
    """Process usfm files specified on command line."""
    books = {}
    descriptions = {}
    booklist = []

    files = []

    # get username from operating system
    username = {True: os.getenv("LOGNAME"), False: os.getenv("USERNAME")}[
        os.getenv("USERNAME") is None
    ]

    # read all files
    LOG.info("Reading files... ")
    for fname in args.file:
        # read our text files
        with open(fname, "rb") as ifile:
            text = ifile.read()

        # strip whitespace from beginning and end of file
        text = text.strip()

        # get encoding. Abort processing if we don't know the encoding.
        # default to utf-8-sig encoding if no encoding is specified.
        try:
            if args.e is not None:
                bookencoding = codecs.lookup(args.e).name
            else:
                bookencoding = getencoding(text)
                if bookencoding is not None:
                    if bookencoding == "65001 - Unicode (UTF-8)":
                        bookencoding = "utf-8-sig"
                    else:
                        bookencoding = codecs.lookup(bookencoding).name
                else:
                    bookencoding = "utf-8-sig"
            # use utf-8-sig in place of utf-8 encoding to eliminate errors that
            # may occur if a Byte Order Mark is present in the input file.
            if bookencoding == "utf-8":
                bookencoding = "utf-8-sig"
        except LookupError:
            LOG.error("ERROR: Unknown encoding... aborting conversion.")
            LOG.error(r"    \ide line for %s says --> %s", fname, bookencoding)
            sys.exit()
        # convert file to unicode and add contents to list for processing...
        files.append(text.decode(bookencoding))

    # set number of processes to use while processing file contents
    numprocesses = 1
    if not args.d and HAVEMULTIPROCESSING:
        try:
            numprocesses = multiprocessing.cpu_count()
        except NotImplementedError:
            numprocesses = 1

    # process file contents
    filelist = files
    results = []
    LOG.info("Processing files...")
    if numprocesses == 1:
        results = [doconvert(_) for _ in filelist]
    else:
        try:
            with multiprocessing.Pool(numprocesses) as pool:
                results = pool.imap(doconvert, filelist)
                pool.close()
                pool.join()
        except AttributeError:
            # pylint: disable=no-member
            with closing(multiprocessing.Pool(numprocesses)) as pool:
                results = pool.imap(doconvert, filelist)
                pool.close()
                pool.join()

    # store results
    for bookid, descriptiontext, newtext in results:
        # store our converted text for output
        if bookid != "TEST":
            if bookid in NONCANONICAL:
                books[bookid] = '<div type="{}">\n{}\n</div>\n\n'.format(
                    NONCANONICAL[bookid], newtext
                )
            else:
                books[
                    bookid
                ] = '<div type="book" osisID="{}" {}>\n{}\n</div>\n\n'.format(
                    bookid, 'canonical="true"', newtext
                )
            descriptions[bookid] = descriptiontext
            booklist.append(bookid)
        else:
            if bookid in books.keys():
                books[bookid] = "{}\n{}".format(books[bookid], newtext)
                descriptions[bookid] = "{}\n{}".format(
                    books[bookid], descriptiontext
                )
            else:
                books[bookid] = newtext
                descriptions[bookid] = descriptiontext
            if "TEST" not in booklist:
                booklist.append("TEST")

    # ## Get order for books...
    if args.s == "none":
        tmp = "\n".join([books[_] for _ in booklist])
        tmp2 = [descriptions[_] for _ in booklist]
    elif args.s == "canonical":
        tmp = "\n".join(
            [books[_] for _ in CANONICALORDER if _ in books.keys()]
        )
        tmp2 = [descriptions[_] for _ in CANONICALORDER if _ in books.keys()]
    else:
        with open("order-{}.txt".format(args.s), "r") as order:
            bookorder = order.read()
            bookorder = [
                _
                for _ in bookorder.split("\n")
                if _ != "" and not _.startswith("#")
            ]
        tmp = "\n".join([books[_] for _ in bookorder if _ in books.keys()])
        tmp2 = [descriptions[_] for _ in bookorder if _ in books.keys()]
    # check for strongs presence in osis
    strongsheader = {True: STRONGSWORK, False: ""}["<w " in tmp]
    # assemble osis doc in desired order
    osisdoc = "{}{}{}\n".format(
        OSISHEADER.format(
            args.workid,
            args.l,
            username,
            datetime.datetime.now().strftime("%Y.%m.%dT%H.%M.%S"),
            args.workid,
            args.workid,
            "\n".join(tmp2),
            args.l,
            args.workid,
            strongsheader,
        ),
        tmp,
        OSISFOOTER,
    )

    # Print note about references not being processed.
    LOG.warning("NOTE: References have not been processed.")

    # apply NFC normalization to text unless explicitly disabled.
    if not args.n:
        osisdoc = codecs.encode(unicodedata.normalize("NFC", osisdoc), "utf-8")
    else:
        osisdoc = codecs.encode(osisdoc, "utf-8")

    # validate and "pretty print" our osis doc if requested.
    if HAVELXML:
        # a test string allows output to still be generated
        # even when when validation fails.
        testosis = SQUEEZE.sub(" ", osisdoc.decode("utf-8"))

        # validation is requested...
        if not args.x:
            LOG.warning("Validating osis xml...")
            osisschema = codecs.decode(
                codecs.decode(codecs.decode(SCHEMA, "base64"), "bz2"), "utf-8"
            )
            try:
                vparser = et.XMLParser(
                    schema=et.XMLSchema(et.XML(osisschema)),
                    remove_blank_text=True,
                )
                _ = et.fromstring(testosis.encode("utf-8"), vparser)
                LOG.warning("Validation passed!")
                osisdoc = et.tostring(
                    _,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="utf-8",
                )
            except et.XMLSyntaxError as err:
                LOG.error("Validation failed: %s", str(err))
        # no validation, just pretty printing...
        else:
            # ... but only if we're not debugging.
            if not args.d:
                vparser = et.XMLParser(remove_blank_text=True)
                _ = et.fromstring(testosis.encode("utf-8"), vparser)
                osisdoc = et.tostring(
                    _,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="utf-8",
                )
    else:
        if not args.x:
            LOG.error("LXML needs to be installed for validation.")

    # find unhandled usfm tags that are leftover after processing
    usfmtagset = set()
    usfmtagset.update(USFMRE.findall(osisdoc.decode("utf-8")))
    if usfmtagset:
        LOG.warning("Unhandled USFM Tags: %s", ", ".join(sorted(usfmtagset)))

    # simple whitespace cleanups before writing to file...
    osisdoc = osisdoc.decode("utf-8")
    for i in (
        (" <note", "<note"),
        (" </p>", "</p>"),
        (" </item>", "</item>"),
        (" </l>", "</l>"),
        ("</w><w", "</w> <w"),
    ):
        osisdoc = osisdoc.replace(i[0], i[1])
    osisdoc = osisdoc.encode("utf-8")

    # write doc to file
    outfile = "{}.osis".format(args.workid)
    if args.o is not None:
        outfile = args.o
    with open(outfile, "wb") as ofile:
        ofile.write(osisdoc)

    if "TEST" in books.keys():
        print(books["TEST"])


# -------------------------------------------------------------------------- #


def main():
    """Process command line and pass options to usfm processing routine."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""
            convert USFM bibles to OSIS.
        """,
        epilog="""
            * Version: {} * {} * This script is public domain. *
        """.format(
            META["VERSION"], META["DATE"]
        ),
    )
    parser.add_argument("workid", help="work id to use for OSIS file")
    parser.add_argument("-d", help="debug mode", action="store_true")
    parser.add_argument(
        "-e",
        help="set encoding to use for USFM files",
        default=None,
        metavar="encoding",
    )
    parser.add_argument(
        "-o", help="specify output file", metavar="output_file"
    )
    parser.add_argument(
        "-l", help="specify langauge code", metavar="LANG", default="und"
    )
    parser.add_argument(
        "-s", help="sort order", choices=BOOKORDERS, default="canonical"
    )
    parser.add_argument("-v", help="verbose output", action="store_true")
    parser.add_argument(
        "-x",
        help="disable OSIS validation and reformatting",
        action="store_true",
    )
    parser.add_argument(
        "-n", help="disable unicode NFC normalization", action="store_true"
    )
    parser.add_argument(
        "file",
        help="file or files to process (wildcards allowed)",
        nargs="+",
        metavar="filename",
    )
    args = parser.parse_args()

    # make sure we skip OSIS validation if we don't have lxml
    if not args.x and not HAVELXML:
        args.x = True
        LOG.warning("Note:  lxml is not installed. Skipping OSIS validation.")

    filenames = []
    for _ in args.file:
        globfiles = glob.glob(_)

        if os.path.isfile(_):
            filenames.append(_)
        elif globfiles:
            filenames.extend(globfiles)
        else:
            filenames.append(_)

    args.file = filenames
    del filenames

    for _ in args.file:
        if not os.path.isfile(_):
            LOG.error("*** input file not present or not a normal file. ***")
            sys.exit()

    if args.v:
        LOG.setLevel(logging.INFO)
    if args.d:
        LOG.setLevel(logging.DEBUG)
    processfiles(args)


# -------------------------------------------------------------------------- #


if __name__ == "__main__":
    main()
