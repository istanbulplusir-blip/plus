from rest_framework import serializers
from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'parent', 'children')

    def get_children(self, obj):
        children = obj.get_children()
        serializer = self.__class__(children, many=True)
        return serializer.data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text')


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'stock', 'type', 'image', 'images', 'categories', 'created_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Hide stock for non-staff or something, but simplify
        return data
