# Job Bot

An automated job application generator that uses LM Studio API to create customized resumes and cover letters — now with support for parsing existing resumes in PDF and DOCX formats.

## Features

- 🤖 **AI-generated Content**: Uses LM Studio to create tailored resumes and cover letters
- 📥 **Resume Parsing**: AI can extract and reuse information from your existing PDF or DOCX resume
- 📝 **Markdown Templates**: Fully customizable templates for consistent formatting
- 📄 **Automatic PDF Generation**: Uses Pandoc and LaTeX to output printable documents
- ⚙️ **JSON Configuration**: All personal and job data is stored in an editable JSON file
- 🎯 **Job Listing Analysis**: Understands job descriptions and tailors application content accordingly

## Prerequisites

### Required Programs

1. **LM Studio**
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Load a local model (preferably one supporting user/assistant roles)
   - Enable the API server in LM Studio

2. **Pandoc**
   - Required for Markdown-to-PDF conversion  
   - [Install Pandoc](https://pandoc.org/installing.html)

3. **LaTeX Distribution** (required for PDF generation):
   - **Windows**: [MiKTeX](https://miktex.org/download) or TeX Live
   - **macOS**: [MacTeX](https://tug.org/mactex/) or BasicTeX (`brew install --cask basictex`)
   - **Linux**: `sudo apt-get install texlive-xetex texlive-fonts-recommended`

> ⚠️ *Note*: The script attempts to use XeLaTeX first, then pdflatex/lualatex if necessary.

### Required Python Libraries

Install via `pip`:

```bash
pip install requests pypdf python-docx markdown openai
```

Alternatively, install from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

#### `requirements.txt`
```
requests
pypdf
python-docx
markdown
openai
```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/job-application-workflow.git
   cd job-application-workflow
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the setup script (optional):
   ```bash
   python setup.py
   ```

4. Configure your profile:
   ```bash
   nano config.json  # or open with any editor
   ```

## Usage

### Command Line Usage
```bash
python job_app_generator.py
```
Then paste your job listing when prompted.

#### Advanced Options
```bash
# Use custom config file
python job_app_generator.py --config my_config.json

# Override company name
python job_app_generator.py --company "Specific Company Name"
```

### GUI Usage
```bash
python gui.py
```
This launches a graphical interface for easier input and configuration. Recommended for users who prefer not to use the command line.

#### Instructions
1. Click the **Parse Resume** button and choose a PDF or DOCX file from the file browser. The application will extract relevant details automatically.
2. Copy the job description from your chosen job listing and paste it into the **Job Listing** text box.
3. Click **Generate Application** to create your customized resume and cover letter.
4. Your generated files will appear in the `/output` directory.

## Configuration

Edit the `config.json` file to update your:

### LM Studio Settings
```json
"lm_studio": {
  "base_url": "http://localhost:1234/v1",
  "model": "local-model",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### Personal Profile
- Full name, email, phone, location
- Education background
- LinkedIn or website links

### Skills and Experience
- Technical skills and soft skills
- Past job roles, achievements, and responsibilities
- Bullet-point highlights per position

## File Structure

```
job-application-workflow/
├── job_app_generator.py      # Main script
├── gui.py                    # Optional GUI interface
├── setup.py                  # Setup utility
├── requirements.txt          # Required Python packages
├── config.json               # User config file
├── templates/                # Markdown templates
│   ├── resume_template.md
│   └── cover_letter_template.md
├── output/                   # Generated files
└── README.md                 # This documentation
```

## Output Files

Generated files are saved to the `output/` directory with timestamped filenames:

- `resume_CompanyName_YYYYMMDD_HHMMSS.md`
- `cover_letter_CompanyName_YYYYMMDD_HHMMSS.md`
- (If PDF tools available):
  - `resume_CompanyName_YYYYMMDD_HHMMSS.pdf`
  - `cover_letter_CompanyName_YYYYMMDD_HHMMSS.pdf`

## Troubleshooting

### LM Studio Connection Issues
- Ensure LM Studio is running and the API server is enabled
- Verify model supports `user/assistant` roles
- Check base URL in `config.json` (default: `http://localhost:1234/v1`)
- Try a different model if responses are blank or malformed

### PDF Generation Errors
- Ensure Pandoc is installed and on your PATH
- Confirm a LaTeX distribution is installed (XeLaTeX preferred)
- If Unicode/font issues appear, use XeLaTeX over pdflatex
- Check output file permissions

### Resume Parsing Issues
- Only `.pdf` and `.docx` files are supported
- File must be readable and structured logically (no image-based PDFs)

### Template Errors
- Templates should be in `templates/` folder
- All variables must be in double curly braces: `{{VariableName}}`
- Run the script once to auto-generate default templates if missing

## API Notes

This project uses **local models** via LM Studio’s **OpenAI-compatible API** — no external keys or cloud connections required.

## Contributing

Feel free to open issues or submit pull requests for features, bug fixes, or suggestions.

## License

The UnLicense — free to use, modify, and distribute.
