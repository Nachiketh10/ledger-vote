from marshmallow import Schema, fields, validate


class FaceRegisterSchema(Schema):
    # List of base64-encoded JPEG/PNG frames (or data URLs) captured
    # from the browser during registration — spec calls for ~20 images.
    images = fields.List(fields.Str(), required=True, validate=validate.Length(min=5))


class FaceVerifySchema(Schema):
    # A short SEQUENCE of frames (not one) — required for liveness
    # detection, which needs motion across frames to assess blink/turn.
    images = fields.List(fields.Str(), required=True, validate=validate.Length(min=2))
    election_id = fields.Str(required=False, allow_none=True)
