"""Serializes a Flask-SQLAlchemy Pagination object into a consistent JSON shape."""


def paginated(pagination, item_serializer) -> dict:
    return {
        "items": [item_serializer(item) for item in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def parse_pagination_args(request, default_per_page: int = 20, max_per_page: int = 100):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = max(1, min(per_page, max_per_page))
    return page, per_page
