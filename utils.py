from json import dump, load
from os import listdir, makedirs, remove
from os.path import dirname, exists, isfile, realpath, splitext
from re import escape, match
from shutil import copyfile
from time import time


class UtilsError(Exception):

    """Base class for exceptions in this module."""

    pass


def get_data_from_json(json_file):
    """Get data from JSON file.

    :param filepath json_file: path to JSON file containing records
    :return: python object
    """
    try:
        with open(json_file) as f:
            try:
                return load(f)
            except ValueError as e:
                raise UtilsError(
                    "Error: failed loading records from file. ({0})".format(e))
    except EnvironmentError as e:
        raise UtilsError(
            "Error: failed opening file '{0}'. ({1})".format(json_file, e))


def diff_records(records_ldap, records_local):
    """Compare records with same employeeID.

    Records are classified in three classes: changed ('change'), new
    ('add'), and removed ('remove') records.

    :param list records_ldap: fetched CERN LDAP records
    :param list records_local: previous fetched CERN LDAP records,
    saved as a JSON file
    :return: list of updated records (tuple: (status, record)), where
       status = 'change', 'add', or 'remove', or empty list
    """
    results = []

    try:
        # Transform list of records to dictionary:
        # [{record}, ...] -> {'employeeID': {record}, ...}
        dict_ldap = dict((x.get('employeeID')[0], x) for x in records_ldap)
        dict_local = dict((x.get('employeeID')[0], x) for x in records_local)

        for employee_id in dict_ldap.iterkeys():
            record = dict_ldap.get(employee_id)
            if employee_id in dict_local:
                if not record == dict_local.get(employee_id):
                    # Changed record
                    results.append(('change', record))
            else:
                # New record
                results.append(('add', record))

        for employee_id in dict_local.iterkeys():
            if employee_id not in dict_ldap:
                # Deleted record
                record = dict_local.get(employee_id)
                results.append(('remove', record))

    except (Exception,) as e:
        raise UtilsError("{0}".format(e))

    return results


def version_file(src, n=10):
    """Version src file.

    Copy src with adding the timestamp as suffix, keep the latest n
    files, and remove the rest.

    :param filepath src: src file to copy
    :param int n: keep the n latest files
    """
    if not isfile(src):
        return

    n = 1 if n < 1 else n

    filename, ext = splitext(src)
    directory = dirname(realpath(src))

    # 1: Copy src
    timestamp = int(time())
    dst = "{0}_{1}{2}".format(filename, timestamp, ext)
    copyfile(src, dst)

    # 2: Remove files
    # RegEx matching files with format "<filename>_<timestamp><ext>"
    regex = r"^" + escape("{0}_".format(filename)) + "\d+" + escape(ext) + "$"
    # Sorted list of files in 'directory' matching 'regex'
    files = sorted([f for f in listdir(directory) if match(regex, f)])
    for f in files[:len(files)-n]:
        try:
            remove(f)
        except OSError as e:
            raise UtilsError(
                "Error: failed removing file '{0}'. ({1})".format(f, e))


def export_json(records, json_file):
    """Export records to file using json.dump.

    :param list records: list of records
    :param filepath json_file: path to JSON file containing records
    """
    directory = dirname(json_file)
    if directory is not "" and not exists(directory):
        makedirs(directory)

    try:
        with open(json_file, "w") as f:
            try:
                dump(records, f)
            except ValueError as e:
                raise UtilsError(
                    "Error: failed dumping records to JSON. ({0})"
                    .format(e))
    except EnvironmentError as e:
        raise UtilsError(
            "Error: failed opening file. ({0})".format(e))
