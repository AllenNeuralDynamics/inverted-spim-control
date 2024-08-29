
from view.acquisition_view import AcquisitionView
import numpy as np
import skimage.measure
from qtpy.QtCore import Slot, Signal
from datetime import datetime


class InvertedSPIMAcquisitionView(AcquisitionView):
    """View for Inverted SPIM Acquisition"""

    acquisitionEnded = Signal()
    acquisitionStarted = Signal((datetime))


    def start_acquisition(self):
        """Overwrite to emit acquisitionStarted signal"""

        super().start_acquisition()
        self.acquisitionStarted.emit(datetime.now())

    def acquisition_ended(self):
        """Overwrite to emit acquisitionEnded signal """
        super().acquisition_ended()
        self.acquisitionEnded.emit()
