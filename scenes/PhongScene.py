import numpy as np

from dent.ActionController import ActionController
from dent.Object import Object
from dent.RectangleObjects import RectangleObject
from dent.Scene import DeferredRenderScene
from dent.Shadows import Shadows

import dent.Shaders
import dent.transforms
import dent.messaging
import dent.args

from PhongViewerGui import PhongViewerGui


class PhongScene(DeferredRenderScene):

    def __init__(self):
        super(PhongScene, self).__init__()
        self.renderPipeline.stages.append(
            PhongViewerGui(self.renderPipeline.stages[-1], self, final_stage=True)
        )

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
        self.camera.move_hook = lambda x: [x[0], max(0.05, x[1]), x[2]]
        self.camera.speed = 1

        self.floor = RectangleObject("floor") if not dent.args.args.no_floor else None
        self.lighting_stage.backgroundColor = np.array([.4, .5, .6])

        dent.messaging.add_handler("timer", self.timer)
        dent.messaging.add_handler("keyboard", self.key)

        if self.object.action_controller is not None:
            self.object.action_controller.action_weight = lambda x: np.linalg.norm(
                x.get_end_position()
            )

        self.time = 0.

        self.shadows = Shadows(self.render_all, self.camera, rng=5)
        self.shadows.shadowCamera.rotUpDown(1.2)
        self.shadows.shadowCamera.rotLeftRight(3.1415 - 0.3)
        self.shadowsEnabled = True

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

        dent.Shaders.setUniform("sunDirection", -self.shadows.shadowCamera.direction)

        self.shadows.shadowCamera.rotLeftRight(1. / fps * 0.2)

    def render(self, *args):
        if self.shadowsEnabled:
            self.shadows.render()
        super(PhongScene, self).render(*args)

    def display(self, width, height, **kwargs):
        projection = dent.transforms.perspective(60.0, width / float(height), 0.03, 1e4)
        dent.Shaders.setUniform("projection", projection)

        self.object.update(self.time)

        self.camera.render()
        self.render_all()
        super(PhongScene, self).display(width=width, height=height, **kwargs)

    def render_all(self):

        self.object.display()
        if self.floor:
            self.floor.shader["objectPos"] = self.object.position
            self.floor.display()
