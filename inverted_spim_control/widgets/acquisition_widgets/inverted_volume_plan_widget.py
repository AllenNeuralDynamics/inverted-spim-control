from view.widgets.acquisition_widgets.volume_plan_widget import VolumePlanWidget
from math import cos, radians, sin

class InvertedVolumePlanWidget(VolumePlanWidget):
    """Handle change in overlap value in 2nd tiling direction"""

    def __init__(self, crossing_angle, *args, **kwargs):
        """
        :param crossing_angle: angle in degrees of imaging
        """
        kwargs['fov_dimensions'] = [kwargs['fov_dimensions'][0],
                                    kwargs['fov_dimensions'][1]*sin(radians(crossing_angle)),
                                    kwargs['fov_dimensions'][1]*cos(radians(crossing_angle))]
        super().__init__(*args, **kwargs)
        self.angle = crossing_angle

