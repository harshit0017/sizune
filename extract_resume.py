import os
import re
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from state.state_management import State, create_empty_state
from datetime import datetime
# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI model
model = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

# Load resume extraction prompt
with open("prompts/resume_extractor_prompt.txt", "r") as f:
    extract_resume_prompt = f.read()

# Prepare the agent prompt
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", extract_resume_prompt),
    ("placeholder", "{messages}"),
    ("user", "Always be accurate."),
])

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

def save_json_to_file(data: dict, output_dir: str = "resumes") -> str:
    """
    Save parsed JSON data to a file named after the candidate.

    Args:
        data (dict): Parsed JSON object.
        output_dir (str): Directory to save the file in.

    Returns:
        str: Path to the saved file.
    """
    candidate_name = data.get("candidate_information", {}).get("name", "unknown_candidate")
    safe_name = candidate_name.replace(" ", "_").replace(".", "").replace(",", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.json"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved JSON to file: {filepath}")
    return filepath

def generate_detailed_resume(resume_text: str) -> str:
    """
    Process a raw resume text through the LLM to extract structured information.

    Args:
        resume_text (str): Raw resume content.

    Returns:
        str: The original LLM output (useful for logs or debugging).
        path: path to file saved
    """
    user_input = f"resume: {resume_text}"
    alignment_agent = create_react_agent(model, tools=[], prompt=agent_prompt)
    inputs = {"messages": [("user", user_input)]}
    result = alignment_agent.invoke(inputs)

    output_content = result["messages"][1].content
    extracted_json = extract_json_from_output(output_content)

    if extracted_json:
        resume_path = save_json_to_file(extracted_json)

    return extracted_json, resume_path

# Example usage
if __name__ == "__main__":
    from config.samples import test_resume_2
    print(generate_detailed_resume(test_resume_2))
