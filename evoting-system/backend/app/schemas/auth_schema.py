from marshmallow import Schema, fields, validate, validates, ValidationError

from app.security.validators import validate_password_strength, validate_phone


class VoterRegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    dob = fields.Date(required=True)
    gender = fields.Str(required=False, validate=validate.OneOf(["male", "female", "other"]))
    phone = fields.Str(required=True)
    email = fields.Email(required=True)
    address = fields.Str(required=False, allow_none=True)
    voter_id = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    password = fields.Str(required=True, load_only=True)

    @validates("password")
    def validate_password(self, value, **kwargs):
        is_valid, msg = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(msg)

    @validates("phone")
    def validate_phone_field(self, value, **kwargs):
        if not validate_phone(value):
            raise ValidationError("Invalid phone number format.")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    # Explicit role selection avoids ambiguity when the same email could
    # theoretically exist in more than one of the three login tables,
    # and avoids leaking which tables were checked via timing/enumeration.
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["super_admin", "election_admin", "voter"]),
    )


class RefreshSchema(Schema):
    # Refresh token itself comes via the JWT (Authorization header), this
    # schema is a placeholder for any future body params (e.g. device info).
    device_info = fields.Str(required=False, allow_none=True)
