from view.acquisition_view import AcquisitionView
from qtpy.QtCore import Slot, Signal, Qt
from datetime import datetime
from view.widgets.acquisition_widgets.volume_plan_widget import \
    (VolumePlanWidget,
     GridRowsColumns,
     GridFromEdges,
     GridWidthHeight)
from view.widgets.acquisition_widgets.volume_model import VolumeModel
from view.widgets.miscellaneous_widgets.gl_shaded_box_item import GLShadedBoxItem
import numpy as np
from qtpy.QtGui import QMatrix4x4, QVector3D, QQuaternion, QColor
from math import sin, cos, pi, sqrt
from qtpy.QtWidgets import QGridLayout, QWidget, QComboBox, QSizePolicy, QScrollArea, QDockWidget, \
    QLabel, QPushButton, QSplitter, QLineEdit, QSpinBox, QDoubleSpinBox, QProgressBar, QSlider, QApplication, \
    QHBoxLayout, QFrame, QFileDialog, QMessageBox
from view.widgets.acquisition_widgets.channel_plan_widget import ChannelPlanWidget
from view.widgets.base_device_widget import BaseDeviceWidget, scan_for_properties, create_widget, label_maker

class InvertedVolumePlanWidget(VolumePlanWidget):
    """Handle change in overlap value in 2nd tiling direction"""

    def value(self):
        """
        Overwrite to increase overlap in 2nd tiling direction
        """
        over = self.overlap.value()
        common = {
            "reverse": self.reverse.isChecked(),
            "overlap": (over, over),
            "mode": self.order.currentText(),
            "fov_width": self.fov_dimensions[0],
            "fov_height": self.fov_dimensions[1]/np.sqrt(2),
        }
        if self._mode == 'number':
            return GridRowsColumns(
                rows=self.rows.value(),
                columns=self.columns.value(),
                relative_to='center' if self.relative_to.currentText() == 'center' else "top_left",
                **common,
            )
        elif self._mode == 'bounds':
            return GridFromEdges(
                top=self.dim_1_high.value(),
                left=self.dim_0_low.value(),
                bottom=self.dim_1_low.value(),
                right=self.dim_0_high.value(),
                **common,
            )
        elif self._mode == 'area':
            return GridWidthHeight(
                width=self.area_width.value(),
                height=self.area_height.value(),
                relative_to='center' if self.relative_to.currentText() == 'center' else "top_left",
                **common,
            )
        raise NotImplementedError

class InvertedVolumeModel(VolumeModel):
    """Display tiles at 45 degree angle"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fov_view.setSize(x=self.fov_dimensions[0],
                              y=self.fov_dimensions[1] / np.sqrt(2),
                              z=0.0)
        self.fov_view.setTransform(QMatrix4x4(1, 0, 0, self.fov_position[0] * self.polarity[0],
                                              0, 1, 0, self.fov_position[1] * self.polarity[1],
                                              0, sin(pi / 4), cos(pi / 4), self.fov_position[2] * self.polarity[2],
                                              0, 0, 0, 1))

    def update_model(self, attribute_name):
        """Overwrite to display tiles at angle
        :param attribute_name: name of attribute to update"""

        # update color of tiles based on z position
        flat_coords = self.grid_coords.reshape([-1, 3])  # flatten array
        flat_dims = self.scan_volumes.flatten()  # flatten array
        coords = np.concatenate((flat_coords, [[x, y, (z + sz)] for (x, y, z), sz in zip(flat_coords, flat_dims)]))
        extrema = [[min(coords[:, 0]), max(coords[:, 0])],
                   [min(coords[:, 1]), max(coords[:, 1])],
                   [min(coords[:, 2]), max(coords[:, 2])]]

        in_grid = not any(
            [pos > pos_max or pos < pos_min for (pos_min, pos_max), pos in zip(extrema, self.fov_position)])

        if attribute_name == 'fov_position':
            # update fov_pos
            self.fov_view.setTransform(QMatrix4x4(1,0, 0, self.fov_position[0] * self.polarity[0],
                                                  0, 1, 0, self.fov_position[1] * self.polarity[1],
                                                  0, sin(pi/4), cos(pi/4), self.fov_position[2] * self.polarity[2],
                                                  0, 0, 0, 1))

            color = self.grid_box_items[0].color() if len(self.grid_box_items) != 0 else None
            if (not in_grid and color != self.inactive_tile_color) or (in_grid and color != self.active_tile_color):
                new_color = self.inactive_tile_color if not in_grid else self.active_tile_color
                for box in self.grid_box_items:
                    box.setColor(color=new_color)

        else:
            self.fov_view.setSize(x=self.fov_dimensions[0],
                                  y=self.fov_dimensions[1]/np.sqrt(2),
                                  z=0.0)

            # faster to remove every box than parse which ones have changes
            for box in self.grid_box_items:
                self.removeItem(box)
            self.grid_box_items = []

            total_rows = len(self.grid_coords)
            total_columns = len(self.grid_coords[0])

            for row in range(total_rows):
                for column in range(total_columns):

                    coord = [x * pol for x, pol in zip(self.grid_coords[row][column], self.polarity)]
                    size = [self.fov_dimensions[0], self.fov_dimensions[1]/np.sqrt(2),  self.scan_volumes[row, column]]

                    # scale opacity for viewing
                    if self.view_plane == (self.coordinate_plane[0], self.coordinate_plane[1]):
                        opacity = self.active_tile_opacity
                    elif self.view_plane == (self.coordinate_plane[2], self.coordinate_plane[1]):
                        opacity = self.active_tile_opacity / total_columns
                    else:
                        opacity = self.active_tile_opacity / total_rows

                    box = GLShadedBoxItem(width=self.tile_line_width,
                                          pos=np.array([[coord]]),
                                          size=np.array(size),
                                          color=self.active_tile_color if in_grid else self.inactive_tile_color,
                                          opacity=opacity,
                                          glOptions='additive',
                                          )
                    box.setTransform(QMatrix4x4(1, 0, 0, self.fov_position[0] * self.polarity[0],
                                              0, 1, 0, self.fov_position[1] * self.polarity[1],
                                              0, sin(pi / 4), cos(pi / 4), self.fov_position[2] * self.polarity[2],
                                              0, 0, 0, 1))
                    box.setVisible(self.tile_visibility[row, column])
                    self.addItem(box)
                    self.grid_box_items.append(box)

        self._update_opts()

    def toggle_view_plane(self, button):
        """ Hide path if not in tiling plane"""
        super().toggle_view_plane(button)
        self.path.setVisible(not self.view_plane != (self.coordinate_plane[0], self.coordinate_plane[1]))

    def _update_opts(self):
        """Overwrite to adjust view in (self.coordinate_plane[0], self.coordinate_plane[1])"""

        super()._update_opts()
        view_plane = self.view_plane
        root = sqrt(2.0) / 2.0
        if view_plane == (self.coordinate_plane[0], self.coordinate_plane[2]):
            self.opts['rotation'] = QQuaternion(0, root, 0, 0)

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

        acquisition_widget = QSplitter(Qt.Vertical)
        acquisition_widget.setChildrenCollapsible(False)

        # create volume plan
        self.volume_plan = InvertedVolumePlanWidget(limits=limits,
                                            fov_dimensions=fov_dimensions,
                                            coordinate_plane=self.coordinate_plane,
                                            unit=self.unit)
        self.volume_plan.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)

        # create volume model
        self.volume_model = InvertedVolumeModel(limits=limits,
                                        fov_dimensions=fov_dimensions,
                                        coordinate_plane=self.coordinate_plane,
                                        unit=self.unit,
                                        **self.config['acquisition_view']['acquisition_widgets'].get('volume_model', {}).get('init', {}))
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
                                              **self.config['acquisition_view']['acquisition_widgets'].get('channel_plan', {}).get('init', {}))
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
