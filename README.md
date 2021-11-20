# Collections Parser
This is a parser based on [p3pperp0tts][p3pperp0tts]' [leaks_parser][leaks_parser] which is used to parse:
- Collection #1
- Collection #2
- Collection #3
- Collection #4
- Collection #5
- AntiPublic #1
- AntiPublic MYR & ZABUGOR #2 

This is an updated script that will not calculate the:
- `MD5`
- `SHA1`
- `SHA256`
- `BCRYPT`

hashes and write them to the database. Thus, the `credentials.sqlite` database will be way more smaller than his 
version, thanks to the lack of "unnecessary" information.

## Usage
First, set up the dependencies:

```
$ wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
$ python2 get-pip.py
$ git clone https://github.com/syrusakbary/validate_email
$ cd validate_email
$ python2 setup.py install
$ cd .. && rm -rf validate_email
```

Afterwards, make sure that `parser.py` and `credentials.sqlite` are in the same folder the collections have been 
**decompressed**:

```
$ tree -x
.
├── Collection #1
│   └── ...
├── Collection #2
│   └── ...
├── Collection #3
│   └── ...
├── Collection #4
│   └── ...
├── Collection #5
│   └── ...
├── Antipublic #1
│   └── ...
├── Antipublic MYR & ZABUGOR #2
│   └── ...
├── credentials.sqlite
├── README.md
└── parser.py
```

Do note that each collection's subcollections **must be** decompressed as well. 

After making sure that everything is ready, run the script with the following command:

```
$ python2 parser.py
```

The script will be aable to parse most of these files with credentials. When a file is correctly parsed (and 
credentials are added to the database), it will renamed by adding the extension `.PARSED`.

After the script is ran, there'll be 3 new files:
1. `consistences.txt`: This will contain the path to the files that were correctly imported to the database.
2. `inconsistencies.txt`: This will contain the path to the files that had an unknown format, thus they were not 
imported to database.
1. `exceptions.txt`: This will contain the path to the files that caused exception(s) while attempting to parse them.

Majority of the files will be imported correctly. For the files that were not imported, check `inconsistencies.txt` 
and `exceptions.txt`. These files will **not** be renamed to `*.PARSED`. For these files, it'll be a good idea to 
create/implement a custom parser.

[p3pperp0tts]:  https://github.com/p3pperp0tts/
[leaks_parser]: https://github.com/p3pperp0tts/leaks_parser
