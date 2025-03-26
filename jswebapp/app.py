from flask import Flask, request, jsonify, render_template
import openai
import json
import logging

app = Flask(__name__)

openai.api_key = "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"

logging.basicConfig(level=logging.DEBUG)

# Store uploaded data
annotations_data = {}
synthesized_data = {}  # Store the synthesized themes and students

@app.route('/')
def index():
    return render_template('index.html')

# Step 1: File Upload
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        annotations_data['file_content'] = file.read().decode("utf-8")
        return jsonify({"success": True, "message": "File uploaded successfully!"})
    return jsonify({"success": False, "message": "File upload failed!"})

# Step 2: Synthesize Annotations
@app.route('/synthesize', methods=['POST'])
def synthesize():
    global synthesized_data
    # Call GPT to analyze and synthesize key themes
    prompt = f"""
    Extract the key themes from the following student annotations. 
    - The key themes should be phrases.
    - Identify recurring themes and major discussion points.
    The output should be in a table with 3 columns:
      1. **Theme**: The theme or main point identified.
      2. **Students**: List of students who mentioned this theme.
      3. **Snippets**: Key snippets of the relevant comments from students related to the theme.
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": annotations_data.get('file_content', '')}]
    )

    # Convert the table string into a structured format
    synthesis_output = response.choices[0].message.content

    # Split the table into rows and remove the markdown table formatting
    rows = [row.strip() for row in synthesis_output.split('\n') if row.strip() and '|-' not in row]
    headers = [h.strip() for h in rows[0].split('|') if h.strip()]

    # Convert to array of objects
    result = []
    for row in rows[2:]:  # Skip header and separator
        cols = [col.strip() for col in row.split('|') if col.strip()]
        if len(cols) >= 3:
            result.append({
                "theme": cols[0],
                "students": cols[1],
                "snippets": cols[2]
            })
    
    # Store the synthesized data for use in grouping
    synthesized_data['themes_and_students'] = result

    return jsonify({
        "synthesis_output": result
    })



# Step 3: Final Grouping and Reflection Questions (based on criteria and Step 2 synthesis)
@app.route('/group_and_questions', methods=['POST'])
def group_and_questions():
    data = request.json
    group_size = data.get("group_size")
    primary_topic = data.get("primary_topic")
    abstraction = data.get("abstraction")
    discussion_goals = data.get("discussion_goals")
    interaction_modes = data.get("interaction_modes")

    # Retrieve the synthesized themes and students
    themes_and_students = synthesized_data.get('themes_and_students', {})

    # GPT prompt for grouping (Step 3a)
    grouping_prompt = f"""
    Group students into discussions based on the following criteria:
    - Group Size: {group_size}
    - Primary Topic: {primary_topic}
    - Level of Abstraction: {abstraction}
    - The themes and the students who mentioned them are as follows:
    {json.dumps(themes_and_students, indent=2)}

    Ensure that:
    - Groups are evenly distributed.
    - Each group has diverse perspectives based on the themes mentioned.
    - Group discussions remain focused on the specified topics.
    """

    group_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You must respond with valid JSON with the following structure: [{\"group_name\": \"Group 1\", \"members\": [{\"name\": \"Student1\", \"perspective\": \"Theme1\"}]}]"},
            {"role": "user", "content": grouping_prompt}
        ]
    )

    try:
        groups = json.loads(group_response.choices[0].message.content)
    except json.JSONDecodeError:
        groups = []

    # GPT prompt for reflection questions (Step 3b)
    question_prompt = f"""
    Generate personalized reflection questions based on the groups and criteria:
    - Goals: {discussion_goals}
    - Interaction Modes: {interaction_modes}
    - The generated groups are as follows: {json.dumps(groups)}
    Ensure the questions:
    - Encourage deeper thinking.
    - Align with each student's group discussion focus.
    - Fit within the interaction mode chosen.
    Format the response as a JSON array of objects with 'student' and 'question' fields.
    """

    question_response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You must respond with valid JSON"},
            {"role": "user", "content": question_prompt}
        ]
    )

    try:
        # Attempt to parse JSON responses from GPT
        grouping_output = json.loads(group_response.choices[0].message.content)
        questions_output = json.loads(question_response.choices[0].message.content)

        # Log the received outputs for debugging
        logging.debug(f"Generated groups: {grouping_output}")
        logging.debug(f"Generated reflection questions: {questions_output}")

    except json.JSONDecodeError as e:
        # Log an error if JSON parsing fails
        logging.error(f"Error decoding JSON response: {e}")
        # Fallback to empty arrays if JSON parsing fails
        grouping_output = []
        questions_output = []

    # Return the results for Step 3 (grouping and questions)
    return jsonify({
        "grouping_output": grouping_output,
        "questions_output": questions_output
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
