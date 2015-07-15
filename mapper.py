from lxml import etree
from collections import OrderedDict


class Mapper:
    """Map LDAP records to MARC 21 authority records in XML sctructure.
    MARC 21 authority reference: http://www.loc.gov/marc/authority/"""
    def __init__(self, record_size=500):
        """Initialize the mapper properties."""
        self.roots = []  # contains all root elements
        self.record_size = record_size  # defines amount of record elements in one root
        self.mapper_dict = {
            "givenName": "100__a",
            "sn": "1101_b",
            "mail": "300__a",
            "displayName": "100__x",
            "employeeID": "035__a"
        }

    def _strip(self, obj):
        """Strip the property string and return it. Using the default strip function."""
        return str(obj).strip("['']")

    def _split_marc_id(self, marc_id):
        """Seperate marc identifier which is defined in the mapper
        dictionary. Return tag, ind1, ind2 and code."""
        return marc_id[:3], marc_id[3], marc_id[4], marc_id[-1:]

    def _add_root(self):
        """Add the root element `collection` with the attribute `xmlns`.
        Append it to the roots list."""
        self.root = etree.Element(
            "collection", {"xmlns": "http://www.loc.gov/MARC21/slim"})
        self.roots.append(self.root)

    def _add_record(self):
        """Add sub element `record` to the root element."""
        return etree.SubElement(self.root, "record")

    def _add_controlfield(self, attr_tag, text):
        """Add sub element `controlfield` to the root element."""
        etree.SubElement(self.root, "controlfield", {
            "tag": attr_tag}).text = text

    def _add_datafield(
      self, attr_tag, attr_ind1, attr_ind2):
        """Add datafield element as a sub element to the record element and
        return it. In case a datafield with the same tag exists, the existing
        one will be returned."""
        if attr_ind1 == "_":
            attr_ind1 = " "
        if attr_ind2 == "_":
            attr_ind2 = " "

        find = self.record.xpath("datafield[@tag=%s]" % attr_tag)
        if not find:
            return etree.SubElement(self.record, "datafield", OrderedDict({
                "tag": attr_tag, "ind1": attr_ind1, "ind2": attr_ind2}))
        return find[0]

    def _add_subfield(self, elem_datafield, attr_code, text):
        """Add child element 'subfield' to the datafield with attributes and
        inner text."""
        etree.SubElement(elem_datafield, "subfield", {
            "code": attr_code}).text = text

    def map_ldap_records(self, ldap_records):
        """Map LDAP records to Marc 21 XML sctructure (XML tree) and return root node.
        Example LDAP record: ('CN=joklein,OU=Users,OU=Organic Units,DC=cern,DC=ch',
            {'mail': ['j.klein@cern.ch'], 'givenName': ['Jochen'], 'displayName': ['Jochen Klein'], 'sn': ['Klein']})"""
        self._add_root()
        record_size_counter = 0

        for record in ldap_records:
            if record_size_counter == self.record_size:
                self._add_root()
                record_size_counter = 0  # reset counter
            record_size_counter += 1
            self.record = self._add_record()
            for attr_key in self.mapper_dict.keys():
                marc_id = self.mapper_dict[attr_key]
                marc_tag, marc_ind1, marc_ind2, marc_code = self._split_marc_id(marc_id)
                inner_text = self._strip(record[1][attr_key])
                elem_datafield = self._add_datafield(
                    marc_tag, marc_ind1, marc_ind2)

                # add prefixes for specific codes
                if marc_id == "035__a":
                    inner_text = "AUTHOR|(SzGeCERN)%s" % inner_text

                if not marc_code == "_":
                    self._add_subfield(elem_datafield, marc_code, inner_text)
        return self.root

    def write_marcxml(self, root_node=None):
        """Write the XML tree to file(s)."""
        if not root_node:
            root_node = self.root
        for i, root in enumerate(self.roots):
            with open("marc_output_%03d.xml" % (i,), "w") as f:
                f.write(etree.tostring(root, pretty_print=True))
