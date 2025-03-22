from flask import Flask, request, jsonify, render_template
import json
import random
import openai

app = Flask(__name__)

# Load mock student data
with open('mock_data.json', 'r') as f:
    students = json.load(f)

# OpenAI API Key
OPENAI_API_KEY = "your-api-key-here"
openai.api_key = OPENAI_API_KEY

# Simple grouping logic
def group_students(discussion_goal, group_size):
    if discussion_goal == "diverse_views":
        random.shuffle(students)  # Simple shuffle for diversity
    else:  # deepen_shared_ideas
        students.sort(key=lambda x: x['discussion_style'])  # Sort by style - need to specify how we end up "tagging these discussion behavior" - or NLP parsing for common topic
    
    groups = [students[i:i+group_size] for i in range(0, len(students), group_size)]
    return groups

# AI-generated prompts
def generate_nudge(student, question):
    prompt = f"{student['name']}, in your previous notes, you emphasized {student['annotations'][0]}. How might that challenge today’s question: '{question}'?"
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_groups', methods=['POST'])
def generate_groups():
    data = request.json
    groups = group_students(data['discussion_goal'], data['group_size'])
    
    for group in groups:
        for student in group:
            student['nudge'] = generate_nudge(student, data['discussion_question'])
    
    return jsonify(groups)

if __name__ == '__main__':
    app.run(debug=True)
