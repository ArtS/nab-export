# Smart transactions exporter for NAB

## Introduction

I hated having to login to NAB's clunky Internet banking and fight with its forms to get my data, so I decided I'd better automate this process.

nab-export exports all of your transactions for all your NAB accounts. Using the `--qif` option, you can load exported QIF files into your desktop or online accounting software, such as Quicken/MS Money/Mint/Xero etc.

The tool is smart enough not to export pending/clearing trasactions, so in theory
you shouldn't get any duplicates.

### Prerequisites

- Python 2.7
- An account with NAB, as well as internet banking login details (username and password)

### Usage

1. Install the virtual environment with dependencies

```bash
virtualenv --python=python2 .venv && source .venv/bin/activate && pip install -r requirements.txt
```

2. Run the program

```bash
python export.py
```

3. Enter your username and password

#### Command Line Arguments

##### --qif

Exports transactions to QIF files

### Privacy and Security

The tool does not use your username and password for anything except logging into NAB's website.

It does not store your username and password on the disk, you have to enter them every time you run it.

You can avoid that by creating a file named *.credentials* in the same folder. The file needs to have two lines, with username on the first line and password on the second line.

### License

Copyright (C) 2012 Artem Skvira

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
