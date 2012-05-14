# Smart transactions exporter for NAB #

### Intro #

I hated having to login to NAB's clunky Internet banking and fight with its forms to get my data, so I decided I'd better automate this process.

This will export all your transactions for all your NAB accounts into nice QIF
files. You can use QIF to load in your desktop or online account software, such as Quicken/MS Money/Mint/Xero etc.

The tool is smart enough not to export pending/clearing trasactions, so in theory
you shouldn't get any duplicates.


### Prerequisites ##

You need to have the following:

- An account with NAB
- Internet banking login details - username and password
- Python 2.7
- Python libs mechanize and BeautifulSoup installed

### Usage ##

Simply start *export.py* from command line. It will ask you for username and password. If you are running it for the first time be prepared to wait since it's going to fetch all available transactions for all of your accounts, which may take a while.

After it is done, you'll see folders like that

```
lrwxr-xr-x   1 art  staff      63 12 May 18:06 083081-16xxxxxxx
lrwxr-xr-x   1 art  staff      63 12 May 18:07 083081-17xxxxxxx
lrwxr-xr-x   1 art  staff      63 12 May 18:08 083081-17xxxxxxx
```

each of those will contain your QIF files for a given account.

###Privacy and Security###

The tool does not use your username and password for anything except logging into NAB's website.

It does not store your username and password on the disk, you have to enter them every time you run it.

You can avoid that by creating a file named *.credentials* in the same folder. The file needs to have two lines, with username on the first line and password on the second line.


###Warranty###
The Software is provided "as is" without warranty of any kind, either express or implied, including without limitation any implied warranties of condition, uninterrupted use, merchantability, fitness for a particular purpose, or non-infringement


###License###
Copyright (C) 2012 Artem Skvira

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
