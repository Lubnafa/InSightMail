"""
Email upload component for Streamlit
"""
import streamlit as st
import requests
import json
import os
from typing import Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"

def render_email_upload():
    """Render email upload interface"""
    
    st.header("📤 Upload Gmail Data")
    st.markdown("Upload your Gmail exports to start analyzing your job search emails.")
    
    # Instructions
    with st.expander("📋 How to export Gmail data", expanded=False):
        st.markdown("""
        **Method 1: Google Takeout (Recommended)**
        1. Go to [Google Takeout](https://takeout.google.com)
        2. Select "Mail" 
        3. Choose "All messages included" or select specific labels
        4. Export format: `.mbox` or individual `.eml` files
        5. Download and extract the archive
        
        **Method 2: Gmail Search Export**
        1. In Gmail, search for job-related emails: `(recruiter OR interview OR application OR offer OR job OR hiring)`
        2. Use a browser extension like "Gmail Email Export" 
        3. Export as JSON or EML files
        
        **Method 3: Gmail API (Advanced)**
        - Use the Gmail API to programmatically export emails
        - JSON format is preferred for metadata preservation
        """)
    
    # Account selection
    st.subheader("👤 Account Information")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        account_email = st.text_input(
            "Gmail Account Email",
            placeholder="your.email@gmail.com",
            help="Enter the Gmail account these emails are from"
        )
    
    with col2:
        account_name = st.text_input(
            "Account Name (Optional)",
            placeholder="Work Account",
            help="Friendly name for this account"
        )
    
    # File upload
    st.subheader("📁 Upload Files")
    
    # Multiple file upload
    uploaded_files = st.file_uploader(
        "Choose Gmail export files",
        accept_multiple_files=True,
        type=['json', 'eml', 'mbox', 'txt'],
        help="Supported formats: JSON (Gmail API), EML (individual emails), MBOX (Gmail Takeout), TXT (plain text)"
    )
    
    # Upload options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        auto_classify = st.checkbox("Auto-classify emails", value=True, help="Automatically classify emails using AI")
    
    with col2:
        job_filter = st.checkbox("Filter job-related only", value=True, help="Only process emails that appear job-related")
    
    with col3:
        overwrite_existing = st.checkbox("Overwrite existing", value=False, help="Replace emails if they already exist")
    
    # Process files
    if uploaded_files and account_email:
        
        # Validation
        if not account_email or '@' not in account_email:
            st.error("Please enter a valid email address")
            return
        
        # Show file info
        st.subheader("📋 Files to Process")
        
        total_size = 0
        file_info = []
        
        for file in uploaded_files:
            size_mb = len(file.getvalue()) / (1024*1024)
            total_size += size_mb
            file_info.append({
                'name': file.name,
                'size': f"{size_mb:.2f} MB",
                'type': file.type or "Unknown"
            })
        
        # Display file table
        import pandas as pd
        df = pd.DataFrame(file_info)
        st.dataframe(df, use_container_width=True)
        
        st.info(f"Total size: {total_size:.2f} MB | Files: {len(uploaded_files)}")
        
        # Upload button
        if st.button("🚀 Start Processing", type="primary", use_container_width=True):
            process_uploaded_files(uploaded_files, account_email, auto_classify, job_filter)
    
    elif not account_email:
        st.warning("Please enter your Gmail account email first")
    
    elif not uploaded_files:
        st.info("Select files to upload")
    
    # Show recent uploads
    show_recent_uploads()

def process_uploaded_files(files, account_email: str, auto_classify: bool, job_filter: bool):
    """Process uploaded files"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.empty()
    
    total_files = len(files)
    processed_files = 0
    total_emails = 0
    errors = []
    
    for i, file in enumerate(files):
        
        # Update progress
        progress = (i + 1) / total_files
        progress_bar.progress(progress)
        status_text.text(f"Processing {file.name}... ({i+1}/{total_files})")
        
        try:
            # Prepare form data
            files_dict = {
                'file': (file.name, file.getvalue(), file.type or 'application/octet-stream')
            }
            
            data = {
                'account_email': account_email,
                'auto_classify': str(auto_classify).lower(),
                'job_filter': str(job_filter).lower()
            }
            
            # Upload file
            response = requests.post(
                f"{API_BASE_URL}/emails/upload",
                files=files_dict,
                data=data,
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                email_count = result.get('email_count', 0)
                total_emails += email_count
                processed_files += 1
                
                st.success(f"✅ {file.name}: {email_count} emails processed")
                
            else:
                error_msg = f"❌ {file.name}: HTTP {response.status_code}"
                st.error(error_msg)
                errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"❌ {file.name}: {str(e)}"
            st.error(error_msg)
            errors.append(error_msg)
    
    # Final results
    progress_bar.progress(1.0)
    status_text.text("Processing complete!")
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Processed", processed_files, delta=f"{processed_files}/{total_files}")
    
    with col2:
        st.metric("Total Emails", total_emails)
    
    with col3:
        error_count = len(errors)
        st.metric("Errors", error_count, delta=f"-{error_count}" if error_count > 0 else None)
    
    # Show errors if any
    if errors:
        with st.expander("❌ View Errors", expanded=False):
            for error in errors:
                st.text(error)
    
    # Next steps
    if processed_files > 0:
        st.success("🎉 Upload complete! Your emails are being processed in the background.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 View Dashboard"):
                st.session_state.current_page = "Dashboard"
                st.rerun()
        
        with col2:
            if st.button("🔄 Check Job Pipeline"):
                st.session_state.current_page = "Job Pipeline"
                st.rerun()

def show_recent_uploads():
    """Show recent upload history"""
    
    st.subheader("📈 Recent Activity")
    
    # Get recent emails from API
    try:
        response = requests.get(f"{API_BASE_URL}/emails", params={'limit': 5})
        
        if response.status_code == 200:
            data = response.json()
            emails = data.get('emails', [])
            
            if emails:
                st.write("**Latest processed emails:**")
                
                for email in emails:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            subject = email.get('subject', 'No Subject')
                            st.write(f"**{subject[:50]}...**" if len(subject) > 50 else f"**{subject}**")
                        
                        with col2:
                            category = email.get('category', 'Other')
                            st.write(f"Category: {category}")
                        
                        with col3:
                            date = email.get('date_received', '')
                            if date:
                                st.write(date[:10])
                        
                        st.markdown("---")
            else:
                st.info("No emails processed yet")
        
        else:
            st.warning("Could not load recent activity")
    
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")

def validate_file_format(file) -> tuple[bool, str]:
    """Validate uploaded file format"""
    
    if not file:
        return False, "No file provided"
    
    # Check file extension
    valid_extensions = ['.json', '.eml', '.mbox', '.txt']
    file_ext = os.path.splitext(file.name)[1].lower()
    
    if file_ext not in valid_extensions:
        return False, f"Unsupported file type: {file_ext}"
    
    # Check file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if len(file.getvalue()) > max_size:
        return False, "File too large (max 100MB)"
    
    # Basic content validation
    try:
        content = file.getvalue()
        
        if file_ext == '.json':
            # Try to parse as JSON
            json.loads(content.decode('utf-8'))
        
        elif file_ext in ['.eml', '.txt']:
            # Check if it's readable text
            content.decode('utf-8')
        
        return True, "Valid file"
    
    except Exception as e:
        return False, f"File validation error: {str(e)}"

