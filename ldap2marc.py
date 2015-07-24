import argparse
import sys

from config import (
    CFG_LDAP_ATTRLIST, CFG_LDAP_SEARCHFILTER, CFG_RECORDS_JSON_FILE,
    CFG_RECORDS_UPDATED_FILE)
from myldap import get_users_records_data, LDAPError
from mapper import Mapper, MapperError
from utils import (
    diff_records, export_json, get_data_from_json, UtilsError, version_file)


def load_json(parser, json_file):
    """Return data from JSON file."""
    try:
        return get_data_from_json(json_file)
    except UtilsError as e:
        parser.error(e)


def get_records(ldap_searchfilter=CFG_LDAP_SEARCHFILTER,
                ldap_attrlist=CFG_LDAP_ATTRLIST):
    """Return user records from LDAP."""
    records = []
    try:
        records = get_users_records_data(
            ldap_searchfilter, ldap_attrlist, "utf-8")
    except LDAPError as e:
        sys.stderr.write(e)
        sys.exit(1)
    return records


def update_records(json_file=CFG_RECORDS_JSON_FILE):
    """Update local stored records with latest LDAP records.

    :param filepath json_file: path to JSON file containing records
    """
    # Fetch CERN LDAP records
    records_ldap = get_users_records_data(
        CFG_LDAP_SEARCHFILTER,
        CFG_LDAP_ATTRLIST,
        "utf-8")
    try:
        records_local = get_data_from_json(json_file)
        # records_diff contains updated records (changed, added, or
        # removed on LDAP)
        records_diff = diff_records(records_ldap, records_local)

        # Map updated records
        if records_diff:
            mapper = Mapper()
            mapper.update_ldap_records(records_diff)
            mapper.write_marcxml(CFG_RECORDS_UPDATED_FILE, 0)
            # Version existing file
            version_file(json_file)
            # Update local file with current LDAP records
            export_json(records_ldap, json_file)
        else:
            print "No updated records found."
    except (UtilsError, MapperError) as e:
        sys.stderr.write(e)
        sys.exit(1)


usage = ("bibauthority_people.py [-h] [[-r RECORDSIZE] [-x FILE [-l FILE] "
         "[-j FILE]]] [-i FILE [FILE ...]] [-c]")

parser = argparse.ArgumentParser(
    description="Command line interface for the CERN people collection. Map "
                "all CERN LDAP records to MARC 21 authority records, write "
                "to XML files and upload to CDS.",
    usage=usage)

group1 = parser.add_argument_group("Export")
group2 = parser.add_argument_group("Update")
group3 = parser.add_argument_group("Information")

group1.add_argument(
    "-r",
    "--recordsize",
    dest="recordsize",
    type=int,
    default=500,
    help="limit number of record elements for each XML file and has to be "
         "used together with '-x' [default: %(default)d]. For unlimited "
         "records use 0")
group1.add_argument(
    "-x",
    "--exportxml",
    dest="exportxml",
    type=str,
    metavar="FILE",
    help="export mapped CERN LDAP records to XML FILE(s). Number of records "
         "each FILE is based on RECORDSIZE")
group1.add_argument(
    "-j",
    "--exportjson",
    dest="exportjson",
    type=str,
    metavar="FILE",
    help="export CERN LDAP records to a JSON-formatted FILE, recommended "
         "using it together with '-x'")
group2.add_argument(
    "-u",
    "--update",
    dest="update",
    type=str,
    metavar="FILE",
    help="check for updated records. Comapare FILE with latest LDAP records "
         "[FILE=JSON file containg records, created with '-j']")
group3.add_argument(
    "-c",
    "--count",
    dest="count",
    action="store_true",
    help="count all primary CERN LDAP records")

args = parser.parse_args()

if args.exportxml or args.exportjson or args.update:
    records = get_records()
    print("{0} records fetched from CERN LDAP".format(len(records)))

if args.exportxml:
    try:
        mapper = Mapper()
        mapper.map_ldap_records(records)
        mapper.write_marcxml(args.exportxml, args.recordsize)
    except MapperError as e:
        sys.stderr.write(e)
        sys.exit(1)

if args.exportjson:
    try:
        export_json(records, args.exportjson)
    except UtilsError as e:
        sys.stderr.write(e)
        sys.exit(1)

if args.update:
    update_records(args.update)

if args.count:
    records = get_records(ldap_attrlist=['employeeID'])
    print("{0} records found on CERN LDAP".format(len(records)))
