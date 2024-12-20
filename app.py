import requests
from flask import Flask, request, render_template, send_file, jsonify
import openai
import markdown
import io

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key (replace with your key)
openai.api_key = "hahhahahahah"

@app.route('/')
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route('/generate-docs', methods=['POST'])
def generate_docs():
    """Generate documentation for the provided GitHub repo."""
    repo_url = request.form.get("repoUrl")

    # Validate GitHub URL
    if not repo_url.startswith("https://github.com/"):
        return "Invalid GitHub URL. Please provide a valid public GitHub repository URL.", 400

    # Derive the GitHub API URL for the repository
    repo_api_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
    
    try:
        # Fetch the file tree from the repository
        response = requests.get(f"{repo_api_url}/contents")
        response.raise_for_status()
        files = response.json()

        # Initialize documentation content
        repo_name = repo_url.split('/')[-1]
        doc_content = f"# Documentation for {repo_name}\n\n"

        # Process each file in the repository
        for file in files:
            if file['type'] == 'file':  # Ignore directories
                file_name = file['name']
                file_content = requests.get(file['download_url']).text

                # Generate summary using OpenAI API
                doc_content += f"## File: {file_name}\n"
                doc_content += generate_file_summary(file_content)

        # Save the documentation to a Markdown file in memory
        doc_buffer = io.StringIO()
        doc_buffer.write(doc_content)
        doc_buffer.seek(0)

        # Return the Markdown file for download
        return send_file(
            io.BytesIO(doc_buffer.getvalue().encode('utf-8')),
            mimetype='text/markdown',
            as_attachment=True,
            download_name=f"{repo_name}_documentation.md"
        )

    except requests.exceptions.RequestException as e:
        return f"Error fetching repository data: {e}", 500
    except Exception as e:
        return f"Error processing repository: {e}", 500

def generate_file_summary(file_content):
    """Use OpenAI API to generate a summary for a file."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo" for a cheaper option
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes code."},
                {"role": "user", "content": f"Summarize the following file:\n\n{file_content}"}
            ],
            max_tokens=150
        )
        return response['choices'][0]['message']['content'].strip() + "\n\n"
    except Exception as e:
        return f"Error summarizing file: {e}\n\n"


if __name__ == "__main__":
    app.run(debug=True)
