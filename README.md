[![Python package](https://github.com/NHMDenmark/NHMDlabelreader/actions/workflows/python-package.yml/badge.svg)](https://github.com/NHMDenmark/NHMDlabelreader/actions/workflows/python-package.yml)

# Labels reader
This project aims to provide automated reading of natural history labels such as Herbarium labels and archive cards.

The project includes Python scripts and ideas for automated reading of machine typed labels (not yet for handwritten labels) and Data Matrix codes or QR codes.

## Requirements
The following must be installed on the system. On MacOS I install via MacPorts.
```sh
tesseract
tesseract-dan
tesseract-eng
tesseract-deu
tesseract-lat
```

Create a virtual environment
```sh
python3 -m venv venv
```

Install requirements via pip into virtual environment
```sh
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
The binary wheels in the pypi repository of the current version 2.2.0 of zxing-cpp has a problem and must be
build from the source code package by
```sh
pip uninstall zxing-cpp
python -m pip install zxing-cpp==2.2.0 --no-binary zxing-cpp
```


## Development

### Testing
To run the tests using pytest do the following from the same directory as this README file.
```sh
source venv/bin/activate
pytest tests
```
Check the output for any failures.

### Packaging
To create wheel and source packages ready for distribution do:
```sh
source venv/bin/activate
pip install --upgrade -r build_requirements.txt
python -m build
```
This creates a dist directory with the two package files. To install the wheel file into another virtual environment do
```sh
python -m venv venv2
source venv2/bin/activate
pip install --upgrade pip
pip install dist/NHMDlabelreader-0.0.1-py3-none-any.whl
```

For more instructions on how to configure setup.cfg, see the [setuptools quickstart](https://setuptools.pypa.io/en/latest/userguide/quickstart.html#).

To upload to PyPI follow these [instructions](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

### Github actions
Currently there are two github actions workflow that both need to be
activated interactively in the repository on github.com.
For more advanced workflows see Ole Engstrøms [IKPLS](https://github.com/Sm00thix/IKPLS/tree/main) repository 

## Documentation
Additional documentation can be found in [docs](https://github.com/NHMDenmark/NHMDlabelreader/tree/main/docs).

### spidercardreader
This script parses archive cards from the Ole Bøggild collection of Danish spiders.

### butterflyatlasreader
This script parses a table of taxa from the butterfly atlas book.

### herbariumcardreader
This script can parse taxonomic and locality information from herbarium 
archive cards.

