from indico.core.db.sqlalchemy import db
from indico.util.string import format_repr


class Starred(db.Model):
    __tablename__ = "starred"
    __table_args__ = {"schema": "plugin_personal_schedule"}

    id = db.Column(db.Integer, primary_key=True)

    contribution_id = db.Column(
        db.Integer, db.ForeignKey("events.contributions.id"), index=True, nullable=False
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.users.id"), nullable=False)

    user = db.relationship("User", lazy=True, backref=db.backref("starred", lazy=True))

    contribution = db.relationship(
        "Contribution", lazy=True, backref=db.backref("starred", lazy=True)
    )

    def __repr__(self):
        return format_repr(self, "id", "contribution_id", "user_id")
