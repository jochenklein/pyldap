# pyldap
Python script to harvest all CERN LDAP accounts using pagination (to avoid exceeding the LDAP sizelimit and get a `LDAPException`). It is accessible from inside CERN only.

## Setup
For using `LDAP` in Python (`import ldap`) the [LDAP library interface module](http://www.python-ldap.org/download.shtml) is necessary.

#### Mac OS X
When installing `ldap` with `$ pip install python-ldap` you might get a fatal error saying `'sasl.h' file not found`. In this case, you can try:

```console

$ pip install python-ldap \
   --global-option=build_ext \
   --global-option="-I$(xcrun --show-sdk-path)/usr/include/sasl"
```
   (See: http://stackoverflow.com/a/25129076/3215361, also for other solutions installing `ldap` on OS X.)
