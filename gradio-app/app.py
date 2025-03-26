import gradio as gr
import openai
import json
import logging
import pandas as pd
import os

# Set OpenAI API Key (Do not hardcode; use environment variables in production)
openai.api_key = os.getenv("API_TOKEN")

if not openai.api_key:
    raise ValueError("API_TOKEN environment variable is not set. Please set it before running the application.")

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
    if 'file_content' not in annotations_data:
        return "Please upload a file first.", "Please upload a file first."

    # Extract unique student names from the "name" field in annotations_data
    try:
        file_content = json.loads(annotations_data['file_content'])  # Parse the uploaded JSON file
        unique_students = [entry['name'] for entry in file_content if 'name' in entry]  # Extract names
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Error parsing uploaded file content: {e}")
        return "Error parsing uploaded file content.", "Error parsing uploaded file content."

    # Ensure unique students are sorted for consistency
    unique_students = sorted(set(unique_students))

    # Build descriptions for selected discussion goals
    selected_goals_descriptions = "\n".join(
        [f"- {goal}: {DISCUSSION_GOALS_DESCRIPTIONS[goal]}" for goal in discussion_goals if goal in DISCUSSION_GOALS_DESCRIPTIONS]
    )

    # Build descriptions for selected interaction modes
    selected_modes_descriptions = "\n".join(
        [f"- {mode}: {INTERACTION_MODES_DESCRIPTIONS[mode]}" for mode in interaction_modes if mode in INTERACTION_MODES_DESCRIPTIONS]
    )

    # Grouping prompt
    grouping_prompt = f"""
    Group the following unique students into discussions based on the criteria below:
    - Unique Students: {', '.join(unique_students)}
    - Group Size: {group_size}
    - Primary Topic: {primary_topic}
    - Level of Abstraction: {abstraction}
    Discussion Goals:
    {selected_goals_descriptions}
    Modes of Interaction:
    {selected_modes_descriptions}
    The themes and the students who mentioned them are as follows:
    {json.dumps(synthesized_data.get('themes_and_students', []), indent=2)}
    Ensure that:
    - Each unique student is assigned to only one group.
    - Groups are evenly distributed.
    - Each group has {group_size} students (or as close as possible).
    - Each group has diverse perspectives based on the themes mentioned.
    Respond with a bulleted list in the following format:
    - Group 1:
      - Student1 (Theme1)
      - Student2 (Theme2)
    - Group 2:
      - Student3 (Theme3)
      - Student4 (Theme4)
    """

    try:
        group_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You must respond with a bulleted list."},
                {"role": "user", "content": grouping_prompt}
            ]
        )
        group_output = group_response.choices[0].message.content.strip()
        logging.debug(f"Raw Grouping Output: {group_output}")  # Log the raw GPT response
    except Exception as e:
        logging.error(f"Error in grouping response: {e}")
        group_output = "Error generating groups."

    # Question generation prompt
    question_prompt = f"""
    Generate personalized reflection questions for each student based on these criteria:
    - Unique Students: {', '.join(unique_students)}
    - Primary Topics to shape the question: {primary_topic}
    - Goals - these goals are not the content of discussion but rather how the question should be desgined based on the topic and content of annotations: {discussion_goals}
    - Interaction Modes: {interaction_modes}
    - The groups generated prior are as follows:
    {group_output}
    Ensure that:
    - Each unique student is assigned only one question.
    Respond with a bulleted list in the following format:
    - Student1: Reflection question for Student1
    - Student2: Reflection question for Student2
    """

    try:
        question_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You must respond with a bulleted list."},
                {"role": "user", "content": question_prompt}
            ]
        )
        question_output = question_response.choices[0].message.content.strip()
        logging.debug(f"Raw Question Output: {question_output}")  # Log the raw GPT response
    except Exception as e:
        logging.error(f"Error in question response: {e}")
        question_output = "Error generating questions."

    return group_output, question_output

# Mapping for Discussion Goals
DISCUSSION_GOALS_DESCRIPTIONS = {
    "Deepen Text Interpretation": "Cluster students based on diverse interpretations. Within each group, assigns students prompts that challenge their perspectives, encouraging textual analysis, inferencing, and synthesis to refine collective understanding.",
    "Encourage Elaboration & Connections": "Form groups of students who hold related yet distinct ideas. Within each group, prompt students to expand on each other’s points, link concepts to real-world contexts, and articulate deeper connections across themes.",
    "Stimulate Questioning & Uncertainty Identification": "Group students to include differing levels of confidence in the topic. Within each group,. prompt each student to challenge assumptions, identify ambiguities, and collaboratively refine their understanding by generating and addressing critical questions.",
    "Promote Conceptual Clarification": "Group students with varying levels of clarity on key concepts. Within each group, assign prompts that require defining, contrasting, and refining ideas to establish shared, well-articulated conceptual understandings.",
    "Foster Consensus Building": "Place together tudents with differing viewpoints. Within each group, give each student prompts to guide them to navigate disagreements, evaluate evidence, and reach reasoned agreements, ensuring balanced discussions that integrate multiple perspectives into a coherent synthesis.",
    "Provide Peer Support": "Combine students with stronger and weaker grasp of topics. Within each group, generate prompts that foster reciprocal teaching where explanations, clarifications, and scaffolding strengthen collective learning while fostering a supportive discussion environment.",
    "Explore & Address Conflicting Perspectives": "Form groups with opposing viewpoints. Within each group, prompt students to critically engage, recognize underlying assumptions, and constructively negotiate differences while maintaining open, respectful discourse."
}

# Mapping for Modes of Interaction
INTERACTION_MODES_DESCRIPTIONS = {
    "Debate: Argue Conflicting Understandings": "Students with opposing perspectives are grouped and assigned roles that require defending, critiquing, and refining their arguments, fostering critical thinking, persuasive reasoning, and engagement with counterarguments.",
    "Informing: One Student Explains to Others": "Groups include knowledge disparities where informed students act as peer educators, explaining concepts, providing examples, and clarifying misunderstandings, reinforcing learning through structured knowledge-sharing.",
    "Co-construction: Collaboratively Build a Shared Understanding": "Students with complementary knowledge work together to integrate insights, refine collective interpretations, and construct nuanced understandings, ensuring active participation and mutual idea development.",
    "Building Understanding Towards an Answer: Develop Foundational Concepts": "Groups engage in stepwise knowledge-building, collectively identifying gaps, structuring foundational ideas, and synthesizing key insights, leading to stronger conceptual frameworks and deeper comprehension."
}

# Gradio UI
upload_interface = gr.Interface(
    fn=upload_file,
    inputs=gr.File(),
    outputs="text",
    title="Upload Annotations File"
)
synthesis_interface = gr.Interface(
    fn=synthesize_annotations,
    inputs=None,
    outputs=gr.Dataframe(headers=["Theme", "Mentioned by", "Snippets"], label="Synthesized Data Table"),
    title="Synthesize Annotations"
)
grouping_interface = gr.Interface(
    fn=group_and_generate_questions,
    inputs=[
        gr.Number(label="Group Size"),
        gr.Textbox(label="Primary Topics", placeholder="e.g., Topic A and Topic B"),
        gr.Radio(["Specific Examples", "Abstract Principles"], label="Level of Abstraction"),
        gr.CheckboxGroup([
            "Deepen Text Interpretation",
            "Encourage Elaboration & Connections",
            "Stimulate Questioning & Uncertainty Identification",
            "Promote Conceptual Clarification",
            "Foster Consensus Building",
            "Provide Peer Support",
            "Explore & Address Conflicting Perspectives"
        ], label="Discussion Goals (pick three to prioritize)"),
        gr.CheckboxGroup([
            "Debate: Argue conflicting understandings",
            "Informing: One student explains to others",
            "Co-construction: Collaboratively build a shared understanding",
            "Building Understanding Towards an Answer: Develop foundational concepts"
        ], label="Interaction Mode (select at most 2)")
    ],
    outputs=[
        gr.Textbox(label="Group Assignments (Bulleted List)", lines=10, placeholder="GPT output for group assignments will appear here."),
        gr.Textbox(label="Rise-above Questions (Bulleted List)", lines=10, placeholder="GPT output for questions will appear here.")
    ],
    title="Generate Groups & Rise-above Questions"
)
# Launch Gradio App
gr.TabbedInterface(
    [upload_interface, synthesis_interface, grouping_interface],
    ["Upload", "Synthesize", "Group & Questions"]
).launch()
