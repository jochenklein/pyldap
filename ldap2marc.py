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
    help="limit LDAP records for each search request to avoid exceeding "
         "sizelimit [default: %(default)d]")
parser.add_argument(
    "-r",
    "--recordsize",
    dest="recordsize",
    type=int,
    default=500,
    help="limit amount of record elements for each XML file and has to be "
         "combined with `-x FILE` [default: %(default)d]")
parser.add_argument(
    "-x",
    "--exportxml",
    dest="exportxml",
    type=str,
    metavar="FILE",
    help="write to XML FILE(s) based on `recordsize`")
parser.add_argument(
    "-j",
    "--exportjson",
    dest="exportjson",
    type=str,
    metavar="FILE",
    help="dump Python dictionary with records to a json-formatted FILE")
parser.add_argument(
    "-u",
    "--update",
    dest="update",
    type=str,
    metavar="FILE",
    help="update stored json-formatted records with current LDAP records "
         "to FILE")
parser.add_argument(
    "-i",
    "--insert",
    dest="insert",
    type=str,
    nargs="+",
    metavar="FILE",
    help="insert/upload MARC 21 authority record FILE(s) to CDS using "
         "bibupload")
parser.add_argument(
    "-c",
    "--count",
    dest="count",
    action="store_true",
    help="counts all primary LDAP records")
args = parser.parse_args()


def get_records():
    all_results = ldap_cern.paged_search(args.pagesize)
    print "Records found: {0}.".format(len(all_results))
    return all_results


if args.exportxml:
    all_results = get_records()
    mapper = Mapper()
    mapper.map_ldap_records(all_results)
    mapper.write_marcxml(args.recordsize, args.exportxml)

if args.exportjson:
    all_results = get_records()
    utils.export_json(all_results, args.exportjson)

if args.update:
    if isfile(args.update):
        with open(args.update) as f:
            stored = json.load(f)

        all_results = get_records()
        records_diff = utils.diff_records(all_results, stored)
        if len(records_diff):
            # Update stored json-formatted records
            utils.export_json(all_results, args.update)

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
                    "-c", f,
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
if args.count:
    get_records()
