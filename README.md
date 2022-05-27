# Labels reader
This project aims to provide automated reading of natural history labels such as Herbarium labels.

Python scripts and ideas for automated reading of machine typed labels (not yet handwritten labels) and Data Matrix codes or QR codes.

## Requirements
The following must be installed on the system. On MacOS I install via MacPorts.
```sh
tesseract
tesseract-dan
tesseract-eng
zbar
libdmtx
```

Create virtual environment
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
pytest src
```
Check the output for any failures.

## Kims notes
POStagger, Named Entity, Language detector, and a lot of other stuff - Polyglot:
https://github.com/aboSamoor/polyglot

DanNLP:
https://github.com/alexandrainst/danlp
