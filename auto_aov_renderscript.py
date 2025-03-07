import bpy
from bpy.app.handlers import persistent
from mathutils import Vector


@persistent
def auto_assignlight_scene(dummy):
    global LAS_newLight
    global LAS_originLight
    lightgroup_dict = {}
    lightcollection_dict = {}
    light_dict = {}
    for viewlayer in bpy.context.scene.view_layers:
        if viewlayer.name[:7] != "-_-exP_" and "_DATA" not in viewlayer.name:
            lightgroups = []
            for lightgroup in viewlayer.lightgroups:
                lightgroups.append(lightgroup.name)
            lightgroup_dict[viewlayer.name] = lightgroups
        for collection in viewlayer.layer_collection.children:
            light_collection = []
            if collection.name.startswith("lgt_") and collection.exclude == False:
                light_collection.append(collection.name)
                lightcollection_dict[viewlayer.name] = light_collection
                lights = []
                for object in bpy.data.collections[collection.name].all_objects:
                    if object.type == "LIGHT":
                        lights.append(object.name)
                light_dict[viewlayer.name] = lights
    LAS_originLight = []
    LAS_newLight = []
    for key in lightgroup_dict.keys():
        for lightgroup in lightgroup_dict[key]:
            for i, lobe in enumerate(["diffuse_", "specular_", "transmission_", "volume_"]):
                z = 0.001 * i
                offset_local = Vector((0, 0, z))
                if lightgroup.startswith(f"{lobe}"):
                    light = lightgroup.removeprefix(f"{lobe}")
                    for light_object_name in light_dict[key]:
                        light_object = bpy.context.scene.objects.get(light_object_name)
                        if (
                            light_object.name == light
                            or light_object.name.split(".")[0] == light
                        ):
                            obj = bpy.data.objects.get(light_object.name)
                            duplicate = obj.copy()
                            duplicate.data = obj.data.copy()
                            bpy.data.collections[
                                lightcollection_dict[key][0]
                            ].objects.link(duplicate)
                            duplicate.name = f"{lobe}{light}"
                            duplicate.lightgroup = lightgroup
                            duplicate.visible_diffuse = False
                            duplicate.visible_glossy = False
                            duplicate.visible_transmission = False
                            duplicate.visible_volume_scatter = False
                            offset_world = (
                                duplicate.matrix_world.to_quaternion() @ offset_local
                            )
                            duplicate.location += offset_world
                            LAS_newLight.append(duplicate.name)
                            if lobe == "diffuse_":
                                duplicate.visible_diffuse = True
                            if lobe == "specular_":
                                duplicate.visible_glossy = True
                            if lobe == "transmission_":
                                duplicate.visible_transmission = True
                            if lobe == "volume_":
                                duplicate.visible_volume_scatter = True
                            LAS_originLight.append(light_object_name)
    LAS_originLight = list(set(LAS_originLight))
    LAS_newLight = list(set(LAS_newLight))
    for light in LAS_originLight:
        obj = bpy.data.objects.get(light)
        obj.hide_render = True


@persistent
def auto_restorelight_scene(dummy):
    global LAS_newLight
    global LAS_originLight
    if LAS_originLight:
        for light in LAS_originLight:
            obj = bpy.data.objects.get(light)
            obj.hide_render = False
    if LAS_newLight:
        for light in LAS_newLight:
            obj = bpy.data.objects.get(light)
            if obj:
                # Unlink from all collections
                for collection in obj.users_collection:
                    collection.objects.unlink(obj)

                # Unlink from the scene if it's directly linked
                if obj and obj.name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(obj)

                # Safely remove the object
                bpy.data.objects.remove(obj, do_unlink=True)
    LAS_originLight = []
    LAS_newLight = []
