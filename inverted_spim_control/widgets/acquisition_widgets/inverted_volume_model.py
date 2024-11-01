from view.widgets.acquisition_widgets.volume_model import VolumeModel
from inverted_spim_control.widgets.miscellaneous_widgets.gl_inverted_shaded_box_item import GLInvertedShadedBoxItem
import numpy as np
from qtpy.QtGui import QMatrix4x4, QQuaternion, QVector3D
from math import sin, cos, pi, sqrt, radians, tan

class InvertedVolumeModel(VolumeModel):
    """Display tiles at 45 degree angle"""

    def __init__(self, crossing_angle, *args, **kwargs):

        """
        :param crossing_angle: angle in degrees of imaging
        """

        kwargs['fov_dimensions'] = [kwargs['fov_dimensions'][0],
                                    kwargs['fov_dimensions'][1],
                                    0]
        self.angle = crossing_angle
        super().__init__(*args, **kwargs)
        self.fov_view.setTransform(QMatrix4x4(1, 0, 0, self.fov_position[0] * self.polarity[0],
                                              0, cos(radians(self.angle)),
                                              -sin(radians(self.angle)), self.fov_position[1] * self.polarity[1],
                                              0, sin(radians(self.angle)),
                                              cos(radians(self.angle)),
                                              self.fov_position[2] * self.polarity[2],
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
            self.fov_view.setTransform(QMatrix4x4(1, 0, 0, self.fov_position[0] * self.polarity[0],
                                                  0, cos(radians(self.angle)),
                                                  -sin(radians(self.angle)),
                                                  self.fov_position[1] * self.polarity[1],
                                                  0, sin(radians(self.angle)),
                                                  cos(radians(self.angle)),
                                                  self.fov_position[2] * self.polarity[2],
                                                  0, 0, 0, 1))

            color = self.grid_box_items[0].color() if len(self.grid_box_items) != 0 else None
            if (not in_grid and color != self.inactive_tile_color) or (in_grid and color != self.active_tile_color):
                new_color = self.inactive_tile_color if not in_grid else self.active_tile_color
                for box in self.grid_box_items:
                    box.setColor(color=new_color)

        else:
            self.fov_view.setSize(x=self.fov_dimensions[0],
                                  y=self.fov_dimensions[1],
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
                    size = [self.fov_dimensions[0], self.fov_dimensions[1], self.scan_volumes[row, column]]

                    # scale opacity for viewing
                    if self.view_plane == (self.coordinate_plane[0], self.coordinate_plane[1]):
                        opacity = self.active_tile_opacity
                    elif self.view_plane == (self.coordinate_plane[2], self.coordinate_plane[1]):
                        opacity = self.active_tile_opacity / total_columns
                    else:
                        opacity = self.active_tile_opacity / total_rows

                    box = GLInvertedShadedBoxItem(angle=self.angle,
                                                  width=self.tile_line_width,
                                          pos=np.array([[coord]]),
                                          size=np.array(size),
                                          color=self.active_tile_color if in_grid else self.inactive_tile_color,
                                          opacity=opacity,
                                          glOptions='additive',
                                          )
                    box.setVisible(self.tile_visibility[row, column])
                    self.addItem(box)
                    self.grid_box_items.append(box)
        self._update_opts()

    def toggle_view_plane(self, button):
        """ Hide path if not in tiling plane"""
        super().toggle_view_plane(button)
        self.path.setVisible(not self.view_plane != (self.coordinate_plane[0], self.coordinate_plane[1]))

    def add_fov_image(self, image: np.array, levels: list):
        """add image to model assuming image has same fov dimensions and orientation. Overwriting to transform
        :param image: numpy array of image to display in model
        :param levels: levels for passed in image"""

        super().add_fov_image(image, levels)
        x, y, z = self.fov_position
        gl_image = self.fov_images[image.tobytes()]
        gl_image.setTransform(QMatrix4x4(self.fov_dimensions[0] / image.shape[0], 0, 0, x * self.polarity[0],
                                         0, (self.fov_dimensions[1] / image.shape[1])*cos(radians(self.angle)), -sin(radians(self.angle)), y * self.polarity[1],
                                         0, (self.fov_dimensions[1] / image.shape[1])*sin(radians(self.angle)), cos(radians(self.angle)), z * self.polarity[2],
                                         0, 0, 0, 1))