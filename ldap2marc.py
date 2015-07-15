import datetime
from optparse import OptionParser
import ldap_cern
from mapper import Mapper

parser = OptionParser()
parser.add_option(
    "-p",
    "--pagesize",
    dest="pagesize",
    type="int",
    default=250,
    help="pagination size to limit LDAP records [default: %default]")
parser.add_option(
    "-r",
    "--recordsize",
    dest="recordsize",
    type="int",
    default=500,
    help="record element size for each XML file [default: %default]")
parser.add_option(
    "-x",
    "--writexml",
    dest="writexml",
    action="store_true",
    default=False,
    help="write to XML file(s): [default: %default]")
(options, args) = parser.parse_args()

t0 = datetime.datetime.now()
all_results = ldap_cern.paged_search(options.pagesize)  # LDAP search with given page size
t1 = datetime.datetime.now()
t_final = t1 - t0
print "Entries found: {0}, Time [seconds]: {1}.{2}".format(
    len(all_results), t_final.seconds, t_final.microseconds/1000)

if options.writexml:
    mapper = Mapper(options.recordsize)  # mapper with given record size
    mapper.map_ldap_records(all_results)
    mapper.write_marcxml()
