from typing import Dict
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState

class State:
    """
    State class to track agent interactions and data.
    
    Attributes:
        job_description: The extracted JSON containing the detailed job description.
        resume: The extracted JSON containing the detailed resume.
        alignments: The key alignments from the resume and job description.
        mail_generated: The final mail generated from the resume, job description, and the alignment.
        connection_note: A short connection note for LinkedIn.
    """
    def __init__(self, 
                 resume="", 
                 job_description="", 
                 extracted_jd={}, 
                 extracted_resume={}, 
                 alignments="", 
                 alignment_corrections="",
                 selected_alignments="",
                 mail="",
                 mail_corrections="",
                 final_mail="",
                 connection_note=""):
        self.resume = resume
        self.job_description = job_description
        self.extracted_jd = extracted_jd
        self.extracted_resume = extracted_resume
        self.alignments = alignments
        self.alignment_corrections = alignment_corrections
        self.selected_alignments = selected_alignments
        self.mail = mail
        self.mail_corrections = mail_corrections
        self.final_mail = final_mail
        self.connection_note = connection_note

def create_empty_state() -> State:
    """
    Create and return an empty State object.
    """
    return State()

# Testing
if __name__ == "__main__":
    test_state = create_empty_state()
    print(f"Type of test_state: {type(test_state)}")
    print(f"Dir of test_state: {dir(test_state)}")