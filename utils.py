import json


def diff_records(list1, list2):
    """Compare two records with same employeeID.

    :param list list1: LDAP records
    :param list list2: list of stored json-formatted records
    :return: list of tuples
        (status, record), status = 'change', 'add', or 'remove'
    """
    # transform list into dict {'employeeID': {record}}
    dict1 = dict((x['employeeID'][0], x) for x in list1)
    dict2 = dict((x['employeeID'][0], x) for x in list2)

    results = []
    for record in list1:
        # check for changes
        employeeID = record['employeeID'][0]
        if employeeID in dict2.keys():
            # compare each (key, value) of two records
            for attr in record:
                if not record[attr] == dict2[employeeID][attr]:
                    results.append(('change', record))
        # new record
        else:
            results.append(('add', record))

    for record in list2:
        # removed record
        if not record['employeeID'][0] in dict1:
            results.append(('remove', record))

    return results


def export_json(records, file="records.json"):
    if len(records):
        with open(file, "w") as f:
            json.dump(records, f)
