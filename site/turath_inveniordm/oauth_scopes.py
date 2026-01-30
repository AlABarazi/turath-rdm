"""OAuth scopes for deposit API access."""

from invenio_i18n import lazy_gettext as _
from invenio_oauth2server.models import Scope


deposit_write_scope = Scope(
    id_="deposit:write",
    group="deposit",
    help_text=_("Allow creating and updating draft records."),
)
"""Allow creating and updating draft records."""


deposit_actions_scope = Scope(
    id_="deposit:actions",
    group="deposit",
    help_text=_("Allow publishing and managing draft actions."),
)
"""Allow publishing and managing draft actions."""
