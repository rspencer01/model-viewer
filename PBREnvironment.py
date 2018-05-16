from dent.RectangleObjects import RectangleObject
import dent.TextureManager
import dent.Texture
import dent.Shaders


def make_irradience_map(input_texture):
    render_stage = dent.RenderStage.RenderStage()
    render_stage.reshape(input_texture.width, input_texture.height)
    render_stage.load(input_texture.width, input_texture.height)
    render_rectangle = dent.RectangleObjects.RectangleObject(
        "diffuse_irradience_compute"
    )
    render_rectangle.shader["input_texture"] = dent.Texture.COLORMAP_NUM
    input_texture.loadAs(dent.Texture.COLORMAP)
    render_rectangle.display()
    return render_stage.displayColorTexture


class PBREnvironment(RectangleObject):
    """Helper object for setting PBR image based lighting.

    This object is a wrapper around a set of skymap textures.

    It exposes a display method to set all the required textures and suchforth.
    It also displays the skymap in the background.

    Args:
        skymap_filepath (str): Path to a IBL descriptor file
    """

    def __init__(self, skymap_filepath):
        super(PBREnvironment, self).__init__("skymap")
        self.texture = dent.TextureManager.get_texture(
            skymap_filepath, dent.Texture.COLORMAP
        )
        self.irradience_texture = make_irradience_map(self.texture)
        self.shader["colormap"] = dent.Texture.COLORMAP_NUM
        self.shader["irradience_map"] = dent.Texture.IRRADIENCEMAP_NUM

    def display(self):
        self.texture.load()
        self.irradience_texture.loadAs(dent.Texture.IRRADIENCEMAP)
        dent.Shaders.updateUniversalUniform(
            "irradience_map", dent.Texture.IRRADIENCEMAP_NUM
        )
        super(PBREnvironment, self).display()
