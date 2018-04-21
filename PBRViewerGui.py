from dent.GuiStage import GuiStage
import imgui


class PBRViewerGui(GuiStage):

    def __init__(self, scene, *args, **kwargs):
        super(PBRViewerGui, self).__init__(*args, **kwargs)
        self._scene = scene

    def make_gui(self, width, height):
        imgui.begin("Lighting", True)

        imgui.end()
