# pyldap2marc
Python script (`ldap2marc`) to harvest all CERN LDAP accounts using pagination (to avoid exceeding the LDAP sizelimit and get a `LDAPException`), map it to MARC 21 authority records, and write it to XML file(s) optionally. The LDAP server is accessible from inside CERN only. The script is currently more for testing and could contain bugs. For other use cases it might be uncomplete.

# Usage
You can run the script from the terminal with optional parameters, using `$ python ldap2marc.py [options]`

* `-h`, `--help`: run to see the available parameters and how to use them
* `-p`, `--pagesize` [default: 250]: set limit for LDAP search requests to avoid sizelimit exceeded
* `-r`, `--recordsize` [default: 500]: set limit for amount of record elements in one XML document
* `-x`, `--writexml` [default: False]: set to write XML file(s)

Example: `$ python ldap2marc.py -r 100 -x`. Running this will fetch all LDAP records, map and write them to XML files with a limitation of 100 record elements each file.

## XML output

If `--writexml` is enabled, the script creates XML files (e.g. `marc_output_000.xml`, `marc_output_001.xml`) located in the same directory than the script.

Without the `-x` parameter, the LDAP records will be stored in a Python object.

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
