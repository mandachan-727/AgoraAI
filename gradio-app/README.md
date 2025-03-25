# Gradio App for Synthesizing Annotations

This project is a Gradio application that allows users to upload student annotations, synthesize key themes, and generate discussion groups and reflection questions based on the synthesized data. The application integrates with OpenAI's GPT model to analyze and process the annotations.

## Project Structure

```
gradio-app
├── app.py
├── requirements.txt
└── README.md
```

## Installation

To run this application, you need to have Python installed on your machine. Follow these steps to set up the project:

1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```
2. Open your web browser and go to `http://localhost:5000` to access the Gradio interface.

## Features

- **File Upload**: Users can upload a file containing student annotations.
- **Synthesize Annotations**: The application extracts key themes from the annotations using OpenAI's GPT model.
- **Group Discussions**: Based on the synthesized themes, the application generates discussion groups.
- **Reflection Questions**: Personalized reflection questions are created for each group to encourage deeper thinking.

## Requirements

Make sure to have the following libraries installed:

- Gradio
- OpenAI

These libraries are listed in the `requirements.txt` file.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.