bl_info = {
    "name" : "Normal & UV Statistics",
    "author" : "Curi0",
    "description" : "Show Normal & UV statistics",
    "blender" : (3, 6, 0),
    'version': (0, 2),
    "location" : "Overlays",
    "warning" : "",
    "category" : "View3D",
    'doc_url': 'https://github.com/xCuri0/NormalUVStats',
    'tracker_url': 'https://github.com/xCuri0/NormalUVStats/issues'
}

import bpy
import blf
import queue
import threading

from bpy.utils import register_class, unregister_class

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       AddonPreferences,
                       )
from bpy.app.handlers import persistent

overlay = bpy.types.VIEW3D_PT_overlay

font_id = 0
overlay_position = (9, -66)
gap = 15.4545
system = bpy.context.preferences.system

def update_normaluvs(self, context):
    addon_prefs = context.preferences.addons[__package__].preferences
    if (not "NormalUVs" in bpy.app.driver_namespace) and addon_prefs.normaluvs_show:
        bpy.app.driver_namespace["NormalUVs"] = NormalUVsHandler(context, None, context.object)
    else:        
        if "NormalUVs" in bpy.app.driver_namespace:
            bpy.app.driver_namespace["NormalUVs"].remove_handles()
            del bpy.app.driver_namespace["NormalUVs"]

def update_normaluvs_size_color(self, context):
    addon_prefs = context.preferences.addons[__package__].preferences
    bpy.app.driver_namespace["NormalUVs"].font_color = addon_prefs.normaluvs_font_color
    bpy.app.driver_namespace["NormalUVs"].gap = gap*(addon_prefs.normaluvs_font_size/10)


class NormalUVsProps(AddonPreferences):
    bl_idname = __name__

    normaluvs_show : BoolProperty(
        name = "Normal & UV Statistics",
        default = False,
        update = update_normaluvs
    )
    
    normaluvs_loadcalc : BoolProperty(
        name = "Calculate totals when .blend file loaded",
        default = True,
    )
    
    normaluvs_nonecalc : BoolProperty(
        name = "Calculate totals when none selected",
        default = False,
    )

    normaluvs_font_color : FloatVectorProperty(
        name = "Font Color",
        subtype = "COLOR",
        default = (1.0,1.0,1.0,1.0),
        size = 4,
        update = update_normaluvs_size_color
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "normaluvs_font_color")
        layout.prop(self, "normaluvs_loadcalc")
        layout.prop(self, "normaluvs_nonecalc")

class NormalUVsHandler:
    def __init__(self, context, prop, obj):
        self.obj = obj
        self.vtx_normal_count = 0
        self.uv_vtx_count = 0
        self.total_vtx_normal_count = -2
        self.total_uv_vtx_count = -2
        self.area_height = 0
        self.screen_position = (0,0)
        self.font_size = 11
        self.font_color = context.preferences.addons[__package__].preferences.normaluvs_font_color
        
        self.gap = 17
        self.draw_normal_uvs = bpy.types.SpaceView3D.draw_handler_add(self.draw_normal_uvs,(context,),'WINDOW', 'POST_PIXEL')
        self.depsgraph_handle = bpy.app.handlers.depsgraph_update_post.append(self.onDepsgraph)
        self.showOverlay = True
        
        self.calcThread = None
        self.aCalcThread = None
        
        # Queue for calculation
        self.q = queue.LifoQueue(maxsize=1)

        # Queue for total calculation
        self.qAll = queue.LifoQueue(maxsize=1)

        self.calcThread = threading.Thread(name="Normal UV Calc", target=self.calcWorker)
        self.aCalcThread = threading.Thread(name="Normal UV Calc All", target=self.calcAllWorker)
        
        self.depsgraph = False

        self.calcThread.start()
        self.aCalcThread.start()

    def calcWorker(self):
        while True:
            objs = self.q.get()
            if objs is None:
                break

            try:
                if len(objs[0]) == len([ob for ob in bpy.context.view_layer.objects if ob.visible_get()]):
                    # move to all queue
                    self.qAll.put_nowait(objs)
                else:
                    self.calcObjs(objs[0], objs[1], False, True)

            except ReferenceError:
                pass

            self.q.task_done()

    def calcAllWorker(self):
        while True:
            objs = self.qAll.get()

            if objs is None:
                break

            self.calcObjs(objs[0], objs[1], True, (not len(objs[0]) == 0))

            self.qAll.task_done()
   
    def redrawOverlay(self):
        for area in bpy.context.screen.areas: 
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return None

    def calcObjs(self, objs, depsgraph, calcAll, updAll):
        obj_to_count = []
        normal_count = 0
        uv_count = 0
        
        if calcAll:
            obj_to_count = [ob for ob in bpy.context.view_layer.objects if ob.visible_get()]
        else:
            obj_to_count = objs
            
        # show as calculating
        if calcAll:           
            self.total_vtx_normal_count = -1
            self.total_uv_vtx_count = -1

        if updAll:
            self.vtx_normal_count = -1
            self.uv_vtx_count = -1
        
        # redraw
        if not bpy.app.timers.is_registered(self.redrawOverlay):
            bpy.app.timers.register(self.redrawOverlay)

        # update count
        for obj in obj_to_count:
            try:
                objd = obj.evaluated_get(depsgraph)
            except ReferenceError:
                continue

            if objd and obj.type == 'MESH':
                normal_count += self.get_normal_count(objd.data)
                uv_count += self.get_uv_vtx_count(objd.data)

        if calcAll:
            self.total_uv_vtx_count = uv_count
            self.total_vtx_normal_count = normal_count
        
        if updAll:
            self.uv_vtx_count = uv_count
            self.vtx_normal_count = normal_count

        # redraw when complete
        if not bpy.app.timers.is_registered(self.redrawOverlay):
            bpy.app.timers.register(self.redrawOverlay)
              
    def onDepsgraph(self, scene, depsgraph):
        if bpy.context.object and not bpy.context.object.mode == 'OBJECT' and not self.showOverlay:
            return
    
        selection = bpy.context.selected_objects

        # Calculate totals on file load
        if not self.depsgraph:
            self.depsgraph = True
            if bpy.context.preferences.addons[__package__].preferences.normaluvs_loadcalc:
                try:
                    self.qAll.put_nowait([[], depsgraph])
                except queue.full:
                    pass

        if (len(selection) == 0 and bpy.context.preferences.addons[__package__].preferences.normaluvs_nonecalc):
            try:
                self.qAll.put_nowait([[], depsgraph])
            except queue.full:
                pass
        else:
            try:
                self.q.put_nowait([selection, depsgraph])
            except queue.full:
                pass

    def get_uv_vtx_count(self,mesh):
        # Based on https://blender.stackexchange.com/a/44896
        uvs = []
        try:
            for loop in mesh.loops:
                uv_indices = mesh.uv_layers.active.data[loop.index].uv
                uvs.append(tuple(map(lambda x: round(x,3), uv_indices[:])))
            return len(set(uvs))
        except (AttributeError, IndexError):
            return 0

    def get_normal_count(self, mesh):
        # Blender 4.1+ does not require this
        if (4, 1, 0) > bpy.app.version:
            mesh.calc_normals_split()

        #With Help from CarrotKing Marko "Fuxna" Tatalovic
        unique_i_to_ns = []
        seen = set()

        for loop in mesh.loops:
            vertex_index = loop.vertex_index
            index_to_normal = { 'index': vertex_index, 'normals' : tuple(loop.normal)}
            unique_id = (vertex_index, tuple(loop.normal))

            if unique_id not in seen:
                seen.add(unique_id)
                unique_i_to_ns.append(index_to_normal)            
        return len(unique_i_to_ns)
    

    def draw_normal_uvs(self, context):
        # only object mode supported for now
        self.showOverlay = bpy.context.space_data.overlay.show_overlays

        if bpy.context.object and not bpy.context.object.mode == 'OBJECT' or not self.showOverlay:
            return

        if len(bpy.context.selected_objects):
            # same behaviour as statistics
            if not bpy.context.view_layer.objects.active.type == 'MESH':
                return

        dpi = float(system.dpi) / 72.0
        for bl_area in bpy.context.window.screen.areas:
            if bl_area.type == "VIEW_3D":
                self.area_height = bl_area.height
        
        width = 0
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for r in a.regions:
                    if r.type == 'TOOLS':
                        width = r.width
                        break

        self.screen_position = (0 + (float(overlay_position[0]) * dpi) + width, self.area_height + (overlay_position[1] * dpi))
        gap = float(self.gap) * dpi

        blf.size(font_id, float(self.font_size) * dpi)
        blf.color(font_id, self.font_color[0], self.font_color[1], self.font_color[2], 1)
        blf.enable(font_id, blf.SHADOW)

        start = 1

        if bpy.context.space_data.region_3d.is_orthographic_side_view and bpy.context.space_data.region_3d.view_perspective == 'ORTHO':
            start += 1
        if bpy.context.space_data.overlay.show_stats:
            start += 5
        if bpy.context.space_data.overlay.show_text:   
            start += 2

        if not self.depsgraph:
            self.onDepsgraph(None, bpy.context.evaluated_depsgraph_get())

        blf.position(font_id, self.screen_position[0], self.screen_position[1] - gap*start, 0)

        str_n_count = '...'
        str_uv_count = '...'

        str_t_n_count = '?'
        str_t_uv_count = '?'

        if not self.vtx_normal_count == -1:
            str_n_count = f'{self.vtx_normal_count:,}'

        if not self.uv_vtx_count == -1:
            str_uv_count = f'{self.uv_vtx_count:,}'
            
        if self.total_vtx_normal_count == -1:
            str_t_n_count = '...'
        elif not self.total_vtx_normal_count == -2:
            str_t_n_count = f'{self.total_vtx_normal_count:,}'
            

        if self.total_uv_vtx_count == -1:
            str_t_uv_count = '...'
        elif not self.total_uv_vtx_count == -2:
            str_t_uv_count = f'{self.total_uv_vtx_count:,}'


        if len(bpy.context.selected_objects):   
            blf.draw(font_id, "Normals      %s / %s" % (str_n_count, str_t_n_count))
        else:
            blf.draw(font_id, "Normals      %s" % (str_t_n_count))

        blf.position(font_id, self.screen_position[0], self.screen_position[1] - gap*(start + 1), 0)

        if len(bpy.context.selected_objects):
            blf.draw(font_id, "UVs             %s / %s" % (str_uv_count, str_t_uv_count))
        else:
            blf.draw(font_id, "UVs             %s" % (str_t_uv_count))

    def remove_handles(self):
        self.q.put(None)
        self.qAll.put(None)

        # wait for calculation to finish
        if self.calcThread:
            self.calcThread.join()

        if self.aCalcThread:
            self.aCalcThread.join()
            
        bpy.app.handlers.depsgraph_update_post.remove(self.onDepsgraph)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_normal_uvs, 'WINDOW')

@persistent
def preload_handle(dummy):
    if "NormalUVs" in bpy.app.driver_namespace:
        bpy.app.driver_namespace["NormalUVs"].remove_handles()
        del bpy.app.driver_namespace["NormalUVs"]

@persistent
def load_handle(dummy):
    update_normaluvs(None, bpy.context)

def draw_normal_uvs_overlay(self, context):
    layout = self.layout
    addon_prefs = context.preferences.addons[__package__].preferences

    row = layout.row(align=True)
    row.prop(addon_prefs, 'normaluvs_show')

def register():
    register_class(NormalUVsProps)
    overlay.append(draw_normal_uvs_overlay)

    if not load_handle in bpy.app.handlers.load_post:
        bpy.app.handlers.load_pre.append(preload_handle)
        bpy.app.handlers.load_post.append(load_handle)

def unregister():
    overlay.remove(draw_normal_uvs_overlay)
    
    if "NormalUVs" in bpy.app.driver_namespace:
        bpy.app.driver_namespace["NormalUVs"].remove_handles()
        del bpy.app.driver_namespace["NormalUVs"]
            
    unregister_class(NormalUVsProps)
    
if __name__ == "__main__":
    register()
