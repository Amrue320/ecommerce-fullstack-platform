from decimal import Decimal
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Sum, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Profile, Category, Product, CartItem, Order, OrderItem
from .serializers import RegisterSerializer, ProfileSerializer, CategorySerializer, ProductSerializer, CartItemSerializer, OrderSerializer, CheckoutSerializer
from .permissions import IsStoreAdmin, ProductWriteAdminOnly, is_admin
from .activity import log_activity

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request): return Response({"status":"ok","service":"ecommerce-api"})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get_profile(self, user):
        profile, _ = Profile.objects.get_or_create(user=user, defaults={"role": "admin" if user.is_staff else "customer"})
        if user.is_staff and profile.role != "admin":
            profile.role = "admin"; profile.save(update_fields=["role"])
        return profile
    def get(self, request): return Response(ProfileSerializer(self.get_profile(request.user)).data)
    def patch(self, request):
        profile = self.get_profile(request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    def get_permissions(self):
        return [IsStoreAdmin()] if self.action in ["create","update","partial_update","destroy"] else [AllowAny()]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related("category")
    serializer_class = ProductSerializer
    permission_classes = [ProductWriteAdminOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name","description","category__name"]
    ordering_fields = ["price","created_at","name"]
    def get_queryset(self):
        qs = Product.objects.select_related("category")
        if not is_admin(self.request.user): qs = qs.filter(is_active=True)
        params = self.request.query_params
        if params.get("min_price"):
            try: qs = qs.filter(price__gte=Decimal(params["min_price"]))
            except Exception: pass
        if params.get("max_price"):
            try: qs = qs.filter(price__lte=Decimal(params["max_price"]))
            except Exception: pass
        if params.get("available") == "true": qs = qs.filter(stock__gt=0)
        return qs
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        log_activity("product_view", user_id=request.user.id if request.user.is_authenticated else None, product_id=kwargs.get("pk"))
        return response
    def list(self, request, *args, **kwargs):
        if request.query_params.get("search"):
            log_activity("product_search", user_id=request.user.id if request.user.is_authenticated else None, query=request.query_params.get("search"))
        return super().list(request, *args, **kwargs)

class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related("product","product__category")
        return Response({"items":CartItemSerializer(items, many=True).data,
                         "total":str(sum((x.product.price*x.quantity for x in items), Decimal("0.00")))})
    def post(self, request):
        product_id = request.data.get("product_id")
        try: quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError): return Response({"detail":"Quantity must be an integer."}, status=400)
        if quantity < 1: return Response({"detail":"Quantity must be at least 1."}, status=400)
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        if product.stock < quantity: return Response({"detail":"Insufficient stock."}, status=400)
        item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={"quantity":quantity})
        if not created:
            if item.quantity + quantity > product.stock: return Response({"detail":"Insufficient stock."}, status=400)
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item).data, status=201 if created else 200)

class CartItemView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, item_id):
        item = get_object_or_404(CartItem, pk=item_id, user=request.user)
        try: quantity = int(request.data.get("quantity"))
        except (TypeError, ValueError): return Response({"detail":"Quantity must be an integer."}, status=400)
        if quantity < 1: return Response({"detail":"Quantity must be at least 1."}, status=400)
        if quantity > item.product.stock: return Response({"detail":"Insufficient stock."}, status=400)
        item.quantity = quantity; item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item).data)
    def delete(self, request, item_id):
        item = get_object_or_404(CartItem, pk=item_id, user=request.user); item.delete()
        return Response(status=204)

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key")
        if key:
            existing = Order.objects.filter(idempotency_key=key, user=request.user).first()
            if existing: return Response(OrderSerializer(existing).data, status=200)
        with transaction.atomic():
            cart = list(CartItem.objects.select_for_update().filter(user=request.user).select_related("product"))
            if not cart: return Response({"detail":"Your cart is empty."}, status=400)
            product_ids = [item.product_id for item in cart]
            locked = {p.id:p for p in Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)}
            lines, subtotal = [], Decimal("0.00")
            for item in cart:
                product = locked.get(item.product_id)
                if product is None: return Response({"detail":"A product is no longer available."}, status=400)
                if item.quantity < 1 or product.stock < item.quantity:
                    return Response({"detail":f"Insufficient stock for {product.name}."}, status=400)
                line = product.price * item.quantity
                subtotal += line
                lines.append((product, item.quantity, line))
            order = Order.objects.create(user=request.user, idempotency_key=key, shipping_address=serializer.validated_data["shipping_address"],
                                         subtotal=subtotal, total=subtotal, payment_method="mock", payment_status="mock_pending", status="confirmed")
            for product, quantity, line in lines:
                product.stock -= quantity; product.save(update_fields=["stock"])
                OrderItem.objects.create(order=order, product=product, product_name=product.name, unit_price=product.price, quantity=quantity, line_total=line)
            CartItem.objects.filter(user=request.user).delete()
        return Response(OrderSerializer(order).data, status=201)

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = Order.objects.prefetch_related("items").order_by("-created_at")
        return qs if is_admin(self.request.user) else qs.filter(user=self.request.user)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        with transaction.atomic():
            order = get_object_or_404(Order.objects.select_for_update().prefetch_related("items"), pk=pk)
            if not is_admin(request.user) and order.user_id != request.user.id: return Response({"detail":"Not permitted."}, status=403)
            if order.status not in ["pending","confirmed"]: return Response({"detail":"This order can no longer be cancelled."}, status=400)
            for item in order.items.all():
                Product.objects.filter(pk=item.product_id).update(stock=F("stock")+item.quantity)
            order.status = "cancelled"; order.save(update_fields=["status","updated_at"])
        return Response(OrderSerializer(order).data)

class AdminSummaryView(APIView):
    permission_classes = [IsStoreAdmin]
    def get(self, request):
        return Response({"orders":Order.objects.count(),"products":Product.objects.count(),
                         "users":User.objects.count(),"revenue":str(Order.objects.exclude(status="cancelled").aggregate(v=Sum("total"))["v"] or Decimal("0.00")),
                         "pending_orders":Order.objects.filter(status="pending").count()})
