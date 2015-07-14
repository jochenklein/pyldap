import datetime
from optparse import OptionParser
import ldap_cern

parser = OptionParser()
parser.add_option(
    "-p",
    "--pagesize",
    dest="pagesize",
    type="int",
    default=250,
    help="pagination size to limit LDAP records [default: %default]")
(options, args) = parser.parse_args()

t0 = datetime.datetime.now()
all_results = ldap_cern.paged_search(options.pagesize)
t1 = datetime.datetime.now()
t_final = t1 - t0
print "Entries found: {0}".format(len(all_results))
print "Time [seconds]: {0}.{1}".format(t_final.seconds, t_final.microseconds/1000)
