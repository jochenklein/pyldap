# pyldap2marc
Python script to harvest all CERN LDAP accounts, map it to [MARCXML](http://www.loc.gov/standards/marcxml/) records based on [MARC 21 authority](http://www.loc.gov/marc/authority/) and upload it to CERN Document Server (CDS). Furthermore the script allows you to export records to JSON and update records on CDS.

A LDAP record contains several attributes which are defined in `ldap_cern.py` and looks like

`{'mail': ['j.klein@cern.ch'],'givenName': ['Jochen'],'sn': ['Klein'], ...}`.

After it is mapped to MARC 21 XML Schema, it looks like:
```
<record>
  <datafield ind1=" " ind2=" " tag="371">
    <subfield code="m">j.klein@cern.ch</subfield>
    <!-- ... -->
  </datafield>
  <datafield ind1="1" ind2=" " tag="100">
    <subfield code="a">Klein</subfield>
  </datafield>
  <datafield ind1="0" ind2=" " tag="100">
    <subfield code="a">Jochen</subfield>
  </datafield>
  <!-- ... -->
</record>
```

Note that the script runs inside the CERN network only.

# Usage
usage: ldap2marc.py [-h] [-p PAGESIZE] [-r RECORDSIZE] [-x FILE] [-j FILE] [-u FILE] [-i FILE [FILE ...]] [-c]

optional arguments:
* `-h`, `--help`: show this help message and exit
* `-p PAGESIZE`, `--pagesize PAGESIZE`: limit number of records to be returned from LDAP for each search request to avoid exceeding sizelimit [default: 250]
* `-r RECORDSIZE`, `--recordsize RECORDSIZE`: limit number of record elements for each XML file and has to be used together with `-x` [default: 500]. For unlimited records use 0
* `-x FILE`, `--exportxml FILE`: write to MARCXML FILE(s), number of records each FILE is based on RECORDSIZE
* `-j FILE`, `--exportjson FILE`: dump records to a json-formatted FILE, used for `-u`, recommended using it together with `-x`
* `-u FILE`, `--update FILE`: compare json-formatted FILE with latest LDAP records and upload it to CDS using bibupload -ri
* `-i FILE [FILE ...]`, `--insert FILE [FILE ...]`: insert/upload MARC 21 authority record FILE(s) to CDS using bibupload -i
* `-c`, `--count`: counts all primary LDAP records

## Example
In the following it will be shown how to upload and update records to CDS.

1. Mapping and exporting: `$ python ldap2marc.py -j "records.json" -x "records.xml"` will export raw LDAP records to JSON as well as mapped LDAP records to XML file(s). In this way, both files are containing the same records. `records.json` is later used for the updating process, in which the records are going to be compared to the latest LDAP records, assumed that the records have already been uploaded. As described next:
2. Inserting: `$ python ldap2marc.py -i "/path/to/records_000.xml" "/path/to/records_001.xml" ...` will insert/upload the MARC 21 authority records to CDS.
3. Updating: The third and last step is supposed to be run every day and checks for changes in the records: `$ python ldap2marc.py -u "records.json"`. If there are changes, `records.json` will be updated and `records_updated.xml` will be created and used for uploading to CDS. Possible change states: `add`, `remove` or `change`. The updating process is described more in detail below.

Update records process:

The JSON file should contain the same records than the XML files which have been uploaded to CDS before. Thats why exporting to JSON at the same time than to MARCXML is the best way to do so. Right now, the script doesn't look up existing records on CDS. Instead, it uses the information out of the JSON file and compares the containing records with the latest on LDAP. In case the JSON file gets lost, or contains not the equal set of records (with all their fields) which have been already uploaded to CDS, create a new JSON file (lets call it `records.json`) and set its content to an empty list `[]`. Finally, run the update process `python ldap2marc.py -u "records.json"`. The script then detects all LDAP records as new ones, replaces and inserts them to CDS and updates `records.json`.

Changed records can be classified into three classes: `add`, `change`, and `remove`. In the last case, a `datafield` (see below) will be added to the record and tells `bibupload` to delete the record on CDS.

```
<datafield ind1=" " ind2=" " tag="980">
  <subfield code="a">DELETED</subfield>
</datafield>
```

# Structure
* `ldap2marc.py`: Run the script from the terminal and handle all steps.
* `ldap_cern.py`: Contain LDAP configuration, initialization and the search function with pagination.
* `mapper.py`: Contain the specifications and functions to map LDAP records to MARC 21 authority records.

## Setup Python LDAP package
For using `LDAP` in Python (`import ldap`) the [LDAP library interface module](http://www.python-ldap.org/download.shtml) is necessary.

### Mac OS X
When installing `ldap` with `$ pip install python-ldap` you might get a fatal error saying `'sasl.h' file not found`. In this case, you can try:

```console

$ pip install python-ldap \
   --global-option=build_ext \
   --global-option="-I$(xcrun --show-sdk-path)/usr/include/sasl"
```
   (See: http://stackoverflow.com/a/25129076/3215361, also for other solutions installing `ldap` on OS X.)
