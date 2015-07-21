from collections import OrderedDict
from config import CFG_AUTHOR_CERN
from datetime import date
from lxml import etree
from os import makedirs
from os.path import dirname, exists, splitext


class MapperError(Exception):

    """Base class for exceptions in this module."""

    pass


class Mapper:

    """Map CERN LDAP records to MARC 21 authority records (MARCXML).

    MARC 21 authority reference: http://www.loc.gov/marc/authority/
    """

    def __init__(self):
        """Initialize the mapper properties."""
        self.roots = []  # Contain all root elements
        self.records = []  # Contain all (mapped) MARC records
        # Mapping rules: LDAP attributes to MARC 21 authority
        # LDAP attributes used in config.CFG_LDAP_ATTRLIST
        self.mapper_dict = {
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
            "extensionAttribute11": "371__1"
        }

    def _split_marc_id(self, marc_id):
        """Split MARC 21 identifier which is defined in the mapper_dict.

        :param string marc_id: format: fffiis,
            f = Field Code (code);
            i = First Indicator (ind1), Second Indicator (ind2);
            s = Subfield Codes (subfield_code, optional)
        :return: code, ind1, ind2, and subfield_code
        """
        try:
            subfield_code = marc_id[5]
        except IndexError:
            subfield_code = None

        return marc_id[:3], marc_id[3], marc_id[4], subfield_code

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
            elem_record = etree.SubElement(parent, "record")
        else:
            elem_record = etree.Element("record")
        return elem_record

    def _create_controlfield(self, parent, attr_code, inner_text=None):
        """Create child element 'controlfield' of parent.

        :param elem parent: parent element, usually 'collection'
        :param string attr_code: value for attribute 'code'
        :param string inner_text: inner text of element
        :return: controlfield element, child of parent
        """
        controlfield = etree.SubElement(parent, "controlfield", {
            "tag": attr_code})
        if inner_text:
            controlfield.text = inner_text
        return controlfield

    def _create_datafield(
            self, parent, attr_code, attr_ind1=" ", attr_ind2=" ",
            repeatable=False):
        """Create child element 'datafield' of parent.

        :param elem parent: parent element, usually 'record'
        :param bool repeatable: allows multiple datafields with same codes
        :return: either new or existing datafield element (depending on
            repeatable), child of parent
        """
        if attr_ind1 == "_":
            attr_ind1 = " "
        if attr_ind2 == "_":
            attr_ind2 = " "

        # If attr_ind1 or attr_ind2 is alpha, make upper case
        if attr_ind1.isalpha():
            attr_ind1 = attr_ind1.upper()

        if attr_ind2.isalpha():
            attr_ind2 = attr_ind2.upper()

        find = parent.xpath(
            "datafield[@tag={0} and @ind1='{1}' and @ind2='{2}']".format(
                attr_code, attr_ind1, attr_ind2))
        if not find or repeatable:
            elem_datafield = etree.SubElement(
                parent,
                "datafield",
                OrderedDict({
                    "tag": attr_code, "ind1": attr_ind1, "ind2": attr_ind2}))
        else:
            elem_datafield = find[0]

        return elem_datafield

    def _create_subfield(self, parent, attr_code, inner_text):
        """Create child element 'subfield' of parent.

        :param elem parent: parent element
        :param string attr_code: value for attribute 'code'
        :param string inner_text: inner text of element
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
        # Append all record elements to one root element
        if record_size <= 0:
            record_size = -1

        # Append records to root element(s) depending on record_size
        if self.records:
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

    def map_ldap_record(self, record):
        """Map LDAP record to MARC 21 authority record (XML).

        :param dictionary record: LDAP record (result-data)
        :param filepath file: look up Inspire-ID at
            ATLAS GLANCE (False) or local directory (True)
        :return: record element
        """
        elem_record = self._create_record()

        # Map each LDAP attribute for one record
        for attr_key in self.mapper_dict.keys():
            marc_id = self.mapper_dict.get(attr_key)
            marc_code, marc_ind1, marc_ind2, marc_subfield_code = \
                self._split_marc_id(marc_id)

            value = record.get(attr_key)
            if value:
                value = value[0]

                elem_datafield = self._create_datafield(
                    elem_record, marc_code, marc_ind1, marc_ind2)

                # Add prefix for employeeID
                if attr_key is "employeeID":
                    value = "{0}{1}".format(
                        CFG_AUTHOR_CERN, value)
                # Add subfield to datafield if marc_code exists
                if marc_code:
                    self._create_subfield(
                        elem_datafield, marc_subfield_code, value)

        # Additional repeatable datafields for collections
        self._create_subfield(
            self._create_datafield(elem_record, "371"),
            "v",
            "CERN LDAP")

        self._create_subfield(
            self._create_datafield(elem_record, "690", "C", repeatable=True),
            "a",
            "CERN")

        self._create_subfield(
            self._create_datafield(elem_record, "980", repeatable=True),
            "a",
            "PEOPLE")

        self._create_subfield(
            self._create_datafield(elem_record, "980", repeatable=True),
            "a",
            "AUTHORITY")

        return elem_record

    def map_ldap_records(self, records):
        """Map LDAP records.

        :param list records: list of LDAP records (result-data)
        :return: list of record elements
        """
        for record in records:
            self.records.append(self.map_ldap_record(record))

        return self.records

    def update_ldap_records(self, records):
        """Map updated LDAP records.

        :param list records: list of tuples (status, record), where status is
            'add', 'remove', or 'change'
        :return: list of record XML elements
        """
        for record in records:
            r = self.map_ldap_record(record[1])

            # Add datafields for removed records
            if record[0] is "remove":
                self._create_subfield(
                    self._create_datafield(r, "595", repeatable=True),
                    "a",
                    "REMOVED FROM SOURCE")
                self._create_subfield(
                    self._create_datafield(r, "595", repeatable=True),
                    "c",
                    date.today().strftime("%Y-%m-%d"))
            self.records.append(r)

        return self.records

    def _write_xml(self, tree, xml_file):
        """Write tree to XML file.

        :param etree tree: XML tree to write
        :param filepath xml_file: XML file to write to
        """
        try:
            with open(xml_file, "w") as f:
                f.write(tree)
        except EnvironmentError as e:
            raise MapperError("Error: failed writing file. ({0})".format(e))

    def write_marcxml(self, xml_file, record_size=500):
        """Prepare to write self.roots to a single file or multiple files.

        :param int record_size: record elements in a root node [default: 500],
            if <= 0: append all records to one root node
        :param filepath xml_file: save to file,
            suffix ('_0', '_1', ...) will be added to file name
        """
        directory = dirname(xml_file)
        if directory is not "" and not exists(directory):
            makedirs(directory)

        self._attach_records(record_size)

        try:
            # Write single file
            if record_size <= 0:
                self._write_xml(
                    etree.tostring(
                        self.roots[0], encoding='utf-8', pretty_print=True),
                    xml_file)
            # Write multiple files
            else:
                filename, ext = splitext(xml_file)
                for i, root in enumerate(self.roots):
                    f = "{0}_{1}{2}".format(filename, i, ext)
                    self._write_xml(
                        etree.tostring(
                            root, encoding='utf-8', pretty_print=True),
                        f)
        except MapperError:
            raise
