import icalendar
from flask import flash, redirect, request, session
from indico.core.db.sqlalchemy import db
from indico.core.plugins import url_for_plugin
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.contributions.util import get_contributions_for_user
from indico.modules.events.controllers.base import (
    RHAuthenticatedEventBase,
    RHDisplayEventBase,
)
from indico.modules.events.management.controllers import RHManageEventBase
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import allow_signed_url
from indico.web.util import jsonify_data
from sqlalchemy import func
from sqlalchemy.orm import defaultload
from werkzeug.exceptions import BadRequest
from werkzeug.routing.exceptions import BuildError

from . import _
from .forms import ManageAgendaForm
from .models.starred import Starred
from .views import WPManageAgenda, WPViewAgenda


def get_plugin():
    from .plugin import PersonalAgendaPlugin

    return PersonalAgendaPlugin


class RHViewAgenda(RHAuthenticatedEventBase):
    def _process_args(self):
        super()._process_args()

        self.plugin = get_plugin()

        self.starred = (
            Starred.query.options(defaultload("contribution"))
            .join(Contribution)
            .filter(Starred.user == session.user)
            .filter(Contribution.event == self.event)
            .all()
        )

        def sortContrib(contrib):
            for person_link in contrib.person_links:
                if person_link.is_speaker:
                    return 0
                elif person_link.author_type == AuthorType.primary:
                    return 1
                elif person_link.author_type == AuthorType.secondary:
                    return 2
                elif contrib.can_manage(
                    session.user, "submit", allow_admin=False, check_parent=False
                ):
                    return 3
            return 4

        contribs = get_contributions_for_user(self.event, session.user)
        self.mycontributions = sorted(contribs, key=sortContrib)

    def _process(self):
        if not self.event.is_user_registered(session.user):
            return redirect(
                url_for(
                    "event_registration.display_regform_list", event_id=self.event.id
                )
            )

        contributions = list(map(lambda starred: starred.contribution, self.starred))
        published = contribution_settings.get(self.event, "published")
        timezone = self.event.display_tzinfo

        speaker_intro_message = self.plugin.event_settings.get(
            self.event, "speaker_intro_message"
        )
        starred_intro_message = self.plugin.event_settings.get(
            self.event, "starred_intro_message"
        )

        try:
            timetable_link = url_for_plugin("ngtimetable.view", self.event)
        except BuildError:
            timetable_link = url_for("timetable.timetable", self.event)

        return WPViewAgenda(
            self,
            self.event,
            starred_intro_message=starred_intro_message,
            starred_contributions=contributions,
            timetable_link=timetable_link,
            speaker_intro_message=speaker_intro_message,
            own_contributions=self.mycontributions,
            published=published,
            timezone=timezone,
        ).display()


class RHStarContribution(RHAuthenticatedEventBase):
    def _process_args(self):
        super()._process_args()

        self.plugin = get_plugin()
        self.contrib = Contribution.get_or_404(
            request.view_args["contrib_id"], is_deleted=False
        )
        self.star = Starred.query.filter_by(
            contribution=self.contrib, user=session.user
        ).first()

    def _process(self):
        if not self.contrib.event.is_user_registered(session.user):
            raise BadRequest()
        elif request.base_url.endswith("/star") and not self.star:
            starred = Starred(contribution=self.contrib, user=session.user)
            db.session.add(starred)
            db.session.flush()
            return jsonify_data(flash=False, action="star", id=starred.id)
        elif request.base_url.endswith("/unstar") and self.star:
            db.session.delete(self.star)
            db.session.flush()
            return jsonify_data(flash=False, action="unstar")
        else:
            raise BadRequest()


class RHManageAgenda(RHManageEventBase):
    def _process_args(self):
        super()._process_args()
        self.plugin = get_plugin()

    def get_star_stats(self):
        star_count = func.count(Starred.id)

        query = (
            Contribution.query.with_entities(
                Contribution, star_count.label("star_count")
            )
            .join(Starred, Contribution.id == Starred.contribution_id)
            .filter(Contribution.event == self.event)
            .group_by(Contribution.id)
            .having(star_count >= 1)
            .order_by(star_count.desc(), Contribution.friendly_id)
        )

        return query.all()

    def _process(self):
        plugin_event_settings = self.plugin.event_settings.get_all(self.event)
        defaults = FormDefaults(
            {k: v for k, v in plugin_event_settings.items() if v is not None}
        )

        form = ManageAgendaForm(obj=defaults)
        contributions = self.get_star_stats()

        if form.validate_on_submit():
            self.plugin.event_settings.set_multi(self.event, form.data)
            flash(_("Settings saved"), "success")

        return WPManageAgenda(
            self, self.event, form=form, contributions=contributions
        ).display()


@allow_signed_url
class RHViewAgendaICS(RHDisplayEventBase):
    def _process(self):
        from indico.modules.events.contributions.ical import (
            generate_contribution_component,
        )

        calendar = icalendar.Calendar()
        calendar.add("version", "2.0")
        calendar.add("prodid", "-//CERN//INDICO//EN")

        if self.event.can_access(session.user):
            starred = (
                Starred.query.options(defaultload("contribution"))
                .join(Contribution)
                .filter(Starred.user == session.user)
                .filter(Contribution.event == self.event)
                .all()
            )

            for star in starred:
                contrib = star.contribution
                if not contrib.start_dt or not contrib.can_access(session.user):
                    continue
                comp = generate_contribution_component(contrib)
                calendar.add_component(comp)

        return calendar.to_ical()
