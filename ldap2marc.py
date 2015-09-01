from optparse import OptionParser
from os.path import isfile
import json
import ldap_cern
from mapper import Mapper
import utils

parser = OptionParser()
parser.add_option(
    "-p",
    "--pagesize",
    dest="pagesize",
    type="int",
    default=250,
    help="limit LDAP records for each search request to avoid exceeding "
         "sizelimit [default: %default]")
parser.add_option(
    "-r",
    "--recordsize",
    dest="recordsize",
    type="int",
    default=500,
    help="limit amount of record elements for each XML file and has to be "
         "combined with `-x FILE` [default: %default]")
parser.add_option(
    "-x",
    "--exportxml",
    dest="exportxml",
    type="string",
    metavar="FILE",
    help="write to XML FILE(s) based on `recordsize`")
parser.add_option(
    "-j",
    "--exportjson",
    dest="exportjson",
    type="string",
    metavar="FILE",
    help="dump Python dictionary with records to a json-formatted FILE")
parser.add_option(
    "-u",
    "--update",
    dest="update",
    type="string",
    metavar="FILE",
    help="update stored json-formatted records with current LDAP records "
         "to FILE")
(options, args) = parser.parse_args()

all_results = ldap_cern.paged_search(options.pagesize)
print "Records found: {0}.".format(len(all_results))

if options.exportxml:
    mapper = Mapper()
    mapper.map_ldap_records(all_results)
    mapper.write_marcxml(options.recordsize, options.exportxml)

if options.exportjson:
    utils.export_json(all_results, options.exportjson)

if options.update:
    if isfile(options.update):
        with open(options.update) as f:
            stored = json.load(f)

        records_diff = utils.diff_records(all_results, stored)
        if len(records_diff):
            # Update stored json-formatted records
            utils.export_json(all_results, options.update)

            # Map updated LDAP records
            mapper = Mapper()
            mapper.update_ldap_records(records_diff)

            # Write changes to XML
            mapper.write_marcxml(0, "records_updated.xml")
        else:
            print "No changes found."
    else:
        print "updating failed. file '{0}' not found".format(options.update)
