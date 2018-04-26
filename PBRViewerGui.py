from dent.GuiStage import GuiStage
import imgui
import numpy as np


class PBRViewerGui(GuiStage):

    def __init__(self, scene, *args, **kwargs):
        super(PBRViewerGui, self).__init__(*args, **kwargs)
        self._scene = scene

    def make_gui(self, width, height):
        imgui.begin("Lighting", True)

        ch, val = imgui.checkbox("Move sun", self._scene.time_enabled)
        if ch:
            self._scene.time_enabled = val

        ch, val = imgui.slider_float(
            "Roughness", self._scene.object.materials.values()[0].specular_tint, 0, 1
        )
        if ch:
            self._scene.object.materials.values()[0].specular_tint = val

        ch, val = imgui.slider_float(
            "Metallic", self._scene.object.materials.values()[0].metallic_tint, 0, 1
        )
        if ch:
            self._scene.object.materials.values()[0].metallic_tint = val

        ch, val = imgui.color_edit3(
            "Material colour", *self._scene.object.materials.values()[0].diffuse_tint
        )
        if ch:
            self._scene.object.materials.values()[0].diffuse_tint = np.array(val)

        ch, val = imgui.color_edit3("Sun colour", *self._scene.sun_color)
        if ch:
            self._scene.sun_color = np.array(val)

        ch, val = imgui.slider_float("Sun intensity", self._scene.sun_intensity, 0, 100)
        if ch:
            self._scene.sun_intensity = val
        imgui.end()
