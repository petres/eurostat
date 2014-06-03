import collections

from .xmlcommon import inner_text, parse_xml


def reader(fileobj):
    tree = parse_xml(fileobj)
    
    reader = DsdReader(tree)
    
    concepts = _read_concepts(reader)
    code_lists = _read_code_lists(reader)
    key_families = _read_key_families(reader)
    return Dsd(concepts, code_lists, key_families)
    

def _read_concepts(reader):
    return reader.concepts()


def _read_code_lists(reader):
    return reader.code_lists()


def _read_key_families(reader):
    return reader.key_families()


class Dsd(object):
    def __init__(self, concepts, code_lists, key_families):
        self._concepts = concepts
        self._concept_lookup = dict(
            (concept.id, concept)
            for concept in concepts
        )
        self._code_lists = code_lists
        self._code_list_lookup = dict(
            (code_list.id, code_list)
            for code_list in code_lists
        )
        self._key_families = key_families
    
    def concepts(self):
        return self._concepts
    
    def concept(self, id):
        return self._concept_lookup.get(id)
    
    def code_lists(self):
        return self._code_lists
    
    def code_list(self, id):
        return self._code_list_lookup.get(id)
    
    def key_families(self):
        return self._key_families


Concept = collections.namedtuple("Concept", [])


class DsdReader(object):
    _concept_path = "//".join([
        "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message}Concepts",
        "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}Concept",
    ])
    
    _code_list_path = "/".join([
        "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message}CodeLists",
        "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}CodeList",
    ])
    
    def __init__(self, tree):
        self._tree = tree
    
    def concepts(self):
        concept_elements = self._tree.findall(self._concept_path)
        return map(self._read_concept_element, concept_elements)
    
    def _read_concept_element(self, concept_element):
        return Concept(concept_element.get("id"), _read_names(concept_element))
    
    def code_lists(self):
        elements = self._tree.findall(self._code_list_path)
        return map(self._read_code_list_element, elements)
    
    def _read_code_list_element(self, element):
        return CodeList(element.get("id"), _read_names(element), _read_codes(element))

    def key_families(self):
        path = [
            "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message}KeyFamilies",
            "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}KeyFamily",
        ]
        elements = self._tree.findall("/".join(path))
        return map(self._read_key_family_element, elements)
    
    def _read_key_family_element(self, element):
        return KeyFamily(
            element.get("id"),
            names=_read_names(element),
            dimensions=self._read_dimensions(element),
            time_dimension=self._read_time_dimension(element),
            primary_measure=self._read_primary_measure(element),
        )
    
    def _read_dimensions(self, element):
        path = self._dimension_path("Dimension")
        elements = element.findall(path)
        return map(self._read_dimension_element, elements)

    def _read_time_dimension(self, element):
        path = self._dimension_path("TimeDimension")
        return self._read_dimension_element(element.find(path))
        
    def _read_primary_measure(self, element):
        path = self._dimension_path("PrimaryMeasure")
        return self._read_dimension_element(element.find(path))
    
    def _dimension_path(self, name):
        return "/".join([
            "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}Components",
            "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}" + name,
        ])

    def _read_dimension_element(self, element):
        if element is None:
            return None
        else:
            return KeyFamilyDimension(
                concept_ref=element.get("conceptRef"),
                code_list_id=element.get("codelist"),
            )
        

class Concept(object):
    def __init__(self, id, names_by_lang):
        self.id = id
        self._names_by_lang = names_by_lang

    def name(self, lang):
        return self._names_by_lang[lang]


class CodeList(object):
    def __init__(self, id, names_by_lang, codes):
        self.id = id
        self._names_by_lang = names_by_lang
        self._codes = codes
        self._codes_by_value = dict(
            (code.value, code)
            for code in codes
        )
    
    def name(self, lang):
        return self._names_by_lang[lang]
        
    def codes(self):
        return self._codes
    
    def code(self, value):
        return self._codes_by_value.get(value)

        
class Code(object):
    def __init__(self, value, parent_code_id, descriptions):
        self.value = value
        self._parent_code_id = parent_code_id
        self._descriptions = descriptions
    
    def parent_code_id(self):
        return self._parent_code_id
    
    def description(self, lang):
        return self._descriptions[lang]


class KeyFamily(object):
    def __init__(self, id, names, dimensions, time_dimension, primary_measure):
        self.id = id
        self._names = names
        self._dimensions = dimensions
        self._time_dimension = time_dimension
        self._primary_measure = primary_measure
    
    def name(self, lang):
        return self._names[lang]
    
    def dimensions(self):
        return self._dimensions
    
    def time_dimension(self):
        return self._time_dimension
    
    def primary_measure(self):
        return self._primary_measure


class KeyFamilyDimension(object):
    def __init__(self, concept_ref, code_list_id):
        self._concept_ref = concept_ref
        self._code_list_id = code_list_id
    
    def concept_ref(self):
        return self._concept_ref
    
    def code_list_id(self):
        return self._code_list_id


def _read_names(element):
    tag_name = "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}Name"
    return _read_elements_with_lang(element, tag_name)


_code_path = "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}Code"

def _read_codes(code_list_element):
    return [
        _read_code_element(code_element)
        for code_element in code_list_element.findall(_code_path)
    ]
        

def _read_code_element(code_element):
    return Code(
        value=code_element.get("value"),
        parent_code_id=code_element.get("parentCode") or None,
        descriptions=_read_descriptions(code_element),
    )

def _read_descriptions(element):
    tag_name = "{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/structure}Description"
    return _read_elements_with_lang(element, tag_name)


def _read_elements_with_lang(element, path):
    return dict(
        (match.get("{http://www.w3.org/XML/1998/namespace}lang"), inner_text(match).strip())
        for match in element.findall(path)
    )
    
