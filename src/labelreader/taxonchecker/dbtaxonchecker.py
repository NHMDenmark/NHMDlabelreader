# -*- coding: utf-8 -*-
"""
This module implements a taxon name checker by using a checklist in the form of a Sqlite3 database.

LICENSE

Created on Thu Aug 26 16:49:00 2022

@author: Kim Steenstrup Pedersen, NHMD

Copyright (c) 2022  Natural History Museum of Denmark (NHMD)

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

import pandas as pd
import sqlite3
from thefuzz import fuzz
from thefuzz import process
from pathlib import Path
from typing import Optional, Tuple


class DBTaxonChecker:
    """
        This class implements a taxon name checker by using a checklist in the form of a Sqlite3 database.
    """

    def __init__(self, dbfilename: str = str(Path.cwd().parent.joinpath("db").joinpath("db.sqlite3")),
                 institution_code: str = "NHMD",
                 collection: str = "NHMD Vascular Plants"):
        """Initialize the TaxonChecker.

            :param dbfilename: Path and filename for the Sqlite3 taxon database
            :type dbfilename: str
            :param institution_code: String with institution acronym. Not in use at the moment.
            :type institution_code: str
            :param collection: String with collection name.  Not in use at the moment.
            :type collection: str
        """
        print("TaxonChecker: Opening connection to " + dbfilename)
        self.dbconnection = sqlite3.connect(dbfilename)

        # TODO: Include selecting taxon subset from collection and institution_code
        # TODO: Use taxontreedefid from collection to select taxonnames valid only for a specific collection
        #cur = self.dbconnection.cursor()
        #res = cur.execute('select id from institution where code = "NHMD"')
        #self.institution_id = res.fetchone()[0]
        #res = cur.execute('select id, spid from collection where name = "NHMD Vascular Plants"')
        #id, spid = res.fetchone()

        self.taxontable = pd.read_sql("select taxonid, name, fullname, parentfullname from taxonname;",
                                      self.dbconnection, index_col="id")
        self.fullname = self.taxontable['fullname']  # Pandas.Series
        self.name = self.taxontable['name']  # Pandas.Series


    def __del__(self):
        """Clean up by closing database connection with object gets deleted."""
        self.dbconnection.close()


    def check_full_name(self, querystring: str, score_threshold: int = 90) -> Optional[Tuple[str, int, int]]:
        """Do a fuzzy match between querystring and the database column taxonname.fullname

            :param querystring: The query string
            :type querystring: str
            :param score_threshold: Fuzzy matching percentage threshold (default 90)
            :type score_threshold: int
            :return: None if no match, otherwise a tuple of (fullname, score, taxon_id)
            :rtype: Optional[Tuple[str, int, int]]
        """
        possibilities = process.extract(querystring, self.fullname, limit=100, scorer=fuzz.ratio)
        res = [possible for possible in possibilities if possible[1] > score_threshold]
        if len(res) > 0:
            return res[0]
        else:
            return None

    def check_name(self, querystring: str, score_threshold: int = 90) -> Optional[Tuple[str, int, int]]:
        """Do a fuzzy match between querystring and the database column taxonname.name

            :param querystring: The query string
            :type querystring: str
            :param score_threshold: Fuzzy matching percentage threshold (default 90)
            :type score_threshold: int
            :return: None if no match, otherwise a tuple of (name, score, taxon_id)
            :rtype: Optional[Tuple[str, int, int]]
        """
        possibilities = process.extract(querystring, self.name, limit=100, scorer=fuzz.ratio)
        res = [possible for possible in possibilities if possible[1] > score_threshold]
        if len(res) > 0:
            return res[0]
        else:
            return None