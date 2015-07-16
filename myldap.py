import ldap
from ldap.controls import SimplePagedResultsControl
from config import (
    CFG_CERN_LDAP_PAGESIZE, CFG_CERN_LDAP_URI, CFG_CERN_LDAP_BASE)


class LDAPError(Exception):

    """Base class for exceptions in this module."""

    pass


def _ldap_initialize():
    """Initialize the LDAP connection.

    :return: LDAP connection
    """
    try:
        ldap_connection = ldap.initialize(CFG_CERN_LDAP_URI)
        ldap_connection.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
        return ldap_connection
    except ldap.LDAPError as e:
        raise LDAPError("Initialization failed: {0}.".format(e))


def _msgid(ldap_connection, req_ctrl, ldap_searchfilter, ldap_attrlist=None):
    """Run the search request using search_ext.

    :param string ldap_searchfilter: filter to apply in the LDAP search
    :param list ldap_attrlist: retrieved LDAP attributes. If None, all
        attributes are returned
    :return: msgid
    """
    try:
        return ldap_connection.search_ext(
            CFG_CERN_LDAP_BASE,
            ldap.SCOPE_SUBTREE,
            ldap_searchfilter,
            ldap_attrlist,
            attrsonly=0,
            serverctrls=[req_ctrl])
    except ldap.SERVER_DOWN as e:
        raise LDAPError("Error: Connection to CERN LDAP failed. ({0})"
                        .format(e))


def _paged_search(ldap_connection, ldap_searchfilter, ldap_attrlist=None):
    """Search the CERN LDAP server using pagination.

    See https://bitbucket.org/jaraco/python-ldap/src/f208b6338a28/Demo/paged_search_ext_s.py

    :param string ldap_searchfilter: filter to apply in the LDAP search
    :param list attr_list: retrieved LDAP attributes. If None, all attributes
        are returned
    :return: list of tuples (result-type, result-data) or empty list,
        where result-data contains the user dictionary
    """
    req_ctrl = SimplePagedResultsControl(True, CFG_CERN_LDAP_PAGESIZE, "")
    msgid = _msgid(ldap_connection, req_ctrl, ldap_searchfilter, ldap_attrlist)
    result_pages = 0
    results = []

    while True:
        rtype, rdata, rmsgid, rctrls = ldap_connection.result3(msgid)
        results.extend(rdata)
        result_pages += 1

        pctrls = [
            c
            for c in rctrls
            if c.controlType == SimplePagedResultsControl.controlType
        ]
        if pctrls:
            if pctrls[0].cookie:
                req_ctrl.cookie = pctrls[0].cookie
                msgid = _msgid(ldap_connection, req_ctrl,
                               ldap_searchfilter, ldap_attrlist)
            else:
                break

    return results


def get_users_records_data(
  ldap_searchfilter, attr_list=None, decode_encoding=None):
    """Get result-data of records.

    :param string ldap_searchfilter: filter to apply in the LDAP search
    :param list attr_list: retrieved LDAP attributes. If None, all attributes
        are returned
    :param string decode_encoding: decode the values of the LDAP records
    :return: list of LDAP records, but result-data only
    """
    ldap_connection = _ldap_initialize()
    records = _paged_search(ldap_connection, ldap_searchfilter, attr_list)

    records_data = []

    if decode_encoding:
        records_data = [
            dict(
                (k, [v[0].decode(decode_encoding)]) for (k, v) in x.iteritems()
            )
            for (dummy, x) in records]
    else:
        records_data = [x for (dummy, x) in records]

    return records_data
