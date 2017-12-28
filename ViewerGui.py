from dent.GuiStage import GuiStage
import imgui

class ViewerGui(GuiStage):
  def __init__(self, lightingStage, scene, *args, **kwargs):
    super(ViewerGui, self).__init__(*args, **kwargs)
    self.lightingStage = lightingStage
    self.scene = scene


  def make_gui(self):
    imgui.begin("Lighting", True)

    imgui.collapsing_header("Shadows")
    imgui.indent()
    ch, val = imgui.checkbox("Render Shadows", self.scene.shadowsEnabled)
    if ch:
      self.scene.shadowsEnabled = val
      if not val:
        self.scene.shadows.clear()

    ch, val = imgui.slider_float("Shadow Strength", self.lightingStage.shadowStrength, 0, 1)
    if ch:
      self.lightingStage.shadowStrength = val

    ch, val = imgui.slider_int("Shadows Update Frequency", self.scene.shadows.exponent, 1, 10)
    if ch:
      self.scene.shadows.exponent = val

    ch, val = imgui.slider_float("Shadows range", self.scene.shadows.rng, 0.01, 20)
    if ch:
      self.scene.shadows.rng = val
    imgui.unindent()

    imgui.collapsing_header("Ambient Occlusion")
    imgui.indent()

    ch, val = imgui.slider_float("Occlusion Strength", self.lightingStage.occlusionStrength, 0, 1)
    if ch:
      self.lightingStage.occlusionStrength = val

    ch, val = imgui.slider_float("SSAO blur radius", self.lightingStage.SSAOBlurAmount, 0, 0.01, display_format='%.4f')
    if ch:
      self.lightingStage.SSAOBlurAmount = val

    ch, val = imgui.slider_int("SSAO Samples", self.lightingStage.SSAOSamples, 0, 20)
    if ch:
      self.lightingStage.SSAOSamples = val

    ch, val = imgui.slider_float("SSAO Radius", self.lightingStage.SSAORadius, 0, 2)
    if ch:
      self.lightingStage.SSAORadius = val

    ch, val = imgui.slider_float("SSAO Min Cutoff", self.lightingStage.SSAOMin, 0, 1)
    if ch:
      self.lightingStage.SSAOMin = val

    ch, val = imgui.slider_float("SSAO Max Cutoff", self.lightingStage.SSAOMax, 0, 1)
    if ch:
      self.lightingStage.SSAOMax = val

    imgui.unindent()

    imgui.collapsing_header("Raytracing")
    imgui.indent()

    ch, val = imgui.slider_int("Raytrace Count", self.lightingStage.raytraceCount, 0, 100)
    if ch:
      self.lightingStage.raytraceCount = val

    ch, val = imgui.slider_float("Raytrace Strength", self.lightingStage.raytraceStrength, 0, 1)
    if ch:
      self.lightingStage.raytraceStrength = val

    imgui.unindent()


    imgui.collapsing_header("Other")
    imgui.indent()

    ch,val = imgui.slider_float("Ambient light strength", self.lightingStage.ambientStrength, 0, 1)
    if ch:
      self.lightingStage.ambientStrength = val

    ch, val = imgui.slider_float("Sun Intesnity", self.lightingStage.sunIntensity , 0, 1)
    if ch:
      self.lightingStage.sunIntensity = val

    ch, val = imgui.slider_float("Specularity", self.lightingStage.specularity, 1, 10000, power=10)
    if ch:
      self.lightingStage.specularity = val
    imgui.unindent()

    imgui.end()
