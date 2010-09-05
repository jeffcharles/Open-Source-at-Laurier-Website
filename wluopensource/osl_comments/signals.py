from django.dispatch import Signal

comment_was_deleted_by_user = Signal(providing_args=["comment", "request"])

