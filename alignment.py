from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import datetime
import re
import pathlib

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

# Read the alignment prompt
with open("prompts/align_prompt2.txt", "r") as file:
    alignment_prompt = file.read()

def extract_json_from_output(text: str) -> dict:
    """
    Extract and parse JSON from LLM output string.

    Args:
        text (str): The LLM's response text containing JSON.

    Returns:
        dict: Parsed JSON object if found, else None.
    """
    match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
    else:
        print("No JSON block found in LLM output.")
    return None

def extract_names_from_filenames(resume_filename, jd_filename):
    """
    Extract client name from resume filename and company name from JD filename.
    
    Args:
        resume_filename (str): Resume filename like Keith_L_Oufnac.json
        jd_filename (str): JD filename like BusPatrol_20250501_210823.json
        
    Returns:
        tuple: (client_name, company_name)
    """
    # Extract client name (remove .json extension)
    client_name = os.path.splitext(os.path.basename(resume_filename))[0]
    
    # Extract company name (remove timestamp and .json extension)
    company_match = re.match(r'([^_]+)_\d+', os.path.basename(jd_filename))
    company_name = company_match.group(1) if company_match else "Unknown_Company"
    
    return client_name, company_name

def save_alignment(alignment_content, client_name, company_name):
    """
    Save alignment content to file in alignments folder.
    
    Args:
        alignment_content (str): The alignment content from LLM containing JSON
        client_name (str): Name of client from resume
        company_name (str): Name of company from JD
    
    Returns:
        str: Path where alignment was saved
    """
    # Create alignments directory if it doesn't exist
    os.makedirs("alignments", exist_ok=True)
    
    # Format filename
    filename = f"{client_name}_{company_name}.json"
    filepath = os.path.join("alignments", filename)
    
    # Extract JSON from the LLM output
    # alignment_json = extract_json_from_output(alignment_content)
    
    if alignment_content:
        # Save only the alignment JSON
        with open(filepath, "w") as f:
            json.dump(alignment_content, f, indent=2)
    else:
        # If no JSON found, save the raw text as a fallback with a warning
        print("WARNING: No JSON found in alignment. Saving raw output.")
        with open(filepath, "w") as f:
            json.dump({"raw_output": alignment_content}, f, indent=2)
    
    return filepath

def generate_initial_alignment(resume_data, jd_data):
    """
    Generate initial alignment between resume and job description.
    
    Args:
        resume_data (dict): Resume data as a dictionary
        jd_data (dict): Job description data as a dictionary
        
    Returns:
        str: Generated alignment text containing JSON
    """
    user_input = f"""detailed_resume:{resume_data}\n\ndetailed_jd: {jd_data}"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", alignment_prompt),
        ("placeholder", "{messages}"),
        ("user", " Always be accurate."),
    ])

    alignment_agent = create_react_agent(model, tools=[], prompt=prompt)
    inputs = {"messages": [("user", user_input)]}
    result = alignment_agent.invoke(inputs)
    
    return result['messages'][1].content

def generate_revised_alignment(previous_alignment, corrections, resume_data, jd_data):
    """
    Generate a revised alignment based on user feedback.
    
    Args:
        previous_alignment (str): The previously generated alignment text
        corrections (str): User feedback on corrections needed
        resume_data (dict): Resume data as a dictionary
        jd_data (dict): Job description data as a dictionary
        
    Returns:
        str: Revised alignment text containing JSON
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", alignment_prompt),
        ("placeholder", "{messages}"),
        ("user",  "Always be accurate."),
    ])

    alignment_agent = create_react_agent(model, tools=[], prompt=prompt)
    
    # Try to extract and use the previous JSON if available
    previous_json = extract_json_from_output(previous_alignment)
    if previous_json:
        previous_content = json.dumps(previous_json, indent=2)
    else:
        previous_content = previous_alignment
    
    revised_input = f"""There are some corrections required in the alignments generated.
    
Resume data: {resume_data}
JD data: {jd_data}

Corrections: {corrections}

Alignment for correction: {previous_content}"""
    
    inputs = {"messages": [("user", revised_input)]}
    result = alignment_agent.invoke(inputs)
    
    return result['messages'][1].content

def process_alignment(resume_path, jd_path, feedback=None, previous_alignment=None):
    """
    Main function to process alignment generation given resume and JD paths.
    
    Args:
        resume_path (str): Path to the resume JSON file
        jd_path (str): Path to the job description JSON file
        feedback (str, optional): User feedback for corrections
        previous_alignment (str, optional): Previous alignment to revise
        
    Returns:
        tuple: (alignment_text, saved_path)
    """
    # Extract client and company names from filenames
    client_name, company_name = extract_names_from_filenames(resume_path, jd_path)
    
    # Load data from files
    with open(resume_path, "r") as f:
        resume_data = json.load(f)
    
    with open(jd_path, "r") as f:
        jd_data = json.load(f)
    
    # Generate alignment based on whether feedback exists
    if feedback and previous_alignment:
        # Generate revised alignment
        alignment_text = generate_revised_alignment(
            previous_alignment, 
            feedback, 
            resume_data, 
            jd_data
        )
    else:
        # Generate initial alignment
        alignment_text = generate_initial_alignment(resume_data, jd_data)
        alignment_json = extract_json_from_output(alignment_text)

    
    # Save the alignment
    saved_path = save_alignment(alignment_json, client_name, company_name)
    
    return alignment_json,saved_path

# Example usage in a standalone context
if __name__ == "__main__":
    # Paths to test files
    jd_path = "job_descriptions/Draper_20250503_001231.json"
    resume_path = "resumes/Keith_L_Oufnac.json"
    
    # Generate initial alignment
    alignment,path = process_alignment(resume_path, jd_path)
    

    print("\nAlignment content:")
    print("----------------------------------------")
    print(alignment)
    
    # Sample demonstration of feedback loop
    test_feedback = input("\nEnter feedback for testing (or press Enter to skip): ")
    
    if test_feedback:
        revised_alignment, revised_path= process_alignment(
            resume_path, 
            jd_path, 
            feedback=test_feedback, 
            previous_alignment=alignment
        )
        
        print("\nRevised alignment:")
        print("----------------------------------------")
        print(revised_alignment)
        print(f"Revised alignment saved to: {revised_path}")