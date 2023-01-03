# Labels reader
This project aims to provide automated reading of natural history labels such as Herbarium labels and archive cards.

The project includes Python scripts and ideas for automated reading of machine typed labels (not yet for handwritten labels) and Data Matrix codes or QR codes.

## Requirements
The following must be installed on the system. On MacOS I install via MacPorts.
```sh
tesseract
tesseract-dan
tesseract-eng
zbar
libdmtx
ImageMagick
```
You also need to have an installation of the ImageMagick library which seems to only work on UNIX/Linux/MacOS.

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


## Documentation
Additional documentation can be found in [docs](https://github.com/NHMDenmark/NHMDlabelreader/tree/main/docs).

### spidercardreader
This script parses archive cards from the Ole Bøggild collection of Danish spiders.

### butterflyatlasreader
This script parses a table of taxa from the butterfly atlas book.

### herbariumcardreader
This script can parse taxonomic and locality information from herbarium 
archive cards.

