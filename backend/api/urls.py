from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from .views import (IngredientsViewSet, RecipesViewSet, TagsViewSet,
                    CustomUsersViewSet)
from foodgram import settings

app_name = "api"

router = routers.DefaultRouter()
router.register("tags", TagsViewSet, basename="tags")
router.register("users", CustomUsersViewSet, basename="users")
router.register("recipes", RecipesViewSet, basename="recipes")
router.register("ingredients", IngredientsViewSet, basename="ingredients")

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]

urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

urlpatterns += static(
    settings.STATIC_URL, document_root=settings.STATIC_ROOT
)
