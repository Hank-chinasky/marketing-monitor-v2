from core.mixins import AdminOnlyMixin
from core.views import (
    CreatorChannelUpdateView as BaseCreatorChannelUpdateView,
    CreatorUpdateView as BaseCreatorUpdateView,
)


class CreatorUpdateView(AdminOnlyMixin, BaseCreatorUpdateView):
    pass


class CreatorChannelUpdateView(AdminOnlyMixin, BaseCreatorChannelUpdateView):
    pass
