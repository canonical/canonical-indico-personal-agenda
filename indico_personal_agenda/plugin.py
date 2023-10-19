import re

from flask import session
from flask_pluginengine import render_plugin_template
from indico.core import signals
from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.core.plugins import IndicoPlugin, IndicoPluginBlueprint, url_for_plugin
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.views import WPContributionsDisplayBase
from indico.modules.events.models.events import Event
from indico.web.menu import SideMenuItem

from . import _
from .controllers import RHManageAgenda, RHStarContribution, RHViewAgenda
from .models.starred import Starred


class PersonalAgendaPlugin(IndicoPlugin):
    """Personal Agenda Plugin
    Star your favorite sessions and keep a personal agenda
    """

    default_event_settings = {"speaker_intro_message": "", "starred_intro_message": ""}

    def init(self):
        super().init()

        self.connect(signals.event.sidemenu, self._inject_menulink)

        self.connect(
            signals.menu.items,
            self._inject_management_menuitems,
            sender="event-management-sidemenu",
        )

        self.template_hook("url-shortener", self._inject_shortener_button)
        self.template_hook("vc-actions", self._inject_vc_button)

        self.inject_bundle("starbutton.css", WPContributionsDisplayBase)
        self.inject_bundle("starbuttonjs.js", WPContributionsDisplayBase)

        try:
            from indico_ngtimetable.views import WPNGTimetable

            self.template_hook("ngtimetable-menu", self._inject_ngtimetable_menu)
            self.inject_bundle("starbutton.css", WPNGTimetable)
            self.inject_bundle("starbuttonjs.js", WPNGTimetable)
        except ImportError:
            pass

    def get_blueprints(self):
        blueprint = IndicoPluginBlueprint(
            "personal_agenda", __name__, url_prefix="/event/<int:event_id>"
        )
        blueprint.add_url_rule(
            "/contributions/<int:contrib_id>/star",
            "star",
            RHStarContribution,
            methods=("POST",),
        )
        blueprint.add_url_rule(
            "/contributions/<int:contrib_id>/unstar",
            "unstar",
            RHStarContribution,
            methods=("POST",),
        )
        blueprint.add_url_rule("/agenda", "view", RHViewAgenda)

        blueprint.add_url_rule(
            "/manage/agenda", "manage", RHManageAgenda, methods=("GET", "POST")
        )
        return blueprint

    def _inject_ngtimetable_menu(self, event=None):
        if not event.is_user_registered(session.user):
            return ""

        return render_plugin_template("ngtimetable_menu.html", event=event)

    def _inject_shortener_button(self, target=None, event=None, classes=None):
        patternmatch = re.search(r"/event/(\d+)/contributions/(\d+)/", target or "")
        if not patternmatch:
            return ""

        event = Event.get(patternmatch.group(1))
        if not event.is_user_registered(session.user):
            return ""

        query = Starred.query.filter_by(
            user=session.user, contribution_id=patternmatch.group(2)
        ).limit(1)
        item = Contribution.get(patternmatch.group(2))

        is_speaker = any(
            link.is_speaker and link.person.user and link.person.user == session.user
            for link in item.person_links
        )

        starred, total = with_total_rows(query, True)

        return render_plugin_template(
            "star_button.html",
            context="contribution",
            starred=bool(starred),
            event=event,
            itemId=patternmatch.group(2),
            is_speaker=is_speaker,
            total=total,
        )

    def _inject_vc_button(self, event=None, item=None):
        if not event.is_user_registered(session.user):
            return ""

        query = Starred.query.filter_by(
            user=session.user, contribution_id=item.id
        ).limit(1)

        starred, total = with_total_rows(query, True)
        is_speaker = any(
            link.is_speaker and link.person.user and link.person.user == session.user
            for link in item.person_links
        )

        return render_plugin_template(
            "star_button.html",
            context="timetable",
            starred=is_speaker or bool(starred),
            event=event,
            itemId=item.id,
            is_speaker=is_speaker,
            total=total,
        )

    def _inject_menulink(self, sender, **kwargs):
        from indico.modules.events.contributions.util import user_has_contributions
        from indico.modules.events.layout.util import MenuEntryData

        def _visible_my_contributions(event):
            if not event.is_user_registered(session.user):
                return False

            return (
                user_has_contributions(event, session.user)
                or contribution_settings.get(event, "published")
                or event.can_manage(session.user)
            )

        yield MenuEntryData(
            title=_("My Conference"),
            name="view_agenda",
            endpoint="personal_agenda.view",
            is_enabled=True,
            position=4,
            visible=_visible_my_contributions,
        )

    def _inject_management_menuitems(self, sender, event, **kwargs):
        return SideMenuItem(
            "personal_agenda_manage",
            _("Personal Agenda"),
            url_for_plugin("personal_agenda.manage", event),
            section="customization",
        )
