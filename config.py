# LDAP configuration
CFG_CERN_LDAP_URI = "ldap://xldap.cern.ch:389"
CFG_CERN_LDAP_BASE = "OU=Users,OU=Organic Units,DC=cern,DC=ch"
CFG_CERN_LDAP_PAGESIZE = 250
CFG_LDAP_SEARCHFILTER = r"(&(objectClass=*)(employeeType=Primary))"

# LDAP attribute list
# bibauthority_people_mapper contains the same attributes
CFG_LDAP_ATTRLIST = [
    "employeeID",
    "givenName",
    "sn",
    "displayName",
    "facsimileTelephoneNumber",
    "telephoneNumber",
    "mobile",
    "mail",
    "department",
    "cernGroup",
    "description",
    "division",
    "extensionAttribute12",
    "cernInstituteName",
    "extensionAttribute11"]

# Stores CERN LDAP records
CFG_RECORDS_JSON_FILE = "records.json"

# Stores updated MARC 21 authority records
CFG_RECORDS_UPDATED_FILE = "records_updates.xml"

# Prefix used in MARC field 035__a
CFG_AUTHOR_CERN = "AUTHOR|(SzGeCERN)"
