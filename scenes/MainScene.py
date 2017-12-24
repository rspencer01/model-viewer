from dent.Scene import Scene
from dent.Object import Object
from dent.RenderStage import RenderStage
from dent.RectangleObjects import RectangleObject, BlankImageObject
from dent.ActionController import ActionController
import dent.Shaders
import numpy as np
import dent.transforms
import dent.messaging
import dent.args

class MainScene(Scene):
  def __init__(self):
    super(MainScene, self).__init__()
    self.renderPipeline.stages.append(
        RenderStage(render_func=self.display, final_stage=True))
    self.object = Object(dent.args.args.model,
        will_animate=
          dent.args.args.animation is not None or
          dent.args.args.actions is not None,
        scale=dent.args.args.scale,
        daemon=False)
    if dent.args.args.animation:
      self.object.add_animation(dent.args.args.animation)
    if dent.args.args.actions:
      self.object.action_controller = ActionController(self.object, dent.args.args.actions)
    self.camera.lockObject = self.object
    self.camera.lockDistance = 2
    self.camera.move_hook = lambda x: \
      [x[0], max(0.05, x[1]), x[2]]

    self.floor = RectangleObject('floor')
    self.sky = BlankImageObject(0.4, 0.5, 0.6)

    dent.messaging.add_handler('timer', self.timer)
    dent.messaging.add_handler('keyboard', self.key)

    if self.object.action_controller is not None:
      self.object.action_controller.action_weight = lambda x:\
        np.linalg.norm(x.get_end_position())

    self.time = 0.

  def key(self, key):
    if key == 'l':
      if self.camera.lockObject:
        self.camera.lockObject = None
      else:
        self.camera.lockObject = self.object

  def timer(self, fps):
    # Simply move the sun around the sky
    dent.Shaders.setUniform('sunDirection', np.array(
      [np.sin(self.time),
        0.4,
        np.cos(self.time)]))
    self.time += 1./fps

  def display(self, width, height, **kwargs):
    projection = dent.transforms.perspective(60.0, width/float(height), 0.03, 1e4)
    dent.Shaders.setUniform('projection', projection)
    self.floor.shader['objectPos'] = self.object.position

    self.object.update(self.time)

    self.camera.render()

    self.sky.display()
    self.object.display()
    self.floor.display()
