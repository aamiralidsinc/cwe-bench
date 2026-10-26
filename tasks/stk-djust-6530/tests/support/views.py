"""Fixture LiveViews used by the hidden security and functional suites.

Every view here is a normal djust ``LiveView``; the only thing they share is a
deterministic render result, because the optional Rust renderer is not built in
this image. The project's own SSE tests use the same shape of stub. The flow
under test (mount -> authorization -> event dispatch) is entirely Python.
"""

from __future__ import annotations

from djust import LiveView
from djust.decorators import event_handler
from djust.hooks import on_mount

# Names of handlers that actually executed in this process. A security test
# asserts that a refused view's handler never adds an entry here.
EXECUTED: list[str] = []


def reset() -> None:
    EXECUTED.clear()


class _RenderStub:
    """Render the mount frame without the optional Rust extension."""

    def _initialize_rust_view(self, request=None):
        return None

    def _sync_state_to_rust(self, *args, **kwargs):
        return None

    def render_with_diff(self, *args, **kwargs):
        return ("<div dj-root><span>ready</span></div>", None, 1)


class PublicView(_RenderStub, LiveView):
    """No view-level authorization; the control that must always work."""

    template = '<div dj-root><span>public</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def public_ping(self, **kwargs):
        EXECUTED.append("public_ping")


class LoginRequiredView(_RenderStub, LiveView):
    """Refused unless the request carries an authenticated user."""

    login_required = True
    template = '<div dj-root><span>secret</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def login_mutation(self, **kwargs):
        EXECUTED.append("login_mutation")


class PermissionRequiredView(_RenderStub, LiveView):
    """Refused for a user that lacks the declared Django permission."""

    permission_required = "demo.view_secret"
    template = '<div dj-root><span>secret</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def perm_mutation(self, **kwargs):
        EXECUTED.append("perm_mutation")


class CheckPermissionsDeniedView(_RenderStub, LiveView):
    """Refused by the developer's own authorization predicate."""

    template = '<div dj-root><span>secret</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    def check_permissions(self, request):
        return False

    @event_handler
    def checkperm_mutation(self, **kwargs):
        EXECUTED.append("checkperm_mutation")


class CheckPermissionsAllowedView(_RenderStub, LiveView):
    """The developer's own authorization predicate allows the mount."""

    template = '<div dj-root><span>allowed</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    def check_permissions(self, request):
        return True

    @event_handler
    def checkpermok_ping(self, **kwargs):
        EXECUTED.append("checkpermok_ping")


class CheckPermissionsCrashesView(_RenderStub, LiveView):
    """The developer's authorization predicate raises instead of deciding."""

    template = '<div dj-root><span>secret</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    def check_permissions(self, request):
        raise RuntimeError("authorization predicate failed")

    @event_handler
    def crash_mutation(self, **kwargs):
        EXECUTED.append("crash_mutation")


def _redirect_hook(view, request, **kwargs):
    return "/accounts/login/"


def _allow_hook(view, request, **kwargs):
    return None


@on_mount
def _decorated_redirect_hook(view, request, **kwargs):
    return "/accounts/login/"


class HookRedirectView(_RenderStub, LiveView):
    """A mount-time hook halts the mount and sends the client elsewhere."""

    template = '<div dj-root><span>redirect</span></div>'
    on_mount = [_redirect_hook]

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def hook_mutation(self, **kwargs):
        EXECUTED.append("hook_mutation")


class DecoratedHookRedirectView(_RenderStub, LiveView):
    """Same, with the project's public ``@on_mount`` decorator."""

    template = '<div dj-root><span>redirect</span></div>'
    on_mount = [_decorated_redirect_hook]

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def decorated_hook_mutation(self, **kwargs):
        EXECUTED.append("decorated_hook_mutation")


class HookAllowedView(_RenderStub, LiveView):
    """A mount-time hook that declines to redirect; the mount must proceed."""

    template = '<div dj-root><span>allowed</span></div>'
    on_mount = [_allow_hook]

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def hookok_ping(self, **kwargs):
        EXECUTED.append("hookok_ping")


class PublicDetailView(_RenderStub, LiveView):
    """A second public view, used for client-side navigation."""

    template = '<div dj-root><span>other</span></div>'

    def mount(self, request, **kwargs):
        self.ready = True

    @event_handler
    def other_ping(self, **kwargs):
        EXECUTED.append("other_ping")


class AuthenticatedUser:
    """An already-signed-in user that holds every Django permission."""

    is_authenticated = True
    is_anonymous = False
    is_staff = False
    is_superuser = False
    pk = 1

    def has_perm(self, perm):
        return True

    def has_perms(self, perms):
        return all(self.has_perm(p) for p in perms)

    def __str__(self):
        return "fixture-user"


class UnprivilegedUser:
    """A signed-in user with no Django permissions."""

    is_authenticated = True
    is_anonymous = False
    is_staff = False
    is_superuser = False
    pk = 2

    def has_perm(self, perm):
        return False

    def has_perms(self, perms):
        return False

    def __str__(self):
        return "unprivileged-user"


class BrokenAuthBackendUser:
    """Signed in, but the permission backend raises instead of answering."""

    is_authenticated = True
    is_anonymous = False
    is_staff = False
    is_superuser = False
    pk = 3

    def has_perm(self, perm):
        raise RuntimeError("permission backend unavailable")

    def has_perms(self, perms):
        raise RuntimeError("permission backend unavailable")

    def __str__(self):
        return "broken-backend-user"
