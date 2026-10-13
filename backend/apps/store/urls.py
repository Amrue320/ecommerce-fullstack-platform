from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileView, CategoryViewSet, ProductViewSet, CartView, CartItemView, CheckoutView, OrderViewSet, AdminSummaryView
router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")
urlpatterns = [
    path("", include(router.urls)),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/<int:item_id>/", CartItemView.as_view(), name="cart-item"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("admin/summary/", AdminSummaryView.as_view(), name="admin-summary"),
]
