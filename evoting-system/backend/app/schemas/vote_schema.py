from marshmallow import Schema, fields, validate


class CastVoteSchema(Schema):
    candidate_id = fields.Str(required=True)
    face_images = fields.List(fields.Str(), required=True, validate=validate.Length(min=2))
