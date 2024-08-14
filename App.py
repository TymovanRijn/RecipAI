from flask import Flask, render_template, request
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key_env = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

client = OpenAI(api_key=f"{api_key_env}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-recipe')
def create_recipe():
    return render_template('create_recipe.html')

@app.route('/submit-recipe', methods=['POST'])
def submit_recipe():
    ingredients = []
    ingredient_names = request.form.getlist('ingredient_name[]')
    ingredient_quantities = request.form.getlist('ingredient_quantity[]')
    ingredient_units = request.form.getlist('ingredient_unit[]')
    use_household_items = request.form.get('use_household_items')
    allow_extra_ingredients = request.form.get('allow_extra_ingredients')
    strict_ingredients = request.form.get('strict_ingredients')

    for name, quantity, unit in zip(ingredient_names, ingredient_quantities, ingredient_units):
        ingredients.append(f"{quantity} {unit} {name}")

    prompt = (
        f"Create a recipe using the following ingredients:\n"
        f"{', '.join(ingredients)}.\n\n"
    )

    if use_household_items:
        prompt += "You can use common household items like salt, pepper, and oil.\n"

    if allow_extra_ingredients and not strict_ingredients:
        prompt += "Feel free to add other ingredients to enhance the recipe.\n"
    elif strict_ingredients:
        prompt += "Only use the provided ingredients. Do not add anything else.\n"

    prompt += "Respond in the following format:\n"
    prompt += "Title: Recipe Title\n"
    prompt += "Ingredients: List of ingredients\n"
    prompt += "Instructions: Step-by-step instructions without numbering."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{prompt}"},
        ]
    )

    message_content = response.choices[0].message.content

    lines = message_content.split('\n')
    title = ""
    ingredients = []
    instructions = []
    current_section = None

    for line in lines:
        if line.startswith("Title:"):
            title = line.replace("Title:", "").strip()
            current_section = "title"
        elif line.startswith("Ingredients:"):
            current_section = "ingredients"
        elif line.startswith("Instructions:"):
            current_section = "instructions"
        else:
            if current_section == "ingredients":
                ingredients.append(line.strip())
            elif current_section == "instructions":
                cleaned_instruction = line.strip().lstrip("0123456789. ")  # Verwijdert eventuele nummers aan het begin
                instructions.append(cleaned_instruction)

    # Gebruik DALL-E om een afbeelding te genereren voor het recept
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=f"Beautiful image of {title}, professionally styled and plated",
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = image_response.data[0].url

    return render_template(
        'recipe.html',
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        image_url=image_url
    )

if __name__ == '__main__':
    app.run(debug=True)
