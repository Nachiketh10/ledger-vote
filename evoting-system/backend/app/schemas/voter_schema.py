from marshmallow import Schema, fields, validate


class VoterVerifyActionSchema(Schema):
    # Optional note stored in the audit log, e.g. "ID verified in person".
    note = fields.Str(required=False, allow_none=True)


class VoterSuspendActionSchema(Schema):
    reason = fields.Str(required=True, validate=validate.Length(min=3))
