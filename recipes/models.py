from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class PantryItem(models.Model):

    CATEGORY_CHOICES = [ ("fridge", "Fridge"), 
                        ("fruit_vegetables", 
                         "Fruit & Vegetables"), 
                         ("meat_fish", "Meat & Fish"), 
                         ("grains_bakery", "Grains & Bakery"), 
                         ("canned_dry", "Canned & Dry Goods"), 
                         ("spices", "Spices"), 
                         ("sauces_condiments", "Sauces & Condiments"), 
                         ("snacks", "Snacks"), 
                         ("drinks", "Drinks"),
                         ("other", "Other") ]
    name = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=128)
    category = models.CharField( max_length=50, choices=CATEGORY_CHOICES, default="fridge" )

    def __str__(self):
        return self.name.name

class Recipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    instructions = models.TextField()

    def __str__(self):
        return self.name
    
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=128)

    def __str__(self):
        return self.ingredient.name