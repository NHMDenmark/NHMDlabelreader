#  Copyright (c) 2022  Natural History Museum of Denmark (NHMD)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import pytest
import sys

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.joinpath('src')))

import spidercardreader

TESTDATAPATH = Path(__file__).parent



def test_roman2int():
    # Check valid roman numerals
    assert spidercardreader.roman2int('I') == 1
    assert spidercardreader.roman2int('II') == 2
    assert spidercardreader.roman2int('III') == 3
    assert spidercardreader.roman2int('IV') == 4
    assert spidercardreader.roman2int('V') == 5
    assert spidercardreader.roman2int('VI') == 6
    assert spidercardreader.roman2int('VII') == 7
    assert spidercardreader.roman2int('VIII') == 8
    assert spidercardreader.roman2int('IX') == 9
    assert spidercardreader.roman2int('X') == 10
    assert spidercardreader.roman2int('XI') == 11
    assert spidercardreader.roman2int('XII') == 12
    assert spidercardreader.roman2int('XIII') == 13
    assert spidercardreader.roman2int('1') == 1

    # Check invalid roman numerals
    assert spidercardreader.roman2int('A') == None
    assert spidercardreader.roman2int('IVI') == None
    assert spidercardreader.roman2int('IXI') == None
    assert spidercardreader.roman2int('IIV') == None
    assert spidercardreader.roman2int('IIX') == None

def test_isdate():
    # Check valid dates
    assert spidercardreader.isdate("1.I.1965")
    assert spidercardreader.isdate("1,I,1965")
    assert spidercardreader.isdate("27.I1.1965")
    assert spidercardreader.isdate("27.111.1965")
    assert spidercardreader.isdate("1.IV.1965")
    assert spidercardreader.isdate("1.V.1965")
    assert spidercardreader.isdate("1.VI.1965")
    assert spidercardreader.isdate("1.VII.1965")
    assert spidercardreader.isdate("1.VII.1965")
    assert spidercardreader.isdate("1.VIII.1965")
    assert spidercardreader.isdate("1.IX.1965")
    assert spidercardreader.isdate("1.X.1965")
    assert spidercardreader.isdate("1.XI.1965")
    assert spidercardreader.isdate("1.XII.1965")

    # Check some invalid dates
    assert not spidercardreader.isdate("101.XII.1965")
    assert not spidercardreader.isdate("1.XIII.1965")
    assert not spidercardreader.isdate("1.IXII.1965")
    assert not spidercardreader.isdate("1.IIX.1965")
    assert not spidercardreader.isdate("1.IIV.1965")
    assert not spidercardreader.isdate("1.XII.165")
    assert not spidercardreader.isdate("..")
    assert not spidercardreader.isdate("1.2.1")
    assert not spidercardreader.isdate("0.0.-1")

def test_parsedate():
    # Check valid dates
    date = spidercardreader.parsedate("1.I.1965")
    assert date == "1-1-1965"

    date = spidercardreader.parsedate("27.I1.1965")
    assert date == "27-2-1965"

    date = spidercardreader.parsedate("27.111.1965")
    assert date == "27-3-1965"

    date = spidercardreader.parsedate("1.IV.1965")
    assert date == "1-4-1965"

    date = spidercardreader.parsedate("1.V.1965")
    assert date == "1-5-1965"

    date = spidercardreader.parsedate("1.VI.1965")
    assert date == "1-6-1965"

    date = spidercardreader.parsedate("1.VII.1965")
    assert date == "1-7-1965"

    date = spidercardreader.parsedate("1.VIII.1965")
    assert date == "1-8-1965"

    date = spidercardreader.parsedate("1.IX.1965")
    assert date == "1-9-1965"

    date = spidercardreader.parsedate("1.X.1965")
    assert date == "1-10-1965"

    date = spidercardreader.parsedate("1.XI.1965")
    assert date == "1-11-1965"

    date = spidercardreader.parsedate("1.XII.1965")
    assert date == "1-12-1965"


    # Check some invalid dates
    date = spidercardreader.parsedate("101.XII.1965")
    assert date == ""

    date = spidercardreader.parsedate("1.XIII.1965")
    assert date == ""

    date = spidercardreader.parsedate("1.IXII.1965")
    assert date == ""

    date = spidercardreader.parsedate("1.XII.165")
    assert date == ""

    date = spidercardreader.parsedate("..")
    assert date == ""

    date = spidercardreader.parsedate("A.4.F")
    assert date == ""

    date = spidercardreader.parsedate("    1.XII.1965")
    assert date == ""
