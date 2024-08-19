# -*- coding: utf-8 -*-
"""
The util module contains utility functions for the labelreader package.

LICENSE

Created on Thu Aug 15 19:10:00 2022

@author: Kim Steenstrup Pedersen, NHMD

Copyright 2022 Natural History Museum of Denmark (NHMD)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from pathlib import Path
import re
import logging
from typing import Optional


def checkfilepath(filepath: Path) -> Path:
    """Check if filepath exists and if so create a new path with '.x' added before file suffix,
    where x is an integer

    :param filepath: A pathlib.Path object pointing to the file path to be checked
    :type filepath: pathlib.Path
    :return: A pathlib.Path object pointing to the file path, possibly with an extra suffix
    :rtype: pathlib.Path
    """
    extension = 2
    while filepath.exists():
        if extension == 2:
            filepath = filepath.parent.joinpath(filepath.stem + "." + str(extension) + filepath.suffix)
        else:
            filepath = filepath.parent.joinpath(Path(filepath.stem).stem + "." + str(extension) + filepath.suffix)
        extension += 1  # Update in case we need it next round

    return filepath


def roman2int(roman: str) -> Optional[int]:
    """Convert a roman numeral string into integer.
       Also interprets 1 to I.

       :param roman: String with a roman numeral
       :type roman: str
       :return: An integer representation of the roman numeral. If an error occurs during parsing it return None
       :rtype: int or None
    """

    # Check for 4 - 12
    res = re.search(r"[VX]", roman)
    if res:

        # check that I only occurs on one side of either V or X
        ressplit = re.split(r"[VX]", roman)
        if len(ressplit) == 2:
            if not (ressplit[0] == '' or ressplit[1] == ''):
                return None
        else:
            return None

        res2 = re.search(r"[I1]+", roman)
        if res2 and res2.start() < res.start():
            if (res2.end() - res2.start()) != 1:
                logging.warning(
                    "roman2int expects a date string as input: Unknown roman numeral = " + str(roman))
                return None

            if res.string[res.start()] == 'V':
                number = 4
            elif res.string[res.start()] == 'X':
                number = 9
            else:
                logging.warning(
                    "roman2int expects a date string as input: Unknown roman numeral = " + str(roman))
                return None
        elif res2 and res2.start() > res.start():
            if res.string[res.start()] == 'V':
                number = 5 + res2.end() - res2.start()
            elif res.string[res.start()] == 'X':
                number = 10 + res2.end() - res2.start()
            else:
                logging.warning(
                    "roman2int expects a date string as input: Unknown roman numeral = " + str(roman))
                return None
        else:
            if res.string[res.start()] == 'V':
                number = 5
            elif res.string[res.start()] == 'X':
                number = 10
            else:
                logging.warning(
                    "roman2int expects a date string as input: Unknown roman numeral = " + str(roman))
                return None
    else:
        res2 = re.match(r"^[I1]+", roman)
        if res2:
            number = res2.end() - res2.start()
        else:
            logging.warning("roman2int expects a date string as input: Unknown roman numeral = " + str(roman))
            return None

    return number


def isromandate(text: str, sep: str = r".,") -> bool:
    """Return true if text has the date format using month in roman numerals (as used by Bøggild et al).
       That is, assume format is one or two digits for Day, Roman numeral for Month and 4 digits for Year.
       Allows for common OCR mistake, meaning that if month contains '1' it will be interpreted as 'I'.

       :param text: String to analyse
       :type text: str
       :param sep: String with characters that is used as separator between day, month and year
       :type sep: str
       :return: True if text has the date format using month in roman numerals, False otherwise
       :rtype: bool
    """
    # Assume format is one or two digits for Day, Roman numeral for Month and 4 digits for Year
    # Include a common OCR mistake of reading I as 1 as acceptable.
    if re.match(r"^\d{1,2}[" + sep + r"][IVX1]{1,4}[" + sep +r"]\d{4}", text):
        # Split into Day, Month, Year parts
        parts = re.split(r"[" + sep + r"]", text)
        if len(parts) >= 3:
            # Parse day
            try:
                day = int(parts[0])
            except ValueError:
                return False # Parsing integer day failed

            # Parse month
            month = roman2int(parts[1])
            if month == None:
                return False

            # Parse year
            try:
                year = int(parts[2])
            except ValueError:
                return False # Parsing integer year failed

            # Check day
            retval = (day >= 1 and day <= 31)

            # Check month
            retval = retval and (month >= 1 and month <= 12)

            # Check year
            retval = retval and (year >= 0)

            return retval
        else:
            return False
    else:
        return False



def parseromandate(text: str, sep: str = r".,") -> str:
    """Parse a date in the format accepted by isromandate() and return a numerical date in DD-MM-YYYY format.

       :param text: String to parse
       :type text: str
       :return: A date string in DD-MM-YYYY format or empty string if error occurs
       :rtype: str
    """
    # Remove prefix and suffix characters
    res = re.search(r"^\d{1,2}[" + sep + r"]{1}[IVX1]{1,4}[" + sep + r"]{1}\d{4}", text)
    if not res:
        logging.warning("parseromandate expects a date string as input!")
        return ""
    else:
        cleantext = res.string[res.start():res.end()]

    if not isromandate(text, sep):
        logging.warning("parseromandate expects a date string as input!")
        return ""

    # Split into Day, Month, Year parts
    parts = re.split(r"[" + sep + r"]{1}", cleantext)
    if len(parts) == 3:
        day = parts[0]
        month = roman2int(parts[1])
        if month == None:
            logging.warning("parseromandate expects a date string as input: Month is unknown = " + parts[1])
            return ""
        year = parts[2]
    else:
        logging.warning("parseromandate expects a date string as input: Missing either day, month or year.")
        return ""

    # Return formatted date
    return "%02d" % int(day) + "-" + "%02d" % month + "-" + year


def isdettext(text: str) -> bool:
    """Return true if text is 'Det' or 'Det.' or 'Det.:' or 'Det:'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^(D|d)et[.]?[:]?', text):
        return True
    else:
        return False

def islegtext(text: str) -> bool:
    """Return true if text is 'Leg' or 'Leg.' or 'Leg.:' or 'Leg:'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^(L|l)eg(it|[.])?[:]?', text):
        return True
    else:
        return False


def islegdettext(text: str) -> bool:
    """Return true if text is 'Leg. et det' and variants.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^(L|l)eg[.]? (et|&) det[.]?[:]?', text):
        return True
    else:
        return False

# TODO: Make a test for coll. text
def iscolltext(text: str) -> bool:
    """Return true if text is 'Coll' or 'Coll.' or 'Coll.:' or 'Coll:'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^(C|c)oll[.]?[:]?', text):
        return True
    else:
        return False