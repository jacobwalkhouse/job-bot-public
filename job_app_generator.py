#!/usr/bin/env python3
"""
Job Application Workflow
Automates resume and cover letter generation using LM Studio API
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse
import shutil 
import re


class JobApplicationGenerator:
    def __init__(self, config_file: str = "config.json"):
        """Initialize the job application generator"""
        self.config = self.load_config(config_file)
        self.templates_dir = Path("templates")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found. Creating default config...")
            default_config = self.create_default_config()
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Please edit {config_file} with your information and try again.")
            exit(1)
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration template"""
        return {
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
                "graduation_year": "2023",
                "degree_status": "completed"  # NEW: "completed", "in_progress", or "expected"
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

    def _extract_job_title(self, job_listing: str) -> str:
        """Extract job title from job listing using multiple strategies"""
        # Strategy 1: Look for common job title patterns
        patterns = [
            r'(?:position|role|job|title):\s*([^\n\r]+)',
            r'(?:hiring|seeking|looking for)\s+(?:a|an)?\s*([^\n\r,]+?)(?:\s+at|\s+for|\s*$)',
            r'^([A-Z][^\n\r]+?)(?:\s+at|\s+for|\s*-)',  # Title at beginning of line
            r'Job Title:\s*([^\n\r]+)',
            r'Position:\s*([^\n\r]+)',
            r'We are hiring\s+(?:a|an)?\s*([^\n\r,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_listing, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Clean up common suffixes/prefixes
                title = re.sub(r'\s*\([^)]*\)$', '', title)  # Remove parentheses at end
                title = re.sub(r'^(the\s+)?', '', title, flags=re.IGNORECASE)  # Remove "the"
                if len(title) > 5 and len(title) < 100:  # Reasonable length
                    return title
        
        # Strategy 2: Use AI to extract job title
        return self._ai_extract_job_title(job_listing)
    
    def _ai_extract_job_title(self, job_listing: str) -> str:
        """Use AI to extract job title when regex fails"""
        prompt = f"""
        Extract ONLY the job title from this job listing. Return only the job title, nothing else.
        
        Job Listing:
        {job_listing[:1000]}  # Limit to first 1000 chars to avoid token limits
        
        Examples of good responses:
        - Software Engineer
        - Marketing Manager
        - Data Scientist
        - Senior Frontend Developer
        
        Respond with ONLY the job title:
        """
        
        try:
            response = self._get_lm_response(prompt.strip())
            # Clean the response
            title = response.strip().strip('"\'')
            # Remove common AI response patterns
            title = re.sub(r'^(the\s+)?job title is:?\s*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'^(position|role|title):\s*', '', title, flags=re.IGNORECASE)
            
            if len(title) > 5 and len(title) < 100:
                return title
        except Exception as e:
            print(f"    Warning: Could not extract job title with AI: {e}")
        
        return "Desired Position"  # Fallback
    
    def _format_degree_info(self, personal_info: Dict[str, Any]) -> Dict[str, str]:
        """Format degree information based on completion status"""
        degree = personal_info.get("degree", "")
        major = personal_info.get("major", "")
        school = personal_info.get("school", "")
        graduation_year = personal_info.get("graduation_year", "")
        degree_status = personal_info.get("degree_status", "completed").lower()
        
        if degree_status == "in_progress":
            degree_text = f"{degree} in {major} (In Progress)" if major else f"{degree} (In Progress)"
            education_line = f"{degree_text}, {school}, Expected {graduation_year}"
        elif degree_status == "expected":
            degree_text = f"{degree} in {major}" if major else degree
            education_line = f"{degree_text}, {school}, Expected {graduation_year}"
        else:  # completed
            degree_text = f"{degree} in {major}" if major else degree
            education_line = f"{degree_text}, {school}, {graduation_year}"
        
        return {
            "degree_text": degree_text,
            "education_line": education_line
        }

    def _get_lm_response(self, prompt: str, system_message: str = "") -> str:
        """Get response from LM Studio API using direct HTTP requests"""
        lm_config = self.config.get("lm_studio", {})
        base_url = lm_config.get("base_url", "http://localhost:1234/v1")
        model = lm_config.get("model", "local-model")
        temperature = lm_config.get("temperature", 0.7)
        max_tokens = lm_config.get("max_tokens", 1000)

        # Modify to combine system message with user prompt directly
        # as some models only support user/assistant roles
        combined_prompt_content = f"{system_message}\n\n{prompt}" if system_message else prompt

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    # Send only a user message with combined content
                    "messages": [{"role": "user", "content": combined_prompt_content}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"LM Studio API error: {response.status_code} - {response.text}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to LM Studio at {base_url}. "
                "Please ensure LM Studio is running and the API server is enabled."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Request to LM Studio timed out")
        except Exception as e:
            raise RuntimeError(f"Error communicating with LM Studio: {e}")

    def _clean_ai_response(self, response: str, section_type: str) -> str:
        """Clean AI response to remove unwanted introductions, closings, and formatting"""
        cleaned = response.strip()
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            r"^Here's?\s+(?:a|the|your)\s+",
            r"^Based on.*?(?:here's|here is)\s+",
            r"^I'll create\s+",
            r"^Let me create\s+",
            r"^This is\s+",
            r"^Below is\s+",
            r"^The following is\s+",
        ]
        
        for prefix in prefixes_to_remove:
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        if section_type == "custom paragraph for cover letter":
            # Remove cover letter specific elements
            cover_letter_patterns = [
                r"^Dear.*?,?\s*\n?",  # Remove "Dear..." lines
                r"^To whom it may concern,?\s*\n?",
                r"^I am writing to.*?position\.?\s*\n?",  # Remove generic opening
                r"Sincerely,?\s*\n?.*$",  # Remove closing
                r"Best regards,?\s*\n?.*$",
                r"Thank you.*?consideration\.?\s*\n?.*$",
                r"I look forward.*?$",
                r"^\[Your Name\].*$",
                r"^.*Yours truly.*$",
            ]
            
            for pattern in cover_letter_patterns:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        # Clean up extra whitespace and empty lines
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Multiple newlines to double newline
        cleaned = re.sub(r'^\s+|\s+$', '', cleaned)    # Trim whitespace
        
        # If multiple paragraphs, take only the first substantial one for cover letter
        if section_type == "custom paragraph for cover letter":
            paragraphs = [p.strip() for p in cleaned.split('\n\n') if p.strip()]
            if paragraphs:
                # Find the first paragraph that's substantial (more than just a greeting)
                for paragraph in paragraphs:
                    if len(paragraph) > 50 and not paragraph.lower().startswith(('dear', 'to whom', 'hello')):
                        cleaned = paragraph
                        break
                else:
                    cleaned = paragraphs[0] if paragraphs else cleaned
        
        return cleaned.strip()

    def _generate_section(self, section_name: str, job_listing: str, personal_info: Dict[str, Any], 
                         company_name: str, example_content: str, job_title: str = "") -> str:
        """Generate a specific section of the application (e.g., summary, custom paragraph)"""
        
        # Format degree information properly
        degree_info = self._format_degree_info(personal_info)
        
        specific_instructions = ""
        if section_name == "summary":
            specific_instructions = (
                "The summary should be a concise paragraph (2-4 sentences) for a resume. "
                "Focus on your key skills, experiences, and career goals relevant to the job. "
                "DO NOT include salutations, closings, or any conversational filler. "
                "It should directly start with your qualifications. "
                "DO NOT mention any company names in the summary - this is for a resume. "
                "Provide ONLY the summary content, nothing else."
            )
        elif section_name == "custom paragraph for cover letter":
            specific_instructions = (
                "Write ONLY a single middle paragraph for a cover letter (not the opening or closing). "
                "This paragraph should connect your experience and skills directly to the job requirements. "
                "You MAY mention the company name when relevant to show specific interest. "
                "DO NOT include:\n"
                "- Opening greetings (Dear..., Hello..., etc.)\n"
                "- Closing statements (Sincerely, Best regards, Thank you, etc.)\n"
                "- Generic openings like 'I am writing to express interest...'\n"
                "- Any signature lines or contact information\n"
                "Focus ONLY on highlighting your relevant qualifications and what you can contribute. "
                "Start directly with your qualifications or experience."
            )

        prompt = f"""
        Based on the following job listing and my personal information, write a concise and professional {section_name}.
        
        ---
        JOB LISTING:
        {job_listing}
        ---
        
        JOB TITLE: {job_title}
        ---
        
        PERSONAL INFORMATION (ONLY use this information for facts about my background):
        {json.dumps(personal_info, indent=2)}
        ---

        TARGET COMPANY NAME:
        {company_name}
        ---
        
        EDUCATION STATUS: {degree_info['education_line']}
        ---
        
        EXAMPLE {section_name.upper()} CONTENT:
        {example_content}
        ---
        
        {specific_instructions}
        
        CRITICAL REQUIREMENTS:
        - When referring to the company, ALWAYS use the 'TARGET COMPANY NAME' provided: {company_name}
        - When mentioning education, use the exact phrasing from 'EDUCATION STATUS' above
        - DO NOT invent or fabricate any information, including skills, experiences, degrees, or certifications that are not explicitly present in the 'PERSONAL INFORMATION' section
        - Tailor the content by emphasizing and rephrasing EXISTING information from 'PERSONAL INFORMATION' to align with the 'JOB LISTING'
        - Do not add new, false facts
        - Focus on highlighting transferable skills and relevant experiences from your background
        - Provide ONLY the {section_name} content, without any conversational filler, explanations, or extra remarks
        - Do not start with phrases like "Here's the..." or "Based on..."
        """
        
        response = self._get_lm_response(prompt.strip())
        return self._clean_ai_response(response, section_name)

    def _fill_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """
        Fills placeholders in a template string with provided variables.
        Also removes lines that would result in empty bullet points.
        """
        filled_template = template_content
        for key, value in variables.items():
            filled_template = filled_template.replace(f"{{{{{key}}}}}", str(value))
        
        # Post-process to remove lines with empty bullet points
        lines = filled_template.splitlines()
        cleaned_lines = []
        for line in lines:
            # Check if the line starts with a bullet point and is effectively empty after replacement
            # This covers both '- ' and '* ' used as bullet points
            if line.strip().startswith(('-', '*')) and len(line.strip()) <= 2:
                # If it's just a bullet point with nothing else, skip it
                continue
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    def generate_application(self, job_listing: str, company_override: Optional[str] = None) -> Dict[str, Path]:
        """Generate resume and cover letter based on job listing and personal info"""
        print("\n⚙️ Analyzing job listing and generating content...")

        personal_info = self.config["personal_info"]
        skills = self.config["skills"]
        coursework = self.config.get("coursework", [])
        experience = self.config["experience"]
        volunteer_activities = self.config.get("volunteer", [])

        # Extract job title from job listing
        print("    Extracting job title...")
        job_title = self._extract_job_title(job_listing)
        print(f"    Detected job title: {job_title}")

        # Determine company name (prioritize override, then try to extract from job listing)
        company_name = company_override
        if not company_name or company_name.strip() == "": # Explicitly check for empty string after strip
            # Simple regex to extract company name - could be improved
            match = re.search(r'(at|for)\s+([A-Z][a-zA-Z0-9\s,&.-]+(?:Co|Inc|Ltd|LLC|Corp|Group|Solutions|Technologies|Systems|Labs|Pte Ltd|GmbH|B.V.)?)', job_listing, re.IGNORECASE)
            if match:
                company_name = match.group(2).strip()
            else:
                company_name = "Target Company" # Default if not found

        # Format degree information
        degree_info = self._format_degree_info(personal_info)

        # 1. Generate Custom Summary for Resume (AI-generated part)
        print("    Generating custom summary...")
        custom_summary_example = f"Highly motivated and results-oriented professional with X years of experience in [YourField], skilled in [Skill1] and [Skill2]. Seeking to leverage expertise in [Area] to contribute as a {job_title}."
        custom_summary = self._generate_section("summary", job_listing, personal_info, company_name, custom_summary_example, job_title)

        # 2. Generate Custom Paragraph for Cover Letter (AI-generated part)
        print("    Generating custom cover letter paragraph...")
        custom_paragraph_example = f"My experience in [relevant experience] aligns perfectly with the requirements for the {job_title} position, particularly my proficiency in [specific skill] and my track record in [achievement]. I am confident that my background in [area] and proven ability to [accomplishment] would enable me to make meaningful contributions to your team."
        custom_paragraph = self._generate_section("custom paragraph for cover letter", job_listing, personal_info, company_name, custom_paragraph_example, job_title)

        # Prepare variables for templates
        template_vars = {
            "JobTitle": job_title,  # NOW FILLED WITH ACTUAL JOB TITLE
            "Company": company_name,
            "HiringManagerName": "Hiring Manager", # Placeholder - AI usually doesn't know this
            "Your Full Name": personal_info["full_name"],
            "Your Email": personal_info["email"],
            "Your Phone Number": personal_info["phone"],
            "Your LinkedIn URL": personal_info["linkedin"],
            "Your Location": personal_info["location"],
            "YourField": personal_info["field"],
            "Degree": degree_info["degree_text"],  # PROPERLY FORMATTED DEGREE
            "Major": personal_info["major"],
            "School": personal_info["school"],
            "GraduationYear": personal_info["graduation_year"],
            "EducationLine": degree_info["education_line"],  # COMPLETE EDUCATION LINE
            "CustomSummary": custom_summary, # AI-generated
            "CustomParagraphFromAI": custom_paragraph, # AI-generated
        }

        # Add skills dynamically (up to 8 skills as per template)
        for i, skill in enumerate(skills):
            template_vars[f"Skill{i+1}"] = skill
        # Fill empty skill slots
        for i in range(len(skills), 8): 
            template_vars[f"Skill{i+1}"] = ""
        
        # Add coursework dynamically (up to 6 courses as per template)
        for i, course in enumerate(coursework):
            template_vars[f"Coursework{i+1}"] = course
        # Fill empty coursework slots
        for i in range(len(coursework), 6):
            template_vars[f"Coursework{i+1}"] = ""
        
        # Add experience dynamically (up to 2 jobs as per template)
        for i, exp in enumerate(experience):
            template_vars[f"JobTitle{i+1}"] = exp["job_title"]
            template_vars[f"Company{i+1}"] = exp["company"]
            template_vars[f"Dates{i+1}"] = exp["dates"]
            for j, bp in enumerate(exp["bullet_points"]):
                template_vars[f"BulletPoint{i+1}{chr(97+j)}"] = bp
            # Fill empty bullet points if needed (assuming max 3 bullet points per job)
            for j in range(len(exp["bullet_points"]), 3):
                template_vars[f"BulletPoint{i+1}{chr(97+j)}"] = ""
        
        # Fill empty experience slots if less than 2 jobs in config
        for i in range(len(experience), 2):
            template_vars[f"JobTitle{i+1}"] = ""
            template_vars[f"Company{i+1}"] = ""
            template_vars[f"Dates{i+1}"] = ""
            for j in range(3):
                template_vars[f"BulletPoint{i+1}{chr(97+j)}"] = ""

        # Add volunteer activities dynamically (up to 1 volunteer position as per template)
        for i, vol in enumerate(volunteer_activities):
            template_vars[f"VolunteerTitle{i+1}"] = vol.get("title", "")
            template_vars[f"VolunteerOrganization{i+1}"] = vol.get("organization", "")
            template_vars[f"VolunteerDates{i+1}"] = vol.get("dates", "")
            
            # Handle bullet points safely
            bullet_points = vol.get("bullet_points", [])
            for j, bp in enumerate(bullet_points):
                template_vars[f"VolunteerBulletPoint{i+1}{chr(97+j)}"] = bp
            # Fill empty volunteer bullet points
            for j in range(len(bullet_points), 3):
                template_vars[f"VolunteerBulletPoint{i+1}{chr(97+j)}"] = ""

        # Fill empty volunteer slots if less than 1
        for i in range(len(volunteer_activities), 1):
            template_vars[f"VolunteerTitle{i+1}"] = ""
            template_vars[f"VolunteerOrganization{i+1}"] = ""
            template_vars[f"VolunteerDates{i+1}"] = ""
            for j in range(3):
                template_vars[f"VolunteerBulletPoint{i+1}{chr(97+j)}"] = ""

        # Read template contents directly
        cover_letter_template_path = self.templates_dir / "cover_letter_template.md"
        resume_template_path = self.templates_dir / "resume_template.md"
        
        with open(cover_letter_template_path, 'r', encoding='utf-8') as f:
            raw_cover_letter_template = f.read()
        with open(resume_template_path, 'r', encoding='utf-8') as f:
            raw_resume_template = f.read()

        # Fill templates using the new _fill_template method
        print("    Filling cover letter template...")
        cover_letter_content = self._fill_template(raw_cover_letter_template, template_vars)

        print("    Filling resume template...")
        resume_content = self._fill_template(raw_resume_template, template_vars)
        
        # Save generated markdown files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Truncate company_name for filename to ensure it's not too long
        truncated_company_name = company_name.replace(' ', '_')[:75] 

        cl_md_path = self.output_dir / f"cover_letter_{truncated_company_name}_{timestamp}.md"
        res_md_path = self.output_dir / f"resume_{truncated_company_name}_{timestamp}.md" # Corrected line
        
        with open(cl_md_path, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
        with open(res_md_path, 'w', encoding='utf-8') as f:
            f.write(resume_content)
            
        print("    Markdown files saved.")

        generated_files = {
            "cover_letter_md": cl_md_path,
            "resume_md": res_md_path
        }
        
        # Convert to PDF if Pandoc is available
        if shutil.which("pandoc"):
            print("    Converting to PDF (requires Pandoc)...")
            cl_pdf_path = self.output_dir / f"cover_letter_{truncated_company_name}_{timestamp}.pdf"
            res_pdf_path = self.output_dir / f"resume_{truncated_company_name}_{timestamp}.pdf"

            # Arguments to reduce margins in PDF
            pandoc_margin_args = ["--variable", "geometry=margin=0.75in"]

            try:
                subprocess.run(
                    ["pandoc", cl_md_path, "-o", cl_pdf_path, "--pdf-engine=xelatex"] + pandoc_margin_args,
                    check=True,
                    capture_output=True
                )
                generated_files["cover_letter_pdf"] = cl_pdf_path
            except subprocess.CalledProcessError as e:
                print(f"    ⚠️ Warning: Could not convert cover letter to PDF. Error: {e.stderr.decode()}")
                print("    Troubleshooting: Ensure LaTeX distribution (like TeX Live) is installed for Pandoc's PDF engine.")

            try:
                subprocess.run(
                    ["pandoc", res_md_path, "-o", res_pdf_path, "--pdf-engine=xelatex"] + pandoc_margin_args,
                    check=True,
                    capture_output=True
                )
                generated_files["resume_pdf"] = res_pdf_path
            except subprocess.CalledProcessError as e:
                print(f"    ⚠️ Warning: Could not convert resume to PDF. Error: {e.stderr.decode()}")
                print("    Troubleshooting: Ensure LaTeX distribution (like TeX Live) is installed for Pandoc's PDF engine.")
            print("    PDF conversion complete (if Pandoc/LaTeX successful).")
        else:
            print("    Pandoc not found. Skipping PDF generation.")

        return generated_files

if __name__ == "__main__":
    # This block is for direct CLI usage of job_app_generator.py (e.g., from job_app_main.py)
    # It parses arguments to allow standalone generation
    parser = argparse.ArgumentParser(description="Generate job application materials")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--company", help="Override company name")
    args = parser.parse_args()
    
    # Create templates directory and copy templates if they don't exist
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    generator = JobApplicationGenerator(args.config)
    
    print("🚀 Job Application Generator")
    print("=" * 50)
    print("Paste your job listing below (press Ctrl+D when finished on Unix/Mac, Ctrl+Z on Windows):")
    print()
    
    # Read job listing from stdin
    job_listing_lines = []
    try:
        while True:
            line = input()
            job_listing_lines.append(line)
    except EOFError:
        pass
    
    job_listing = '\n'.join(job_listing_lines).strip()
    
    if not job_listing:
        print("❌ No job listing provided!")
        exit(1) # Use exit(1) for error, not return in main execution block
    
    try:
        generated_files = generator.generate_application(job_listing, args.company)
        
        print("\n✅ Application generated successfully!")
        print("📁 Generated files:")
        for file_type, file_path in generated_files.items():
            print(f"    {file_type}: {file_path}")
        
    except KeyboardInterrupt:
        print("\n❌ Generation cancelled by user")
        exit(1) # Use exit(1) for error
    except Exception as e:
        print(f"❌ Error generating application: {e}")
        print("\nTroubleshooting tips:")
        print("- Ensure LM Studio is running with a model loaded")
        print("- Check your internet connection")
        print("- Verify config.json has correct LM Studio URL")
        exit(1) # Use exit(1) for error