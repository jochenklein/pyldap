# pyldap2marc
Python script (`ldap2marc`) to harvest all CERN LDAP accounts using pagination (to avoid exceeding the LDAP sizelimit and get a `LDAPException`), map it to MARC 21 authority records, and write it to XML file(s) optionally. The LDAP server is accessible from inside CERN only. The script is currently more for testing and could contain bugs. For other use cases it might be uncomplete. Furthermore, it collects only specific LDAP attributes (listed in `CFG_LDAP_ATTRLIST`): `givenName`, `sn`, `mail`, `displayName`, and `employeeID`.

# Usage
You can run the script from the terminal with optional parameters, using `$ python ldap2marc.py [options]`. Options:
* `-h`, `--help`: show this help message and exit
* `-p PAGESIZE`, `--pagesize=PAGESIZE`: limit LDAP records for each search request to avoid exceeding sizelimit [default: 250]
* `-r RECORDSIZE`, `--recordsize=RECORDSIZE`: limit amount of record elements for each XML file [default: 500]
* `-x FILE`, `--exportxml=FILE`: write to XML FILE(s) based on `recordsize`
* `-j FILE`, `--exportjson=FILE`: dump Python dictionary with records to a json-formatted FILE
* `-u FILE`, `--update=FILE`: update stored json-formatted records with current LDAP records to FILE

Example: running `$ python ldap2marc.py` will fetch all LDAP records and store them in a Python object.

## Output
It is possible to save the records in XML (MARC 21 authority records) and in json-formatted files (LDAP records).

### XML
Example: running `$ python ldap2marc.py -p 100 -x marc_output.xml` will fetch all LDAP records, map and write them to XML files with a limitation of 100 record elements each file (`marc_output_000.xml`, `marc_output_001.xml`, ...) located in the same directory than the script.

### JSON
Example: running `$ python ldap2marc.py -j ldap_records.json` will fetch all LDAP records and store them in a json-formatted string in the given file.

## Update records
Example: running `$ python ldap2marc.py -u ldap_records.json` will compare the given file with the LDAP records and update/patch it if they differ. Using [Dictdiffer](https://github.com/inveniosoftware/dictdiffer).

# Structure
* `ldap2marc.py`: Run the script from the terminal and handle all steps.
* `ldap_cern.py`: Contain LDAP configuration, initialization and the search function with pagination.
* `mapper.py`: Contain the specifications and functions to map LDAP records to MARC 21 authority records.

## Setup Python LDAP package
For using `LDAP` in Python (`import ldap`) the [LDAP library interface module](http://www.python-ldap.org/download.shtml) is necessary.

#### Mac OS X
When installing `ldap` with `$ pip install python-ldap` you might get a fatal error saying `'sasl.h' file not found`. In this case, you can try:

```console

$ pip install python-ldap \
   --global-option=build_ext \
   --global-option="-I$(xcrun --show-sdk-path)/usr/include/sasl"
```
   (See: http://stackoverflow.com/a/25129076/3215361, also for other solutions installing `ldap` on OS X.)
