DEMO_VIEWER_GROUP_NAME = "demo_viewer"
DEMO_DATA_MARKER = "buddy-demo-scenarios-v1"

SAFE_DEMO_HTTP_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

ALLOWED_DEMO_SAFE_URL_NAMES = frozenset(
    {
        # LOGIN_REDIRECT_URL points here. The dashboard view redirects
        # demo viewers immediately to the AdultAdSuite cockpit.
        "operations-dashboard",
        "adultadsuite-cockpit",
        "adultadsuite-triggers",
        "chat-hub",
        "conversation-thread-detail",
        "logout",
    }
)

ALLOWED_DEMO_UNSAFE_URL_NAMES = frozenset({"logout"})


def is_demo_viewer(user) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and user.groups.filter(name=DEMO_VIEWER_GROUP_NAME).exists()
    )
