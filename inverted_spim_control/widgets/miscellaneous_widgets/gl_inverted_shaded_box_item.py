from math import sin, cos, pi, sqrt, radians, tan
import numpy as np
from OpenGL.GL import *  # noqa
from view.widgets.miscellaneous_widgets.gl_shaded_box_item import GLShadedBoxItem
from pyqtgraph.opengl import GLMeshItem
from qtpy.QtGui import QColor


class GLInvertedShadedBoxItem(GLMeshItem):
    """Subclass of GLMeshItem creates a rectangular mesh item"""

    def __init__(self, angle, pos, size, color='cyan', width=1, opacity=1, glOptions=None, parentItem=None):
        """

        :param pos: position of ite,
        :param size: size of item
        :param color: color of item
        :param glOptions:
        :param parentItem:
        """

        self._angle = angle
        self._size = size
        self._width = width
        self._opacity = opacity
        self._color = color
        colors = np.array([self._convert_color(color) for i in range(12)])

        self._pos = pos
        self._vertexes, self._faces = self._create_box(pos, size, angle)

        super().__init__(vertexes=self._vertexes, faces=self._faces, faceColors=colors,
                         drawEdges=True, edgeColor=(0, 0, 0, 1), glOptions=glOptions, parentItem=parentItem)

    def _create_box(self, pos, size, angle):
        """Convenience method create the vertexes and faces of box to draw"""

        z_offset = size[1] * cos(radians(angle))
        size = np.array([size[0], size[1] * sin(radians(angle)), size[2]])
        nCubes = np.prod(pos.shape[:-1])
        cubeVerts = np.mgrid[0:2, 0:2, 0:2].reshape(3, 8).transpose().reshape(1, 8, 3)
        cubeFaces = np.array([
            [0, 1, 2], [3, 2, 1],
            [4, 5, 6], [7, 6, 5],
            [0, 1, 4], [5, 4, 1],
            [2, 3, 6], [7, 6, 3],
            [0, 2, 4], [6, 4, 2],
            [1, 3, 5], [7, 5, 3]]).reshape(1, 12, 3)
        size_reshape = size.reshape((nCubes, 1, 3))
        pos = pos.reshape((nCubes, 1, 3))
        vertexes = (cubeVerts * size_reshape + pos)[0]
        faces = (cubeFaces + (np.arange(nCubes) * 8).reshape(nCubes, 1, 1))[0]

        # update vertexes for angle
        vertexes[2][2] += z_offset
        vertexes[3][2] += z_offset
        vertexes[6][2] += z_offset
        vertexes[7][2] += z_offset

        return vertexes, faces

    def color(self):
        """Color of box and outline"""
        return self._color

    def setColor(self, color: str or list):
        self._color = color
        colors = np.array([self._convert_color(self._color) for i in range(12)])
        self.setMeshData(vertexes=self._vertexes, faces=self._faces, faceColors=colors)

    def _convert_color(self, color):
        """Convenience method used to convert string color"""
        if isinstance(color, str):
            rgbf = list(QColor(color).getRgbF())
            color = rgbf[:3] + [self._opacity * rgbf[3]]
        return color

    def size(self):
        """Size of box and outline"""
        return self._size

    def setSize(self, x, y, z):
        self._size = np.array([x, y, z])
        self._vertexes, self._faces = self._create_box(self._pos, self._size)
        colors = np.array([self._convert_color(self._color) for i in range(12)])
        self.setMeshData(vertexes=self._vertexes,
                         faces=self._faces,
                         faceColors=colors)

    def paint(self):
        """Overwriting to include box outline"""

        super().paint()

        self.setupGLState()
        glLineWidth(self._width)  # added line for thickness setting

        glBegin(GL_LINES)

        glColor4f(*self._convert_color(self._color))

        x, y, z = [self._pos[0, 0, i] + x for i, x in enumerate(self.size())]
        x_pos, y_pos, z_pos = self._pos[0, 0, :]

        z_offset = self.size()[1] * cos(radians(self._angle))
        y = self._pos[0, 0, 1] + (self.size()[1] * sin(radians(self._angle)))

        glVertex3f(x_pos, y_pos, z_pos)
        glVertex3f(x_pos, y_pos, z)
        glVertex3f(x, y_pos, z_pos)
        glVertex3f(x, y_pos, z)
        glVertex3f(x_pos, y, z_pos + z_offset)
        glVertex3f(x_pos, y, z + z_offset)
        glVertex3f(x, y, z_pos )
        glVertex3f(x, y, z)

        glVertex3f(x_pos, y_pos, z_pos)
        glVertex3f(x_pos, y, z_pos + z_offset)
        glVertex3f(x, y_pos, z_pos)
        glVertex3f(x, y, z_pos + z_offset)
        glVertex3f(x_pos, y_pos, z)
        glVertex3f(x_pos, y, z + z_offset)
        glVertex3f(x, y_pos, z)
        glVertex3f(x, y, z + z_offset)

        glVertex3f(x_pos, y_pos, z_pos)
        glVertex3f(x, y_pos, z_pos)
        glVertex3f(x_pos, y, z_pos + z_offset)
        glVertex3f(x, y, z_pos + z_offset)
        glVertex3f(x_pos, y_pos, z)
        glVertex3f(x, y_pos, z)
        glVertex3f(x_pos, y, z + z_offset)
        glVertex3f(x, y, z + z_offset)

        glEnd()
