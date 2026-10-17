from marshmallow import Schema, fields


class WebAuthnVerifySchema(Schema):
    # The raw JSON string produced by serializing the browser's
    # PublicKeyCredential response (see scripts/webauthn_test.html for
    # the exact client-side shape expected).
    credential = fields.Str(required=True)
    state = fields.Str(required=True)
