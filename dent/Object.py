import OpenGL.GL as gl
import os
import numpy as np
import pyassimp
import pyassimp.material
import Texture
import Shaders
import transforms
import logging
import taskQueue
import threading
from collections import namedtuple
import Animation

MeshOptions = namedtuple("MeshOptions", ('has_bumpmap', 'has_bones'))
MeshDatum = namedtuple("MeshDatum", ('name', 'data', 'indices', 'colormap', 'normalmap', 'options'))
time = 0

def getOptionNumber(meshOptions):
  ans = 0
  for i,v in enumerate(meshOptions):
    if v:
      ans += 2 ** i
  return ans

def getTexturePath(path):
  """This is a stupid hack required for particular unity assets."""
  if path[:19] == '..\\..\\..\\..\\..\\tex\\':
    return 'textures/'+path[19:]
  return path

def get_node_parent(scene, name):
  def dfs(node,parent):
    if node.name == name:
      return parent
    for i in node.children:
      a = dfs(i, node)
      if a: return a
    return None
  return dfs(scene.rootnode, '')

def getTextureFile(material, textureType, directory=None):
  if textureType == pyassimp.material.aiTextureType_DIFFUSE:
    if os.path.exists(directory+'/{}.diff.png'.format(material.properties[('name', 0)])):
      return '{}.diff.png'.format(material.properties[('name', 0)])
  elif textureType == pyassimp.material.aiTextureType_NORMALS:
    if os.path.exists(directory+'/{}.norm.png'.format(material.properties[('name', 0)])):
      return '{}.norm.png'.format(material.properties[('name', 0)])

shader             = Shaders.getShader('general')
shader['colormap'] = Texture.COLORMAP_NUM
shader['normalmap'] = Texture.NORMALMAP_NUM

class Object(object):
  def __init__(
      self,
      filename,
      name=None,
      scale=1,
      position=np.zeros(3),
      offset=np.zeros(3),
      will_animate=False,
      daemon=True):

    if name == None:
      name = os.path.basename(filename)

    if will_animate:
      daemon = False

    self.filename = filename
    self.directory = os.path.dirname(filename)
    self.name = name
    self.scene = None
    self.meshes = []
    self.renderIDs = []
    self.textures = []
    self.scale = scale
    self.bones = {}
    self.bone_transforms = [np.eye(4, dtype=float) for _ in xrange(60)]
    self.animations = []
    self.animation = None
    self.will_animate = will_animate
    self.position = np.array(position, dtype=np.float32)
    self.offset = np.array(offset, dtype=np.float32)
    self.direction = np.array((0,0,1), dtype=float)
    self.bidirection = np.array((1,0,0), dtype=float)
    self.daemon = daemon

    if self.daemon:
      thread = threading.Thread(target=self.loadFromFile)
      thread.setDaemon(True)
      thread.start()
    else:
      self.loadFromFile()


  def __del__(self):
    logging.info("Releasing object {}".format(self.name))
    # Release the pyassimp, as we no longer need it
    pyassimp.release(self.scene)


  def loadFromFile(self):
    logging.info("Loading object {} from {}".format(self.name, self.filename))
    # Some of these are for static only and must be removed when doing bones.
    self.scene = pyassimp.load(self.filename,
        processing=pyassimp.postprocess.aiProcess_CalcTangentSpace|
                   pyassimp.postprocess.aiProcess_Triangulate|
                   pyassimp.postprocess.aiProcess_JoinIdenticalVertices|
                   pyassimp.postprocess.aiProcess_LimitBoneWeights |
                   pyassimp.postprocess.aiProcess_GenNormals)

    def addNode(node, trans, depth = 0):
      newtrans = trans.dot(node.transformation)
      for msh in node.meshes:
        self.addMesh(node.name, msh, newtrans)
      for nod in node.children:
        addNode(nod, newtrans, depth+1)

    t = np.eye(4)
    t[:3] *= self.scale
    addNode(self.scene.rootnode, t)


  def addMesh(self, name, mesh, trans):
    logging.debug("Loading mesh {}".format(mesh.__repr__()))
    options = MeshOptions(False, False)
    data = np.zeros(len(mesh.vertices),
                      dtype=[("position" , np.float32,3),
                             ("normal"   , np.float32,3),
                             ("textcoord", np.float32,2),
                             ("tangent"  , np.float32,3),
                             ("bitangent", np.float32,3),
                             ("bone_ids", np.int32,4),
                             ("weights", np.float32,4)])
    # Get the vertex positions and add a w=1 component
    vertPos = mesh.vertices
    add = np.ones((vertPos.shape[0], 1),dtype=np.float32)
    vertPos = np.append(vertPos, add, axis=1)
    # Get the vertex normals and add a w=1 component
    vertNorm = mesh.normals
    add = np.zeros((vertNorm.shape[0],1),dtype=np.float32)
    vertNorm = np.append(vertNorm, add, axis=1)

    vertTangents = mesh.tangents
    vertBitangents = mesh.bitangents

    tinvtrans = np.linalg.inv(trans).transpose()
    if not self.will_animate:
      # Transform all the vertex positions.
      for i in xrange(len(vertPos)):
        vertPos[i] = trans.dot(vertPos[i])
        vertNorm[i] = tinvtrans.dot(vertNorm[i]) * self.scale
    # Splice correctly, killing last components
    vertPos = vertPos[:,0:3]# - self.offset
    vertNorm = vertNorm[:,0:3]

    vertUV = mesh.texturecoords[0][:, [0,1]]
    vertUV[:, 1] = 1 - vertUV[:, 1]

    # Set the data
    data["position"] = vertPos
    data["normal"] = vertNorm
    data["textcoord"] = vertUV
    data["tangent"] = vertTangents
    data["bone_ids"] = 59
    data["bitangent"] = vertBitangents

    # Get the indices
    indices = mesh.faces.reshape((-1,))

    # Load the texture
    texture = Texture.Texture(Texture.COLORMAP, nonblocking=self.daemon)
    if getTextureFile(mesh.material, pyassimp.material.aiTextureType_DIFFUSE, self.directory):
      logging.info("Getting texture from {}".format(getTexturePath(getTextureFile(mesh.material, pyassimp.material.aiTextureType_DIFFUSE, self.directory))))
      texture.loadFromImage(self.directory+'/'+getTexturePath(getTextureFile(mesh.material, pyassimp.material.aiTextureType_DIFFUSE, self.directory)))
    else:
      texture = Texture.getWhiteTexture();

    if getTextureFile(mesh.material, pyassimp.material.aiTextureType_NORMALS, self.directory):
      logging.info("Getting texture from {}".format(getTexturePath(getTextureFile(mesh.material, pyassimp.material.aiTextureType_NORMALS, self.directory))))
      normalTexture = Texture.Texture(Texture.NORMALMAP, nonblocking=self.daemon)
      options = options._replace(has_bumpmap=True)
      normalTexture.loadFromImage(self.directory+'/'+getTexturePath(getTextureFile(mesh.material, pyassimp.material.aiTextureType_NORMALS, self.directory)))
    else:
      normalTexture = None
      options = options._replace(has_bumpmap=False)

    # Do skinning
    if self.will_animate:
      if len(mesh.bones) > 0:
        options = options._replace(has_bones=True)
        data["weights"] = 0
        for bone in mesh.bones:
          n = len(self.bones)
          if bone.name not in self.bones:
            self.bones[bone.name] = (n, get_node_parent(self.scene, bone.name).name, bone.offsetmatrix)
            nn =n
          else:
            nn = self.bones[bone.name][0]
          for relationship in bone.weights:
            bone_vec_number = 0
            for i in xrange(3):
              if data["weights"][relationship.vertexid][bone_vec_number] > 0:
                bone_vec_number += 1
              else:
                break
            data["weights"][relationship.vertexid][bone_vec_number] = relationship.weight
            data["bone_ids"][relationship.vertexid][bone_vec_number] = nn

    # Add the textures and the mesh data
    self.textures.append(texture)
    self.meshes.append(MeshDatum(name, data, indices, texture, normalTexture, options))

    taskQueue.addToMainThreadQueue(self.uploadMesh, (data, indices, mesh))


  def uploadMesh(self, data, indices, mesh):
    self.renderIDs.append(shader.setData(data, indices))
    logging.info("Loaded mesh {}".format(mesh.__repr__()))


  def display(self):
    global time
    time+=1
    shader.load()
    t = np.eye(4, dtype=np.float32)
    t[2,0:3] = self.direction
    t[0,0:3] = self.bidirection
    transforms.translate(t, self.position[0],self.position[1],self.position[2])
    shader['model'] = t

    options = None

    for meshdatum,renderID in zip(self.meshes,self.renderIDs):
      # Set options
      if options != getOptionNumber(meshdatum.options):
        options = getOptionNumber(meshdatum.options)
        shader['options'] = options

      if meshdatum.options.has_bones:
        if self.animation is not None:
          bones = self.animation.get_bone_transforms(time)
          shader['bones'] = bones

      # Load textures
      meshdatum.colormap.load()
      if meshdatum.options.has_bumpmap:
        meshdatum.normalmap.load()
      shader.draw(gl.GL_TRIANGLES, renderID)


  def add_animation(self, filename):
    self.animation = Animation.Animation(filename, self.bones)

  def __repr__(self):
    return "<pmObject \"{}\">".format(self.name)
