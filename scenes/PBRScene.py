import numpy as np

from dent.ActionController import ActionController
from dent.Object import Object
from dent.RectangleObjects import RectangleObject, BlankImageObject
from dent.RenderStage import RenderStage
from dent.Scene import Scene

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
        )
        if dent.args.args.animation:
            self.object.add_animation(dent.args.args.animation)
        if dent.args.args.actions:
            self.object.action_controller = ActionController(
                self.object, dent.args.args.actions
            )
        self.camera.lockObject = self.object
        self.camera.lockDistance = 2
        self.camera.speed = 1

        self.floor = RectangleObject("floor") if not dent.args.args.no_floor else None

        dent.messaging.add_handler("timer", self.timer)
        dent.messaging.add_handler("keyboard", self.key)

        self.time = 0.

        self._objects = []

    def key(self, key):
        if key == "l":
            if self.camera.lockObject:
                self.camera.lockObject = None
            else:
                self.camera.lockObject = self.object

    def timer(self, fps):
        # Simply move the sun around the sky
        dent.Shaders.setUniform(
            "sunDirection", np.array([np.sin(self.time), 0.4, np.cos(self.time)])
        )
        self.time += 1. / fps

    def display(self, width, height, **kwargs):
        projection = dent.transforms.perspective(60.0, width / float(height), 0.03, 1e4)
        dent.Shaders.setUniform("projection", projection)

        self.object.update(self.time)

        self.camera.render()
        self.render_all()
        super(PBRScene, self).display(width=width, height=height, **kwargs)

    def render_all(self):

        self.object.display()
        if self.floor:
            self.floor.shader["objectPos"] = self.object.position
            self.floor.display()
