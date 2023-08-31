import re

from flask import session
from flask_pluginengine import render_plugin_template
from indico.core import signals
from indico.core.plugins import IndicoPlugin, IndicoPluginBlueprint
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.views import WPContributionsDisplayBase
from indico.modules.events.layout.util import MenuEntryData

from . import _
from .controllers import (
    RHPersonalScheduleStarContribution,
    RHPersonalScheduleViewStarred,
)
from .models.starred import Starred


class PersonalSchedulePlugin(IndicoPlugin):
    """Personal Schedule Plugin
    Star your favorite sessions and keep a personal schedule
    """

    def init(self):
        super().init()

        self.connect(signals.event.sidemenu, self._inject_menulink)

        self.template_hook("url-shortener", self._inject_contrib_button)

        self.inject_bundle("contribution_display.css", WPContributionsDisplayBase)
        self.inject_bundle("contribution_display_js.js", WPContributionsDisplayBase)

    def _inject_contrib_button(self, target=None, event=None, classes=None):
        patternmatch = re.search(r"/event/(\d+)/contributions/(\d+)/", target or "")
        if patternmatch:
            starred = Starred.query.filter_by(
                user=session.user, contribution_id=patternmatch.group(2)
            ).first()
            return render_plugin_template(
                "contrib_star_button.html", starred=bool(starred)
            )

    def get_blueprints(self):
        blueprint = IndicoPluginBlueprint(
            "personal_schedule", __name__, url_prefix="/event/<int:event_id>"
        )
        blueprint.add_url_rule(
            "/contributions/<int:contrib_id>/star",
            "star",
            RHPersonalScheduleStarContribution,
            methods=("POST",),
        )
        blueprint.add_url_rule(
            "/contributions/<int:contrib_id>/unstar",
            "unstar",
            RHPersonalScheduleStarContribution,
            methods=("POST",),
        )
        blueprint.add_url_rule(
            "/contributions/starred", "view", RHPersonalScheduleViewStarred
        )
        return blueprint

    def _inject_menulink(self, sender, **kwargs):
        def _visible_timetable(event):
            return contribution_settings.get(event, "published") or event.can_manage(
                session.user
            )

        yield MenuEntryData(
            title=_("Your talks"),
            name="personal_schedule",
            endpoint="personal_schedule.view",
            is_enabled=True,
            position=4,
            visible=_visible_timetable,
        )
