import os
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from authentication.authentication import JWTAuthentication
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, Images
from .serializers import *  # import all classes from serializers
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404
import urllib
import shutil

@api_view(['POST'])
@require_http_methods(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_product(request):
    """POST: add a new product with images"""
    if not request.content_type.startswith('multipart/form-data'):
        return Response({"error": "error content type"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # extract post data and files
    data = request.POST.copy()
    images_files = request.FILES.getlist('images')

    # clean and convert data
    try:
        data["price"] = float(data['price'])
    except (ValueError, KeyError) as e:
        return Response({"error":f"Invalid data: {str(e)}"},status=status.HTTP_400_BAD_REQUEST)

    # serializer and save product
    product_serializer = ProductSerializer(data = data)
    if not product_serializer.is_valid():
        return Response({"error":product_serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    product = product_serializer.save()

    # handle images uploaded
    folder_path = os.path.join(settings.MEDIA_ROOT, str(product.pk))
    os.makedirs(folder_path, exist_ok=True)
    fs = FileSystemStorage(location=folder_path)

    for image_file in images_files:
        filename = fs.save(image_file.name, image_file)
        image_url = os.path.join(settings.MEDIA_ROOT, str(product.pk), filename)
        print({"image_url":image_url})
        image_data = {"image_url":image_url.replace("\\","/"), "product":product.id}

        # serializer and save images
        images_serializer = ImagesSerializer(data=image_data)
        if not images_serializer.is_valid():
            return Response({"error": images_serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        images_serializer.save()
    return Response({"message": "product added successfully"},status=status.HTTP_201_CREATED)

@api_view(['GET'])
@require_http_methods(['GET'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def all_products(request):
    """GET: get all products"""
    list_products = []
    list_images = []
    product_json = {}
    products = Product.objects.all()
    for product in products:
        product_json['id'] = product.pk
        product_json['name'] = product.name
        product_json['price'] = product.price
        product_json['subcategories'] = list(product.subcategories.values_list('name',flat=True))
        # without flat [(name1,),(name2,)] ==> with flat result = [name1,name2]

        images = Images.objects.filter(product_id=product.pk)
        for image in images:
            list_images.append(image.image_url)
        product_json["images"] = list_images
        list_products.append(product_json)
        product_json = {}
        list_images = []
    return Response({"count":len(list_products), "list product":list_products},status=status.HTTP_200_OK)

@api_view(['DELETE'])
@require_http_methods(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_product(request, product_id):
    """DELETE: delete a product"""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error":"product not found"},status=status.HTTP_404_NOT_FOUND)

    try:
        images = Images.objects.filter(product=product.id)
    except Images.DoesNotExist:
        return Response({"error":"images not found"},status=status.HTTP_404_NOT_FOUND)

    folder_path = os.path.join(settings.MEDIA_ROOT, str(product.pk))
    for image in images:
        name_image = image.image_url.split('/')[6].replace('%20'," ")
        file_path = os.path.join(folder_path, name_image)
        os.remove(file_path)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    try:
        product.delete()
        return Response({"message":"product  deleted successfully"},status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error":f"error deleting product: {str(e)}"},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@require_http_methods(['GET'])
# @authentication_classes([JWTAuthentication])
@permission_classes([AllowAny])
def product_details(request, pk):
    """GET: get details of a product"""
    product_json = {}
    list_images = []
    try:
        product = Product.objects.get(id=pk)
    except Product.DoesNotExist:
        return Response({"error": "product not found"}, status=status.HTTP_404_NOT_FOUND)

    product_json["id"] = product.pk
    product_json["name"] = product.name
    product_json["price"] = product.price
    product_json["subcategories"] =  list(product.subcategories.values_list('name',flat=True))

    images = Images.objects.filter(product_id=product.pk)
    for image in images:
        list_images.append(image.image_url)

    product_json['images'] = list_images
    return Response({"product":product_json},status=status.HTTP_200_OK)

@api_view(['PUT'])
@require_http_methods(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_product(request,product_id):
    """PUT: update a product"""

    if not request.content_type.startswith('multipart/form-data'):
        return Response({"error":"error content type"},status=status.HTTP_400_BAD_REQUEST)

    data = request.POST.copy()
    images_files = request.FILES.getlist('images')

    try:
        print({"price type":type(data['price'])})
        data['price'] = float(data['price'])
    except (ValueError, KeyError) as e:
        return Response({"error":f"invalid data: {str(e)}"})

    product = get_object_or_404(Product, id=product_id)
    product_serializer = ProductSerializer(product, data=data, partial=True)

    if not product_serializer.is_valid():
        return Response({"error":product_serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    product_serializer.save()
    ################################################################################################

    folder_path = os.path.join(settings.MEDIA_ROOT, str(product.pk))
    fs = FileSystemStorage(location=folder_path)
    # get existing images associated with product
    existing_images = Images.objects.filter(product=product.id)
    existing_images_urls = [os.path.basename(image.image_url) for image in existing_images] # short forme of for
    ############# eq #########
    # existing_images_urls = []
    # for image in existing_images:
    #     existing_images_urls.append(os.path.basename(image.image_url))
    ############# eq #########

    # delete old images not in uploaded list
    for existing_image_url in existing_images_urls:
        if existing_image_url not in [image_file.name for image_file in images_files]:
            os.remove(os.path.join(folder_path, urllib.parse.unquote(existing_image_url)))
            Images.objects.filter(image_url__endswith=existing_image_url, product=product.id).delete()
    

    # save new images
    for image_file in images_files:
        if image_file.name not in existing_images_urls:
            filename = fs.save(image_file.name,image_file)
            image_url =f"/media/{product.pk}/{urllib.parse.unquote(filename)}"

            image_data = {"image_url":image_url, "product":product.id}
            image_serializer = ImagesSerializer(data=image_data)
            if image_serializer.is_valid():
                image_serializer.save()
            else:
                return Response({"error":image_serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    return Response({"message":"product updated successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@require_http_methods(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_product_by_subcategory(request):
    """POST: get product by subcategory"""
    subcategory_id = request.data.get('subcategory_id')
    products = Product.objects.filter(subcategories__id= subcategory_id)
    # serializer = ProductSerializer(products, many=True) # to get only data of product 
    serializer = AllProductSerializer(products, many=True) # to get data of product + his images
    return Response(serializer.data)

from django.db.models import Q
@api_view(['POST'])
@require_http_methods(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search_product(request):
    """POST: search product by his name"""
    query = request.data.get('search')
    if not query:
        return Response({"error":"must have search key"},status=status.HTTP_400_BAD_REQUEST)

    products = Product.objects.filter(
        Q(name__icontains=query)  # where name like %sA%s ==> every name content A between letters 
                                  # where name like %sA ==> every name end with A
                                  # where name like A%s ==> every name start with A
    )

    serializer = AllProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@require_http_methods(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny])
def filter_products(request):
    """POST: create a filter by columns on products table"""
    products = Product.objects.all()

    name = request.data.get('name')
    min_price = request.data.get('min_price')
    max_price = request.data.get('max_price')
    category_id = request.data.get('category_id')
    subcategory_id = request.data.get('subcategory_id')

    # filter by name
    if name:
        products = products.filter(
            name__icontains=name
        )

    # filter by min_price
    if min_price:
        products = products.filter(
            price__gte = min_price
        )

    # filter by max_price
    if max_price:
        products = products.filter(
            price__lte = max_price
        )

    # filter by category
    if category_id:
        products = products.filter(
            subcategories__category__id=subcategory_id
        )

    # filter by subcategory
    if subcategory_id:
        products = products.filter(
            subcategories__id = subcategory_id
        )

    # because product <--> subcategory is ManyToMany
    products = products.distinct()

    serializer = AllProductSerializer(products, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


from django.core.management import call_command

@api_view(['POST'])
@require_http_methods(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def init_categories_and_subcategories(request):
    try:
        call_command('init_category_subcategory')

        return Response({
            "message":"Categories ans SubCategories initialized successfully",
            "success": True
            },status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({
            "error": str(e),
            "success": False
        },status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )