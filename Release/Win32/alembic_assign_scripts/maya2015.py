import maya.cmds as cmds
import os
import sys

class Mtl():
    def __init__(self):
        self.name = ""    
        self.textureMap = ""
        self.alphaMap = ""
        self.diffuse = [0.7, 0.7, 0.7]
        self.specular = [0.0, 0.0, 0.0]
        self.ambient = [0.0, 0.0, 0.0]
        self.trans = 1.0
        self.power = 0.0
        self.lum = 1
        self.faceSize = 0
	self.isAccessory = False

def import_mtl(path, result, relation):
    
    current = None
    
    export_mode = 0
    
    mtl = open(path, 'r')
    for line in mtl.readlines():
        words = line.split()
        if len(words) < 2:
            continue
        if "newmtl" in words[0]:
            # save previous mtl
            if current != None and current.name != "":
                # save previous mtl
                result[current.name] = current
            # new mtl
            current = Mtl()
            current.name = str(words[1])           
            
            # object relations
            nameSplits = current.name.split("_")
            objectNumber = int(nameSplits[1])
            materialNumber = int(nameSplits[2])
            if not objectNumber in relation.keys():
                relation[objectNumber] = []
            
            relation[objectNumber].append(materialNumber)
            
        if "Ka" == words[0]:
            current.ambient[0] = float(words[1])
            current.ambient[1] = float(words[2])
            current.ambient[2] = float(words[3])
        elif "Kd" == words[0]:
            current.diffuse[0] = float(words[1])
            current.diffuse[1] = float(words[2])
            current.diffuse[2] = float(words[3])
        elif "Ks" == words[0]:
            current.specular[0] = float(words[1])
            current.specular[1] = float(words[2])
            current.specular[2] = float(words[3])
        elif "Ns" == words[0]:
            current.power = float(words[1])
        elif "d" == words[0]:
            current.trans = float(words[1])
        elif "map_Kd" == words[0]:
            current.textureMap = line[line.find(words[1]):line.find(".png")+4]
        elif "map_d" == words[0]:
            current.alphaMap = line[line.find(words[1]):line.find(".png")+4]
        elif "#" == words[0]:
            if words[1] == "face_size":
                current.faceSize = int(words[2])
            elif words[1] == "is_accessory":
		current.isAccessory = True
            elif words[1] == "mode":
                export_mode = int(words[2])
    mtl.close()
        
    if current != None and current.name != "":
        result[current.name] = current

    for rel in relation.values():
        rel.sort()
        
    return export_mode

def execute():
    title = "MMDBridge merge tool - Select .abc directory"
    directory = cmds.fileDialog2(fileFilter=".abc directory", dialogStyle=2, caption=title, fileMode=3)
    abc = os.path.normpath(directory[0])
    print(abc)
    if not os.path.isdir(abc):
        return
    
    files = os.listdir(abc)
    
    if len(files) <= 0:
        return

    mtl = ""
    # find first mtl
    for file in files:
        root, ext = os.path.splitext(file)
        if ext == ".mtl":
            mtl = os.path.join(abc, file)
            break
    
    if mtl == "":
        return
    
    mtlDict = {}
    relationDict = {}
    import_mtl(mtl, mtlDict, relationDict)
    
    for name in cmds.ls():
        print(name)
        if 'xform_' in name and 'material_' in name:
            temp = name[name.find('xform_')+6 : len(name)]
            objectNumber = int(temp[0 : temp.find('_material_')])
            materialNumber = temp[temp.find('_material_')+10 : len(temp)]

            #applyFaceNumber = 0
            materialName = 'material_' + str(objectNumber) + '_' + str(materialNumber)

            if materialName in mtlDict.keys():
                # new material
                mtlData = mtlDict[materialName]
                material = cmds.shadingNode('blinn', asShader=1, name=materialName)
                sg = cmds.sets(renderable=1, noSurfaceShader=1, empty=1, name=materialName+'SG')
                cmds.connectAttr((material+'.outColor'),(sg+'.surfaceShader'),f=1)
                # select object
                cmds.select(name)

                # select face
                #cmds.select(name + '.f[' + str(applyFaceNumber) + ':' + str(applyFaceNumber + mtlData.faceSize) + ']', r=True)
                #applyFaceNumber = applyFaceNumber + mtlData.faceSize

                # assign material to object
                cmds.hyperShade(a=materialName, assign=1)

                # assign texture
                if len(mtlData.textureMap) > 0:
                    texturePath = os.path.join(abc, mtlData.textureMap)
                    file_node = cmds.shadingNode("file", asTexture=True, n=name+"_tex")
                    cmds.setAttr((file_node+'.fileTextureName'), texturePath, type = "string")
                    cmds.connectAttr((file_node+'.outColor'), (material+'.color'))
                else:
                    if mtlData.isAccessory:
                        cmds.setAttr(material+'.color', \
                            mtlData.diffuse[0] + 0.5 * mtlData.ambient[0],\
                            mtlData.diffuse[1] + 0.5 * mtlData.ambient[1],\
                            mtlData.diffuse[2] + 0.5 * mtlData.ambient[2])
                    else:
                        cmds.setAttr(material+'.color', \
                            mtlData.diffuse[0],\
                            mtlData.diffuse[1],\
                            mtlData.diffuse[2])
                            
                if len(mtlData.alphaMap) > 0:
                    texturePath = os.path.join(abc, mtlData.alphaMap)
                    file_node = cmds.shadingNode("file", asTexture=True, n=name+"_atex")
                    cmds.setAttr((file_node+'.fileTextureName'), texturePath, type = "string")
                    cmds.connectAttr((file_node+'.outAlpha'), (material+'.translucence'))

                """
                cmds.setAttr(material+'.transparency', \
                    mtlData.trans,\
                    mtlData.trans,\
                    mtlData.trans)
                """
                
                cmds.setAttr(material+'.specularColor', \
                    mtlData.specular[0],\
                    mtlData.specular[1],\
                    mtlData.specular[2])
                    
                cmds.setAttr(material+'.ambientColor', \
                    mtlData.ambient[0],\
                    mtlData.ambient[1],\
                    mtlData.ambient[2])
                
                # deselect all
                cmds.select(all=True, deselect=True)
execute()

