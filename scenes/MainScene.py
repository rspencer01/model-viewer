from dent.Scene import Scene
from dent.Object import Object
from dent.RenderStage import RenderStage
from dent.RectangleObjects import RectangleObject, BlankImageObject
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
    print dent.args.args.animation
    self.object = Object(dent.args.args.model,
        will_animate=dent.args.args.animation is not None,
        daemon=False)
    if dent.args.args.animation:
      self.object.add_animation(dent.args.args.animation)
    self.camera.lockObject = self.object
    self.camera.lockDistance = 200
    self.camera.move_hook = lambda x: \
      [x[0], max(5, x[1]), x[2]]

    self.floor = RectangleObject('floor')
    self.sky = BlankImageObject(0.4, 0.5, 0.6)

    dent.messaging.add_handler('timer', self.timer)
    self.time = 0.

  def timer(self, fps):
    # Simply move the sun around the sky
    dent.Shaders.setUniform('sunDirection', np.array(
      [np.sin(self.time),
        0.4,
        np.cos(self.time)]))
    self.time += 1./fps

  def display(self, width, height, **kwargs):
    projection = dent.transforms.perspective(60.0, width/float(height), 0.3, 1e7)
    dent.Shaders.setUniform('projection', projection)
    self.floor.shader['objectPos'] = self.object.position

    self.camera.render()

    self.sky.display()
    self.object.display(time=self.time)
    self.floor.display()
