# -*- coding: utf-8 -*-
"""
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


def checkfilepath(filepath):
    """Check if filepath exists and if so create a new path with '.x' added before file suffix,
    where x is an integer

    filepath: A pathlib.Path object pointing to the file path to be checked
    Return: A pathlib.Path object pointing to the file path possible with an extra suffix
    """
    extension = 2
    while filepath.exists():
        if extension == 2:
            filepath = filepath.parent.joinpath(filepath.stem + "." + str(extension) + filepath.suffix)
        else:
            filepath = filepath.parent.joinpath(Path(filepath.stem).stem + "." + str(extension) + filepath.suffix)
        extension += 1  # Update in case we need it next round

    return filepath
