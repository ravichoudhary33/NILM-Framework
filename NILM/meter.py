# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import os
from measurements import Measurements
from events import Events
from clusters import Clusters
from appliance_models import ApplianceModels
from appliance_behaviors import ApplianceBehaviors


class Store(object):

    def __init__(self, filename=None, key=None):
        self.filename = str(filename)
        self.key = str(key)

    def __repr__(self):
        return self.__dict__.__repr__()


class Meter(object):

    def __init__(self, metadata=None, phases=None, power_types=None,
                 store=None, ID=None):
        self.phases = phases
        self.metadata = metadata
        self.power_types = power_types
        self.store = store
        self.ID = ID

    @staticmethod
    def from_user(user, meter_ID):
        assert meter_ID in user.meters_ID
        metadata = user.metadata['meters'][meter_ID]

        measurements = metadata['measurements']
        phases = measurements['phases']
        power_types = measurements['power_types']

        key = "/".join((meter_ID, 'measurements'))
        store = Store(user.filename, key)

        meter = Meter(metadata, phases, power_types, store, meter_ID)
        return meter

    @staticmethod
    def from_meter_hdf(hdf_filename):
        assert os.path.isfile(hdf_filename)
        with pd.get_store(hdf_filename) as store:
            metadata = store.root._v_attrs.metadata
        
        meter_ID = hdf_filename.split('/')[-1]
        phases = list(metadata['phases'])
        power_types = list(metadata['power_types'])

        key = 'measurements'
        store = Store(hdf_filename, key)
        meter = Meter(metadata, phases, power_types, store, meter_ID)
        return meter

    def __repr__(self):
        return str(self.ID)

    def load_measurements(self, sampling_period=1):
        """
        Load the measurments in a pd.DataFrame. The elapsed time between each
        sample is given by sampling_period in seconds
        """
        self.measurements.load_data(sampling_period)
        self.state['data_loaded'] = True
        self.state['sampling'] = '{:d}s'.format(sampling_period)

    def detect_events(self, detection_type='steady_states', **kwargs):
        assert self.state["data_loaded"]
        self.events.detection(detection_type, **kwargs)
        self.state['event_detected'] = True
        self.state['detection_type'] = detection_type

    def cluster_events(self, clustering_type='DBSCAN', phases_separation=True,
                       features=None, **clustering_parameters):
        assert self.state['event_detected']
        self.clusters = Clusters(self, clustering_type,
                                 phases_separation=self.phase_by_phase,
                                 features=None, **clustering_parameters)

        self.clusters.clustering()
        self.state['clustering'] = True

    def model_appliances(self, modeling_type='simple',
                         **modeling_parameters):
        try:
            self.clusters
        except AttributeError:
            raise AttributeError('Meter: cluster first the events!')
        self.appliance_models = ApplianceModels(modeling_type,
                                                **modeling_parameters)
        self.appliance_models.modeling(self)

    def track_behaviors(self):
        try:
            self.appliance_models
        except AttributeError:
            raise AttributeError('Meter: model first the appliances!')
        self.appliance_behaviors = ApplianceBehaviors()
        self.appliance_behaviors.tracking(self)
        

if __name__ == '__main_s_':
    from utils.tools import create_user
    user1 = create_user()
    meter1_name = user1.metadata['meters'].keys()[0]
    meter1 = Meter(user1, meter1_name)
    meter1.load_measurements(sampling_period=1)
    meter1.detect_events(detection_type='steady_states', edge_threshold=100)
    meter1.cluster_events(clustering_type='DBSCAN', phases_separation=True,
                          features=None, eps=35)
    meter1.model_appliances(modeling_type='simple')
    meter1.track_behaviors()
    for phase, appliance in meter1.appliance_behaviors.columns:
        print appliance
        meter1.measurements[phase][meter1.power_types[0]].plot()
        meter1.appliance_behaviors[phase][appliance].plot(color='r')
        plt.show()
        
        
