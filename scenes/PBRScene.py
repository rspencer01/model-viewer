import numpy as np

from dent.ActionController import ActionController
from dent.Object import Object
from dent.Scene import Scene
from dent.Camera import Camera

import dent.Shaders
import dent.args
import dent.messaging
import dent.transforms

from PBRViewerGui import PBRViewerGui


class PBRScene(Scene):

    def __init__(self):
        super(PBRScene, self).__init__()
        self.renderPipeline.stages.append(PBRViewerGui(self, final_stage=True))

        self.object = Object(
            dent.args.args.model,
            will_animate=dent.args.args.animation is not None
            or dent.args.args.actions is not None,
            scale=dent.args.args.scale,
            daemon=False,
            shader_name="pbr-forward",
        )
        if dent.args.args.animation:
            self.object.add_animation(dent.args.args.animation)
        if dent.args.args.actions:
            self.object.action_controller = ActionController(
                self.object, dent.args.args.actions
            )
        self.camera = Camera()
        self.camera.lockObject = self.object
        self.camera.lockDistance = 2

        dent.messaging.add_handler("timer", self.timer)

        self.time = 0.
        self.roughness = 0.
        self.metallic = 0.
        self.material_color = np.array([1.,1.,1.])
        self.sun_color = np.array([1.,1.,1.])
        self.sun_intensity = 10

        self._objects = [self.object]
        self.time_enabled = True

    def timer(self, fps):
        # Simply move the sun around the sky
        dent.Shaders.setUniform(
            "sunDirection", np.array([np.sin(self.time), 0.4, np.cos(self.time)])
        )
        if self.time_enabled:
          self.time += 1. / fps

    def display(self, width, height, **kwargs):
        projection = dent.transforms.perspective(60.0, width / float(height), 0.03, 1e4)
        dent.Shaders.setUniform("projection", projection)
        dent.Shaders.setUniform("roughness", self.roughness)
        dent.Shaders.setUniform("metallic", self.metallic)
        dent.Shaders.setUniform("albedo", self.material_color)
        dent.Shaders.setUniform("sunIntensity", self.sun_color * self.sun_intensity)

        self.object.update(self.time)

        self.camera.render()
        super(PBRScene, self).display(width=width, height=height, **kwargs)
