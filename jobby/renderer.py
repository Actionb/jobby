from django_bootstrap5.renderers import FieldRenderer


class NoIsValidFieldRenderer(FieldRenderer):
    """
    A bootstrap5 renderer that does not add the 'is-valid' class to valid form
    elements.
    """

    # See: https://github.com/zostera/django-bootstrap5/issues/302

    def get_server_side_validation_classes(self):
        """Return CSS classes for server-side validation."""
        if self.field_errors:
            return "is-valid"
        return ""
