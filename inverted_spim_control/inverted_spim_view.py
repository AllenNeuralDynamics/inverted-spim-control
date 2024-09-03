from view.acquisition_view import AcquisitionView
from qtpy.QtCore import Signal, Qt
from datetime import datetime
from qtpy.QtWidgets import QGridLayout, QWidget, QSizePolicy, QSplitter, QHBoxLayout, QFrame
from view.widgets.acquisition_widgets.channel_plan_widget import ChannelPlanWidget
from view.widgets.base_device_widget import create_widget
from inverted_spim_control.widgets.acquisition_widgets.inverted_volume_model import InvertedVolumeModel
from inverted_spim_control.widgets.acquisition_widgets.inverted_volume_plan_widget import InvertedVolumePlanWidget


class InvertedSPIMAcquisitionView(AcquisitionView):
    """View for Inverted SPIM Acquisition"""

    acquisitionEnded = Signal()
    acquisitionStarted = Signal((datetime))

    def create_acquisition_widget(self):
        """Overwrite to use custom VolumeModel and VolumePlan"""

        # find limits of all axes
        lim_dict = {}
        # add tiling stages
        for name, stage in self.instrument.tiling_stages.items():
            lim_dict.update({f'{stage.instrument_axis}': stage.limits_mm})
        # last axis should be scanning axis
        (scan_name, scan_stage), = self.instrument.scanning_stages.items()
        lim_dict.update({f'{scan_stage.instrument_axis}': scan_stage.limits_mm})
        try:
            limits = [lim_dict[x.strip('-')] for x in self.coordinate_plane]
        except KeyError:
            raise KeyError('Coordinate plane must match instrument axes in tiling_stages')

        fov_dimensions = self.config['acquisition_view']['fov_dimensions']
        crossing_angle = self.config['acquisition_view']['crossing_angle']
        acquisition_widget = QSplitter(Qt.Vertical)
        acquisition_widget.setChildrenCollapsible(False)

        # create volume plan
        self.volume_plan = InvertedVolumePlanWidget(crossing_angle=crossing_angle,
                                                    limits=limits,
                                                    fov_dimensions=fov_dimensions,
                                                    coordinate_plane=self.coordinate_plane,
                                                    unit=self.unit,
                                                    )
        self.volume_plan.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)

        # create volume model
        self.volume_model = InvertedVolumeModel(crossing_angle=crossing_angle,
                                                limits=limits,
                                                fov_dimensions=fov_dimensions,
                                                coordinate_plane=self.coordinate_plane,
                                                unit=self.unit,
                                                **self.config['acquisition_view']['acquisition_widgets'].get(
                                                    'volume_model', {}).get('init', {}))
        # combine floating volume_model widget with glwindow
        combined_layout = QGridLayout()
        combined_layout.addWidget(self.volume_model, 0, 0, 3, 1)
        combined_layout.addWidget(self.volume_model.widgets, 3, 0, 1, 1)
        combined = QWidget()
        combined.setLayout(combined_layout)
        acquisition_widget.addWidget(create_widget('H', self.volume_plan, combined))

        # create channel plan
        self.channel_plan = ChannelPlanWidget(instrument_view=self.instrument_view,
                                              channels=self.instrument.config['instrument']['channels'],
                                              unit=self.unit,
                                              **self.config['acquisition_view']['acquisition_widgets'].get(
                                                  'channel_plan', {}).get('init', {}))
        # place volume_plan.tile_table and channel plan table side by side
        table_splitter = QSplitter(Qt.Horizontal)
        table_splitter.setChildrenCollapsible(False)
        table_splitter.setHandleWidth(20)

        widget = QWidget()  # dummy widget to move tile_table down in layout
        widget.setMinimumHeight(25)
        table_splitter.addWidget(create_widget('V', widget, self.volume_plan.tile_table))
        table_splitter.addWidget(self.channel_plan)

        # format splitter handle. Must do after all widgets are added
        handle = table_splitter.handle(1)
        handle_layout = QHBoxLayout(handle)
        line = QFrame(handle)
        line.setStyleSheet('QFrame {border: 1px dotted grey;}')
        line.setFixedHeight(50)
        line.setFrameShape(QFrame.VLine)
        handle_layout.addWidget(line)

        # add tables to layout
        acquisition_widget.addWidget(table_splitter)

        # connect signals
        self.instrument_view.snapshotTaken.connect(self.volume_model.add_fov_image)  # connect snapshot signal
        self.instrument_view.contrastChanged.connect(
            self.volume_model.adjust_glimage_contrast)  # connect snapshot adjusted
        self.volume_model.fovHalt.connect(self.stop_stage)  # stop stage if halt button is pressed
        self.volume_model.fovMove.connect(self.move_stage)  # move stage to clicked coords
        self.volume_plan.valueChanged.connect(self.volume_plan_changed)
        self.channel_plan.channelAdded.connect(self.channel_plan_changed)
        self.channel_plan.channelChanged.connect(self.update_tiles)

        # TODO: This feels like a clunky connection. Works for now but could probably be improved
        self.volume_plan.header.startChanged.connect(lambda i: self.create_tile_list())
        self.volume_plan.header.stopChanged.connect(lambda i: self.create_tile_list())

        return acquisition_widget

    def start_acquisition(self):
        """Overwrite to emit acquisitionStarted signal"""

        super().start_acquisition()
        self.acquisitionStarted.emit(datetime.now())

    def acquisition_ended(self):
        """Overwrite to emit acquisitionEnded signal """
        super().acquisition_ended()
        self.acquisitionEnded.emit()
