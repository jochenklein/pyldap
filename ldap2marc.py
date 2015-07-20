import datetime
from optparse import OptionParser
import json
from dictdiffer import diff, patch
from os.path import isfile
import ldap_cern
from mapper import Mapper


parser = OptionParser()
parser.add_option(
    "-p",
    "--pagesize",
    dest="pagesize",
    type="int",
    default=250,
    help="limit LDAP records for each search request to avoid exceeding sizelimit [default: %default]")
parser.add_option(
    "-r",
    "--recordsize",
    dest="recordsize",
    type="int",
    default=500,
    help="limit amount of record elements for each XML file and has to be combined with `-x FILE` [default: %default]")
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
    help="update stored json-formatted records with current LDAP records to FILE")
(options, args) = parser.parse_args()

t0 = datetime.datetime.now()
all_results = ldap_cern.paged_search(options.pagesize)  # LDAP search with given page size
t1 = datetime.datetime.now()
t_final = t1 - t0
print "Entries found: {0}, Time [seconds]: {1}.{2}".format(
    len(all_results), t_final.seconds, t_final.microseconds/1000)

if options.exportxml:
    mapper = Mapper(options.recordsize)  # mapper with given record size
    mapper.map_ldap_records(all_results)
    mapper.write_marcxml(options.exportxml)

if options.exportjson:
    with open(options.exportjson, "w") as f:
        json.dump([x for _, x in all_results], f)

if options.update:
    if not isfile(options.update):
        print "updating failed. file '%s' not found" % options.update
    with open(options.update) as f:
        stored = json.load(f)
    result = diff([x for _, x in all_results], stored)
    result_list = list(result)

    if len(result_list):
        # update saved records
        raw_input("Press 'Enter' to patch or 'Control+C' to cancel.")
        patched = patch(result, stored)
        with open(options.update, "w") as f:
            json.dump(patched, f)
