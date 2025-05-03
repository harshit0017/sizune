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
with open("prompts/jd_extract_prompt.txt", "r") as f:
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

from datetime import datetime
import os
import json

def save_jd_json(data: dict, output_dir: str = "job_descriptions") -> str:
    """
    Save a JD JSON using only the company name and a timestamp for the filename.
    
    Args:
        data (dict): Parsed JD JSON from LLM.
        output_dir (str): Directory to save the file in.
    
    Returns:
        str: Path to the saved file.
    """
    company_name = data.get("company_overview", {}).get("company_name", "unknown_company")
    
    # Sanitize and build filename
    safe_company = company_name.replace(" ", "_").replace(".", "").replace(",", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_company}_{timestamp}.json"
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Write JSON to file
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved JD JSON to: {filepath}")
    return filepath

def generate_detailed_jd(jd: str) -> str:
    """
    Process a raw job description text through the LLM to extract structured information.

    Args:
        jd (str): Raw job description content.

    Returns:
        str: The original LLM output (useful for logs or debugging).
        path: path to file saved
    """
    user_input = f"job description: {jd}"
    alignment_agent = create_react_agent(model, tools=[], prompt=agent_prompt)
    inputs = {"messages": [("user", user_input)]}
    result = alignment_agent.invoke(inputs)

    output_content = result["messages"][1].content
    extracted_json = extract_json_from_output(output_content)

    if extracted_json:
        jd_path=save_jd_json(extracted_json)

    return extracted_json,jd_path

# Example usage
if __name__ == "__main__":
    from config.samples import test_jd_4
    print(generate_detailed_jd(test_jd_4))
