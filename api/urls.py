from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from .views import CoursesViewSet

router = routers.SimpleRouter()
router.register(r'courses', CoursesViewSet)

urlpatterns = format_suffix_patterns(router.urls, allowed=['json', 'csv'])
