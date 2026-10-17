from marshmallow import Schema, fields, validate


class CandidateCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    party = fields.Str(required=False, allow_none=True, validate=validate.Length(max=120))
    photo_url = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(required=False, allow_none=True)


class CandidateUpdateSchema(Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120))
    party = fields.Str(required=False, allow_none=True, validate=validate.Length(max=120))
    photo_url = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(required=False, allow_none=True)
