from django.contrib import admin
from .models import Ingredient, PantryItem, Recipe, RecipeIngredient

admin.site.register(Ingredient)
admin.site.register(PantryItem)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)