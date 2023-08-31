from flask import request, session
from indico.core.db.sqlalchemy import db
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.controllers.base import RHAuthenticatedEventBase
from indico.web.util import jsonify_data
from sqlalchemy.orm import defaultload
from werkzeug.exceptions import BadRequest

from .models.starred import Starred
from .views import WPViewStarred


class RHPersonalScheduleViewStarred(RHAuthenticatedEventBase):
    def _process_args(self):
        super()._process_args()

        from .plugin import PersonalSchedulePlugin

        self.plugin = PersonalSchedulePlugin

        self.starred = (
            Starred.query.options(defaultload("contribution"))
            .filter_by(user=session.user)
            .all()
        )

    def _process(self):
        contributions = list(map(lambda starred: starred.contribution, self.starred))
        published = contribution_settings.get(self.event, "published")
        timezone = self.event.display_tzinfo

        return WPViewStarred(
            self,
            self.event,
            contributions=contributions,
            published=published,
            timezone=timezone,
        ).display()


class RHPersonalScheduleStarContribution(RHAuthenticatedEventBase):
    def _process_args(self):
        super()._process_args()

        from .plugin import PersonalSchedulePlugin

        self.plugin = PersonalSchedulePlugin
        self.contrib = Contribution.get_or_404(
            request.view_args["contrib_id"], is_deleted=False
        )
        self.star = Starred.query.with_parent(self.contrib).first()

    def _process(self):
        if request.base_url.endswith("/star"):
            if self.star:
                raise BadRequest()
            else:
                starred = Starred(contribution=self.contrib, user=session.user)
                db.session.flush()
                return jsonify_data(flash=False, action="star", id=starred.id)
        elif request.base_url.endswith("/unstar"):
            if not self.star:
                raise BadRequest()
            else:
                Starred.query.with_parent(self.contrib).delete()

            return jsonify_data(flash=False, action="unstar")
        else:
            raise BadRequest()
