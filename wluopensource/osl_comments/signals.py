from django.dispatch import Signal

comment_was_deleted_by_user = Signal(providing_args=["comment", "request"])
ip_address_ban_was_updated = Signal(providing_args=["banned", "request"])
comment_was_edited = Signal(providing_args=["comment", "request"])
comment_will_be_edited = Signal(providing_args=["comment", "request"])

