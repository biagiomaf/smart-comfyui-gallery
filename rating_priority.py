"""Helpers for keeping each reviewer's unrated media ahead of completed ratings."""


def resolve_rating_client_uuid(session_user_id, force_login, exhibition_mode):
    """Return the identity used by ``file_ratings`` for the current request."""
    if session_user_id is not None and str(session_user_id):
        return str(session_user_id)
    if not force_login and not exhibition_mode:
        return "admin"
    return ""


def prioritize_personal_unrated(files):
    """Stable-partition files so unrated items precede personally rated items."""
    for index, item in enumerate(files):
        item["review_sort_index"] = index
    return sorted(files, key=lambda item: bool(item.get("my_rating")))
