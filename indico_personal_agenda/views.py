from flask_pluginengine import render_plugin_template
from indico.core.plugins import WPJinjaMixinPlugin
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase


class WPViewAgenda(WPJinjaMixinPlugin, WPConferenceDisplayBase):
    menu_entry_plugin = "personal_agenda"
    menu_entry_name = "view_agenda"

    def _get_body(self, params):
        return render_plugin_template("agenda.html", **params)


class WPManageAgenda(WPJinjaMixinPlugin, WPEventManagement):
    sidemenu_option = "personal_agenda_manage"

    def _get_body(self, params):
        return render_plugin_template("manage.html", **params)
