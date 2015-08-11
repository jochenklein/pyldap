from lxml import etree
from collections import OrderedDict
import os


class Mapper:
    """Map LDAP records to MARC 21 authority records in XML sctructure.
    MARC 21 authority reference: http://www.loc.gov/marc/authority/
    """
    def __init__(self, record_size=500):
        """Initialize the mapper properties."""
        self.roots = []  # contain all root elements
        self.record_size = record_size  # amount of record elements in root
        self.mapper_dict = {  # mapping definition LDAP to MARC 21 authority
            "givenName": "1000_a",
            "sn": "1001_a",
            "displayName": "100__a",
            "mail": "371__m",
            "employeeID": "035__a"
        }

    def _strip(self, obj, strip="['']"):
        """Using the default strip function.

        :return: stripped string
        """
        return str(obj).strip(strip)

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

    def _create_record(self, parent):
        """Create child element 'record' of parent.

        :return: record element, child of parent
        """
        return etree.SubElement(parent, "record")

    def _create_controlfield(self, parent, attr_tag, inner_text):
        """Create child element 'controlfield' of parent.

        :param elem parent: parent element, usually 'collection'
        :return: controlfield element, child of parent
        """
        controlfield = etree.SubElement(parent, "controlfield", {
            "tag": attr_tag})
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
            "datafield[@tag=%s and @ind1='%s' and @ind2='%s']"
            % (attr_tag, attr_ind1, attr_ind2))
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

    def map_ldap_records(self, ldap_records):
        """Map LDAP records to MARC 21 authority records (XML).

        :return: list of root elements containg N record elements,
            N = record_size
        """
        current_root = self._create_root()
        self.roots.append(current_root)
        record_size_counter = 0

        for record in ldap_records:
            if record_size_counter == self.record_size:
                current_root = self._create_root()
                self.roots.append(current_root)
                record_size_counter = 0  # reset counter
            record_size_counter += 1
            current_record = self._create_record(current_root)
            for attr_key in self.mapper_dict.keys():
                marc_id = self.mapper_dict[attr_key]
                marc_tag, marc_ind1, marc_ind2, marc_code = \
                    self._split_marc_id(marc_id)

                # in case `attr_key` doesn't exist in the LDAP record
                try:
                    inner_text = self._strip(record[attr_key])
                except:
                    pass

                elem_datafield = self._create_datafield(
                    current_record, marc_tag, marc_ind1, marc_ind2)

                # add prefixes for specific codes
                if marc_id == "035__a":
                    inner_text = "AUTHOR|(SzGeCERN)%s" % inner_text

                if marc_code:
                    self._create_subfield(
                        elem_datafield, marc_code, inner_text)
        return self.roots

    def write_marcxml(self, file="marc_output.xml"):
        """Write the XML tree to (multiple) file(s).

        :param str file: filename, suffix ('_001', '_002', ...) will be added
        """
        filename, file_extension = os.path.splitext(file)

        # multiple file output
        for i, root in enumerate(self.roots):
            with open("%s_%03d.xml" % (filename, i), "w") as f:
                f.write(etree.tostring(root, pretty_print=True))
