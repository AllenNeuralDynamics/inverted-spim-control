from qtpy.QtWidgets import QApplication
import sys
from pathlib import Path, WindowsPath
import os
import numpy as np
from ruamel.yaml import YAML
from inverted_spim_control.metadata_launch import MetadataLaunch
from inverted_spim_control.inverted_spim_view import InvertedSPIMAcquisitionView
from view.instrument_view import InstrumentView
from voxel.instruments.instrument import Instrument
from inverted_spim_control.inverted_spim_acquisition import InvertedSPIMAcquisition

RESOURCES_DIR = (Path(os.path.dirname(os.path.realpath(__file__))))
ACQUISITION_YAML = RESOURCES_DIR / 'acquisition.yaml'
INSTRUMENT_YAML = RESOURCES_DIR / 'instrument.yaml'
GUI_YAML = RESOURCES_DIR / 'gui_config.yaml'

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # create yaml handler
    yaml = YAML()
    yaml.representer.add_representer(np.int32, lambda obj, val: obj.represent_int(int(val)))
    yaml.representer.add_representer(np.str_, lambda obj, val: obj.represent_str(str(val)))
    yaml.representer.add_representer(np.float64, lambda obj, val: obj.represent_float(float(val)))
    yaml.representer.add_representer(Path, lambda obj, val: obj.represent_str(str(val)))
    yaml.representer.add_representer(WindowsPath, lambda obj, val: obj.represent_str(str(val)))

    # instrument
    instrument = Instrument(config_path=INSTRUMENT_YAML,
                            yaml_handler=yaml,
                            log_level='INFO')
    # acquisition_widgets
    acquisition = InvertedSPIMAcquisition(instrument=instrument,
                                          config_filename=ACQUISITION_YAML,
                                          yaml_handler=yaml,
                                          log_level='INFO')
    instrument_view = InstrumentView(instrument, GUI_YAML, log_level='INFO')
    acquisition_view = InvertedSPIMAcquisitionView(acquisition, instrument_view)

    MetadataLaunch(instrument=instrument,
                   acquisition=acquisition,
                   instrument_view=instrument_view,
                   acquisition_view=acquisition_view)

    sys.exit(app.exec_())
