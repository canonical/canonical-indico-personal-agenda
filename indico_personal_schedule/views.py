from flask_pluginengine import render_plugin_template
from indico.core.plugins import WPJinjaMixinPlugin
from indico.modules.events.views import WPConferenceDisplayBase


class WPViewStarred(WPJinjaMixinPlugin, WPConferenceDisplayBase):
    def _get_body(self, params):
        return render_plugin_template("starred_list.html", **params)
