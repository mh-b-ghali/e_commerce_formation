from django.urls import path
from . import views

urlpatterns = [
    path('all_categories', views.get_all_categories, name='all_categories'),
    path('category_by_id/<int:id>', views.get_category_by_id, name='category_by_id'),
    path('create_category', views.create_category, name='create_category'),
    path('delete_category/<int:category_id>', views.delete_category, name='delete_category'),
    path('update_category/<int:pk>', views.update_category, name='update_category'),


    path('all_subcategories', views.get_all_subcategories, name='all_subcategories'),
    path('subcategory_by_id/<int:id>', views.get_subcategory_by_id, name='get_subcategory_by_id'),
    path('create_subcategory', views.create_sub_category, name='create_sub_category'),
    path('update_subcategory/<int:id>', views.update_subcategory, name='update_subcategory'),
    path('delete_subcategory/<int:id>', views.delete_subcategory, name='delete_subcategory'),
    path('get_subcategories_by_category', views.get_subcategories_by_category, name='get_subcategories_by_category'),
]
