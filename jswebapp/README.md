# HTML/JS Web App for Agora

This web app is built using HTML and JavaScript, and it integrates with the `app.py` backend to upload and process student annotations. The app synthesizes key themes, generates discussion groups, and creates personalized reflection questions based on the annotations.

## Project Structure

```
jswebapp
├── app.py
└── template
    └── index.html
```

## Installation

Follow these steps to get the project up and running:

1. **Clone the Repository** or download the project files:
   ```bash
   git clone https://github.com/yourusername/jswebapp.git
   cd jswebapp
   ```
2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Application**:
   After installing the dependencies, start the app by running:
   ```bash
   python app.py
   ```

2. **Access the Interface**:
   Open your browser and go to `http://localhost:5000` to access the HTML/JS front end.

## Features

- **File Upload**: Users can upload a `.json` file containing student annotations.
- **Synthesize Annotations**: The app processes and synthesizes key themes from the annotations using the backend (handled by `app.py`).
- **Generate Discussion Groups**: Based on the synthesized data, the app creates optimal discussion group assignments.
- **Create Reflection Questions**: Personalized reflection questions are generated for each discussion group to encourage deeper engagement.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
