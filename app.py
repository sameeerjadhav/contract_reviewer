import streamlit as st
import asyncio
import tempfile
import os
from pathlib import Path
from src.tools.pdf_parser import DocumentParser
from src.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

import base64
from dotenv import load_dotenv
from google import genai
from src.utils.docx_generator import generate_docx

load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Legal AI | Contract Review",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Typography */
    /* Custom Header Sizes for Report */
    h1 {
        font-size: 1.8rem !important;
    }
    h2 {
        font-size: 1.5rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #FFFFFF;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #2EA043;
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
    }
    
    /* File Uploader */
    .stFileUploader {
        border: 1px dashed #30363D;
        border-radius: 8px;
        padding: 2rem;
        background-color: #0D1117;
    }
    
    /* Cards/Containers */
    .css-1r6slb0 {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 1.5rem;
    }
    
    /* Status Indicators */
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-family: monospace;
        font-size: 0.9em;
    }
    .status-info { background-color: #1F6FEB33; color: #58A6FF; border-left: 3px solid #1F6FEB; }
    .status-success { background-color: #23863633; color: #3FB950; border-left: 3px solid #238636; }
    .status-warning { background-color: #9E6A0333; color: #D29922; border-left: 3px solid #9E6A03; }
    .status-error { background-color: #DA363333; color: #F85149; border-left: 3px solid #DA3633; }

</style>
""", unsafe_allow_html=True)

def displayPDF(file_path):
    """Display PDF in Streamlit using an iframe"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    pdf_display = f'''
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="800" 
                type="application/pdf"
                style="border: 2px solid #ddd; border-radius: 5px;">
        </iframe>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚖️ Multi Agent System")
    st.markdown("---")
    st.markdown("""
    **System Status:** 🟢 Online
    
    **Agents Active:**
    - 🔍 Intake Agent
    - 📄 Clause Extractor
    - ⚠️ Risk Scorer
    - 📚 Playbook Auditor
    - 📝 Report Generator
    """)

# --- Main Content ---
st.title("Contract Review System")
st.markdown("Upload a legal contract (PDF) for comprehensive AI analysis against company playbooks.")

uploaded_file = st.file_uploader("Drop your contract here", type="pdf")

if uploaded_file is not None:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    # Initialize Session State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "report_text" not in st.session_state:
        st.session_state.report_text = ""
    if "contract_text" not in st.session_state:
        st.session_state.contract_text = ""
    if "debug_text" not in st.session_state:
        st.session_state.debug_text = ""
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False

    # 1. Setup Layout (Always visible if file uploaded)
    # Sidebar: Debug Logs
    with st.sidebar:
        st.markdown("---")
        st.subheader("🕵️ Agent Traces")
        status_container = st.container(height=600)
        with status_container:
            # If we have logs in history, show them
            if st.session_state.debug_text:
                st.code(st.session_state.debug_text, language="text")
            debug_placeholder = st.empty() # Placeholder for new logs
        
    # Main Area: Split View
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"📄 {uploaded_file.name}")
        displayPDF(tmp_path)
        st.markdown("###") # Spacer
        # Use nested columns to match the button size of the right column
        start_col1, start_col2 = st.columns(2)
        with start_col1:
            start_analysis = st.button("🚀 Start Analysis", use_container_width=True)
        
    with col2:
        st.subheader("📊 Analysis Report")
        # Scrollable container for the report
        report_scroll = st.container(height=800)
        with report_scroll:
            report_placeholder = st.empty()
            # If we have a report in history, show it
            if st.session_state.report_text:
                report_placeholder.markdown(st.session_state.report_text)

        # Action Buttons (Download / Copy)
        if st.session_state.report_text:
            st.markdown("###") # Spacer
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                docx_file = generate_docx(st.session_state.report_text)
                st.download_button(
                    label="📄 Download Report (.docx)",
                    data=docx_file,
                    file_name="contract_review.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            
            with btn_col2:
                # Use a popover for the copy functionality
                # This is cleaner than an expander and uses native Streamlit features
                with st.popover("📋 Copy Report Text", use_container_width=True):
                    st.markdown("Click the copy icon in the top right of the code block:")
                    st.code(st.session_state.report_text, language="markdown")

    # Start Analysis Logic
    if start_analysis:
        # Reset state
        st.session_state.messages = []
        st.session_state.report_text = ""
        st.session_state.contract_text = ""
        st.session_state.debug_text = ""
        st.session_state.analysis_complete = False
        
        # Clear the debug placeholder if it has content from previous run
        debug_placeholder.empty()
        
        # 2. Run Subprocess
        import subprocess
        import sys
        import os
        
        # Use the same python executable that is running streamlit
        cmd = [sys.executable, "run_single.py", tmp_path]
        
        # Copy current env and set unbuffered output
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        full_report_text = ""
        full_debug_text = ""
        captured_contract_text = ""
        is_report_content = False
        is_contract_text = False
        
        # Progress tracking
        progress_stages = {
            "intake": {"weight": 0.15, "complete": False, "name": "📋 Contract Intake"},
            "extraction": {"weight": 0.25, "complete": False, "name": "📄 Clause Extraction"},
            "risk": {"weight": 0.25, "complete": False, "name": "⚠️ Risk Assessment"},
            "playbook": {"weight": 0.20, "complete": False, "name": "📚 Playbook Compliance"},
            "report": {"weight": 0.15, "complete": False, "name": "📝 Report Generation"}
        }
        current_progress = 0.0
        
        # 3. Stream Output with Progress Indicators
        # Create progress UI elements in report area
        progress_bar = report_placeholder.progress(0.0)
        status_text = st.empty()
        status_text.markdown("🚀 **Starting analysis...")
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Update progress based on agent output
                # Stage 1: Intake
                if "contract_intake_agent" in line and not progress_stages["intake"]["complete"]:
                    current_progress += progress_stages["intake"]["weight"]
                    progress_stages["intake"]["complete"] = True
                    progress_bar.progress(min(current_progress, 1.0))
                    status_text.markdown(f"✅ **{progress_stages['intake']['name']}** - Complete")
                
                # Stage 2: Clause Extraction
                if "clause_extraction_agent" in line or "ClauseExtractor" in line:
                    if not progress_stages["extraction"]["complete"]:
                        status_text.markdown(f"⏳ **{progress_stages['extraction']['name']}** - In Progress...")
                
                # Check if extraction complete (when risk scoring starts)
                if "risk_scoring_agent" in line and not progress_stages["extraction"]["complete"]:
                    current_progress += progress_stages["extraction"]["weight"]
                    progress_stages["extraction"]["complete"] = True
                    progress_bar.progress(min(current_progress, 1.0))
                    status_text.markdown(f"✅ **{progress_stages['extraction']['name']}** - Complete")
                
                # Stage 3: Risk Assessment
                if "risk_scoring_agent" in line or "RiskScorer" in line:
                    if not progress_stages["risk"]["complete"]:
                        status_text.markdown(f"⏳ **{progress_stages['risk']['name']}** - In Progress...")
                
                # Check if risk scoring complete (when playbook starts)
                if "playbook_comparison_agent" in line and not progress_stages["risk"]["complete"]:
                    current_progress += progress_stages["risk"]["weight"]
                    progress_stages["risk"]["complete"] = True
                    progress_bar.progress(min(current_progress, 1.0))
                    status_text.markdown(f"✅ **{progress_stages['risk']['name']}** - Complete")
                
                # Stage 4: Playbook Comparison
                if "PlaybookAgent" in line:
                    if not progress_stages["playbook"]["complete"]:
                        status_text.markdown(f"⏳ **{progress_stages['playbook']['name']}** - In Progress...")
                
                # Check if playbook complete (when report generation starts)
                if "ReportGenerator" in line and not progress_stages["playbook"]["complete"]:
                    current_progress += progress_stages["playbook"]["weight"]
                    progress_stages["playbook"]["complete"] = True
                    progress_bar.progress(min(current_progress, 1.0))
                    status_text.markdown(f"✅ **{progress_stages['playbook']['name']}** - Complete")
                
                # Stage 5: Report Generation
                if "report_generator_agent" in line or "ReportGenerator" in line:
                    if not progress_stages["report"]["complete"]:
                        status_text.markdown(f"⏳ **{progress_stages['report']['name']}** - Synthesizing final report...")
                        current_progress += progress_stages["report"]["weight"] * 0.5  # 50% of report weight
                        progress_bar.progress(min(current_progress, 1.0))
                
                # Capture Contract Text
                if "---CONTRACT_TEXT_START---" in line:
                    is_contract_text = True
                    continue
                if "---CONTRACT_TEXT_END---" in line:
                    is_contract_text = False
                    continue
                if is_contract_text:
                    captured_contract_text += line
                    continue

                # Logic to separate Debug vs Report
                # We look for specific markers that indicate the final report
                # Triggers: Agent name, Title, or Executive Summary
                is_report_line = (
                    "report_generator_agent >" in line or 
                    "# Contract Review Report" in line or 
                    "Contract Review Report:" in line or
                    "1. Executive Summary" in line
                )
                
                # Stop treating as report if we see other agent outputs after report started
                if is_report_content and ("playbook_comparison_agent >" in line or "PlaybookAgent:" in line):
                    is_report_content = False
                
                if is_report_line:
                    is_report_content = True
                    # Clean up the line if it has the agent prefix
                    line = line.replace("report_generator_agent >", "")
                
                if is_report_content:
                    # Mark report stage as complete and clear progress UI
                    if not progress_stages["report"]["complete"]:
                        current_progress = 1.0  # Complete
                        progress_stages["report"]["complete"] = True
                        # Clear all progress UI elements
                        status_text.empty()
                    
                    # Skip debug print statements from report content
                    if "ReportGenerator: Formatting final report" not in line:
                        full_report_text += line
                    
                    # Always display the accumulated report (even if this line was filtered)
                    if full_report_text.strip():
                        report_placeholder.markdown(full_report_text)
                else:
                    # Debug logs
                    if "---REPORT_START---" not in line:
                        full_debug_text += line
                        # Update the debug log placeholder
                        debug_placeholder.code(full_debug_text, language="text")

        # Clean up the report text
        def clean_report_text(text):
            """Remove conversational filler and markdown code fences from report."""
            import re
            # Remove markdown code fences
            text = re.sub(r'^```markdown\s*\n', '', text, flags=re.MULTILINE)
            text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
            # Remove common conversational prefixes
            prefixes_to_remove = [
                r'^Sure,?\s+I\s+can\s+help.*?\.?\s*',
                r'^Here\'s\s+.*?report.*?\.?\s*',
                r'^I\'ll\s+.*?\.?\s*',
                r'^Let\s+me\s+.*?\.?\s*',
            ]
            for prefix in prefixes_to_remove:
                text = re.sub(prefix, '', text, flags=re.IGNORECASE)
            # Strip leading/trailing whitespace
            text = text.strip()
            return text
        
        full_report_text = clean_report_text(full_report_text)
        
        if process.returncode == 0:
            st.sidebar.success("✅ Analysis Complete!")
            # Save to session state
            st.session_state.report_text = full_report_text
            st.session_state.contract_text = captured_contract_text
            st.session_state.debug_text = full_debug_text
            st.session_state.analysis_complete = True
            st.rerun()
        else:
            stderr = process.stderr.read()
            st.error(f"Process failed with error: {stderr}")

    # --- Chat Interface ---
    if st.session_state.analysis_complete:
        st.markdown("---")
        st.subheader("💬 Chat with your Contract")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask a question about the contract..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
                    
                    # Construct context
                    context = f"""
                    You are a helpful legal assistant. You have analyzed a contract.
                    
                    CONTRACT TEXT:
                    {st.session_state.contract_text}
                    
                    ANALYSIS REPORT:
                    {st.session_state.report_text}
                    
                    User Question: {prompt}
                    
                    Answer the user's question based on the contract and the report. Be concise and helpful.
                    """
                    
                    response = client.models.generate_content_stream(
                        model="gemini-2.0-flash-exp",
                        contents=context
                    )
                    
                    for chunk in response:
                        full_response += chunk.text
                        response_placeholder.markdown(full_response)
                        
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    st.error(f"Error generating response: {e}")
            
    # Cleanup (optional, maybe keep it for debugging or move inside button)
    # os.unlink(tmp_path)
