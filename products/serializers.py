from rest_framework import serializers
from .models import Product, Images

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model= Product
        fields = '__all__'

class ImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ['image_url', 'product']

class AllProductSerializer(serializers.ModelSerializer):
    images = ImagesSerializer(many=True, read_only =True)
    class Meta:
        model = Product
        fields = '__all__'