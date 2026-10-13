from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Profile, Category, Product, CartItem, Order, OrderItem

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    class Meta:
        model = User
        fields = ["id","username","email","password","first_name","last_name"]
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.get_or_create(user=user)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    role = serializers.CharField(source="role", read_only=True)
    class Meta:
        model = Profile
        fields = ["username","email","first_name","last_name","phone","address","role"]
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for key, value in user_data.items(): setattr(instance.user, key, value)
        instance.user.save()
        return super().update(instance, validated_data)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Product
        fields = ["id","category","category_name","name","slug","description","image_url","price","stock","is_active","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]
    def validate_price(self, value):
        if value < 0: raise serializers.ValidationError("Price cannot be negative.")
        return value

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)
    line_total = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ["id","product","product_detail","quantity","line_total"]
        read_only_fields = ["id","line_total"]
    def get_line_total(self, obj): return str(obj.product.price * obj.quantity)
    def validate_quantity(self, value):
        if value < 1: raise serializers.ValidationError("Quantity must be at least 1.")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id","product","product_name","unit_price","quantity","line_total"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ["id","shipping_address","subtotal","total","payment_method","payment_status","status","created_at","items"]

class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(min_length=8, max_length=1000)
    payment_method = serializers.ChoiceField(choices=["mock"], default="mock")
