from gradio import Interface, inputs, outputs
import openai
import json
import logging

openai.api_key = "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"

logging.basicConfig(level=logging.DEBUG)

annotations_data = {}
synthesized_data = {}

def upload_file(file):
    if file:
        annotations_data['file_content'] = file.read().decode("utf-8")
        return "File uploaded successfully!"
    return "File upload failed!"

def synthesize_annotations():
    global synthesized_data
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

    synthesis_output = response.choices[0].message.content
    rows = [row.strip() for row in synthesis_output.split('\n') if row.strip() and '|-' not in row]
    headers = [h.strip() for h in rows[0].split('|') if h.strip()]

    result = []
    for row in rows[2:]:
        cols = [col.strip() for col in row.split('|') if col.strip()]
        if len(cols) >= 3:
            result.append({
                "theme": cols[0],
                "students": cols[1],
                "snippets": cols[2]
            })
    
    synthesized_data['themes_and_students'] = result
    return result

def group_and_questions(group_size, primary_topic, abstraction, discussion_goals, interaction_modes):
    data = {
        "group_size": group_size,
        "primary_topic": primary_topic,
        "abstraction": abstraction,
        "discussion_goals": discussion_goals,
        "interaction_modes": interaction_modes
    }

    themes_and_students = synthesized_data.get('themes_and_students', {})

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
        questions_output = json.loads(question_response.choices[0].message.content)
    except json.JSONDecodeError:
        questions_output = []

    return {
        "groups": groups,
        "questions": questions_output
    }

iface = Interface(
    fn=upload_file,
    inputs=inputs.File(label="Upload Annotations File"),
    outputs=outputs.Textbox(label="Upload Status"),
    title="Annotation Synthesizer",
    description="Upload student annotations to synthesize themes and generate discussion groups."
)

iface.add_component(
    fn=synthesize_annotations,
    inputs=[],
    outputs=outputs.JSON(label="Synthesized Annotations"),
    title="Synthesize Annotations",
    description="Synthesize key themes from the uploaded annotations."
)

iface.add_component(
    fn=group_and_questions,
    inputs=[
        inputs.Slider(minimum=1, maximum=10, label="Group Size"),
        inputs.Textbox(label="Primary Topic"),
        inputs.Textbox(label="Level of Abstraction"),
        inputs.Textbox(label="Discussion Goals"),
        inputs.Textbox(label="Interaction Modes")
    ],
    outputs=outputs.JSON(label="Grouping and Questions"),
    title="Group and Reflection Questions",
    description="Generate discussion groups and reflection questions based on synthesized annotations."
)

iface.launch()