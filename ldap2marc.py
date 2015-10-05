import argparse
from os.path import isfile, abspath
import json
import ldap_cern
from mapper import Mapper
import utils
from invenio.bibtask import task_low_level_submission

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--pagesize",
    dest="pagesize",
    type=int,
    default=250,
    help="limit number of records to be returned from LDAP for each search "
         "request to avoid exceeding sizelimit [default: %(default)d]")
parser.add_argument(
    "-r",
    "--recordsize",
    dest="recordsize",
    type=int,
    default=500,
    help="limit number of record elements for each XML file and has to be "
         "used together with `-x` [default: %(default)d]. For unlimited "
         "records use 0")
parser.add_argument(
    "-x",
    "--exportxml",
    dest="exportxml",
    type=str,
    metavar="FILE",
    help="write to MARCXML FILE(s), number of records each FILE is based on "
         "RECORDSIZE")
parser.add_argument(
    "-j",
    "--exportjson",
    dest="exportjson",
    type=str,
    metavar="FILE",
    help="dump records to a json-formatted FILE, used for `-u`, recommended "
         "using it together with `-x`")
parser.add_argument(
    "-u",
    "--update",
    dest="update",
    type=str,
    metavar="FILE",
    help="compare json-formatted FILE with latest LDAP records and upload it "
         "to CDS using bibupload -ri")
parser.add_argument(
    "-i",
    "--insert",
    dest="insert",
    type=str,
    nargs="+",
    metavar="FILE",
    help="insert/upload MARC 21 authority record FILE(s) to CDS using "
         "bibupload -i")
parser.add_argument(
    "-c",
    "--count",
    dest="count",
    action="store_true",
    help="counts all primary LDAP records")
args = parser.parse_args()

if args.exportxml or args.exportjson or args.update or args.count:
    records = ldap_cern.paged_search(args.pagesize)
    print "Records found: {0}.".format(len(records))

if args.exportxml:
    mapper = Mapper()
    mapper.map_ldap_records(records)
    mapper.write_marcxml(args.recordsize, args.exportxml)

if args.exportjson:
    utils.export_json(records, args.exportjson)

if args.update:
    if isfile(args.update):
        with open(args.update) as f:
            stored_records = json.load(f)

        records_diff = utils.diff_records(records, stored_records)
        if len(records_diff):
            # Update stored json-formatted records
            utils.export_json(records, args.update)

            # Map updated LDAP records
            mapper = Mapper()
            mapper.update_ldap_records(records_diff)

            # Write changes to XML
            mapper.write_marcxml(0, "records_updated.xml")

            # Bibupload to CDS
            f = abspath("records_updated.xml")
            if isfile(f):
                task_low_level_submission(
                    "bibupload",
                    "ldap2marc",
                    "-ri", f,
                    "-P", "-1",
                    "-N", "ldap-author-data")
            else:
                print "file '{0}' not found".format(args.update)
        else:
            print "No changes found."
    else:
        print "updating failed. file '{0}' not found".format(args.update)

if args.insert:
    for f in args.insert:
        if isfile(f):
            task_low_level_submission(
                "bibupload",
                "ldap2marc",
                "-i", f,
                "-P", "-1",
                "-N", "ldap-author-data")
        else:
            print "file '{0}' not found".format(args.update)

# speed could be improved by changing the CFG_LDAP_ATTRLIST in
# mapper.py to one attribute only, e.g. employeeID
# if args.count:
    # get_records()
