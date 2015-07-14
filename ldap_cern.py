import ldap
from ldap.controls import SimplePagedResultsControl


CFG_CERN_LDAP_URI = "ldap://xldap.cern.ch:389"
CFG_CERN_LDAP_BASE = "OU=Users,OU=Organic Units,DC=cern,DC=ch"
CFG_LDAP_ATTRLIST = None
CFG_LDAP_SEARCHFILTER = r"(objectClass=*)"


class LDAPError(Exception):
    pass


def _ldap_initialize():
    """Initialize the LDAP connection and return the LDAP connection."""
    try:
        ldap_connection = ldap.initialize(CFG_CERN_LDAP_URI)
        ldap_connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
        return ldap_connection
    except ldap.LDAPError as e:
        raise LDAPError("Initialization failed: {0}.".format(e))


def _msgid(ldap_connection, req_ctrl):
    """Run the search request and return the `msgid`."""
    try:
        return ldap_connection.search_ext(
            CFG_CERN_LDAP_BASE,
            ldap.SCOPE_ONELEVEL,
            CFG_LDAP_SEARCHFILTER,
            CFG_LDAP_ATTRLIST,
            attrsonly=0,
            serverctrls=[req_ctrl])
    except ldap.SERVER_DOWN as e:
        raise LDAPError("Connection failed: {0}.".format(e))


def paged_search(pagesize=250):
    """
    Call the search function with using pagination to avoid exceeding LDAP sizelimit.
    Return a list with the LDAP objects.
    See: https://bitbucket.org/jaraco/python-ldap/src/f208b6338a28/Demo/paged_search_ext_s.py
    """
    ldap_connection = _ldap_initialize()
    req_ctrl = SimplePagedResultsControl(True, pagesize, "")
    msgid = _msgid(ldap_connection, req_ctrl)
    result_pages = 0
    all_results = []

    while True:
        rtype, rdata, rmsgid, rctrls = ldap_connection.result3(msgid)
        all_results.extend(rdata)
        result_pages += 1

        pctrls = [
            c
            for c in rctrls
            if c.controlType == SimplePagedResultsControl.controlType
        ]
        if pctrls:
            if pctrls[0].cookie:
                req_ctrl.cookie = pctrls[0].cookie
                msgid = _msgid(ldap_connection, req_ctrl)
            else:
                break
    return all_results
