from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
import pathlib

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

# Read the mail generation system prompt
with open("prompts/create_mail_prompt.txt", "r") as file:
    content_prompt = file.read()

def save_mail(mail_content, alignment_path):
    """
    Save generated mail to file.
    
    Args:
        mail_content (str): The generated mail content
        alignment_path (str): Path to the alignment file used to generate the mail
        
    Returns:
        str: Path where mail content was saved
    """
    # Create connection_mails directory if it doesn't exist
    os.makedirs("connection_mails", exist_ok=True)
    
    # Extract basename from alignment file path
    alignment_filename = os.path.basename(alignment_path)
    base_name = os.path.splitext(alignment_filename)[0]  # Remove extension
    
    # Create mail filename
    mail_filename = f"{base_name}_mail.json" 
    mail_filepath = os.path.join("connection_mails", mail_filename)
    
    # Save the mail content as JSON
    mail_data = {
        "mail_content": mail_content
    }
    
    with open(mail_filepath, "w") as f:
        json.dump(mail_data, f, indent=2)
    
    return mail_filepath

def generate_initial_mail(alignments):
    """
    Generate initial connection mail.
    
    Args:
        resume_data (dict): Resume data
        jd_data (dict): Job description data
        alignments_data (dict or str): Alignment data
        
    Returns:
        str: Generated mail content
    """
    user_input=f"key allignments between candidate's resume and job description are: \n\n {alignments}" 
    prompt = ChatPromptTemplate.from_messages([
        ("system", content_prompt),
        ("placeholder", "{messages}"),
        ("user", "Always be accurate."),
    ])
    
    mail_agent = create_react_agent(model, tools=[], prompt=prompt)
    inputs = {"messages": [("user", user_input)]}
    result = mail_agent.invoke(inputs)
    
    return result['messages'][1].content

def generate_revised_mail(previous_mail, corrections,alignments_data):
    """
    Generate a revised mail based on user feedback.
    
    Args:
        previous_mail (str): Previously generated mail content
        corrections (str): User feedback on corrections needed
        resume_data (dict): Resume data
        jd_data (dict): Job description data
        alignments_data (dict or str): Alignment data
        
    Returns:
        str: Revised mail content
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", content_prompt),
        ("placeholder", "{messages}"),
        ("user", "Always be accurate. Format the mail properly with line breaks."),
    ])
    
    mail_agent = create_react_agent(model, tools=[], prompt=prompt)
    
    # Prepare feedback input with context
    revised_input = f"""You have received user feedback on the generated mail. Please fix it according to the feedback.

                        Key alignments: {alignments_data}

                        Feedback: {corrections}

                        Existing mail: {previous_mail}
                    """
    
    inputs = {"messages": [("user", revised_input)]}
    result = mail_agent.invoke(inputs)
    
    return result['messages'][1].content

def process_mail_generation( alignment_path, feedback=None, previous_mail=None):
    """
    Main function to process mail generation.
    
    Args:
        alignment_path (str): Path to the alignment JSON file
        feedback (str, optional): User feedback for corrections
        previous_mail (str, optional): Previous mail to revise
        
    Returns:
        tuple: (mail_content, saved_path)
    """
   
    
    with open(alignment_path, "r") as f:
        alignments_data = json.load(f)
    
    # Generate mail based on whether feedback exists
    if feedback and previous_mail:
        # Generate revised mail
        mail_content = generate_revised_mail(
            previous_mail, 
            feedback, 
            alignments_data
        )
    else:
        # Generate initial mail
        mail_content = generate_initial_mail(alignments_data)
    
    # Save the mail
    saved_path = save_mail(mail_content, alignment_path)
    
    return mail_content, saved_path

# Example usage in a standalone context

if __name__ == "__main__":
    
    alignment_path = "alignments/Ramesh_Mishra_20250503_014749_Netflix.json"
    
    # Generate initial mail
    mail, saved_path = process_mail_generation(alignment_path)
    
    print(f"Generated mail saved to: {saved_path}")
    print("\nMail content:")
    print("----------------------------------------")
    print(mail)
    
    # Sample demonstration of feedback loop
    test_feedback = input("\nEnter feedback for testing (or press Enter to skip): ")
    
    if test_feedback:
        revised_mail, revised_path = process_mail_generation(
            alignment_path, 
            feedback=test_feedback, 
            previous_mail=mail
        )
        
        print("\nRevised mail:")
        print("----------------------------------------")
        print(revised_mail)
        print(f"Revised mail saved to: {revised_path}")