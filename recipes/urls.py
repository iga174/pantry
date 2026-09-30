from . import views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("recipes/", views.recipes, name="recipes"),
    path("pantry/", views.pantry, name="pantry"),
    path("add/", views.add_pantry_item, name="add_pantry_item"),
    path("recipe/<int:meal_id>", views.recipe_detail, name="recipe_detail"),
    path("my-recipes/", views.my_recipes, name="my_recipes"),
    path("my-recipes/add/", views.add_recipe, name="add_recipe"),
    path("my-recipes/<int:recipe_id>",views.my_recipe_detail,name="my_recipe_detail"),
    path("recipe/<int:meal_id>/shopping-list/",views.shopping_list_api,name="shopping_list_api"),
    path("my-recipes/<int:recipe_id>/shopping-list/",views.my_shopping_list,name="my_shopping_list")
    ]