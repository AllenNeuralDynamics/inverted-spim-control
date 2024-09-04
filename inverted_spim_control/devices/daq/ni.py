from voxel.devices.daq.ni import DAQ as VoxelDaq
from inverted_spim_control.devices.daq.base import BaseDAQ
import nidaqmx

class DAQ(BaseDAQ, VoxelDaq):

    def __init__(self, ci_chan, *args, **kwargs):

        super(VoxelDaq).__init__(*args, *kwargs)
        super(BaseDAQ).__init__()

        self.ci_physical_chans = self.dev.ci_physical_chans.channel_names

        # set up counter input task
        counter_task = nidaqmx.Task("counter_task")
        self.counter_input_task = counter_task.ci_channels.add_ci_count_edges_chan(f'/{self.id}/{ci_chan}',
                                                                                  edge=nidaqmx.constants.Edge.RISING)

    def add_task(self, task_type: str, pulse_count=None):
        """If ao task is added, set counter input to count edges of trigger"""
        super(VoxelDaq).add_task(task_type, pulse_count)

        if task_type == 'ao':
            self.counter_input_task.ci_count_edges_term = f"/{self.id}/{self.input_trigger_name}"


    @property
    def pulse_count(self):
