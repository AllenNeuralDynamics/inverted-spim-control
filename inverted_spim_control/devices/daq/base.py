from voxel.devices.daq.base import BaseDAQ as Base


class BaseDAQ(Base):

    @property
    def pulse_count(self):
        """Returns number of pulses emitted by stage"""
