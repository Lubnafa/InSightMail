"""
Job pipeline visualization component
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"

def render_job_pipeline():
    """Render job pipeline dashboard"""
    
    st.header("🔄 Job Application Pipeline")
    st.markdown("Track your job search progress through each stage of the hiring process.")
    
    # Get pipeline data
    stats = get_pipeline_stats()
    emails = get_pipeline_emails()
    
    if not stats and not emails:
        st.info("No data available. Upload some emails first!")
        return
    
    # Pipeline overview
    render_pipeline_overview(stats)
    
    # Pipeline flow chart
    render_pipeline_flow(stats)
    
    # Stage details
    render_stage_details(emails)
    
    # Timeline view
    render_timeline_view(emails)
    
    # Action items
    render_action_items(emails)

def get_pipeline_stats() -> Dict[str, Any]:
    """Get pipeline statistics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            return response.json().get('pipeline_stats', {})
        return {}
    except Exception as e:
        st.error(f"Error loading pipeline stats: {e}")
        return {}

def get_pipeline_emails() -> List[Dict[str, Any]]:
    """Get pipeline emails from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/emails", params={'limit': 200})
        if response.status_code == 200:
            return response.json().get('emails', [])
        return []
    except Exception as e:
        st.error(f"Error loading emails: {e}")
        return []

def render_pipeline_overview(stats: Dict[str, Any]):
    """Render pipeline overview metrics"""
    
    st.subheader("📊 Pipeline Overview")
    
    # Main metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    applications = stats.get('Application Sent', 0)
    responses = stats.get('Recruiter Response', 0)
    interviews = stats.get('Interview', 0)
    offers = stats.get('Offer', 0)
    rejections = stats.get('Rejection', 0)
    other = stats.get('Other', 0)
    
    with col1:
        st.metric("📤 Applications", applications)
    
    with col2:
        st.metric("💬 Responses", responses, delta=f"{((responses/applications)*100):.1f}%" if applications > 0 else "0%")
    
    with col3:
        st.metric("🎯 Interviews", interviews, delta=f"{((interviews/applications)*100):.1f}%" if applications > 0 else "0%")
    
    with col4:
        st.metric("🎉 Offers", offers, delta=f"{((offers/applications)*100):.1f}%" if applications > 0 else "0%")
    
    with col5:
        st.metric("❌ Rejections", rejections, delta=f"-{((rejections/applications)*100):.1f}%" if applications > 0 else "0%")
    
    with col6:
        st.metric("📋 Other", other)
    
    # Conversion rates
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        response_rate = (responses / applications * 100) if applications > 0 else 0
        st.metric("Response Rate", f"{response_rate:.1f}%", 
                 delta="Good" if response_rate > 20 else "Needs Improvement")
    
    with col2:
        interview_rate = (interviews / applications * 100) if applications > 0 else 0
        st.metric("Interview Rate", f"{interview_rate:.1f}%",
                 delta="Excellent" if interview_rate > 10 else "Good" if interview_rate > 5 else "Needs Work")
    
    with col3:
        offer_rate = (offers / applications * 100) if applications > 0 else 0
        st.metric("Offer Rate", f"{offer_rate:.1f}%",
                 delta="Outstanding" if offer_rate > 5 else "Good" if offer_rate > 2 else "Keep Going")

def render_pipeline_flow(stats: Dict[str, Any]):
    """Render pipeline flow visualization"""
    
    st.subheader("🌊 Pipeline Flow")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sankey diagram
        if stats:
            applications = stats.get('Application Sent', 0)
            responses = stats.get('Recruiter Response', 0)
            interviews = stats.get('Interview', 0)
            offers = stats.get('Offer', 0)
            rejections = stats.get('Rejection', 0)
            
            # Create Sankey diagram
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=["Applications", "Responses", "No Response", "Interviews", "Rejections", "Offers", "Pending"],
                    color=["blue", "green", "gray", "orange", "red", "gold", "lightblue"]
                ),
                link=dict(
                    source=[0, 0, 1, 1, 1, 3, 3],
                    target=[1, 2, 3, 4, 6, 5, 4],
                    value=[responses, applications-responses, interviews, rejections, responses-interviews-rejections, offers, interviews-offers]
                )
            )])
            
            fig.update_layout(
                title_text="Job Application Flow",
                font_size=10,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pipeline health score
        st.markdown("### 🏥 Pipeline Health")
        
        total_score = 0
        max_score = 100
        
        # Calculate health metrics
        if applications > 0:
            response_rate = (responses / applications) * 100
            interview_rate = (interviews / applications) * 100
            offer_rate = (offers / applications) * 100
            
            # Weighted scoring
            total_score = (
                min(response_rate * 2, 40) +  # Response rate (max 40 points)
                min(interview_rate * 4, 30) +  # Interview rate (max 30 points)
                min(offer_rate * 6, 30)        # Offer rate (max 30 points)
            )
        
        # Health indicator
        if total_score >= 80:
            health_status = "🟢 Excellent"
            health_color = "green"
        elif total_score >= 60:
            health_status = "🟡 Good"
            health_color = "orange"
        elif total_score >= 40:
            health_status = "🟠 Fair"
            health_color = "orange"
        else:
            health_status = "🔴 Needs Work"
            health_color = "red"
        
        st.markdown(f"**Status:** {health_status}")
        st.progress(total_score / 100)
        st.markdown(f"**Score:** {total_score:.0f}/100")
        
        # Recommendations
        st.markdown("**Recommendations:**")
        if response_rate < 15:
            st.markdown("• Improve application quality")
        if interview_rate < 5:
            st.markdown("• Enhance networking")
        if offer_rate < 2:
            st.markdown("• Practice interview skills")

def render_stage_details(emails: List[Dict[str, Any]]):
    """Render detailed view of each pipeline stage"""
    
    st.subheader("📋 Pipeline Stages")
    
    # Group emails by category
    categories = {
        'Application Sent': [],
        'Recruiter Response': [],
        'Interview': [],
        'Offer': [],
        'Rejection': [],
        'Other': []
    }
    
    for email in emails:
        category = email.get('category', 'Other')
        if category in categories:
            categories[category].append(email)
    
    # Create tabs for each category
    tab_names = list(categories.keys())
    tabs = st.tabs([f"{name} ({len(categories[name])})" for name in tab_names])
    
    for i, (category, category_emails) in enumerate(categories.items()):
        with tabs[i]:
            if category_emails:
                # Sort by date
                sorted_emails = sorted(
                    category_emails, 
                    key=lambda x: x.get('date_received', ''), 
                    reverse=True
                )
                
                for email in sorted_emails[:20]:  # Show top 20
                    render_email_card(email, category)
            else:
                st.info(f"No {category.lower()} emails found")

def render_email_card(email: Dict[str, Any], category: str):
    """Render individual email card"""
    
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            subject = email.get('subject', 'No Subject')
            st.write(f"**{subject}**")
            sender = email.get('sender', 'Unknown')
            st.write(f"From: {sender}")
            
            if email.get('summary'):
                st.write(f"💡 {email['summary']}")
        
        with col2:
            date = email.get('date_received', '')
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                    st.write(f"📅 {date_obj.strftime('%Y-%m-%d')}")
                    st.write(f"⏰ {days_ago} days ago")
                except:
                    st.write(f"📅 {date[:10]}")
            
            # Show confidence if available
            if email.get('confidence_score'):
                confidence = float(email['confidence_score'])
                st.write(f"🎯 Confidence: {confidence:.2f}")
        
        with col3:
            # Action buttons
            if st.button("👁️", key=f"view_{email.get('id')}", help="View details"):
                show_email_details(email)
            
            # Category-specific actions
            if category == 'Application Sent':
                days_since = get_days_since(email.get('date_received'))
                if days_since > 7:
                    st.write("⚠️ Follow up?")
            
            elif category == 'Interview':
                st.write("✉️ Thank you sent?")
            
            elif category == 'Recruiter Response':
                days_since = get_days_since(email.get('date_received'))
                if days_since > 2:
                    st.write("🔔 Needs reply")
        
        st.markdown("---")

def render_timeline_view(emails: List[Dict[str, Any]]):
    """Render timeline view of job search activity"""
    
    st.subheader("📅 Activity Timeline")
    
    if not emails:
        st.info("No emails to display")
        return
    
    # Prepare timeline data
    timeline_data = []
    for email in emails:
        if email.get('date_received'):
            try:
                date = datetime.fromisoformat(email['date_received'].replace('Z', '+00:00'))
                timeline_data.append({
                    'date': date.date(),
                    'category': email.get('category', 'Other'),
                    'subject': email.get('subject', 'No Subject'),
                    'sender': email.get('sender', 'Unknown')
                })
            except:
                continue
    
    if not timeline_data:
        st.info("No dated emails found")
        return
    
    # Create timeline chart
    df = pd.DataFrame(timeline_data)
    
    # Group by date and category
    daily_counts = df.groupby(['date', 'category']).size().reset_index(name='count')
    
    # Create stacked bar chart
    fig = px.bar(
        daily_counts,
        x='date',
        y='count',
        color='category',
        title='Daily Email Activity',
        labels={'count': 'Number of Emails', 'date': 'Date'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Emails",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity list
    st.markdown("### 📋 Recent Activity (Last 7 Days)")
    
    recent_date = datetime.now().date() - timedelta(days=7)
    recent_emails = [item for item in timeline_data if item['date'] >= recent_date]
    
    if recent_emails:
        recent_df = pd.DataFrame(recent_emails)
        recent_df = recent_df.sort_values('date', ascending=False)
        
        for _, row in recent_df.head(10).iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**{row['subject'][:40]}...**" if len(row['subject']) > 40 else f"**{row['subject']}**")
            
            with col2:
                st.write(f"{row['category']} • {row['sender'][:30]}")
            
            with col3:
                st.write(f"{row['date']}")
    else:
        st.info("No recent activity")

def render_action_items(emails: List[Dict[str, Any]]):
    """Render suggested action items"""
    
    st.subheader("🎯 Suggested Actions")
    
    actions = generate_action_items(emails)
    
    if not actions:
        st.success("🎉 All caught up! No immediate actions needed.")
        return
    
    # Priority actions
    high_priority = [a for a in actions if a.get('priority') == 'high']
    medium_priority = [a for a in actions if a.get('priority') == 'medium']
    low_priority = [a for a in actions if a.get('priority') == 'low']
    
    if high_priority:
        st.markdown("### 🔴 High Priority")
        for action in high_priority:
            render_action_card(action, "error")
    
    if medium_priority:
        st.markdown("### 🟡 Medium Priority")
        for action in medium_priority:
            render_action_card(action, "warning")
    
    if low_priority:
        st.markdown("### 🟢 Low Priority")
        for action in low_priority:
            render_action_card(action, "info")

def render_action_card(action: Dict[str, Any], alert_type: str):
    """Render individual action item card"""
    
    with st.container():
        if alert_type == "error":
            st.error(f"**{action['action']}**\n\n{action['reasoning']}\n\n*{action.get('days_since', 0)} days ago*")
        elif alert_type == "warning":
            st.warning(f"**{action['action']}**\n\n{action['reasoning']}\n\n*{action.get('days_since', 0)} days ago*")
        else:
            st.info(f"**{action['action']}**\n\n{action['reasoning']}\n\n*{action.get('days_since', 0)} days ago*")

def generate_action_items(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate action items based on email analysis"""
    
    actions = []
    now = datetime.now()
    
    for email in emails:
        if not email.get('date_received'):
            continue
        
        try:
            email_date = datetime.fromisoformat(email['date_received'].replace('Z', '+00:00'))
            days_ago = (now - email_date).days
            category = email.get('category', '')
            
            # Follow-up rules
            if category == 'Application Sent' and days_ago >= 7:
                actions.append({
                    'action': f"Follow up on application: {email.get('subject', '')[:50]}",
                    'reasoning': 'No response received after 1 week',
                    'priority': 'medium',
                    'days_since': days_ago,
                    'email_id': email.get('id')
                })
            
            elif category == 'Interview' and days_ago >= 1:
                actions.append({
                    'action': f"Send thank you note: {email.get('subject', '')[:50]}",
                    'reasoning': 'Interview follow-up is important',
                    'priority': 'high',
                    'days_since': days_ago,
                    'email_id': email.get('id')
                })
            
            elif category == 'Recruiter Response' and days_ago >= 2:
                actions.append({
                    'action': f"Respond to recruiter: {email.get('subject', '')[:50]}",
                    'reasoning': 'Recruiter responses should be timely',
                    'priority': 'high',
                    'days_since': days_ago,
                    'email_id': email.get('id')
                })
        
        except Exception:
            continue
    
    # Sort by priority and days
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    actions.sort(key=lambda x: (priority_order.get(x['priority'], 3), -x['days_since']))
    
    return actions[:10]  # Top 10 actions

def show_email_details(email: Dict[str, Any]):
    """Show email details in modal"""
    
    with st.expander(f"📧 Email Details: {email.get('subject', 'No Subject')}", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**From:** {email.get('sender', 'Unknown')}")
            st.write(f"**To:** {email.get('recipient', 'Unknown')}")
            st.write(f"**Category:** {email.get('category', 'Other')}")
        
        with col2:
            st.write(f"**Date:** {email.get('date_received', 'Unknown')[:10]}")
            st.write(f"**Confidence:** {email.get('confidence_score', 'N/A')}")
            st.write(f"**Account:** {email.get('account_email', 'Unknown')}")
        
        if email.get('summary'):
            st.write(f"**Summary:** {email['summary']}")
        
        if email.get('snippet'):
            st.write("**Content Preview:**")
            st.text_area("", email['snippet'], height=100, disabled=True)

def get_days_since(date_str: str) -> int:
    """Calculate days since a date string"""
    
    if not date_str:
        return 0
    
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return (datetime.now(date_obj.tzinfo) - date_obj).days
    except:
        return 0
