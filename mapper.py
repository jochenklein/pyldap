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

    def _strip(self, obj):
        """Strip the property string and return it.
        Using the default strip function.
        """
        return str(obj).strip("['']")

    def _split_marc_id(self, marc_id):
        """Seperate MARC 21 identifier which is defined in the mapper_dict.
        Return tag, ind1, ind2 and code.
        """
        # MARC code is optional
        try:
            marc_code = marc_id[5]
        except IndexError:
            marc_code = None

        return marc_id[:3], marc_id[3], marc_id[4], marc_code

    def _create_root(self):
        """Create root element 'collection' with the attribute 'xmlns' and
        return it.
        """
        return etree.Element(
            "collection", {"xmlns": "http://www.loc.gov/MARC21/slim"})

    def _create_record(self, parent):
        """Create child element 'record' of parent, and return it."""
        return etree.SubElement(parent, "record")

    def _create_controlfield(self, parent, attr_tag, inner_text):
        """Create child element 'controlfield' of parent and return it.

        :param elem parent: parent element, usually 'collection'
        """
        controlfield = etree.SubElement(parent, "controlfield", {
            "tag": attr_tag})
        controlfield.text = inner_text
        return controlfield

    def _create_datafield(
      self, parent, attr_tag, attr_ind1, attr_ind2, repeatable=False):
        """Create child element 'datafield', add it to the record element and
        return it.

        :param elem parent: parent element, usually 'record'
        :param bool repeatable: Allows multiple datafields with same tags
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
        attr_code and inner_text, and return it.
        """
        subfield = etree.SubElement(
            parent, "subfield", {"code": attr_code})
        subfield.text = inner_text
        return subfield

    def map_ldap_records(self, ldap_records):
        """Map LDAP records to MARC 21 authority records (XML).
        Return the list of root elements.
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
        """Write the XML tree to file(s)."""
        filename, file_extension = os.path.splitext(file)

        # multiple file output
        for i, root in enumerate(self.roots):
            with open("%s_%03d.xml" % (filename, i), "w") as f:
                f.write(etree.tostring(root, pretty_print=True))
