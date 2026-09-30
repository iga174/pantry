from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from recipes.models import PantryItem, Ingredient
from .models import Recipe, RecipeIngredient
from django.contrib.auth.decorators import login_required
import requests

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "pantry/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "pantry/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "pantry/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "pantry/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "pantry/register.html")


def index(request):
    response = requests.get("https://www.themealdb.com/api/json/v1/1/random.php")

    data = response.json()

    meal = data["meals"][0]

    return render(request, "pantry/index.html", {"meal": meal})

@login_required
def pantry(request):
    items = PantryItem.objects.all().order_by("category","name__name")

    categories = []

    for category_value, category_name in PantryItem.CATEGORY_CHOICES:
        category_items = []

        for item in items:
            if item.category == category_value:
                category_items.append(item)

        if category_items:
            categories.append({"name": category_name, "items": category_items})

    return render(request, "pantry/pantry.html", {"categories": categories})

@login_required
def add_pantry_item(request):
    if request.method == "POST":
        ingredient_name = request.POST["ingredient"]
        category = request.POST["category"]

        ingredient = Ingredient.objects.filter(name=ingredient_name).first()

        if ingredient is None:
            ingredient = Ingredient.objects.create(name=ingredient_name)

        PantryItem.objects.create(
            name=ingredient,
            quantity=request.POST["quantity"],
            unit=request.POST["unit"],
            category=category,)

        return HttpResponseRedirect(reverse("pantry"))

    return render(request, "pantry/add_pantry_item.html")


def recipes(request):
    search = request.GET.get("search", "").strip()

    if search:
        response = requests.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={search}")

        data = response.json()
        meals = data["meals"] or []

    else:
        #List all categories
        response = requests.get("https://www.themealdb.com/api/json/v1/1/categories.php")

        data = response.json()

        meals = []

        for category in data["categories"]:
            category_name = category["strCategory"]

            response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category_name}")

            data = response.json()

            meals.extend(data["meals"])

    return render(request, "pantry/recipes.html", {
        "meals": meals,
        "search": search})

def convert_measure(measure):
    if not measure:
        return ""

    measure = measure.strip()

    measure = measure.replace("tbsp", "tbs")
    measure = measure.replace("tablespoon", "tbs")
    measure = measure.replace("tablespoons", "tbs")
    measure = measure.replace("teaspoon", "tsp")
    measure = measure.replace("teaspoons", "tsp")

    if "cup" in measure or "cups" in measure:
        parts = measure.split("cup")
        number = parts[0].strip()

        try:
            number = float(number)

        # if fraction (e.g. 2 1/2 cups)
        except ValueError:

            number_parts = number.split()

            if len(number_parts) == 2 and "/" in number_parts[1]:
                whole_number = float(number_parts[0])

                fraction = number_parts[1].split("/")
                numerator = float(fraction[0])
                denominator = float(fraction[1])

                number = whole_number + numerator / denominator

            else:
                pass

        try:
            grams = round(number * 200)

            return str(grams) + " g" 
        
        except (ValueError, UnboundLocalError):
            pass

    if "oz" in measure:
        parts = measure.split("oz")
        number = parts[0].strip()

        try:
            number = float(number)
            grams = round(number * 28.35)

            return str(grams) + " g" 
       
        except ValueError:
            pass

    if "lb" in measure:
        parts = measure.split("lb")
        number = parts[0].strip()

        try:
            number = float(number)
            grams = round(number * 453.59)

            return str(grams) + " g" 
        
        except ValueError:
            pass

    if "L" in measure:
            parts = measure.split("L")
            number = parts[0].strip()
    
            try:
                number = float(number)
                mililiters = round(number * 1000)
    
                return str(mililiters) + " ml" 
            
            except ValueError:
                pass

    if "kg" in measure:
                parts = measure.split("kg")
                number = parts[0].strip()
        
                try:
                    number = float(number)
                    grams = round(number * 1000)
        
                    return str(grams) + " g" 
                
                except ValueError:
                    pass

    return measure

def parse_measure(measure):
    measure = convert_measure(measure)

    parts = measure.split()

    if len(parts) >= 2:
        try:
            quantity = float(parts[0])
            return quantity, parts[1].lower()
        except ValueError:
            pass

    # e.g. if measure is "200g" (no space between quantity and unit)
    number = ""

    for character in measure:
        if character.isdigit() or character == ".":
            number += character
        else:
            break

    if number:
        number_length = len(number)
        unit = measure[number_length:].strip()

        try:
            quantity = float(number)
            return quantity, unit.lower()
        except ValueError:
            pass

    return None, None


def recipe_detail(request, meal_id):
    response = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")

    data = response.json()
    meal = data["meals"][0]

    ingredients = []

    for i in range(1, 21):
        ingredient = meal[f"strIngredient{i}"]
        measure = meal[f"strMeasure{i}"]

        if ingredient:
            quantity, unit = parse_measure(measure)

            ingredients.append({
                "ingredient": ingredient,
                "measure": convert_measure(measure),
                "quantity": quantity,
                "unit": unit})

    return render(request, "pantry/recipe_detail.html", {
        "meal": meal,
        "ingredients": ingredients
    })

@login_required
def my_recipes(request):
    recipes = Recipe.objects.filter(user=request.user)
    return render(request, "pantry/my_recipes.html", {
    "recipes": recipes})

@login_required
def add_recipe(request):
    if request.method == "POST":
        name = request.POST["name"]
        instructions = request.POST["instructions"]

        recipe = Recipe.objects.create(
            user=request.user,
            name=name,
            instructions=instructions)

        ingredients = request.POST.getlist("ingredient")
        quantities = request.POST.getlist("quantity")
        units = request.POST.getlist("unit")

        for i in range(len(ingredients)):
            ingredient_name = ingredients[i]

            ingredient = Ingredient.objects.filter(name=ingredient_name).first()

            if ingredient is None:
                ingredient = Ingredient.objects.create(name=ingredient_name)

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantities[i],
                unit=units[i])

        return HttpResponseRedirect(reverse("my_recipes"))

    return render(request, "pantry/add_recipe.html")

@login_required
def my_recipe_detail(request, recipe_id):
    recipe = Recipe.objects.get(
    id=recipe_id,
    user=request.user)

    ingredients = RecipeIngredient.objects.filter(recipe=recipe)

    return render(request, "pantry/my_recipe_detail.html", {
        "recipe": recipe,
        "ingredients": ingredients})

def check_ingredients(recipe_ingredients, pantry_items):
    shopping_list = []
    ignore_ingredients = ["water", "salt", "Water", "Salt"]

    for recipe_item in recipe_ingredients:
        name = recipe_item["ingredient"]
        recipe_name = name.lower().strip()
        quantity = recipe_item["quantity"]
        unit = recipe_item["unit"]

        if recipe_name in ignore_ingredients:
            continue

        pantry_item = None

        for item in pantry_items:
            if item.name.name.lower().strip() == recipe_name:
                pantry_item = item
                break

        if pantry_item:
            if quantity is None or unit in ["tsp", "tbs", "Pinch"]:
                continue

            if unit != pantry_item.unit:
                shopping_list.append({
                    "ingredient": name,
                    "quantity": quantity,
                    "unit": unit,
                    "manual_check": True})
                continue

            if pantry_item.quantity < quantity:
                shopping_list.append({
                    "ingredient": name,
                    "quantity": quantity - pantry_item.quantity,
                    "unit": unit,
                    "manual_check": False})

            continue

        shopping_list.append({
            "ingredient": name,
            "quantity": quantity,
            "unit": unit,
            "manual_check": False,
            "measure": recipe_item.get("measure", "")})

    return shopping_list

@login_required
def shopping_list_api(request, meal_id):
    response = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")

    data = response.json()
    meal = data["meals"][0]

    recipe_ingredients = []

    # The API provides up to 20 ingredients for every recipe by default
    for i in range(1, 21):
        ingredient = meal[f"strIngredient{i}"]
        measure = meal[f"strMeasure{i}"]

        if ingredient:
            quantity, unit = parse_measure(measure)

            recipe_ingredients.append({
                "ingredient": ingredient,
                "quantity": quantity,
                "unit": unit,
                "measure": measure})

    pantry_items = PantryItem.objects.all()

    shopping_list = check_ingredients(
    recipe_ingredients,
    pantry_items)

    manual_check = False

    for item in shopping_list:
        # unit of pantry ingredient doesn't match unit of recipe ingredient (e.g 200g vs. 200ml)
        if item["manual_check"]:
            manual_check = True
            break

    return render(request, "pantry/shopping_list.html", {
        "meal": meal,
        "shopping_list": shopping_list,
        "manual_check": manual_check})

@login_required
def my_shopping_list(request, recipe_id):
    recipe = Recipe.objects.get(
        id=recipe_id,
        user=request.user)

    recipe_ingredients = []

    ingredients = RecipeIngredient.objects.filter(
        recipe=recipe)

    for item in ingredients:
        recipe_ingredients.append({
            "ingredient": item.ingredient.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "measure": str(item.quantity) + " " + item.unit})

    pantry_items = PantryItem.objects.all()

    shopping_list = check_ingredients(
        recipe_ingredients,
        pantry_items)

    manual_check = False

    for item in shopping_list:
        if item["manual_check"]:
            manual_check = True
            break

    return render(request, "pantry/my_shopping_list.html", {
        "recipe": recipe,
        "shopping_list": shopping_list,
        "manual_check": manual_check})