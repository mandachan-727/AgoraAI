import gradio as gr
import openai
import json
import logging
import pandas as pd

# yay
# Set OpenAI API Key (Do not hardcode; use environment variables in production)
openai.api_key = "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"

logging.basicConfig(level=logging.DEBUG)

# Store uploaded data
annotations_data = {}
synthesized_data = {}

def upload_file(file):
    """Handles file upload and stores its content."""
    if file is None:
        return "No file uploaded. Please select a file."

    # Gradio's gr.File() returns a NamedString object, so we need to use file.name
    with open(file.name, "r", encoding="utf-8") as f:
        content = f.read()

    annotations_data['file_content'] = content
    return "File uploaded successfully!"


def synthesize_annotations():
    """Synthesize key themes from uploaded annotations using GPT."""
    global synthesized_data
    if 'file_content' not in annotations_data:
        return "No file uploaded. Please upload a file first."

    prompt = """
    Extract the key themes from the following student annotations. 
    Identify recurring themes and major discussion points.
    Return a JSON array where each object has 'theme', 'students', and 'snippets'.
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": annotations_data['file_content']}
        ]
    )

    try:
        synthesis_output = json.loads(response.choices[0].message.content)
        synthesized_data['themes_and_students'] = synthesis_output

        # Save the output as a JSON file for global use
        with open("synthesized_data.json", "w", encoding="utf-8") as f:
            json.dump(synthesis_output, f, indent=4)

        # Convert the JSON output to a Pandas DataFrame for table display
        df = pd.DataFrame(synthesis_output)
        return df  # Only return the table for Gradio interface
    except json.JSONDecodeError:
        return "Error processing GPT response."

def group_and_generate_questions(group_size, primary_topic, abstraction, discussion_goals, interaction_modes):
    """Groups students and generates reflection questions based on criteria."""
    if 'themes_and_students' not in synthesized_data:
        return "Please run synthesis first.", None

    themes_and_students = synthesized_data['themes_and_students']
    
    grouping_prompt = f"""
    Group students into distinct groups for discussion based on the following criteria:
    - Group size: How many students in a group: {group_size}
    - Primary Topic: {primary_topic}
    - Level of Abstraction: {abstraction}
    - Interaction Modes: {interaction_modes}
    - The themes and the students who mentioned them are as follows:
    {json.dumps(themes_and_students, indent=2)}

    Ensure that:
    - Groups are evenly distributed.
    - Each group has diverse perspectives based on the themes mentioned.
    - Group discussions remain focused on the specified topics.

    The output should be a table with two fields: Group and Students. In each row of the students column, list each student's name and the theme they should discuss in brackets.
    """

    try:
        group_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Provide a plain text response."},
                      {"role": "user", "content": grouping_prompt}]
        )
        group_output = group_response.choices[0].message.content.strip()

        # Parse the GPT output into a structured format (e.g., a list of dictionaries)
        rows = [line.split('|') for line in group_output.split('\n') if '|' in line]
        table_data = [{"Group": row[0].strip(), "Students": row[1].strip()} for row in rows]

    except Exception as e:
        logging.error(f"Error in grouping response: {e}")
        table_data = [{"Group": "Error", "Students": "Error generating groups"}]

    question_prompt = f"""
    Generate personalized reflection questions for each student based on the groups and criteria:
    - Goals: {discussion_goals}
    - Interaction Modes: {interaction_modes}
    Ensure the questions:
    - Encourage deeper thinking.
    - Align with each student's group discussion focus.
    - Fit within the interaction mode chosen.
    Format the response as plain text with each question on a new line.
    """

    try:
        question_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Provide a plain text response."},
                      {"role": "user", "content": question_prompt}]
        )
        question_output = question_response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error in question response: {e}")
        question_output = "Error generating questions."

    return table_data, question_output

# Gradio UI
upload_interface = gr.Interface(
    fn=upload_file,
    inputs=gr.File(),
    outputs="text",
    fn=synthesize_annotations,tations"
    inputs=None,
    outputs=gr.Dataframe(label="Synthesized Data Table"),
    title="Synthesize Annotations"
)ynthesis_interface = gr.Interface(
    fn=synthesize_annotations,
grouping_interface = gr.Interface(
    fn=group_and_generate_questions,hesized Data Table"),
    inputs=[ynthesize Annotations"
        gr.Number(label="Group Size"),
        gr.Textbox(label="Primary Topic"),
        gr.Radio(["Specific Examples", "Abstract Principles"], label="Level of Abstraction"),
        gr.CheckboxGroup([questions,
            "Deepen Text Interpretation",
            "Encourage Elaboration & Connections",
            "Stimulate Questioning & Uncertainty Identification",
            "Promote Conceptual Clarification",t Principles"], label="Level of Abstraction"),
            "Foster Consensus Building",
            "Provide Peer Support",tion",
            "Explore & Address Conflicting Perspectives"
        ], label="Discussion Goals"),Uncertainty Identification",
        gr.CheckboxGroup([ptual Clarification",
            "Debate: Argue conflicting understandings",
            "Informing: One student explains to others",
            "Co-construction: Collaboratively build a shared understanding",
            "Building Understanding Towards an Answer: Develop foundational concepts"
        ], label="Interaction Mode")
    ],      "Debate: Argue conflicting understandings",
    outputs=[Informing: One student explains to others",
        gr.Dataframe(headers=["Group", "Students"], label="Student Grouping Table"),
        gr.Textbox(label="Reflection Questions Output", lines=10, placeholder="GPT output for questions will appear here.")
    ],  ], label="Interaction Mode")
    title="Generate Groups & Reflection Questions"
)   outputs=[
        gr.Textbox(label="Student Grouping Output", lines=10, placeholder="GPT output for groupings will appear here."),
# Launch Gradio Applabel="Reflection Questions Output", lines=10, placeholder="GPT output for questions will appear here.")
gr.TabbedInterface([upload_interface, synthesis_interface, grouping_interface], ["Upload", "Synthesize", "Group & Questions"]).launch()
    title="Generate Groups & Reflection Questions"
)

# Launch Gradio App
gr.TabbedInterface([upload_interface, synthesis_interface, grouping_interface], ["Upload", "Synthesize", "Group & Questions"]).launch()