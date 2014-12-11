IF Test Purpose to C Test Purpose translator for TestGen-IF (IFtpt)
===================================================================
This is a script to translate a TestGen-IF test purpose definition written in IF language to C language, so it can be processed by the current version of TestGen-IF.

Installation
============
- Install Python 2.7 and pip from your Linux distribution's package manager.
- Install requirements:
  `$ pip install -r requirements.txt`
- Set permissions:
  `$ chmod 755 iftpt.py`

Usage
=====
```
$ ./iftpt.py -o <output file .C> <input file .if>
```
For more information, run `./iftpt.py -h` 

