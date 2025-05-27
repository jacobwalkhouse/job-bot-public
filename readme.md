# Job Application Workflow

An automated job application generator that uses LM Studio API to create customized resumes and cover letters.

## Features

- 🤖 AI-powered content generation using LM Studio
- 📝 Customizable markdown templates
- 📄 Automatic PDF generation with Pandoc
- ⚙️ JSON-based configuration
- 🎯 Job listing analysis and content tailoring

## Prerequisites

### Required Software

1. **LM Studio**: Download and set up LM Studio with a local model
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Load a compatible model (models that support user/assistant roles work best)
   - Enable the API server in LM Studio

2. **Python**: Python 3.7+ with required packages

3. **Pandoc + LaTeX** (for PDF generation):
   
   **Windows:**
   ```bash
   # Install Pandoc from https://pandoc.org/installing.html
   # Install MiKTeX from https://miktex.org/download
   ```
   
   **macOS:**
   ```bash
   brew install pandoc
   # Install MacTeX from https://tug.org/mactex/ OR BasicTeX:
   brew install --cask basictex
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get install pandoc texlive-xetex texlive-fonts-recommended
   ```
   
   **Note:** XeLaTeX is required for PDF generation. The script will try multiple LaTeX engines (xelatex, pdflatex, lualatex) but XeLaTeX typically works best with Unicode content.

## Installation

1. Clone or download this repository:
   ```bash
   git clone <repository-url>
   cd job-application-workflow
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run setup (optional - creates default config if not present):
   ```bash
   python setup.py
   ```

4. Configure your information:
   ```bash
   # Edit the generated config.json file with your details
   nano config.json  # or use your preferred editor
   ```

## Usage

### Basic Usage
```bash
python job_app_generator.py
```
Then paste your job listing when prompted.

### Advanced Usage
```bash
# Use custom config file
python job_app_generator.py --config my_config.json

# Override company name
python job_app_generator.py --company "Specific Company Name"
```

### Interactive Mode
1. Run the script
2. Paste the job listing (multiple lines supported)
3. Press Ctrl+D (Unix/Mac) or Ctrl+Z (Windows) to finish
4. Wait for generation to complete

## Configuration

Edit `config.json` to customize:

### LM Studio Settings
```json
{
  "lm_studio": {
    "base_url": "http://localhost:1234/v1",
    "model": "local-model",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Personal Information
- Contact details (name, email, phone, location)
- Education background
- Professional field
- LinkedIn profile

### Skills and Experience
- Key competencies and technical skills
- Work history with detailed achievements
- Bullet points for each position

## File Structure

```
job-application-workflow/
├── job_app_generator.py    # Main application
├── gui.py                 # GUI interface (if using DearPyGui)
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
├── config.json           # Configuration file
├── templates/            # Markdown templates
│   ├── cover_letter_template.md
│   └── resume_template.md
├── output/              # Generated files
└── README.md           # This file
```

## Output Files

The generator creates timestamped files in the `output/` directory:
- `cover_letter_CompanyName_YYYYMMDD_HHMMSS.md`
- `resume_CompanyName_YYYYMMDD_HHMMSS.md`  
- `cover_letter_CompanyName_YYYYMMDD_HHMMSS.pdf` (if Pandoc/LaTeX available)
- `resume_CompanyName_YYYYMMDD_HHMMSS.pdf` (if Pandoc/LaTeX available)

## Troubleshooting

### LM Studio Connection Issues
- **"Could not connect to LM Studio"**: Ensure LM Studio is running and the API server is enabled
- **"Only user and assistant roles are supported"**: This is normal - the script handles this automatically by combining system and user messages
- Check the base URL in config.json (default: http://localhost:1234/v1)
- Verify a model is loaded in LM Studio
- Try using a different model if issues persist

### PDF Generation Issues
- **"Pandoc not found"**: Install Pandoc from [pandoc.org](https://pandoc.org/installing.html)
- **"LaTeX Error"**: Install a LaTeX distribution:
  - **Windows**: MiKTeX or TeX Live
  - **macOS**: MacTeX or BasicTeX
  - **Linux**: texlive-xetex package
- **Unicode/Font issues**: XeLaTeX (preferred) handles Unicode better than pdflatex
- Check file permissions in output directory
- Ensure markdown files are properly formatted

### Template Issues
- Check template files exist in `templates/` directory
- Verify all placeholder variables are properly formatted: `{{VariableName}}`
- Run the script once to auto-generate default templates
- Templates use double curly braces for variable substitution

### Model Compatibility
- Some models work better than others with the API format
- If you get template errors, try searching for your model under "lmstudio-community" for better prompt templates
- You can override prompt templates in LM Studio: My Models > model settings > Prompt Template

## API Dependencies

This project uses direct HTTP requests to communicate with LM Studio's OpenAI-compatible API. No external API keys or internet connection required for AI generation - everything runs locally.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License - feel free to use and modify as needed.