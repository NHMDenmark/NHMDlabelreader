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

from labelreader.util import util

TESTDATAPATH = Path(__file__).parent


# TODO: Missing tests for checkfilepath

def test_roman2int():
    # Check valid roman numerals
    assert util.roman2int('I') == 1
    assert util.roman2int('II') == 2
    assert util.roman2int('III') == 3
    assert util.roman2int('IV') == 4
    assert util.roman2int('V') == 5
    assert util.roman2int('VI') == 6
    assert util.roman2int('VII') == 7
    assert util.roman2int('VIII') == 8
    assert util.roman2int('IX') == 9
    assert util.roman2int('X') == 10
    assert util.roman2int('XI') == 11
    assert util.roman2int('XII') == 12
    assert util.roman2int('XIII') == 13
    assert util.roman2int('1') == 1

    # Check invalid roman numerals
    assert util.roman2int('A') == None
    assert util.roman2int('IVI') == None
    assert util.roman2int('IXI') == None
    assert util.roman2int('IIV') == None
    assert util.roman2int('IIX') == None

def test_isromandate():
    # Check valid dates
    assert util.isromandate("1.I.1965")
    assert util.isromandate("1,I,1965")
    assert util.isromandate("27.I1.1965")
    assert util.isromandate("27.111.1965")
    assert util.isromandate("1.IV.1965")
    assert util.isromandate("1.V.1965")
    assert util.isromandate("1.VI.1965")
    assert util.isromandate("1.VII.1965")
    assert util.isromandate("1.VII.1965")
    assert util.isromandate("1.VIII.1965")
    assert util.isromandate("1.IX.1965")
    assert util.isromandate("1.X.1965")
    assert util.isromandate("1.XI.1965")
    assert util.isromandate("1.XII.1965")

    # Check some invalid dates
    assert not util.isromandate("101.XII.1965")
    assert not util.isromandate("1.XIII.1965")
    assert not util.isromandate("1.IXII.1965")
    assert not util.isromandate("1.IIX.1965")
    assert not util.isromandate("1.IIV.1965")
    assert not util.isromandate("1.XII.165")
    assert not util.isromandate("..")
    assert not util.isromandate("1.2.1")
    assert not util.isromandate("0.0.-1")

def test_parseromandate():
    # Check valid dates
    date = util.parseromandate("1.I.1965")
    assert date == "1-1-1965"

    date = util.parseromandate("27.I1.1965")
    assert date == "27-2-1965"

    date = util.parseromandate("27.111.1965")
    assert date == "27-3-1965"

    date = util.parseromandate("1.IV.1965")
    assert date == "1-4-1965"

    date = util.parseromandate("1.V.1965")
    assert date == "1-5-1965"

    date = util.parseromandate("1.VI.1965")
    assert date == "1-6-1965"

    date = util.parseromandate("1.VII.1965")
    assert date == "1-7-1965"

    date = util.parseromandate("1.VIII.1965")
    assert date == "1-8-1965"

    date = util.parseromandate("1.IX.1965")
    assert date == "1-9-1965"

    date = util.parseromandate("1.X.1965")
    assert date == "1-10-1965"

    date = util.parseromandate("1.XI.1965")
    assert date == "1-11-1965"

    date = util.parseromandate("1.XII.1965")
    assert date == "1-12-1965"


    # Check some invalid dates
    date = util.parseromandate("101.XII.1965")
    assert date == ""

    date = util.parseromandate("1.XIII.1965")
    assert date == ""

    date = util.parseromandate("1.IXII.1965")
    assert date == ""

    date = util.parseromandate("1.XII.165")
    assert date == ""

    date = util.parseromandate("..")
    assert date == ""

    date = util.parseromandate("A.4.F")
    assert date == ""

    date = util.parseromandate("    1.XII.1965")
    assert date == ""
