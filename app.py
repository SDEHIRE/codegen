import ast
import random
from flask import Flask, request, jsonify
import os
from flask_cors import CORS  # Import CORS requirements

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

class EnhancedQuestionGenerator:
    def __init__(self):
        """
        Initialize the question generator with enhanced templates.
        """
        self.question_templates = {
            "function": "What does the function '{name}' at line {lineno} do?",
            "function_args": "What are the purposes of the arguments in the function '{name}'?",
            "variable": "What is the role of the variable '{name}' at line {lineno}?",
            "loop": "What is the significance of the loop starting at line {lineno}?",
            "conditional": "Under what conditions does the code block at line {lineno} execute?",
            "import": "Why is the module '{name}' imported, and how is it used?",
            "docstring": "What does the following docstring explain: '{doc}'?"
        }

    def analyze_code(self, code_snippet):
        """
        Analyze the code to extract structural information.
        """
        try:
            tree = ast.parse(code_snippet)
            analysis = {
                "functions": [
                    {
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args]
                    }
                    for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                ],
                "variables": [
                    {"name": node.id, "lineno": node.lineno}
                    for node in ast.walk(tree) if isinstance(node, ast.Name)
                ],
                "loops": [
                    {"lineno": node.lineno}
                    for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))
                ],
                "conditionals": [
                    {"lineno": node.lineno}
                    for node in ast.walk(tree) if isinstance(node, ast.If)
                ],
                "imports": [
                    {"name": node.names[0].name, "lineno": node.lineno}
                    for node in ast.walk(tree) if isinstance(node, ast.Import)
                ],
                "docstrings": self.extract_docstrings(tree)
            }
            return analysis
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def extract_docstrings(tree):
        """
        Extract docstrings from the module and functions.
        """
        docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append(docstring.strip())
        return docstrings

    def generate_questions(self, code_snippet):
        """
        Generate questions based on the analysis and enhanced templates.
        """
        analysis = self.analyze_code(code_snippet)
        if "error" in analysis:
            return [f"Error analyzing code: {analysis['error']}"]

        questions = []

        # Generate questions for functions and arguments
        for func in analysis["functions"]:
            questions.append(
                self.question_templates["function"].format(name=func["name"], lineno=func["lineno"])
            )
            if func["args"]:
                questions.append(
                    self.question_templates["function_args"].format(name=func["name"])
                )

        # Generate questions for variables
        for var in analysis["variables"]:
            questions.append(
                self.question_templates["variable"].format(name=var["name"], lineno=var["lineno"])
            )

        # Generate questions for loops
        for loop in analysis["loops"]:
            questions.append(
                self.question_templates["loop"].format(lineno=loop["lineno"])
            )

        # Generate questions for conditionals
        for cond in analysis["conditionals"]:
            questions.append(
                self.question_templates["conditional"].format(lineno=cond["lineno"])
            )

        # Generate questions for imports
        for imp in analysis["imports"]:
            questions.append(
                self.question_templates["import"].format(name=imp["name"])
            )

        # Generate questions for docstrings
        for doc in analysis["docstrings"]:
            questions.append(
                self.question_templates["docstring"].format(doc=doc)
            )

        # Deduplicate questions while preserving order
        unique_questions = list(dict.fromkeys(questions))
        
        # Select and return a random question
        return random.choice(unique_questions)


@app.route('/generate_question', methods=['POST'])
def generate_question():
    try:
        code_snippet = request.json.get("code_snippet")
        if not code_snippet:
            return jsonify({"error": "No code snippet provided"}), 400

        generator = EnhancedQuestionGenerator()
        question = generator.generate_questions(code_snippet)
        return jsonify({"question": question})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
