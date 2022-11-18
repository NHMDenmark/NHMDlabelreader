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


def test_parsedate():
    # Check valid dates
    date = spidercardreader.parsedate("1.I.1965")
    assert date == "1/1/1965"

    date = spidercardreader.parsedate("1.I.1965")
    assert date == "1/1/1965"

    date = spidercardreader.parsedate("27.I1.1965")
    assert date == "27/2/1965"

    date = spidercardreader.parsedate("27.111.1965")
    assert date == "27/3/1965"

    date = spidercardreader.parsedate("1.IV.1965")
    assert date == "1/4/1965"

    date = spidercardreader.parsedate("1.V.1965")
    assert date == "1/5/1965"

    date = spidercardreader.parsedate("1.VI.1965")
    assert date == "1/6/1965"

    date = spidercardreader.parsedate("1.VII.1965")
    assert date == "1/7/1965"

    date = spidercardreader.parsedate("1.VIII.1965")
    assert date == "1/8/1965"

    date = spidercardreader.parsedate("1.IX.1965")
    assert date == "1/9/1965"

    date = spidercardreader.parsedate("1.X.1965")
    assert date == "1/10/1965"

    date = spidercardreader.parsedate("1.XI.1965")
    assert date == "1/11/1965"

    date = spidercardreader.parsedate("1.XII.1965")
    assert date == "1/12/1965"


    # Check some invalid dates
    date = spidercardreader.parsedate("101.XII.1965")
    assert date == ""

    date = spidercardreader.parsedate("1.XIII.1965")
    assert date == ""

    date = spidercardreader.parsedate("1.XII.165")
    assert date == ""

