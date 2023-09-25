from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import CKEditorWidget
from wtforms.fields import TextAreaField
from wtforms.validators import Optional

from . import _


class ManageAgendaForm(IndicoForm):
    speaker_intro_message = TextAreaField(
        _("Speaker Information"),
        [Optional()],
        widget=CKEditorWidget(height=250),
        description=_(
            "Information shown at the top of the speaker section on the my conference page"
        ),
    )
    starred_intro_message = TextAreaField(
        _("Starred Information"),
        [Optional()],
        widget=CKEditorWidget(height=250),
        description=_(
            "Information shown at the top of the starred section on the my conference page"
        ),
    )
