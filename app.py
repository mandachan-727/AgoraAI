from flask import Flask, request, jsonify, render_template
import json
import random
import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict

app = Flask(__name__)

# Load mock student data
with open('mock_data.json', 'r') as f:
    students = json.load(f)

# OpenAI API Key
OPENAI_API_KEY = "key"
openai.api_key = OPENAI_API_KEY

### NLP-BASED GROUPING LOGIC ###

# Extract key themes from student annotations
def extract_themes(annotations):
    prompt = f"Analyze the following annotations and extract the key academic themes:\n{annotations}"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.split(", ")

# Cluster students by annotation themes
def cluster_students(discussion_goal, group_size):
    all_annotations = [" ".join(student["annotations"]) for student in students]

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(all_annotations)

    num_clusters = max(2, len(students) // group_size)  # Adjust cluster count dynamically
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    # First, gather students into initial clusters
    clustered_students = defaultdict(list)
    for i, student in enumerate(students):
        clustered_students[labels[i]].append(student)
    
    # Then redistribute to achieve desired group size
    groups = []
    current_group = []
    for cluster in clustered_students.values():
        for student in cluster:
            current_group.append(student)
            if len(current_group) == group_size:
                groups.append(current_group)
                current_group = []
    
    # Add any remaining students to last group
    if current_group:
        if len(current_group) < group_size and groups:
            groups[-1].extend(current_group)  # add to last group if smaller than desired size
        else:
            groups.append(current_group)  # or create new group if reasonable size
    if discussion_goal == "diverse_views":
        random.shuffle(groups)
    return groups

### SYNTHESIZE THEMES FOR INSTRUCTOR ###

def synthesize_themes():
    theme_summary = {}
    for student in students:
        themes = extract_themes(" ".join(student["annotations"]))
        for theme in themes:
            if theme not in theme_summary:
                theme_summary[theme] = []
            theme_summary[theme].append(student["name"])

    return theme_summary  # Returns {theme: [students discussing it]}

@app.route('/get_themes', methods=['GET'])
def get_themes():
    themes = synthesize_themes()
    return jsonify(themes)

### FINAL PROMPT GENERATION ###

def generate_final_prompts(refined_themes):
    prompts = {}
    for theme, student_list in refined_themes.items():
        prompt_text = f"Discuss the theme '{theme}' in relation to previous annotations. Consider new perspectives."
        for student in student_list:
            prompts[student] = prompt_text
    return prompts

@app.route('/assign_final_prompts', methods=['POST'])
def assign_final_prompts():
    data = request.json
    refined_themes = data['refined_themes']
    final_prompts = generate_final_prompts(refined_themes)
    return jsonify(final_prompts)

### MAIN ROUTES ###

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_groups', methods=['POST'])
def generate_groups():
    if request.is_json:
        data = request.json
    else:
        data = request.form
    groups = cluster_students(data['discussion_goal'], data['group_size'])
    return jsonify(groups)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
