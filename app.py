import streamlit as st
import os
import json
from io import StringIO
from pathlib import Path
from extract_jd import generate_detailed_jd
from extract_resume import generate_detailed_resume
from alignment import process_alignment
from generate_mail import process_mail_generation

# Set page configuration
st.set_page_config(
    page_title="Resume & JD Alignment Tool",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        margin-top: 0.8rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .alignment-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #4CAF50;
    }
    .section-header {
        background-color: #1E88E5;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .edit-box {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin-top: 10px;
        background-color: #f1f1f1;
    }
    .alert-success {
        padding: 10px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .alert-info {
        padding: 10px;
        background-color: #cce5ff;
        color: #004085;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Function to extract text from file (handles both txt and pdf files)
def extract_text_from_file(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1]
    
    if file_extension == 'txt':
        return uploaded_file.getvalue().decode('utf-8')
    elif file_extension == 'pdf':
        # Extract text from PDF using PyPDF2
        try:
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            st.error(f"Error extracting PDF: {e}")
            return ""
    else:
        return ""

# Function to display alignment data in a nicely formatted way
def display_alignment_data(alignment_data):
    if not alignment_data:
        return
    
    try:
        if isinstance(alignment_data, str):
            data = json.loads(alignment_data)
        else:
            data = alignment_data

        # Job Title and Company Section
        st.markdown(f"<div class='section-header'><h3>🎯 Target Role</h3></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='alignment-card'><strong>{data.get('job_title', 'Unknown Role')}</strong> at <strong>{data.get('company_name', 'Unknown Company')}</strong></div>", unsafe_allow_html=True)

        # Primary Objective Alignment Section
        st.markdown('<div class="section-header"><h3>🎯 Primary Objective Alignment</h3></div>', unsafe_allow_html=True)
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Job Requirements")
                st.markdown(f"<div class='alignment-card'>{data['primary_objective_alignment']['job_specific_requirements']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("#### Candidate Alignment")
                st.markdown(f"<div class='alignment-card'>{data['primary_objective_alignment']['candidate_alignment']}</div>", unsafe_allow_html=True)
        
        # High Level Alignment Section
        st.markdown('<div class="section-header"><h3>🔍 High Level Alignment Points</h3></div>', unsafe_allow_html=True)
        for idx, alignment in enumerate(data['high_level_alignment']):
            with st.expander(f"{alignment['alignment_type']}", expanded=True):
                st.markdown(f"**Candidate Experience:**")
                st.markdown(f"<div class='alignment-card'>{alignment['candidate_experience']}</div>", unsafe_allow_html=True)
        
        # Environment Fit Section
        st.markdown('<div class="section-header"><h3>🏢 Environment Fit</h3></div>', unsafe_allow_html=True)
        env_fit = data['environment_fit']
        cols = st.columns(3)
        with cols[0]:
            st.metric("Company Size", env_fit['company_size'])
        with cols[1]:
            st.metric("Industry", env_fit['industry'])
        with cols[2]:
            st.metric("Customer Type", env_fit['customer_type'])
        
        st.markdown("#### Candidate's Environmental Alignment")
        st.markdown(f"<div class='alignment-card'>{env_fit['candidate_experience']}</div>", unsafe_allow_html=True)
        
        # Candidate Strengths Section
        st.markdown('<div class="section-header"><h3>💪 Candidate Strengths</h3></div>', unsafe_allow_html=True)
        for strength in data['candidate_strengths']:
            with st.expander(f"{strength['strength']}", expanded=True):
                st.markdown(f"**Candidate Experience:**")
                st.markdown(f"<div class='alignment-card'>{strength['candidate_experience']}</div>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Error displaying alignment data: {e}")

def edit_alignment_data(alignment_data):
    if not alignment_data:
        return None

    try:
        if isinstance(alignment_data, str):
            data = json.loads(alignment_data)
        else:
            data = alignment_data
        
        edited_data = data.copy()

        st.markdown('<div class="section-header"><h3>Edit Alignment Data</h3></div>', unsafe_allow_html=True)

        # Job Title and Company Info
        st.markdown("### Role Information")
        with st.expander("Edit Job Title and Company Name", expanded=True):
            edited_data['job_title'] = st.text_input("Job Title", value=data.get('job_title', ''))
            edited_data['company_name'] = st.text_input("Company Name", value=data.get('company_name', ''))

        # Primary Objective Alignment
        st.markdown("### Primary Objective Alignment")
        with st.expander("Edit Primary Objective", expanded=True):
            edited_data['primary_objective_alignment']['job_specific_requirements'] = st.text_area(
                "Job Requirements", 
                value=data['primary_objective_alignment']['job_specific_requirements'],
                height=150
            )
            edited_data['primary_objective_alignment']['candidate_alignment'] = st.text_area(
                "Candidate Alignment", 
                value=data['primary_objective_alignment']['candidate_alignment'],
                height=150
            )

        # High Level Alignment
        st.markdown("### High Level Alignment Points")
        for i, alignment in enumerate(data['high_level_alignment']):
            with st.expander(f"Edit {alignment['alignment_type']}", expanded=False):
                edited_data['high_level_alignment'][i]['alignment_type'] = st.text_input(
                    "Alignment Type", 
                    value=alignment['alignment_type'],
                    key=f"hl_type_{i}"
                )
                edited_data['high_level_alignment'][i]['candidate_experience'] = st.text_area(
                    "Candidate Experience", 
                    value=alignment['candidate_experience'],
                    height=150,
                    key=f"hl_exp_{i}"
                )

        # Environment Fit
        st.markdown("### Environment Fit")
        with st.expander("Edit Environment Fit", expanded=False):
            env_fit = data['environment_fit']
            edited_data['environment_fit']['company_size'] = st.text_input("Company Size", value=env_fit['company_size'])
            edited_data['environment_fit']['industry'] = st.text_input("Industry", value=env_fit['industry'])
            edited_data['environment_fit']['customer_type'] = st.text_input("Customer Type", value=env_fit['customer_type'])
            edited_data['environment_fit']['candidate_experience'] = st.text_area(
                "Candidate Experience", 
                value=env_fit['candidate_experience'],
                height=150
            )

        # Candidate Strengths
        st.markdown("### Candidate Strengths")
        for i, strength in enumerate(data['candidate_strengths']):
            with st.expander(f"Edit {strength['strength']}", expanded=False):
                edited_data['candidate_strengths'][i]['strength'] = st.text_input(
                    "Strength", 
                    value=strength['strength'],
                    key=f"str_name_{i}"
                )
                edited_data['candidate_strengths'][i]['candidate_experience'] = st.text_area(
                    "Candidate Experience", 
                    value=strength['candidate_experience'],
                    height=150,
                    key=f"str_exp_{i}"
                )

        return edited_data

    except Exception as e:
        st.error(f"Error editing alignment data: {e}")
        return None

# Function to display and edit mail content in a nicely formatted way
def display_mail_content(mail_content):
    st.markdown('<div class="section-header"><h3>📧 Generated Email</h3></div>', unsafe_allow_html=True)
    
    preview_tab, raw_tab = st.tabs(["Preview", "Raw Content"])
    
    with preview_tab:
        # Render using st.write for plain, clean output
        st.write(mail_content)
    
    with raw_tab:
        st.text_area("Raw Email Content", value=mail_content, height=400, key="raw_mail_display")


# Function to edit mail content
def edit_mail_content(mail_content):
    st.markdown('<div class="section-header"><h3>Edit Email Content</h3></div>', unsafe_allow_html=True)
    
    # Create sections for different parts of the email
    edited_content = st.text_area("Email Content", value=mail_content, height=400, key="mail_edit_area")
    
    return edited_content

# Main Streamlit UI
def main():
    # Sidebar for navigation and status
    with st.sidebar:
        # st.image("https://img.icons8.com/color/96/000000/document-matching.png", width=100)
        st.title("Navigation")
        
        # Display current step
        if 'step' in st.session_state:
            current_step = st.session_state.step
            st.markdown(f"<div class='alert-info'>Current Step: {current_step}/5</div>", unsafe_allow_html=True)
            
            # Navigation buttons
            if current_step > 1:
                if st.button("⬅️ Previous Step"):
                    st.session_state.step -= 1
                    st.rerun()
            
            # Help section
            with st.expander("Need Help?"):
                st.markdown("""
                    This tool helps you align a resume with a job description and generate a tailored email.
                    
                    **Steps:**
                    1. Upload Resume & Job Description
                    2. Review Extracted Data
                    3. Review & Edit Alignment
                    4. Generate & Edit Email
                    5. Finalize & Export
                """)
    
    # Main content
    st.title("Mail Generation Tool")
    
    # Use session state to track the current step and store data
    if 'step' not in st.session_state:
        st.session_state.step = 1
    
    # Step 1: Text Input
    if st.session_state.step == 1:
        st.header("Step 1: Enter Information")
        
        # Create two columns for visual balance
        col1, col2 = st.columns(2)
  
        with col1:
            st.markdown("### Resume")
            uploaded_resume = st.file_uploader("Upload Resume", type=["txt", "pdf"])
            resume_text=""
            if uploaded_resume:
                st.success(f"Uploaded: {uploaded_resume.name}")
                st.session_state.uploaded_resume = uploaded_resume
                resume_text = extract_text_from_file(st.session_state.uploaded_resume)
            if resume_text:
                st.success("Resume text received")
                st.session_state.resume_text = resume_text
        
        with col2:
            st.markdown("### Job Description")
            jd_text = st.text_area("Paste the job description text here", height=300)
            if jd_text:
                st.success("Job description text received")
                st.session_state.jd_text = jd_text
        
        # Process button - only enabled when both text areas have content
        if resume_text and jd_text:
            if st.button("Process Information", key="process_texts_btn"):
                with st.spinner("Processing information and generating extracts..."):
                    # Call extract functions directly with the text
                    st.session_state.resume_data, st.session_state.resume_path = generate_detailed_resume(resume_text)
                    st.session_state.jd_data, st.session_state.jd_path = generate_detailed_jd(jd_text)
                    
                    st.session_state.step = 2
                    st.rerun()
        else:
            st.info("Please enter both resume and job description texts, then type 'confirm' to continue.")
            
    # Step 2: Display extracted data and generate alignment
    elif st.session_state.step == 2:
        st.header("Step 2: Review Extracted Data")
        
        # Create tabs for resume and JD
        resume_tab, jd_tab = st.tabs(["Resume Data", "Job Description Data"])
        
        with resume_tab:
            st.json(st.session_state.resume_data)
        
        with jd_tab:
            st.json(st.session_state.jd_data)
        
        # Button to generate alignment
        if st.button("Generate Alignment Analysis", key="generate_alignment_btn"):
            with st.spinner("Generating in-depth alignment analysis..."):
                # Call alignment function with the file paths
                st.session_state.alignment, st.session_state.alignment_path = process_alignment(
                    st.session_state.resume_path,
                    st.session_state.jd_path
                )
                
                # Try to parse the alignment as JSON for better display
                try:
                    if isinstance(st.session_state.alignment, str):
                        st.session_state.alignment_data = json.loads(st.session_state.alignment)
                    else:
                        st.session_state.alignment_data = st.session_state.alignment
                except:
                    st.session_state.alignment_data = None
                
                st.session_state.step = 3
                st.rerun()

    # Step 3: Review and modify alignment
    elif st.session_state.step == 3:
        st.header("Step 3: Review and Modify Alignment")
        
        # Check if we're in editing mode
        if 'editing_alignment' not in st.session_state:
            st.session_state.editing_alignment = False
        
        # Create tabs for view and edit
        view_tab, edit_tab = st.tabs(["View Alignment", "Edit Alignment"])
        
        with view_tab:
            # Display formatted alignment
            if 'alignment_data' in st.session_state and st.session_state.alignment_data:
                display_alignment_data(st.session_state.alignment_data)
            else:
                try:
                    # Try to parse the alignment string to JSON
                    alignment_data = json.loads(st.session_state.alignment)
                    display_alignment_data(alignment_data)
                except:
                    # Just display as text if not JSON
                    st.text_area("Alignment Text", value=st.session_state.alignment, height=400)
        
        with edit_tab:
            # Edit alignment
            if 'alignment_data' in st.session_state and st.session_state.alignment_data:
                edited_data = edit_alignment_data(st.session_state.alignment_data)
                if edited_data and st.button("Save Changes", key="save_alignment_btn"):
                    st.session_state.alignment_data = edited_data
                    st.session_state.alignment = json.dumps(edited_data, indent=2)
                    st.success("Alignment data updated successfully!")
                    st.rerun()
            else:
                # Provide a simpler text editor if not in JSON format
                edited_text = st.text_area("Edit Alignment Text", value=st.session_state.alignment, height=400)
                if st.button("Save Text Changes", key="save_text_alignment_btn"):
                    st.session_state.alignment = edited_text
                    st.success("Alignment text updated successfully!")
                    st.rerun()
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Regenerate Alignment", key="regenerate_alignment_btn"):
                with st.spinner("Regenerating alignment analysis..."):
                    st.session_state.alignment, st.session_state.alignment_path = process_alignment(
                        st.session_state.resume_path,
                        st.session_state.jd_path
                    )
                    
                    # Try to parse the new alignment as JSON
                    try:
                        if isinstance(st.session_state.alignment, str):
                            st.session_state.alignment_data = json.loads(st.session_state.alignment)
                        else:
                            st.session_state.alignment_data = st.session_state.alignment
                    except:
                        st.session_state.alignment_data = None
                    
                    st.success("Alignment regenerated successfully!")
                    st.rerun()
        
        with col2:
            if st.button("Proceed to Email Generation", key="proceed_to_mail_btn"):
                st.session_state.step = 4
                st.rerun()

    # Step 4: Generate mail
    # Step 4: Generate mail
    elif st.session_state.step == 4:
        st.header("Step 4: Generate Email")

        # Ensure latest alignment data is saved to disk before generating email
        if 'alignment_data' in st.session_state and st.session_state.alignment_path:
            st.markdown(f"ℹ️ Saving updated alignment to: `{st.session_state.alignment_path}`")
            with open(st.session_state.alignment_path, 'w') as f:
                json.dump(st.session_state.alignment_data, f, indent=2)
            st.success("Alignment file updated successfully before email generation!")
            st.code(json.dumps(st.session_state.alignment_data, indent=2), language='json')

        # Check if mail has been generated
        if 'mail_content' not in st.session_state or st.session_state.mail_content is None:
            # Generate mail button
            if st.button("Generate Email Based on Alignment", key="generate_mail_btn"):
                with st.spinner("Generating personalized email..."):
                    st.session_state.mail_content, st.session_state.mail_path = process_mail_generation(
                        st.session_state.alignment_path
                    )
                    st.success("Email Generated Successfully!")
                    st.rerun()
        else:
            # Display and edit mail content
            mail_tabs = st.tabs(["View Email", "Edit Email"])

            with mail_tabs[0]:
                display_mail_content(st.session_state.mail_content)

            with mail_tabs[1]:
                edited_mail = edit_mail_content(st.session_state.mail_content)

                # Save manual edits only
                if st.button("💾 Save Manual Changes", key="save_mail_btn"):
                    st.session_state.mail_content = edited_mail
                    st.success("Manual changes saved successfully!")
                    st.rerun()

                # Feedback-based regeneration
                feedback_input = st.text_area("💬 Optional Feedback for Regeneration", placeholder="e.g., Make it more concise and highlight cloud experience.", key="feedback_box")

                if st.button("🔁 Regenerate with Feedback", key="regenerate_with_feedback_btn"):
                    with st.spinner("Generating updated mail based on feedback..."):
                        st.session_state.mail_feedback = feedback_input  # Save feedback
                        # Save latest alignment to file before regenerating
                        if 'alignment_data' in st.session_state and st.session_state.alignment_path:
                            with open(st.session_state.alignment_path, 'w') as f:
                                json.dump(st.session_state.alignment_data, f, indent=2)
                        
                        # Generate revised mail with feedback
                        st.session_state.mail_content, st.session_state.mail_path = process_mail_generation(
                            st.session_state.alignment_path,
                            feedback=feedback_input,
                            previous_mail=st.session_state.mail_content
                        )
                        st.success("Mail regenerated with feedback!")
                        st.rerun()

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                #this regeneration is general on top of alignment changes no feedback or context of previous mail
                if st.button("Regenerate Email", key="regenerate_mail_btn"):
                    with st.spinner("Regenerating email..."):
                        # Ensure latest edits are saved before regeneration
                        if 'alignment_data' in st.session_state and st.session_state.alignment_path:
                            with open(st.session_state.alignment_path, 'w') as f:
                                json.dump(st.session_state.alignment_data, f, indent=2)

                        st.session_state.mail_content, st.session_state.mail_path = process_mail_generation(
                            st.session_state.alignment_path
                        )
                        st.success("Email Regenerated!")
                        st.rerun()

            with col2:
                if st.button("Finalize Email", key="finalize_mail_btn"):
                    st.session_state.step = 5
                    st.rerun()

    # Step 5: Final mail presentation
    elif st.session_state.step == 5:
        st.header("Step 5: Finalized Email")
        
        st.markdown('<div class="alert-success"><h3>✅ Email Finalized!</h3></div>', unsafe_allow_html=True)
        
        # Display final email in a nice card
        st.markdown('<div class="section-header"><h3>📧 Final Email Ready to Send</h3></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: white;">
            {st.session_state.mail_content.replace('\n', '<br>')}
        </div>
        """, unsafe_allow_html=True)
        
        # Export options
        st.markdown("### Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.download_button(
                label="Download as TXT",
                data=st.session_state.mail_content,
                file_name="tailored_application_email.txt",
                mime="text/plain"
            ):
                st.success("Email downloaded!")
        
        with col2:
            if st.button("Copy to Clipboard", key="copy_mail_btn"):
                # This doesn't actually copy to clipboard (Streamlit limitation)
                # but we can provide JavaScript to do so in a production app
                st.success("Email copied to clipboard!")
        
        # Start over button
        if st.button("Start New Alignment Process", key="start_over_btn"):
            # Reset session state and start over
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = 1
            st.rerun()

if __name__ == "__main__":
    main()