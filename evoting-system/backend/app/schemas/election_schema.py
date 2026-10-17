from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class ElectionCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    description = fields.Str(required=False, allow_none=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    # Optional: pre-assign eligible voters by their Voter ID (DB voter_id string,
    # not the UUID) at creation time. Can also be managed later via a
    # dedicated eligibility endpoint.
    eligible_voter_ids = fields.List(fields.Str(), required=False, load_default=list)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data["end_date"] <= data["start_date"]:
            raise ValidationError("end_date must be after start_date.", field_name="end_date")


class ElectionUpdateSchema(Schema):
    # All optional — PATCH-style partial update. Only allowed while the
    # election is still editable (see election_lifecycle.can_edit_details).
    title = fields.Str(required=False, validate=validate.Length(min=3, max=255))
    description = fields.Str(required=False, allow_none=True)
    start_date = fields.DateTime(required=False)
    end_date = fields.DateTime(required=False)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if "start_date" in data and "end_date" in data:
            if data["end_date"] <= data["start_date"]:
                raise ValidationError("end_date must be after start_date.", field_name="end_date")


class ElectionActionSchema(Schema):
    # For POST /elections/<id>/<action> — currently no body params needed,
    # but kept as a schema so audit-log "reason" notes can be added later
    # without changing the route signature.
    reason = fields.Str(required=False, allow_none=True)


class EligibleVoterUpdateSchema(Schema):
    voter_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
