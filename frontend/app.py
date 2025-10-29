"""
InSightMail Streamlit Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from components.sidebar import render_sidebar
from components.email_upload import render_email_upload
from components.job_pipeline import render_job_pipeline
from components.email_viewer import render_email_viewer  
from components.rag_search import render_rag_search
from components.analytics import render_analytics

# Page configuration
st.set_page_config(
    page_title="InSightMail - Job Search Copilot",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    .status-danger {
        color: #dc3545;
        font-weight: bold;
    }
    
    .email-card {
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
    
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: bold;
        border-radius: 0.25rem;
        margin-right: 0.5rem;
    }
    
    .category-application { background-color: #e3f2fd; color: #1565c0; }
    .category-recruiter { background-color: #f3e5f5; color: #7b1fa2; }
    .category-interview { background-color: #e8f5e8; color: #2e7d32; }
    .category-offer { background-color: #fff3e0; color: #ef6c00; }
    .category-rejection { background-color: #ffebee; color: #c62828; }
    .category-other { background-color: #f5f5f5; color: #616161; }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

class APIClient:
    """Client for communicating with FastAPI backend"""
    
    @staticmethod
    def get(endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request to API"""
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def post(endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """POST request to API"""
        try:
            if files:
                response = requests.post(f"{API_BASE_URL}{endpoint}", data=data, files=files)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

def check_api_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">📧 InSightMail</h1>', unsafe_allow_html=True)
    st.markdown("**Your AI-powered job search email copilot**")
    
    # Check API status
    if not check_api_health():
        st.error("🔴 Backend API is not running. Please start the FastAPI server first.")
        st.code("cd backend && python -m uvicorn main:app --reload")
        return
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    # Sidebar
    page = render_sidebar()
    st.session_state.current_page = page
    
    # Main content area
    if page == "Dashboard":
        render_dashboard()
    elif page == "Email Upload":
        render_email_upload()
    elif page == "Job Pipeline":
        render_job_pipeline()
    elif page == "Email Viewer":
        render_email_viewer()
    elif page == "Ask My Inbox":
        render_rag_search()
    elif page == "Analytics":
        render_analytics()

def render_dashboard():
    """Render main dashboard"""
    st.header("📊 Dashboard Overview")
    
    # Get stats from API
    stats = APIClient.get("/stats")
    if "error" in stats:
        st.error(f"Failed to load stats: {stats['error']}")
        return
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    pipeline_stats = stats.get('pipeline_stats', {})
    total_emails = sum(pipeline_stats.values())
    
    with col1:
        st.metric("Total Emails", total_emails)
    
    with col2:
        applications = pipeline_stats.get('Application Sent', 0)
        st.metric("Applications Sent", applications)
    
    with col3:
        interviews = pipeline_stats.get('Interview', 0)
        st.metric("Interviews", interviews)
    
    with col4:
        offers = pipeline_stats.get('Offer', 0)
        st.metric("Offers Received", offers)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Email Categories")
        if pipeline_stats:
            # Pie chart
            fig = px.pie(
                values=list(pipeline_stats.values()),
                names=list(pipeline_stats.keys()),
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Job Search Funnel")
        if pipeline_stats:
            # Funnel chart
            funnel_data = {
                'Applications': pipeline_stats.get('Application Sent', 0),
                'Responses': pipeline_stats.get('Recruiter Response', 0),
                'Interviews': pipeline_stats.get('Interview', 0),
                'Offers': pipeline_stats.get('Offer', 0)
            }
            
            fig = go.Figure(go.Funnel(
                y=list(funnel_data.keys()),
                x=list(funnel_data.values()),
                textinfo="value+percent initial"
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("📧 Recent Activity")
    
    # Get recent emails
    emails = APIClient.get("/emails", params={'limit': 10})
    if "error" not in emails and emails.get('emails'):
        df = pd.DataFrame(emails['emails'])
        
        for _, email in df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{email['subject'][:60]}...**" if len(email['subject']) > 60 else f"**{email['subject']}**")
                    st.write(f"From: {email['sender']}")
                
                with col2:
                    category = email['category']
                    st.markdown(f'<span class="category-badge category-{category.lower().replace(" ", "")}">{category}</span>', 
                              unsafe_allow_html=True)
                    st.write(f"Date: {email['date_received'][:10] if email['date_received'] else 'Unknown'}")
                
                with col3:
                    if email.get('confidence_score'):
                        confidence = float(email['confidence_score'])
                        st.metric("Confidence", f"{confidence:.2f}")
    else:
        st.info("No emails found. Upload some Gmail exports to get started!")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload Emails", use_container_width=True):
            st.session_state.current_page = "Email Upload"
            st.rerun()
    
    with col2:
        if st.button("🔍 Search Inbox", use_container_width=True):
            st.session_state.current_page = "Ask My Inbox"
            st.rerun()
    
    with col3:
        if st.button("📈 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
    
    # System status
    st.subheader("🔧 System Status")
    
    health = APIClient.get("/health")
    if "error" not in health:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ API: Running")
        
        with col2:
            llm_status = health.get('llm', 'unknown')
            if 'healthy' in llm_status:
                st.success(f"✅ LLM: {llm_status}")
            else:
                st.warning(f"⚠️ LLM: {llm_status}")
        
        with col3:
            email_count = health.get('email_count', 0)
            st.info(f"📊 Emails: {email_count}")
    else:
        st.error("❌ API: Not responding")

if __name__ == "__main__":
    main()

