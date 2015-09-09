from lxml import etree
from collections import OrderedDict
import os
from invenio.search_engine import search_pattern


class Mapper:
    """Map LDAP records to MARC 21 authority records in XML sctructure.
    MARC 21 authority reference: http://www.loc.gov/marc/authority/
    """
    def __init__(self):
        """Initialize the mapper properties."""
        self.roots = []  # contain all root elements
        self.records = []  # contain all (mapped) MARC records
        self.mapper_dict = {  # mapping definition LDAP to MARC 21 authority
            "employeeID": "035__a",
            "givenName": "1000_a",
            "sn": "1001_a",
            "displayName": "100__a",
            "facsimileTelephoneNumber": "371__f",
            "telephoneNumber": "371__k",
            "mobile": "371__l",
            "mail": "371__m",
            "department": "371__d",
            "cernGroup": "371__g",
            "description": "371__h",
            "division": "371__i",
            "extensionAttribute12": "371__j",
            "cernInstituteName": "371__0",
            "extensionAttribute11": "371__1",

        }    # see CFG_LDAP_ATTRLIST in ldap_cern.py

    def _split_marc_id(self, marc_id):
        """Split MARC 21 identifier which is defined in the mapper_dict.

        :return: MARC 21 tag, ind1, ind2 and code
        """
        # code is optional
        try:
            marc_code = marc_id[5]
        except IndexError:
            marc_code = None

        return marc_id[:3], marc_id[3], marc_id[4], marc_code

    def _create_root(self):
        """Create root element 'collection' with the attribute 'xmlns'.

        :return: root element
        """
        return etree.Element(
            "collection", {"xmlns": "http://www.loc.gov/MARC21/slim"})

    def _create_record(self, parent=None):
        """Create record element.

        :param elem parent: parent of record element (optional)
        :return: record element
        """
        if parent:
            return etree.SubElement(parent, "record")
        else:
            return etree.Element("record")

    def _create_controlfield(self, parent, attr_tag, inner_text=None):
        """Create child element 'controlfield' of parent.

        :param elem parent: parent element, usually 'collection'
        :return: controlfield element, child of parent
        """
        controlfield = etree.SubElement(parent, "controlfield", {
            "tag": attr_tag})
        if inner_text:
            controlfield.text = inner_text
        return controlfield

    def _create_datafield(
      self, parent, attr_tag, attr_ind1, attr_ind2, repeatable=False):
        """Create child element 'datafield', add it to the record element.

        :param elem parent: parent element, usually 'record'
        :param bool repeatable: Allows multiple datafields with same tags
        :return: either new or existing datafield element (depending on
            repeatable), child of parent
        """
        if attr_ind1 == "_":
            attr_ind1 = " "
        if attr_ind2 == "_":
            attr_ind2 = " "

        find = parent.xpath(
            "datafield[@tag={0} and @ind1='{1}' and @ind2='{2}']".format(
                attr_tag, attr_ind1, attr_ind2))
        if not find or repeatable:
            return etree.SubElement(parent, "datafield", OrderedDict({
                "tag": attr_tag, "ind1": attr_ind1, "ind2": attr_ind2}))
        return find[0]

    def _create_subfield(self, parent, attr_code, inner_text):
        """Create child element 'subfield' of parent including
        attr_code and inner_text.

        :return: subfield element, child of parent
        """
        subfield = etree.SubElement(
            parent, "subfield", {"code": attr_code})
        subfield.text = inner_text
        return subfield

    def _attach_records(self, record_size=500):
        """Attach record elements to root element(s).

        :param int record_size: record child elements in a root node,
            if <= 0: append all records to one root node
        :return : list of root elements
        """
        # append all record elements to one root element
        if record_size <= 0:
            record_size = -1

        # append records to root element(s) depending on record_size
        current_root = self._create_root()
        self.roots.append(current_root)
        record_size_counter = 0

        for record in self.records:
            if record_size_counter == record_size:
                current_root = self._create_root()
                self.roots.append(current_root)
                record_size_counter = 0  # reset counter
            record_size_counter += 1
            current_root.append(record)

        return self.roots

    def map_ldap_record(self, ldap_record):
        """Map LDAP record to MARC 21 authority record (XML).

        :return: record element
        """
        record = self._create_record()
        # map each attribute for one record
        for attr_key in self.mapper_dict.keys():
            marc_id = self.mapper_dict[attr_key]
            marc_tag, marc_ind1, marc_ind2, marc_code = \
                self._split_marc_id(marc_id)

            # in case `attr_key` doesn't exist in the LDAP record
            try:
                # type(value of attribute): list
                inner_text = ldap_record[attr_key][0]  # always 1 element only
                # inner_text = self._strip(ldap_record[attr_key])
                elem_datafield = self._create_datafield(
                    record, marc_tag, marc_ind1, marc_ind2)

                # add prefixes for specific codes
                if marc_id == "035__a":
                    inner_text = "AUTHOR|(SzGeCERN){0}".format(inner_text)

                if marc_code:
                    self._create_subfield(
                        elem_datafield, marc_code, inner_text)
            except:
                pass

        return record

    def map_ldap_records(self, ldap_records):
        """Map LDAP records to MARC 21 authority records (XML).

        :return: list of record elements
        """
        for record in ldap_records:
            self.records.append(self.map_ldap_record(record))

        return self.records

    def update_ldap_records(self, records):
        """Update LDAP record and add a controlfield if needed.

        :param tuple records: (status, record), where status is 'add',
            'remove', or 'change'
        :return: list of record elements
        """
        for record in records:
            r = self.map_ldap_record(record[1])
            prefix = "AUTHOR|(SzGeCERN)"
            employeeID = record[1]["employeeID"][0]
            result = search_pattern(
                p='035__:{0}{1}'.format(prefix, employeeID))
            if len(result) == 1:
                self._create_controlfield(r, "001")
            self.records.append(r)

        return self.records

    def write_marcxml(
      self, record_size=500, file="marc_output.xml"):
        """Write the XML tree to (multiple) file(s). Each XML file contains
        one root element (default 'collection') containing record_size
        record elements.

        :param int record_size: record child elements in a root node,
            if <= 0: append all records to one root node
        :param str file: filename, suffix ('_000', '_001', ...) will be added
        """
        filename, file_extension = os.path.splitext(file)
        self._attach_records(record_size)

        # single file ouput, without suffix
        if record_size <= 0:
            with open("{0}.xml".format(filename), "w") as f:
                f.write(etree.tostring(self.roots[0], pretty_print=True))
        # (multiple) file output
        else:
            for i, root in enumerate(self.roots):
                with open("{0}_{1}.xml".format(
                  filename, format(i, "03d")), "w") as f:
                    f.write(etree.tostring(root, pretty_print=True))
