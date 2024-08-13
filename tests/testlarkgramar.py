#  Copyright (c) 2024  Natural History Museum of Denmark (NHMD)
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

import argparse
from lark import Lark


def main():
    ap = argparse.ArgumentParser(description='Parse a text file with the Lark grammar')
    ap.add_argument("-i", "--input", required=True, type=str,
                    help="file name for and path to input text")
    ap.add_argument("-g", "--grammar", required=True, type=str,
                    help="file name for and path to grammar")
    args = vars(ap.parse_args())


    # Read the grammar
    gf = open(args["grammar"], "r")
    grammar = gf.read()

    # Read text example to parse
    f = open(args["input"], "r")
    text = f.read()

    # Create the parser
    parser = Lark(grammar, start='card')

    # Parse tree
    ptree = parser.parse(text)
    print(ptree.pretty())
    print(ptree)

if __name__ == '__main__':
    main()