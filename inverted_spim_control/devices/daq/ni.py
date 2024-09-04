from voxel.devices.daq.ni import DAQ as VoxelDaq
from inverted_spim_control.devices.daq.base import BaseDAQ
import nidaqmx

class DAQ(BaseDAQ, VoxelDaq):

    @property
    def pulse_count(self):
        """Return count of ci task"""
        if self.ci_task is not None:
            return self.ci_task.read()