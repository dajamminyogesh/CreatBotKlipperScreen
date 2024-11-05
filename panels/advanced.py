import logging
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

class Panel(ScreenPanel):
    def __init__(self, screen, title):
        title = title or _("Advanced")
        super().__init__(screen, title)
        self.advanced = {}
        self.menu_list ={}
        self.advanced_options = [
            {"adaptive_leveling": {"section": "main", "name": _("Adaptive Bed Leveling"), "type": "binary",
                               "tooltip": _("Leveling Only in the Actual Print Area"),
                               "value": "True", "callback": self.set_adaptive_leveling}},
        ]
        options = self.advanced_options
        self.labels['advanced_menu'] = self._gtk.ScrolledWindow()
        self.labels['advanced'] = Gtk.Grid()
        self.labels['advanced_menu'].add(self.labels['advanced'])
        for option in options:
            name = list(option)[0]
            res = self.add_option('advanced', self.advanced, name, option[name])
            self.menu_list.update(res)
        self.content.add(self.labels['advanced_menu'])

    def set_adaptive_leveling(self, *args):
        enable_adaptive_leveling = any(args)
        script_value = True if enable_adaptive_leveling else False
        script = KlippyGcodes.set_save_variables("adaptive_meshing", script_value)
        self._screen._send_action(None, "printer.gcode.script", {"script": script})
        logging.info(f"Set adaptive leveling: {script_value}")

    def process_update(self, action, data):
        if action != "notify_status_update":
            return
        if 'save_variables' in data and 'variables' in data['save_variables']:
            variables = data['save_variables']['variables']
            if 'adaptive_meshing' in variables:
                self.menu_list['adaptive_leveling'].set_active(variables['adaptive_meshing'])
