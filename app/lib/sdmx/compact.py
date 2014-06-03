import functools

from .dataset import data_message_reader, Observation


class CompactDataMessageParser(object):
    def get_dataset_elements(self, message_element):
        return _children_with_local_name(message_element, "DataSet")
        
    def key_family_for_dataset(self, dataset_element, dsd_reader):
        # Assume a single key family
        key_family, = dsd_reader.key_families()
        return key_family
    
    def get_series_elements(self, dataset_element):
        return [
            (element, self._series_key(element))
            for element in _children_with_local_name(dataset_element, "Series")
        ]
            
        
    def _series_key(self, series_element):
        return series_element.attributes()
        
    def read_observations(self, key_family, series_element):
        return map(
            lambda element: self._read_obs_element(key_family, element),
            _children_with_local_name(series_element, "Obs"),
        )
        
    def _read_obs_element(self, key_family, obs_element):
        time = obs_element.get(key_family.time_dimension().concept_ref())
        value = obs_element.get(key_family.primary_measure().concept_ref())
        return Observation(time, value)


def _children_with_local_name(parent, local_name):
    # Ignore the namespace since it's dataset dependent
    # The alternative is to use the SDMX converter to convert to a Generic
    # Data Message, but the source code appears to indicate they also ignore
    # namespace
    for element in parent.children():
        if element.local_name() == local_name:
            yield element


compact_data_message_reader = functools.partial(data_message_reader, CompactDataMessageParser())
