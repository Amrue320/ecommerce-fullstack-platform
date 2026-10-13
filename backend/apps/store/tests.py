from django.test import override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Profile, Category, Product, CartItem, Order
from .activity import log_activity

class StoreAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer", password="TestPass!2026")
        Profile.objects.create(user=self.user)
        self.category = Category.objects.create(name="Books", slug="books")
        self.product = Product.objects.create(category=self.category, name="Python Book", slug="python-book", price="250.00", stock=5)
    def auth(self):
        response = self.client.post("/api/auth/token/", {"username":"customer","password":"TestPass!2026"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
    def test_product_list_and_search(self):
        self.assertEqual(self.client.get("/api/products/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/products/?search=Python").status_code, status.HTTP_200_OK)
    def test_register_password_validation(self):
        response = self.client.post("/api/auth/register/", {"username":"new","password":"short","email":"new@example.com"}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_cart_rejects_invalid_quantity(self):
        self.auth()
        response = self.client.post("/api/cart/", {"product_id":self.product.id,"quantity":0}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_checkout_creates_order_and_decrements_inventory(self):
        self.auth()
        self.client.post("/api/cart/", {"product_id":self.product.id,"quantity":2}, format="json")
        response = self.client.post("/api/checkout/", {"shipping_address":"12 Example Street, Kerala","payment_method":"mock"}, format="json", HTTP_IDEMPOTENCY_KEY="test-order-1")
        self.assertEqual(response.status_code, 201, response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(Order.objects.count(), 1)
    def test_order_ownership(self):
        other = User.objects.create_user(username="other", password="OtherPass!2026")
        order = Order.objects.create(user=other, shipping_address="Other address", subtotal="10", total="10")
        self.auth()
        self.assertEqual(self.client.get(f"/api/orders/{order.id}/").status_code, 404)
    def test_cancel_restores_inventory(self):
        self.auth()
        self.client.post("/api/cart/", {"product_id":self.product.id,"quantity":2}, format="json")
        order = self.client.post("/api/checkout/", {"shipping_address":"12 Example Street, Kerala"}, format="json").data
        response = self.client.post(f"/api/orders/{order['id']}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
    @override_settings(MONGO_ENABLED=False)
    def test_activity_logging_disabled_gracefully(self):
        self.assertFalse(log_activity("test_event", user_id=self.user.id))
