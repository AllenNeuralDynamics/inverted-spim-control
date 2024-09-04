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

    def _update_opts(self):
        """Overwrite to adjust view in (self.coordinate_plane[0], self.coordinate_plane[1])"""

        view_plane = self.view_plane
        view_pol = [self.polarity[self.coordinate_plane.index(view_plane[0])],
                    self.polarity[self.coordinate_plane.index(view_plane[1])]]
        coords = self.grid_coords.reshape([-1, 3])  # flatten array
        dims = self.scan_volumes.flatten()  # flatten array

        # set rotation
        root = sqrt(2.0) / 2.0
        if view_plane == (self.coordinate_plane[0], self.coordinate_plane[1]):
            self.opts['rotation'] = QQuaternion(-1, 0, 0, 0)
        elif view_plane == (self.coordinate_plane[0], self.coordinate_plane[2]):
            self.opts['rotation'] = QQuaternion(-root, root, 0, 0)
            # take into account end of tile and account for difference in size if z included in view
            coords = np.concatenate((coords, [[x, y,
                                               (z + sz)] for (x, y, z), sz in zip(coords, dims)]))
        else:
            self.opts['rotation'] = QQuaternion(-root, 0, -root, 0)
            coords = np.concatenate((coords, [[x, y,
                                               (z + sz)] for (x, y, z), sz in zip(coords, dims)]))
        extrema = {'x_min': min(coords[:, 0]), 'x_max': max(coords[:, 0]),
                   'y_min': min(coords[:, 1]), 'y_max': max(coords[:, 1]),
                   'z_min': min(coords[:, 2]), 'z_max': max(coords[:, 2])}

        fov = {'x': self.fov_dimensions[0],
               'y': self.fov_dimensions[1] * sin(radians(self.angle)),
               'z': self.fov_dimensions[1] * cos(radians(self.angle))}
        pos = {axis: dim for axis, dim in zip(['x', 'y', 'z'], self.fov_position)}

        distances = {'xy': [sqrt((pos[view_plane[0]] - x) ** 2 + (pos[view_plane[1]] - y) ** 2) for x, y, z in coords],
                     'xz': [sqrt((pos[view_plane[0]] - x) ** 2 + (pos[view_plane[1]] - z) ** 2) for x, y, z in coords],
                     'zy': [sqrt((pos[view_plane[0]] - z) ** 2 + (pos[view_plane[1]] - y) ** 2) for x, y, z in coords]}
        max_index = distances[''.join(view_plane)].index(max(distances[''.join(view_plane)], key=abs))
        furthest_tile = {'x': coords[max_index][0],
                         'y': coords[max_index][1],
                         'z': coords[max_index][2]}
        center = {}

        # Horizontal sizing, if fov_position is within grid or farthest distance is between grid tiles
        x = view_plane[0]
        if extrema[f'{x}_min'] <= pos[x] <= extrema[f'{x}_max'] or \
                abs(furthest_tile[x] - pos[x]) < abs(extrema[f'{x}_max'] - extrema[f'{x}_min']):
            center[x] = (((extrema[f'{x}_min'] + extrema[f'{x}_max']) / 2) + (fov[x] / 2 * view_pol[0])) * view_pol[0]
            horz_dist = ((extrema[f'{x}_max'] - extrema[f'{x}_min']) + (fov[x] * 2)) / 2 * tan(
                radians(self.opts['fov']))
        else:
            center[x] = (((pos[x] + furthest_tile[x]) / 2) + (fov[x] / 2 * view_pol[0])) * view_pol[0]
            horz_dist = (abs(pos[x] - furthest_tile[x]) + (fov[x] * 2)) / 2 * tan(radians(self.opts['fov']))
        # Vertical sizing, if fov_position is within grid or farthest distance is between grid tiles
        y = view_plane[1]
        scaling = (self.size().width() / self.size().height())
        if extrema[f'{y}_min'] <= pos[y] <= extrema[f'{y}_max'] or \
                abs(furthest_tile[y] - pos[y]) < abs(extrema[f'{y}_max'] - extrema[f'{y}_min']):
            center[y] = (((extrema[f'{y}_min'] + extrema[f'{y}_max']) / 2) + (fov[y] / 2 * view_pol[1])) * view_pol[1]
            # View doesn't scale when changing vertical size so take into account the dif between the height and width
            vert_dist = ((extrema[f'{y}_max'] - extrema[f'{y}_min']) + (fov[y] * 2)) / 2 \
                        * tan(radians(self.opts['fov'])) * scaling

        else:
            center[y] = (((pos[y] + furthest_tile[y]) / 2) + (fov[y] / 2 * view_pol[1])) * view_pol[1]
            vert_dist = (abs(pos[y] - furthest_tile[y]) + (fov[y] * 2)) / 2 * scaling
        # @Micah in ortho mode it seems to scale properly with x1200... not sure how to explain why though
        # not sure if this actually works, and whether it needs to be copied to other places in the fx
        self.opts['distance'] = horz_dist * 1200 if horz_dist > vert_dist else vert_dist * 1200
        self.opts['center'] = QVector3D(
            center.get('x', 0),
            center.get('y', 0),
            center.get('z', 0))

        self.update()
    def add_fov_image(self, image: np.array, levels: list):
        """add image to model assuming image has same fov dimensions and orientation. Overwriting to transform
        :param image: numpy array of image to display in model
        :param levels: levels for passed in image"""

        super().add_fov_image(image, levels)
        x, y, z = self.fov_position
        gl_image = self.fov_images[image.tobytes()]
        gl_image.setTransform(QMatrix4x4(self.fov_dimensions[0] / image.shape[0], 0, 0, x * self.polarity[0],
                                         0, (self.fov_dimensions[1] / image.shape[1])*cos(radians(self.angle)), -sin(radians(self.angle)), y * self.polarity[1],
                                         0, sin(radians(self.angle)),cos(radians(self.angle)), z * self.polarity[2],
                                         0, 0, 0, 1))
