import functools
import itertools

from .dataset import data_message_reader, Observation
from . import xmlcommon as xml


class MessageElementTypes(object):
    def _expand(name):
        return "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/message", name
    
    MessageGroup = _expand("MessageGroup")
    DataSet = _expand("DataSet")


class GenericElementTypes(object):
    def _expand(name):
        return "http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic", name
    
    DataSet = _expand("DataSet")
    Group = _expand("Group")
    GroupKey = _expand("GroupKey")
    Series = _expand("Series")
    SeriesKey = _expand("SeriesKey")
    KeyFamilyRef = _expand("KeyFamilyRef")
    Obs = _expand("Obs")
    Value = _expand("Value")
    Time = _expand("Time")
    ObsValue = _expand("ObsValue")



class GenericDataMessageParser(object):
    def get_dataset_elements(self, message_element):
        if message_element.qualified_name() == xml.qualified_name(MessageElementTypes.MessageGroup):
            return message_element.findall(xml.path(GenericElementTypes.DataSet))
        else:
            return message_element.findall(xml.path(MessageElementTypes.DataSet))
        
    def key_family_for_dataset(self, dataset_element, dsd_reader):
        key_family_ref_element = dataset_element.find(xml.path(GenericElementTypes.KeyFamilyRef))
        ref = key_family_ref_element.inner_text().strip()
        key_families = dict(
            (key_family.id, key_family)
            for key_family in dsd_reader.key_families()
        )
        return key_families[ref]
    
    def get_series_elements(self, dataset_element):
        for child in dataset_element.children():
            name = child.qualified_name()
            if name == xml.qualified_name(GenericElementTypes.Group):
                group_key = self._group_key(child)
                for series_element in child.findall(xml.path(GenericElementTypes.Series)):
                    series_key = group_key + self._series_key(series_element)
                    yield series_element, series_key
            
            elif name == xml.qualified_name(GenericElementTypes.Series):
                yield child, self._series_key(child)
        
    def _group_key(self, group_element):
        key_element = group_element.find(xml.path(GenericElementTypes.GroupKey))
        return self._read_key_element(key_element)
        
    def _series_key(self, series_element):
        key_element = series_element.find(xml.path(GenericElementTypes.SeriesKey))
        return self._read_key_element(key_element)
        
    def read_observations(self, key_family, series_element):
        return series_element.map_nodes(
            xml.path(GenericElementTypes.Obs),
            self._read_obs_element,
        )
        
    def _read_key_element(self, key_element):
        key_value_elements = key_element.findall(xml.path(GenericElementTypes.Value))
        
        return [
            (element.get("concept"), element.get("value"))
            for element in key_value_elements
        ]
        
    def _read_obs_element(self, obs_element):
        time_element = obs_element.find(xml.path(GenericElementTypes.Time))
        time = time_element.inner_text()
        value_element = obs_element.find(xml.path(GenericElementTypes.ObsValue))
        value = value_element.get("value")
        return Observation(time, value)


generic_data_message_reader = functools.partial(data_message_reader, GenericDataMessageParser())
