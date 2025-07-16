bl_info = {
    "name": "Switch Layout",
    "author": "Mox Alehin",
    "version": (1, 17),
    "blender": (3, 0, 0),
    "description": "Pie menus for switching scenes and workspaces with sector-based positioning and custom icons",
    "category": "Interface",
}

import bpy
from bpy.types import Operator, Menu, AddonPreferences
from bpy.props import StringProperty, EnumProperty, CollectionProperty
import json
import os

class SCENE_MT_switch_menu(Menu):
    bl_idname = "SCENE_MT_switch_menu"
    bl_label = "Switch Scene"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        addon_prefs = context.preferences.addons[__name__].preferences
        sectors = {i: None for i in range(8)}
        for item in addon_prefs.scene_items:
            if item.settings.scene_target_enum != 'NONE':
                sector_map = {
                    'Top': 3, 'Top Right': 5, 'Right': 1, 'Bottom Right': 7,
                    'Bottom': 2, 'Bottom Left': 6, 'Left': 0, 'Top Left': 4
                }
                sector_idx = sector_map[item.position]
                target_name = item.settings.scene_target_enum
                icon = item.settings.icon
                if target_name in bpy.data.scenes:
                    sectors[sector_idx] = (target_name, icon, "scene.switch", 'scene_name')

        for i in range(8):
            if sectors[i]:
                name, icon, op, prop = sectors[i]
                operator = pie.operator(op, text=name, icon=icon)
                setattr(operator, prop, name)
            else:
                pie.separator()

class SCENE_OT_switch_operator(Operator):
    bl_idname = "scene.switch"
    bl_label = "Switch Scene"
    scene_name: StringProperty()

    def execute(self, context):
        context.window.scene = bpy.data.scenes[self.scene_name]
        return {'FINISHED'}

class WORKSPACE_MT_switch_menu(Menu):
    bl_idname = "WORKSPACE_MT_switch_menu"
    bl_label = "Switch Workspace"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        addon_prefs = context.preferences.addons[__name__].preferences
        sectors = {i: None for i in range(8)}
        for item in addon_prefs.workspace_items:
            if item.settings.workspace_target_enum != 'NONE':
                sector_map = {
                    'Top': 3, 'Top Right': 5, 'Right': 1, 'Bottom Right': 7,
                    'Bottom': 2, 'Bottom Left': 6, 'Left': 0, 'Top Left': 4
                }
                sector_idx = sector_map[item.position]
                target_name = item.settings.workspace_target_enum
                icon = item.settings.icon
                if target_name in bpy.data.workspaces:
                    sectors[sector_idx] = (target_name, icon, "workspace.switch", 'workspace_name')

        for i in range(8):
            if sectors[i]:
                name, icon, op, prop = sectors[i]
                operator = pie.operator(op, text=name, icon=icon)
                setattr(operator, prop, name)
            else:
                pie.separator()

class WORKSPACE_OT_switch_operator(Operator):
    bl_idname = "workspace.switch"
    bl_label = "Switch Workspace"
    workspace_name: StringProperty()

    def execute(self, context):
        context.window.workspace = bpy.data.workspaces[self.workspace_name]
        return {'FINISHED'}

class PieItemSettings(bpy.types.PropertyGroup):
    target: StringProperty(default='NONE')
    scene_target_enum: EnumProperty(
        name="",
        description="Select scene",
        items=lambda self, context: [
            ('NONE', "", "Do not show in pie menu")
        ] + [
            (s.name, s.name, "") for s in bpy.data.scenes
        ],
        update=lambda self, context: update_target(self, context, 'scene')
    )
    workspace_target_enum: EnumProperty(
        name="",
        description="Select workspace",
        items=lambda self, context: [
            ('NONE', "", "Do not show in pie menu")
        ] + [
            (w.name, w.name, "") for w in bpy.data.workspaces
        ],
        update=lambda self, context: update_target(self, context, 'workspace')
    )
    icon: EnumProperty(
        name="",
        description="Select icon",
        items=[
            ('NONE', "", ""),
            ('SCENE_DATA', "Scene", ""),
            ('WORKSPACE', "Workspace", ""),
            ('OUTLINER_OB_OBJECT', "Object", ""),
            ('MESH_CUBE', "Cube", ""),
            ('LIGHT', "Light", ""),
            ('CAMERA_DATA', "Camera", ""),
            ('MODIFIER', "Modifier", ""),
            ('RENDER_RESULT', "Render", ""),
            ('VIEW3D', "3D View", ""),
            ('NODETREE', "Node Tree", ""),
            ('IMAGE_DATA', "Image", ""),
            ('RESTRICT_VIEW_OFF', "Computer", ""),
            ('SHADING_RENDERED', "Shading", ""),
            ('ANIM', "Anim", ""),
            ('FILE_SCRIPT', "Script", ""),
            ('MATERIAL', "Material", ""),
            ('GEOMETRY_NODES', "Geo Nodes", ""),
            ('SCENE_DATA', "Scene", ""),
            ('COLLAPSEMENU', "Menu", ""),
            ('MESH_DATA', "Mesh", ""),
            ('UV', "UV", ""),
            ('SCULPTMODE_HLT', "Sculpting", ""),
        ],
        default='NONE'
    )

class PieItem(bpy.types.PropertyGroup):
    position: StringProperty()
    settings: bpy.props.PointerProperty(type=PieItemSettings)

def update_target(self, context, target_type):
    if target_type == 'scene':
        self.target = self.scene_target_enum
    else:
        self.target = self.workspace_target_enum
    addon_prefs = context.preferences.addons[__name__].preferences
    items = addon_prefs.scene_items if target_type == 'scene' else addon_prefs.workspace_items
    for item in items:
        if item.settings != self and item.settings.target == self.target and self.target != 'NONE':
            item.settings.target = 'NONE'
            if target_type == 'scene':
                item.settings.scene_target_enum = 'NONE'
            else:
                item.settings.workspace_target_enum = 'NONE'

class PREFS_OT_save_settings(Operator):
    bl_idname = "prefs.save_settings"
    bl_label = "Save Settings"

    def execute(self, context):
        addon_prefs = context.preferences.addons[__name__].preferences
        config = {
            'scene_items': [
                {'position': item.position, 'target': item.settings.target, 'icon': item.settings.icon}
                for item in addon_prefs.scene_items
            ],
            'workspace_items': [
                {'position': item.position, 'target': item.settings.target, 'icon': item.settings.icon}
                for item in addon_prefs.workspace_items
            ]
        }
        config_path = os.path.join(bpy.utils.user_resource('CONFIG'), 'switch_layout_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return {'FINISHED'}

class PREFS_OT_load_settings(Operator):
    bl_idname = "prefs.load_settings"
    bl_label = "Load Settings"

    def execute(self, context):
        addon_prefs = context.preferences.addons[__name__].preferences
        config_path = os.path.join(bpy.utils.user_resource('CONFIG'), 'switch_layout_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            addon_prefs.scene_items.clear()
            addon_prefs.workspace_items.clear()
            
            positions = ['Top', 'Top Left', 'Top Right', 'Left', 'Right', 'Bottom Left', 'Bottom Right', 'Bottom']
            
            for item_data in config['scene_items']:
                if item_data['position'] in positions:
                    item = addon_prefs.scene_items.add()
                    item.position = item_data['position']
                    item.settings.target = item_data['target']
                    item.settings.scene_target_enum = item_data['target']
                    item.settings.icon = item_data['icon']
            
            for item_data in config['workspace_items']:
                if item_data['position'] in positions:
                    item = addon_prefs.workspace_items.add()
                    item.position = item_data['position']
                    item.settings.target = item_data['target']
                    item.settings.workspace_target_enum = item_data['target']
                    item.settings.icon = item_data['icon']
        return {'FINISHED'}

class SwitchMasterPreferences(AddonPreferences):
    bl_idname = __name__

    scene_items: CollectionProperty(type=PieItem)
    workspace_items: CollectionProperty(type=PieItem)

    def draw(self, context):
        layout = self.layout

        positions = ['Top', 'Top Left', 'Top Right', 'Left', 'Right', 'Bottom Left', 'Bottom Right', 'Bottom']
        
        if not self.scene_items:
            for pos in positions:
                item = self.scene_items.add()
                item.position = pos
                item.settings.target = 'NONE'
                item.settings.scene_target_enum = 'NONE'
                item.settings.icon = 'NONE'

        if not self.workspace_items:
            for pos in positions:
                item = self.workspace_items.add()
                item.position = pos
                item.settings.target = 'NONE'
                item.settings.workspace_target_enum = 'NONE'
                item.settings.icon = 'NONE'

        box = layout.box()
        box.label(text="Scene Menu Settings")
        
        row = box.row(align=True)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Top')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Top')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Top')].settings.icon)
        row.label(text="")
        
        row = box.row(align=True)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Top Left')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Top Left')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Top Left')].settings.icon)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Top Right')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Top Right')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Top Right')].settings.icon)
        row.label(text="")

        row = box.row(align=True)
        row.prop(self.scene_items[positions.index('Left')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Left')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Left')].settings.icon)
        row.label(text="")
        row.label(text="")
        row.prop(self.scene_items[positions.index('Right')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Right')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Right')].settings.icon)

        row = box.row(align=True)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Bottom Left')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Bottom Left')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Bottom Left')].settings.icon)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Bottom Right')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Bottom Right')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Bottom Right')].settings.icon)
        row.label(text="")

        row = box.row(align=True)
        row.label(text="")
        row.prop(self.scene_items[positions.index('Bottom')].settings, "scene_target_enum", text="")
        row.prop(self.scene_items[positions.index('Bottom')].settings, "icon", text="", icon_only=True, icon=self.scene_items[positions.index('Bottom')].settings.icon)
        row.label(text="")

        box = layout.box()
        box.label(text="Workspace Menu Settings")
        
        row = box.row(align=True)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Top')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Top')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Top')].settings.icon)
        row.label(text="")
        
        row = box.row(align=True)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Top Left')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Top Left')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Top Left')].settings.icon)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Top Right')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Top Right')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Top Right')].settings.icon)
        row.label(text="")

        row = box.row(align=True)
        row.prop(self.workspace_items[positions.index('Left')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Left')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Left')].settings.icon)
        row.label(text="")
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Right')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Right')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Right')].settings.icon)

        row = box.row(align=True)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Bottom Left')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Bottom Left')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Bottom Left')].settings.icon)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Bottom Right')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Bottom Right')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Bottom Right')].settings.icon)
        row.label(text="")

        row = box.row(align=True)
        row.label(text="")
        row.prop(self.workspace_items[positions.index('Bottom')].settings, "workspace_target_enum", text="")
        row.prop(self.workspace_items[positions.index('Bottom')].settings, "icon", text="", icon_only=True, icon=self.workspace_items[positions.index('Bottom')].settings.icon)
        row.label(text="")

        box = layout.box()
        box.label(text="Config Management")
        row = box.row()
        row.operator("prefs.save_settings", text="Save Settings")
        row.operator("prefs.load_settings", text="Load Settings")

addon_keymaps = []

def load_settings_on_file_open(dummy):
    # Delay execution to ensure file is fully loaded
    bpy.app.timers.register(lambda: bpy.ops.prefs.load_settings(), first_interval=1.0)

def register():
    bpy.utils.register_class(PieItemSettings)
    bpy.utils.register_class(PieItem)
    bpy.utils.register_class(SCENE_MT_switch_menu)
    bpy.utils.register_class(SCENE_OT_switch_operator)
    bpy.utils.register_class(WORKSPACE_MT_switch_menu)
    bpy.utils.register_class(WORKSPACE_OT_switch_operator)
    bpy.utils.register_class(PREFS_OT_save_settings)
    bpy.utils.register_class(PREFS_OT_load_settings)
    bpy.utils.register_class(SwitchMasterPreferences)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY', region_type='WINDOW')
        
        kmi_scene = km.keymap_items.new('wm.call_menu_pie', type='Q', value='PRESS', shift=True)
        kmi_scene.properties.name = "SCENE_MT_switch_menu"
        addon_keymaps.append((km, kmi_scene))
        
        kmi_workspace = km.keymap_items.new('wm.call_menu_pie', type='Q', value='PRESS', alt=True)
        kmi_workspace.properties.name = "WORKSPACE_MT_switch_menu"
        addon_keymaps.append((km, kmi_workspace))
    bpy.app.handlers.load_post.append(load_settings_on_file_open)

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    addon_prefs = bpy.context.preferences.addons.get(__name__)
    if addon_prefs:
        addon_prefs.preferences.scene_items.clear()
        addon_prefs.preferences.workspace_items.clear()

    bpy.utils.unregister_class(PieItemSettings)
    bpy.utils.unregister_class(PieItem)
    bpy.utils.unregister_class(SCENE_MT_switch_menu)
    bpy.utils.unregister_class(SCENE_OT_switch_operator)
    bpy.utils.unregister_class(WORKSPACE_MT_switch_menu)
    bpy.utils.unregister_class(WORKSPACE_OT_switch_operator)
    bpy.utils.unregister_class(PREFS_OT_save_settings)
    bpy.utils.unregister_class(PREFS_OT_load_settings)
    bpy.utils.unregister_class(SwitchMasterPreferences)
    bpy.app.handlers.load_post.remove(load_settings_on_file_open)

if __name__ == "__main__":
    register()