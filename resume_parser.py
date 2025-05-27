#!/usr/bin/env python3
"""
Resume Parser - Extract structured data from PDF/DOCX resumes
Uses LM Studio to intelligently parse resume content into config format
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional
import requests

# Minimal dependencies for file parsing
try:
    import PyPDF2  # For PDF parsing
except ImportError:
    PyPDF2 = None

try:
    import docx  # python-docx for DOCX parsing
except ImportError:
    docx = None


class ResumeParser:
    def __init__(self, config_file: str = "config.json"):
        """Initialize the resume parser"""
        self.config_file = config_file
        self.config = self._load_base_config()
        
    def _load_base_config(self) -> Dict[str, Any]:
        """Load existing config or create default LM Studio config"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "lm_studio": {
                    "base_url": "http://localhost:1234/v1",
                    "model": "local-model",
                    "temperature": 0.3,  # Lower temperature for more consistent parsing
                    "max_tokens": 2000
                }
            }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
        
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise RuntimeError(f"Error reading PDF: {e}")
        
        return text.strip()
    
    def extract_text_from_docx(self, docx_path: Path) -> str:
        """Extract text from DOCX file"""
        if docx is None:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        try:
            doc = docx.Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Error reading DOCX: {e}")
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from supported file formats"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}. Supported: .pdf, .docx")
    
    def _get_lm_response(self, prompt: str, system_message: str = "") -> str:
        """Get response from LM Studio API"""
        lm_config = self.config.get("lm_studio", {})
        base_url = lm_config.get("base_url", "http://localhost:1234/v1")
        model = lm_config.get("model", "local-model")
        temperature = lm_config.get("temperature", 0.3)
        max_tokens = lm_config.get("max_tokens", 2000)

        if system_message:
            combined_prompt = f"{system_message}\n\n{prompt}"
        else:
            combined_prompt = prompt

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": combined_prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60  # Longer timeout for parsing
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
        except Exception as e:
            raise RuntimeError(f"Error communicating with LM Studio: {e}")
    
    def _determine_degree_status(self, resume_text: str, graduation_year: str) -> str:
        """
        Determine degree status based on resume text and graduation year.
        Returns: 'completed', 'in_progress', or 'expected'
        """
        current_year = 2025  # Update this as needed
        resume_lower = resume_text.lower()
        
        # Check for explicit indicators
        in_progress_indicators = [
            'in progress', 'in-progress', 'current', 'pursuing', 'working toward',
            'candidate for', 'anticipated', 'pursuing degree', 'currently enrolled'
        ]
        
        expected_indicators = [
            'expected', 'anticipated graduation', 'expected graduation',
            'graduating', 'will graduate', 'expected completion'
        ]
        
        # Check for explicit status indicators in resume text
        for indicator in in_progress_indicators:
            if indicator in resume_lower:
                return 'in_progress'
        
        for indicator in expected_indicators:
            if indicator in resume_lower:
                return 'expected'
        
        # If graduation year is available, use it to infer status
        if graduation_year:
            try:
                grad_year = int(graduation_year)
                if grad_year > current_year:
                    return 'expected'
                elif grad_year == current_year:
                    # Could be either expected or completed - check for more context
                    if any(indicator in resume_lower for indicator in expected_indicators + in_progress_indicators):
                        return 'expected'
                    else:
                        return 'completed'
                else:  # grad_year < current_year
                    return 'completed'
            except (ValueError, TypeError):
                pass  # Fall through to default
        
        # Default to completed if we can't determine otherwise
        return 'completed'
    
    def _format_degree_info(self, personal_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Format degree information based on completion status.
        Returns formatted degree text and education line.
        """
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
    
    def _extract_professional_title(self, resume_text: str) -> str:
        """
        Extract professional title/field from resume text using multiple strategies.
        Similar to job title extraction but for professional identity.
        """
        # Strategy 1: Look for common title patterns
        patterns = [
            r'(?:objective|summary|profile).*?(?:seeking|as|for)\s+(?:a|an)?\s*([^\n\r.]+?)(?:\s+position|\s+role|\.|$)',
            r'(?:experienced|skilled|professional)\s+([^\n\r,]+?)(?:\s+with|\s+in|\s*,)',
            r'^([A-Z][^\n\r]+?(?:Engineer|Developer|Manager|Analyst|Specialist|Coordinator|Director|Designer|Consultant)).*$',
            r'(?:title|position|role):\s*([^\n\r]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resume_text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Clean up common suffixes/prefixes
                title = re.sub(r'\s*\([^)]*\)$', '', title)  # Remove parentheses at end
                title = re.sub(r'^(the\s+)?', '', title, flags=re.IGNORECASE)  # Remove "the"
                if len(title) > 5 and len(title) < 100:  # Reasonable length
                    return title
        
        # Strategy 2: Use AI to extract professional title
        return self._ai_extract_professional_title(resume_text)
    
    def _ai_extract_professional_title(self, resume_text: str) -> str:
        """Use AI to extract professional title/field when regex fails"""
        prompt = f"""
        Extract the main professional title or field from this resume. Return only the professional title/field, nothing else.
        
        Resume Text:
        {resume_text[:1500]}  # Limit to avoid token limits
        
        Examples of good responses:
        - Software Engineer
        - Marketing Professional
        - Data Scientist
        - Business Analyst
        - Graphic Designer
        
        Respond with ONLY the professional title/field:
        """
        
        try:
            response = self._get_lm_response(prompt.strip())
            # Clean the response
            title = response.strip().strip('"\'')
            # Remove common AI response patterns
            title = re.sub(r'^(the\s+)?professional title is:?\s*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'^(field|title|profession):\s*', '', title, flags=re.IGNORECASE)
            
            if len(title) > 3 and len(title) < 100:
                return title
        except Exception as e:
            print(f"    Warning: Could not extract professional title with AI: {e}")
        
        return "Professional"  # Fallback
    
    def parse_resume_with_ai(self, resume_text: str) -> Dict[str, Any]:
        """Use LM Studio to parse resume text into structured format"""
        
        system_message = """You are an expert resume parser. Your task is to extract structured information from a resume and return it as valid JSON. 

IMPORTANT: You must return ONLY valid JSON, no additional text or explanations.

The JSON structure should match this exact format:
{
  "personal_info": {
    "full_name": "extracted name",
    "email": "extracted email",
    "phone": "extracted phone",
    "linkedin": "extracted linkedin url or empty string",
    "location": "extracted location",
    "field": "professional field/title",
    "degree": "highest degree",
    "major": "field of study",
    "school": "university/college name",
    "graduation_year": "year of graduation",
    "degree_status": "completed"
  },
  "skills": ["skill1", "skill2", "skill3", "skill4"],
  "coursework": ["course1", "course2", "course3", "course4"],
  "experience": [
    {
      "job_title": "position title",
      "company": "company name",
      "dates": "employment period",
      "bullet_points": [
        "achievement or responsibility 1",
        "achievement or responsibility 2"
      ]
    }
  ],
  "volunteer": [
    {
      "title": "volunteer position title",
      "organization": "organization name",
      "dates": "volunteer period",
      "bullet_points": [
        "volunteer achievement or responsibility 1",
        "volunteer achievement or responsibility 2"
      ]
    }
  ]
}

Rules:
- Extract only factual information present in the resume
- If information is missing, use empty string "" or empty array []
- For degree_status, analyze the education section and determine if it's "completed", "in_progress", or "expected"
  - Use "completed" if degree was earned in past years
  - Use "in_progress" if currently pursuing or mentions "current", "pursuing", etc.
  - Use "expected" if graduation date is in the future or mentions "expected graduation"
- For skills, extract the most relevant technical and professional skills
- For coursework, extract relevant academic courses, classes, or certifications
- For experience, include 2-3 most recent/relevant positions
- For volunteer work, extract volunteer positions and activities if present
- For bullet points, extract 2-3 key achievements per job/volunteer role
- Ensure all JSON is properly formatted and valid"""
        
        prompt = f"""Parse the following resume text and extract structured information:

RESUME TEXT:
{resume_text}

Return the extracted information as valid JSON following the specified format."""
        
        try:
            response = self._get_lm_response(prompt, system_message)
            
            # Try to extract JSON from response (in case LM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            # Parse and validate JSON
            parsed_data = json.loads(json_str)
            
            # Validate structure
            required_keys = ["personal_info", "skills", "experience"]
            optional_keys = ["volunteer", "coursework"]
            
            for key in required_keys:
                if key not in parsed_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Set defaults for optional keys
            for key in optional_keys:
                if key not in parsed_data:
                    parsed_data[key] = []
            
            # Post-process personal_info to enhance extracted data
            personal_info = parsed_data["personal_info"]
            
            # If field is missing or generic, try to extract it
            if not personal_info.get("field") or personal_info.get("field").lower() in ["professional", "employee", "worker"]:
                personal_info["field"] = self._extract_professional_title(resume_text)
            
            # If degree_status is missing, determine it intelligently
            if "degree_status" not in personal_info or not personal_info["degree_status"]:
                personal_info["degree_status"] = self._determine_degree_status(
                    resume_text, 
                    personal_info.get("graduation_year", "")
                )
            
            # Validate degree_status
            valid_statuses = ["completed", "in_progress", "expected"]
            if personal_info.get("degree_status", "").lower() not in valid_statuses:
                personal_info["degree_status"] = "completed"  # Default fallback
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {e}\nResponse: {response}")
        except Exception as e:
            raise RuntimeError(f"Error parsing resume with AI: {e}")
    
    def parse_resume_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse resume file and return structured config data"""
        print(f"📄 Extracting text from {file_path}...")
        resume_text = self.extract_text_from_file(file_path)
        
        if not resume_text.strip():
            raise ValueError("No text could be extracted from the file")
        
        print("🤖 Parsing resume with AI...")
        parsed_data = self.parse_resume_with_ai(resume_text)
        
        # Format degree information to validate it works correctly
        degree_info = self._format_degree_info(parsed_data["personal_info"])
        print(f"📚 Detected education: {degree_info['education_line']}")
        
        # Merge with existing LM Studio config
        full_config = {
            "lm_studio": self.config.get("lm_studio", {
                "base_url": "http://localhost:1234/v1",
                "model": "local-model",
                "temperature": 0.7,
                "max_tokens": 2000
            }),
            **parsed_data
        }
        
        return full_config
    
    def update_config_from_resume(self, resume_file_path: Path, backup_existing: bool = True) -> Path:
        """Parse resume and update config.json"""
        
        # Backup existing config if requested
        if backup_existing and Path(self.config_file).exists():
            backup_path = Path(f"{self.config_file}.backup")
            import shutil
            shutil.copy2(self.config_file, backup_path)
            print(f"📋 Backed up existing config to {backup_path}")
        
        # Parse resume
        new_config = self.parse_resume_file(resume_file_path)
        
        # Save new config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Config updated from resume: {self.config_file}")
        return Path(self.config_file)


def main():
    """Command line interface for resume parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse resume and update config.json")
    parser.add_argument("resume_file", help="Path to resume file (.pdf or .docx)")
    parser.add_argument("--config", default="config.json", help="Config file to update")
    parser.add_argument("--no-backup", action="store_true", help="Don't backup existing config")
    
    args = parser.parse_args()
    
    try:
        resume_parser = ResumeParser(args.config)
        resume_parser.update_config_from_resume(
            Path(args.resume_file), 
            backup_existing=not args.no_backup
        )
        
        print("\n🎉 Resume parsing complete!")
        print("You can now use the Job Application Generator with your extracted information.")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nTo install required dependencies:")
        print("pip install PyPDF2 python-docx")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())