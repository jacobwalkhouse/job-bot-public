#!/usr/bin/env python3
"""
Job Application Generator - GUI Frontend
Built with Dear PyGui for a modern, user-friendly interface
"""

import dearpygui.dearpygui as dpg
import threading
import json
import os
from pathlib import Path
from job_app_generator import JobApplicationGenerator
from resume_parser import ResumeParser  # Import ResumeParser
import webbrowser
import subprocess
import sys
import requests 
import lmstudio as lms 
import urllib.parse 

class JobApplicationGUI:
    def __init__(self):
        self.generator = None
        self.resume_parser = None  # Initialize resume parser
        self.config_file = "config.json"
        self.job_listing_text = ""
        self.company_override = ""
        self.generated_files = {}
        self.is_generating = False
        self.is_parsing = False # New flag for parsing status
        self.available_models = []
        self.selected_model = "" 

        dpg.create_context()
        self.setup_theme()
        self.create_gui() 

        self.config = self._load_config()
        self.lm_studio_base_url = self.config["lm_studio"]["base_url"]
        self.selected_model = self.config["lm_studio"]["model"]

        if dpg.does_item_exist("lm_studio_url_input"):
            dpg.set_value("lm_studio_url_input", self.lm_studio_base_url)

        self.fetch_available_models()


    def _load_config(self) -> dict:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Creating default config...")
            default_config = {
                "lm_studio": {"base_url": "http://localhost:1234/v1", "model": "local-model", "temperature": 0.7, "max_tokens": 1000},
                "personal_info": { 
                    "full_name": "Your Full Name", "email": "your.email@example.com",
                    "phone": "(123) 456-7890", "linkedin": "", "location": "",
                    "field": "", "degree": "", "major": "", "school": "",
                    "graduation_year": ""
                },
                "skills": [], "experience": []
            }
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2)
            except Exception as e:
                pass 
            return default_config
        except json.JSONDecodeError:
            dpg.set_value("status_text", "Error: config.json is invalid JSON. Please fix it.")
            return { 
                "lm_studio": {"base_url": "http://localhost:1234/v1", "model": "local-model", "temperature": 0.7, "max_tokens": 1000},
                "personal_info": {}, "skills": [], "experience": []
            }


    def _save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            dpg.set_value("status_text", f"Error saving config: {e}")

    def fetch_available_models(self):
        dpg.set_value("status_text", "Fetching available models from LM Studio...")
        self.available_models = []
        try:
            parsed_url = urllib.parse.urlparse(self.lm_studio_base_url)
            host_port = parsed_url.netloc 
            if not host_port: 
                # If netloc is empty, try to get host:port from path if it's like 'localhost:1234/v1'
                host_port = parsed_url.path.split('/')[0] if parsed_url.path else "localhost:1234" 
            
            lms.configure_default_client(host_port)
            
            llm_models = lms.list_downloaded_models("llm") 
            
            # Use a dictionary to store unique models, preferring simplified names
            model_name_map = {} # key: simplified_name, value: preferred_full_name
            
            for model in llm_models:
                # Prioritize display_name, fall back to model_key
                current_full_name = getattr(model, 'display_name', None)
                if current_full_name is None:
                    current_full_name = model.model_key

                simplified_name = current_full_name
                # If it's a HuggingFace-style name (e.g., 'org/model'), simplify it
                if '/' in current_full_name:
                    parts = current_full_name.split('/')
                    simplified_name = parts[-1]

                if simplified_name not in model_name_map:
                    # If this simplified name is new, add the current full name as preferred
                    model_name_map[simplified_name] = current_full_name
                else:
                    # If simplified name already exists, compare lengths and keep the shorter/simpler one
                    existing_preferred_name = model_name_map[simplified_name]
                    if len(current_full_name) < len(existing_preferred_name):
                        model_name_map[simplified_name] = current_full_name # Current name is shorter/preferred

            # Extract the preferred names and sort them
            self.available_models = sorted(list(model_name_map.values()))
            
            if not self.available_models:
                dpg.set_value("status_text", "No LLM models found in LM Studio. Please load one.")
                self.available_models = [self.selected_model] if self.selected_model else ["No models found"]
            else:
                dpg.set_value("status_text", f"Found {len(self.available_models)} LLM models.")
                
                # Adjust selected model if it's no longer in the list or is 'local-model'
                if self.selected_model not in self.available_models or \
                   (self.selected_model == "local-model" and len(self.available_models) > 0 and self.available_models[0] != "local-model"):
                    if self.available_models:
                        self.selected_model = self.available_models[0] 
                        self.config["lm_studio"]["model"] = self.selected_model
                        self._save_config()
                    else:
                        self.selected_model = "No models found" 
                        self.config["lm_studio"]["model"] = self.selected_model
                        self._save_config()
        
        except requests.exceptions.ConnectionError:
            dpg.set_value("status_text", f"Error: Could not connect to LM Studio at {self.lm_studio_base_url}. Is it running and API enabled?")
            self.available_models = [self.selected_model] if self.selected_model else ["LM Studio not connected"] 
        except Exception as e:
            dpg.set_value("status_text", f"Error fetching models: {e}")
            self.available_models = [self.selected_model] if self.selected_model else ["Error fetching models"] 

        if dpg.does_item_exist("model_selector_combo"):
            dpg.configure_item("model_selector_combo", items=self.available_models)
            dpg.set_value("model_selector_combo", self.selected_model)


    def update_model_selection(self, sender, app_data):
        self.selected_model = app_data
        self.config["lm_studio"]["model"] = self.selected_model
        self._save_config() 
        dpg.set_value("status_text", f"Model set to: {self.selected_model}")

    def update_lm_studio_url(self, sender, app_data):
        self.lm_studio_base_url = app_data
        self.config["lm_studio"]["base_url"] = self.lm_studio_base_url
        self._save_config()
        dpg.set_value("status_text", f"LM Studio URL set to: {self.lm_studio_base_url}. Refreshing models...")
        self.fetch_available_models() 

    def open_generated_file(self, file_path):
        """Open a generated file using the default system viewer."""
        try:
            if sys.platform == "win32":
                os.startfile(str(file_path))
            else:
                webbrowser.open_new_tab(f"file:///{file_path.absolute()}")
            dpg.set_value("status_text", f"Opened: {file_path.name}")
        except Exception as e:
            dpg.set_value("status_text", f"Error opening file: {e}")

    def setup_theme(self):
        """Setup custom theme for better visual appeal"""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 15, 15, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 25, 25, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 130, 180, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 150, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (200, 200, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 40, 40, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (60, 60, 60, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (50, 100, 150, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (30, 30, 30, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (70, 130, 180, 255)) 
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (90, 150, 200, 255))
            dpg.bind_theme(global_theme)
        
    def create_gui(self):
        with dpg.window(tag="main_window", label="Job Application Generator"):
            dpg.add_text("Job Application Generator", tag="title_text")
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_button(label="Generate Application", callback=self.start_generation_thread)
                dpg.add_button(label="Parse Resume (PDF/DOCX)", callback=self.parse_resume_file_dialog) # New button for resume parsing
                dpg.add_button(label="Open Output Folder", callback=lambda: webbrowser.open(os.path.abspath("output")))
                dpg.add_button(label="Refresh Models", callback=self.fetch_available_models)
                dpg.add_button(label="About", callback=lambda: dpg.show_item("about_window"))
                dpg.add_text("", tag="status_text", color=(255, 255, 0)) 

            dpg.add_separator()

            dpg.add_text("LM Studio Settings:")
            with dpg.group(horizontal=True):
                dpg.add_text("LM Studio API Base URL:")
                dpg.add_input_text(
                    tag="lm_studio_url_input",
                    default_value="http://localhost:1234/v1", 
                    callback=self.update_lm_studio_url,
                    on_enter=True,
                    width=300
                )
            with dpg.group(horizontal=True):
                dpg.add_text("Select Model:")
                dpg.add_combo(
                    items=["Loading models..."], 
                    default_value="Loading models...", 
                    tag="model_selector_combo",
                    callback=self.update_model_selection,
                    width=300
                )
            dpg.add_separator()

            dpg.add_text("Job Listing:")
            dpg.add_input_text(
                multiline=True,
                height=200,
                width=-1, 
                tag="job_listing_input",
                hint="Paste the job listing here..."
            )

            dpg.add_text("Optional Company Override:")
            dpg.add_input_text(
                tag="company_override_input",
                hint="e.g., 'Google' if not clear from listing",
                width=-1
            )

            dpg.add_text("Output:")
            # The child_window provides the scrollability and boundary for the text
            # --- MODIFICATION START ---
            # Changed autosize_x=True to width=-1 for the child_window
            # This makes the child_window itself fill its parent's width,
            # which then constrains the input_text within it, forcing wrapping.
            with dpg.child_window(tag="output_log", width=-1, height=-1, border=True):
                # --- MODIFICATION END ---
                dpg.add_input_text(
                    default_value="Generated files and process log will appear here.", 
                    multiline=True, 
                    readonly=True, 
                    width=-1, 
                    height=-1, # Ensure it takes up vertical space within the child window
                    tag="output_text"
                ) 
    
    def parse_resume_file_dialog(self, sender, app_data):
        """Opens a file dialog to select the resume file."""
        if self.is_parsing:
            dpg.set_value("status_text", "Resume parsing already in progress...")
            return

        with dpg.file_dialog(
            directory_selector=False, 
            show=True, 
            modal=True, 
            callback=self.start_parsing_thread, 
            id="file_dialog_id",
            width=700,
            height=400
        ):
            dpg.add_file_extension(".pdf", color=(255, 0, 255, 255))
            dpg.add_file_extension(".docx", color=(255, 0, 255, 255))
            dpg.add_file_extension(".*") # Allow all files just in case, but prefer pdf/docx

    def start_parsing_thread(self, sender, app_data):
        """Starts the resume parsing process in a separate thread."""
        if self.is_parsing:
            dpg.set_value("status_text", "Resume parsing already in progress...")
            return

        # app_data from file_dialog is a dict with 'selections'
        selected_files = app_data['selections']
        if not selected_files:
            with dpg.mutex():
                dpg.set_value("status_text", "No resume file selected.")
            return

        resume_file_path = list(selected_files.values())[0] # Get the first selected file

        with dpg.mutex():
            dpg.set_value("status_text", f"Starting resume parsing for: {Path(resume_file_path).name}...")
            dpg.set_value("output_text", "") # Clear previous output
            self.update_output_log(f"Attempting to parse resume: {Path(resume_file_path).name}")
        
        self.is_parsing = True
        threading.Thread(target=self.parse_resume_thread, args=(resume_file_path,), daemon=True).start()

    def parse_resume_thread(self, resume_file_path: str):
        """Handles the actual resume parsing in a separate thread."""
        try:
            self.resume_parser = ResumeParser(self.config_file)
            
            with dpg.mutex():
                self.update_output_log("Extracting text and sending to LM Studio for parsing...")
            
            parsed_config_path = self.resume_parser.update_config_from_resume(Path(resume_file_path))
            
            # Reload config to reflect changes
            self.config = self._load_config()

            with dpg.mutex():
                self.update_output_log(f"✅ Resume parsed successfully! Config updated at: {parsed_config_path.name}")
                self.update_output_log("Your personal information, skills, and experience in config.json have been updated.")
                dpg.set_value("status_text", "Resume parsing complete.")

        except requests.exceptions.ConnectionError:
            with dpg.mutex():
                self.update_output_log(f"❌ Error: Could not connect to LM Studio at {self.lm_studio_base_url}. Is it running and API enabled?")
        except ImportError as e:
            with dpg.mutex():
                self.update_output_log(f"❌ Missing dependency for resume parsing: {e}")
                self.update_output_log("\nTroubleshooting tips:")
                self.update_output_log("- Ensure PyPDF2 and python-docx are installed: `pip install PyPDF2 python-docx`")
        except Exception as e:
            with dpg.mutex():
                self.update_output_log(f"❌ Error parsing resume: {e}")
                self.update_output_log("\nTroubleshooting tips:")
                self.update_output_log("- Ensure LM Studio is running with a model loaded and API enabled.")
                self.update_output_log("- Check your internet connection (if using remote API).")
                self.update_output_log("- Verify the resume file is a valid PDF or DOCX.")
        finally:
            self.is_parsing = False

    def start_generation_thread(self, sender, app_data):
        """Starts the generation process in a separate thread."""
        if self.is_generating:
            dpg.set_value("status_text", "Generation already in progress...")
            return

        self.job_listing_text = dpg.get_value("job_listing_input")
        self.company_override = dpg.get_value("company_override_input")

        if not self.job_listing_text:
            # GUI updates MUST be wrapped in dpg.mutex() when called from another thread
            with dpg.mutex():
                dpg.set_value("status_text", "Please paste a job listing first!")
            return
        
        if not self.selected_model or self.selected_model in ["No models found", "LM Studio not connected", "Error fetching models", "Loading models..."]:
            # GUI updates MUST be wrapped in dpg.mutex() when called from another thread
            with dpg.mutex():
                dpg.set_value("status_text", "Please select a valid LM Studio model before generating!")
            return

        with dpg.mutex(): # Initial status update
            dpg.set_value("status_text", "Starting generation... Please wait.")
            dpg.set_value("output_text", "") # Clear previous output
        
        self.is_generating = True
        threading.Thread(target=self.generate_application_thread, daemon=True).start()

    def generate_application_thread(self):
        """Handles the actual application generation in a separate thread."""
        try:
            self.generator = JobApplicationGenerator(self.config_file)
            self.generator.config = self.config

            # GUI updates MUST be wrapped in dpg.mutex()
            with dpg.mutex():
                self.update_output_log("Generating tailored content...")
            
            generated_files = self.generator.generate_application(self.job_listing_text, self.company_override)
            self.generated_files = generated_files

            # GUI updates MUST be wrapped in dpg.mutex()
            with dpg.mutex():
                self.update_output_log("✅ Application generated successfully!")
                
                output_message = "\n📁 Generated files:\n"
                for file_type, file_path in self.generated_files.items(): 
                    file_size = file_path.stat().st_size if file_path.exists() else 0
                    output_message += f"    📄 {file_type.replace('_', ' ').title()}: {file_path.name} ({file_size} bytes)\n"
                    # Removed dpg.add_button here as it doesn't make sense inside an input_text widget
                self.update_output_log(output_message)
                self.update_output_log(f"\n📂 All files saved to: {Path('output').absolute()}")


        except requests.exceptions.ConnectionError:
            with dpg.mutex():
                self.update_output_log(f"❌ Error: Could not connect to LM Studio at {self.lm_studio_base_url}. Is it running and API enabled?")
        except Exception as e:
            with dpg.mutex():
                self.update_output_log(f"❌ Error generating application: {e}")
                self.update_output_log("\nTroubleshooting tips:")
                self.update_output_log("- Ensure LM Studio is running with a model loaded and API enabled.")
                self.update_output_log("- Check your internet connection (if using remote API).")
                self.update_output_log("- Verify config.json has the correct LM Studio URL.")
                self.update_output_log("- Ensure Pandoc is installed for PDF generation.")
        finally:
            self.is_generating = False
            with dpg.mutex(): # Final status update
                dpg.set_value("status_text", "Generation complete or failed.")

    def update_output_log(self, message):
        """Appends a message to the output log text widget."""
        # This function is called from within a dpg.mutex() block in generate_application_thread
        current_text = dpg.get_value("output_text")
        dpg.set_value("output_text", current_text + "\n" + message)
        dpg.set_y_scroll("output_log", dpg.get_y_scroll_max("output_log"))

    def show_about_window(self, sender, app_data):
        """Displays an 'About' popup window."""
        with dpg.window(label="About Job Application Generator", modal=True, no_resize=True, no_close=False, autosize=True, tag="about_window"):
            dpg.add_text("Job Application Generator", color=(70, 130, 180, 255))
            dpg.add_text("Version: 1.0.0")
            dpg.add_text("Developed by AI Assistant")
            dpg.add_separator()
            dpg.add_text("Features:")
            dpg.add_text("• AI-powered content generation using LM Studio")
            dpg.add_text("• Customizable markdown templates")
            dpg.add_text("• Automatic PDF output")
            dpg.add_text("• Easy-to-use interface")
            dpg.add_spacing(count=2)
            dpg.add_button(
                label="Close", 
                callback=lambda: dpg.delete_item("about_window"),
                width=100
            )
    
    def run(self):
        """Run the GUI application"""
        dpg.create_viewport(
            title="Job Application Generator", 
            width=920, 
            height=720,
            min_width=800,
            min_height=600
        )
        dpg.set_primary_window("main_window", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()


def main():
    """Main entry point"""
    if not os.path.exists("job_app_generator.py"):
        print("❌ job_app_generator.py not found!")
        print("Make sure all files are in the same directory.")
        return
    
    try:
        app = JobApplicationGUI()
        app.run()
    except ImportError:
        print("❌ Dear PyGui not installed!")
        print("Install it using: pip install dearpygui")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()