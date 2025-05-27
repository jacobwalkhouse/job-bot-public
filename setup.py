#!/usr/bin/env python3
"""
Setup script for Job Application Workflow
"""

import os
import shutil
import json
from pathlib import Path


def setup_project():
    """Set up the project structure and templates"""
    print("🚀 Setting up Job Application Workflow...")
    
    # Create directory structure
    directories = ["templates", "output"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Create template files with updated format
    cover_letter_template = """{{Your Full Name}}  
{{Your Email}} | {{Your Phone Number}}  
{{Your Location}}

{{HiringManagerName}}  
{{Company}}

Dear {{HiringManagerName}},

I am writing to express my strong interest in the {{JobTitle}} position at {{Company}}. As a {{YourField}} professional with experience in {{Skill1}} and {{Skill2}}, I am excited about the opportunity to contribute to your team.

{{CustomParagraphFromAI}}

My background includes:
- {{BulletPoint1a}}
- {{BulletPoint1b}}
- {{BulletPoint2a}}

I am particularly drawn to {{Company}} because of your innovative approach and commitment to excellence. I would welcome the opportunity to discuss how my skills and experience can contribute to your team's success.

Thank you for your time and consideration. I look forward to hearing from you.

Sincerely,  
{{Your Full Name}}"""

    resume_template = """# {{Your Full Name}}

**Email:** {{Your Email}} | **Phone:** {{Your Phone Number}} | **Location:** {{Your Location}}  
**LinkedIn:** {{Your LinkedIn URL}}

## Professional Summary

{{CustomSummary}}

## Skills

{{Skill1}}, {{Skill2}}, {{Skill3}}, {{Skill4}}, {{Skill5}}, {{Skill6}}, {{Skill7}}, {{Skill8}}

## Relevant Coursework

{{Coursework1}}, {{Coursework2}}, {{Coursework3}}, {{Coursework4}}, {{Coursework5}}, {{Coursework6}}

## Experience

### {{JobTitle1}} | {{Company1}}
*{{Dates1}}*

- {{BulletPoint1a}}
- {{BulletPoint1b}}
- {{BulletPoint1c}}

### {{JobTitle2}} | {{Company2}}
*{{Dates2}}*

- {{BulletPoint2a}}
- {{BulletPoint2b}}
- {{BulletPoint2c}}

## Education

**{{Degree}} in {{Major}}**  
{{School}} | {{GraduationYear}}

## Volunteer

### {{VolunteerTitle1}} | {{VolunteerOrganization1}}
*{{VolunteerDates1}}*

- {{VolunteerBulletPoint1a}}
- {{VolunteerBulletPoint1b}}
- {{VolunteerBulletPoint1c}}"""

    templates_to_create = {
        "cover_letter_template.md": cover_letter_template,
        "resume_template.md": resume_template,
    }

    for filename, content in templates_to_create.items():
        filepath = Path("templates") / filename
        if not filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 Created template: {filepath}")
        else:
            print(f"📝 Template already exists: {filepath}")

    # Create default config.json if it doesn't exist
    config_path = Path("config.json")
    if not config_path.exists():
        print("📝 Creating default config.json...")
        default_config = {
            "lm_studio": {
                "base_url": "http://localhost:1234/v1",
                "model": "local-model",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "personal_info": {
                "full_name": "Your Full Name",
                "email": "your.email@example.com",
                "phone": "(555) 123-4567",
                "linkedin": "https://linkedin.com/in/yourprofile",
                "location": "City, State",
                "field": "Your Professional Field",
                "degree": "Your Degree",
                "major": "Your Major",
                "school": "Your University",
                "graduation_year": "2023"
            },
            "skills": [
                "Skill 1",
                "Skill 2",
                "Skill 3",
                "Skill 4",
                "Skill 5",
                "Skill 6",
                "Skill 7",
                "Skill 8"
            ],
            "coursework": [
                "Course 1",
                "Course 2", 
                "Course 3",
                "Course 4",
                "Course 5",
                "Course 6"
            ],
            "experience": [
                {
                    "job_title": "Job Title 1",
                    "company": "Company 1",
                    "dates": "Start Date - End Date",
                    "bullet_points": [
                        "Achievement or responsibility 1",
                        "Achievement or responsibility 2",
                        "Achievement or responsibility 3"
                    ]
                },
                {
                    "job_title": "Job Title 2",
                    "company": "Company 2",
                    "dates": "Start Date - End Date",
                    "bullet_points": [
                        "Achievement or responsibility 1",
                        "Achievement or responsibility 2",
                        "Achievement or responsibility 3"
                    ]
                }
            ],
            "volunteer": [
                {
                    "title": "Volunteer Title 1",
                    "organization": "Volunteer Organization 1",
                    "dates": "Start Date - End Date",
                    "bullet_points": [
                        "Volunteer responsibility or achievement 1",
                        "Volunteer responsibility or achievement 2",
                        "Volunteer responsibility or achievement 3"
                    ]
                }
            ]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        print(f"📝 Created config file: {config_path}")
        print("⚠️  Please edit config.json with your actual information before running the application generator!")
    else:
        print("📝 Config file already exists: config.json")

    # Check for Pandoc and LaTeX installations
    print("\n🔍 Checking system dependencies...")
    if shutil.which("pandoc"):
        print("✅ Pandoc found")
        latex_engines = ["xelatex", "pdflatex", "lualatex"]
        found_engines = [engine for engine in latex_engines if shutil.which(engine)]
        
        if found_engines:
            print(f"✅ LaTeX engines found: {', '.join(found_engines)}")
            if "xelatex" in found_engines:
                print("✅ XeLaTeX available - optimal for PDF generation")
        else:
            print("⚠️  No LaTeX engines found - install MiKTeX, TeX Live, or MacTeX for PDF generation")
    else:
        print("⚠️  Pandoc not found - install from https://pandoc.org/installing.html")
        print("   PDF generation requires both Pandoc and a LaTeX distribution")
    
    # Check if LM Studio might be running
    try:
        import requests
        response = requests.get("http://localhost:1234/v1/models", timeout=2)
        if response.status_code == 200:
            print("✅ LM Studio API appears to be running")
        else:
            print("⚠️  LM Studio API not responding - start LM Studio and enable API server")
    except:
        print("⚠️  LM Studio not detected - start LM Studio and load a model")
    
    print("\n🎉 Setup complete! You're ready to generate job applications!")
    print("\nNext steps:")
    print("1. Edit config.json with your personal information")
    print("2. Start LM Studio and load a model")
    print("3. Run the job application generator")
    print("\nTroubleshooting:")
    print("- If you get 'Only user and assistant roles are supported' - this is normal and handled automatically")
    print("- For PDF issues, ensure both Pandoc and LaTeX are installed")
    print("- Make sure to customize config.json with your actual details")


if __name__ == "__main__":
    setup_project()