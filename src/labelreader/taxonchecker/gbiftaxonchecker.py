# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 14:42:00 2022

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
from pygbif import species


class GBIFTaxonChecker:
    """This class implements a taxon name checker by using the GBIF taxon backbone via the GBIF web API
       using PyGBIF.
    """

    def __init__(self):
        """Empty - do we really need a class for this?"""
        pass


    def check_full_name(self, querystring):
        """Do a fuzzy match between querystring and GBIF taxon backbone

            querystring: A string containing a full species name (Starting with the Genus name)
            Returns: None if no match, otherwise the full name closest to querystring
        """
        res = species.name_lookup(q=querystring, rank="species", type="checklist", limit=1)

        if res['count'] == 0:
            return None
        else:
            # TODO: Check maybe more names than just the first match
            return res['results'][0]['scientificName']

