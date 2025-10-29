"""
Email viewer component for Streamlit
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# API Configuration
API_BASE_URL = "http://localhost:8000"

def render_email_viewer():
    """Render email viewer interface"""
    
    st.header("📋 Email Viewer")
    st.markdown("Browse and search through your processed emails with detailed views.")
    
    # Search and filter controls
    render_search_filters()
    
    # Get emails based on filters
    emails = get_filtered_emails()
    
    if not emails:
        st.info("No emails found. Try adjusting your filters or upload some emails first.")
        return
    
    # Email list and details
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_email_list(emails)
    
    with col2:
        render_email_details()

def render_search_filters():
    """Render search and filter controls"""
    
    with st.expander("🔍 Search & Filters", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Text search
            search_query = st.text_input(
                "Search emails",
                placeholder="Enter keywords, sender, or subject...",
                key="email_search"
            )
            
            # Date range
            st.write("**Date Range:**")
            date_option = st.selectbox(
                "Select range",
                ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom range"],
                key="date_range"
            )
            
            if date_option == "Custom range":
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("From", key="start_date")
                with col_end:
                    end_date = st.date_input("To", key="end_date")
        
        with col2:
            # Category filter
            categories = [
                "All Categories",
                "Application Sent",
                "Recruiter Response", 
                "Interview",
                "Offer",
                "Rejection",
                "Other"
            ]
            
            selected_category = st.selectbox(
                "Category",
                categories,
                key="category_filter"
            )
            
            # Account filter
            accounts = get_available_accounts()
            if accounts:
                selected_account = st.selectbox(
                    "Account",
                    ["All Accounts"] + accounts,
                    key="account_filter"
                )
            
            # Confidence filter
            min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                key="confidence_filter",
                help="Filter by classification confidence score"
            )
        
        # Sort options
        col1, col2 = st.columns(2)
        
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ["Date (newest first)", "Date (oldest first)", "Subject", "Sender", "Confidence"],
                key="sort_by"
            )
        
        with col2:
            # Results per page
            per_page = st.selectbox(
                "Results per page",
                [10, 25, 50, 100],
                index=1,
                key="per_page"
            )

def get_filtered_emails() -> List[Dict[str, Any]]:
    """Get emails based on current filters"""
    
    try:
        # Build query parameters
        params = {
            'limit': st.session_state.get('per_page', 25),
            'offset': st.session_state.get('email_offset', 0)
        }
        
        # Category filter
        category = st.session_state.get('category_filter', 'All Categories')
        if category != 'All Categories':
            params['category'] = category
        
        # Account filter
        account = st.session_state.get('account_filter', 'All Accounts')
        if account != 'All Accounts':
            params['account'] = account
        
        # API call
        response = requests.get(f"{API_BASE_URL}/emails", params=params)
        
        if response.status_code == 200:
            data = response.json()
            emails = data.get('emails', [])
            
            # Apply client-side filters
            filtered_emails = apply_client_filters(emails)
            
            return filtered_emails
        
        return []
    
    except Exception as e:
        st.error(f"Error loading emails: {e}")
        return []

def apply_client_filters(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply client-side filters"""
    
    filtered = emails
    
    # Text search
    search_query = st.session_state.get('email_search', '').lower()
    if search_query:
        filtered = [
            email for email in filtered
            if (search_query in email.get('subject', '').lower() or
                search_query in email.get('sender', '').lower() or
                search_query in email.get('snippet', '').lower())
        ]
    
    # Confidence filter
    min_confidence = st.session_state.get('confidence_filter', 0.0)
    if min_confidence > 0:
        filtered = [
            email for email in filtered
            if float(email.get('confidence_score', 0)) >= min_confidence
        ]
    
    # Date range filter
    date_option = st.session_state.get('date_range', 'All time')
    if date_option != 'All time':
        filtered = filter_by_date_range(filtered, date_option)
    
    # Sort emails
    sort_by = st.session_state.get('sort_by', 'Date (newest first)')
    filtered = sort_emails(filtered, sort_by)
    
    return filtered

def filter_by_date_range(emails: List[Dict[str, Any]], date_option: str) -> List[Dict[str, Any]]:
    """Filter emails by date range"""
    
    now = datetime.now()
    
    if date_option == "Last 7 days":
        cutoff = now - pd.Timedelta(days=7)
    elif date_option == "Last 30 days":
        cutoff = now - pd.Timedelta(days=30)
    elif date_option == "Last 90 days":
        cutoff = now - pd.Timedelta(days=90)
    elif date_option == "Custom range":
        start_date = st.session_state.get('start_date')
        end_date = st.session_state.get('end_date')
        if start_date and end_date:
            return [
                email for email in emails
                if email.get('date_received') and
                start_date <= datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')).date() <= end_date
            ]
        return emails
    else:
        return emails
    
    return [
        email for email in emails
        if email.get('date_received') and
        datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')) >= cutoff
    ]

def sort_emails(emails: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort emails based on criteria"""
    
    if sort_by == "Date (newest first)":
        return sorted(emails, key=lambda x: x.get('date_received', ''), reverse=True)
    elif sort_by == "Date (oldest first)":
        return sorted(emails, key=lambda x: x.get('date_received', ''))
    elif sort_by == "Subject":
        return sorted(emails, key=lambda x: x.get('subject', '').lower())
    elif sort_by == "Sender":
        return sorted(emails, key=lambda x: x.get('sender', '').lower())
    elif sort_by == "Confidence":
        return sorted(emails, key=lambda x: float(x.get('confidence_score', 0)), reverse=True)
    
    return emails

def get_available_accounts() -> List[str]:
    """Get list of available email accounts"""
    
    try:
        response = requests.get(f"{API_BASE_URL}/emails", params={'limit': 1000})
        if response.status_code == 200:
            emails = response.json().get('emails', [])
            accounts = list(set(email.get('account_email', '') for email in emails if email.get('account_email')))
            return sorted(accounts)
        return []
    except:
        return []

def render_email_list(emails: List[Dict[str, Any]]):
    """Render list of emails"""
    
    st.subheader(f"📧 Emails ({len(emails)})")
    
    # Pagination
    per_page = st.session_state.get('per_page', 25)
    current_page = st.session_state.get('email_page', 0)
    total_pages = (len(emails) - 1) // per_page + 1
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("← Previous", disabled=current_page == 0):
                st.session_state.email_page = current_page - 1
                st.rerun()
        
        with col2:
            st.write(f"Page {current_page + 1} of {total_pages}")
        
        with col3:
            if st.button("Next →", disabled=current_page == total_pages - 1):
                st.session_state.email_page = current_page + 1
                st.rerun()
    
    # Email items
    start_idx = current_page * per_page
    end_idx = start_idx + per_page
    page_emails = emails[start_idx:end_idx]
    
    for i, email in enumerate(page_emails):
        render_email_list_item(email, start_idx + i)

def render_email_list_item(email: Dict[str, Any], index: int):
    """Render individual email list item"""
    
    # Create a unique key for this email
    email_key = f"email_{email.get('id', index)}"
    
    # Check if this email is selected
    selected_email_key = st.session_state.get('selected_email', None)
    is_selected = selected_email_key == email_key
    
    # Email card
    with st.container():
        
        # Category badge
        category = email.get('category', 'Other')
        category_class = category.lower().replace(' ', '')
        
        # Date formatting
        date_str = ""
        if email.get('date_received'):
            try:
                date_obj = datetime.fromisoformat(email['date_received'].replace('Z', '+00:00'))
                date_str = date_obj.strftime('%m/%d')
            except:
                date_str = email['date_received'][:10]
        
        # Subject truncation
        subject = email.get('subject', 'No Subject')
        if len(subject) > 40:
            subject = subject[:40] + "..."
        
        # Sender truncation
        sender = email.get('sender', 'Unknown')
        if len(sender) > 30:
            sender = sender[:30] + "..."
        
        # Click handler
        if st.button(
            f"{'🔵' if is_selected else '⚪'} **{subject}**\n{sender} • {date_str} • {category}",
            key=f"select_{email_key}",
            use_container_width=True,
            help="Click to view details"
        ):
            st.session_state.selected_email = email_key
            st.session_state.selected_email_data = email
            st.rerun()
        
        # Show snippet for selected email
        if is_selected and email.get('snippet'):
            st.markdown(f"*{email['snippet'][:100]}...*")
        
        st.markdown("---")

def render_email_details():
    """Render detailed view of selected email"""
    
    selected_email = st.session_state.get('selected_email_data')
    
    if not selected_email:
        st.info("👈 Select an email from the list to view details")
        return
    
    st.subheader("📧 Email Details")
    
    # Header info
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Subject:** {selected_email.get('subject', 'No Subject')}")
            st.markdown(f"**From:** {selected_email.get('sender', 'Unknown')}")
            st.markdown(f"**To:** {selected_email.get('recipient', 'Unknown')}")
        
        with col2:
            # Date
            if selected_email.get('date_received'):
                try:
                    date_obj = datetime.fromisoformat(selected_email['date_received'].replace('Z', '+00:00'))
                    st.markdown(f"**Date:** {date_obj.strftime('%Y-%m-%d %H:%M')}")
                except:
                    st.markdown(f"**Date:** {selected_email['date_received'][:10]}")
            
            # Category with confidence
            category = selected_email.get('category', 'Other')
            confidence = selected_email.get('confidence_score', 'N/A')
            st.markdown(f"**Category:** {category}")
            if confidence != 'N/A':
                st.markdown(f"**Confidence:** {float(confidence):.2f}")
    
    st.markdown("---")
    
    # AI Summary
    if selected_email.get('summary'):
        st.markdown("### 🤖 AI Summary")
        st.info(selected_email['summary'])
    
    # Email content
    st.markdown("### 📄 Content")
    
    # Show snippet or body
    content = selected_email.get('body') or selected_email.get('snippet', 'No content available')
    
    # Clean up content for display
    content = clean_email_content(content)
    
    # Content tabs
    tab1, tab2 = st.tabs(["Formatted", "Raw"])
    
    with tab1:
        # Formatted content
        st.markdown(content)
    
    with tab2:
        # Raw content
        st.text_area("Raw Content", content, height=300, disabled=True)
    
    # Actions
    st.markdown("### 🛠️ Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Reclassify", help="Reclassify this email"):
            reclassify_email(selected_email)
    
    with col2:
        if st.button("🔍 Find Similar", help="Find similar emails"):
            find_similar_emails(selected_email)
    
    with col3:
        if st.button("📋 Copy Content", help="Copy email content"):
            st.code(content, language="text")
    
    with col4:
        if st.button("🗑️ Delete", help="Delete this email", type="secondary"):
            if st.session_state.get('confirm_delete'):
                delete_email(selected_email)
            else:
                st.session_state.confirm_delete = True
                st.warning("Click again to confirm deletion")
    
    # Key information extraction
    if st.checkbox("🔍 Extract Key Information", help="Extract structured information from this email"):
        extract_key_information(selected_email)

def clean_email_content(content: str) -> str:
    """Clean email content for display"""
    
    if not content:
        return "No content available"
    
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r' +', ' ', content)
    
    # Basic HTML removal (if any)
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove common email artifacts
    content = re.sub(r'--\s*Original Message\s*--.*', '', content, flags=re.DOTALL)
    content = re.sub(r'On.*wrote:.*', '', content, flags=re.DOTALL)
    
    return content.strip()

def reclassify_email(email: Dict[str, Any]):
    """Reclassify an email"""
    
    try:
        email_content = f"{email.get('subject', '')} {email.get('snippet', '')}"
        
        response = requests.post(
            f"{API_BASE_URL}/emails/classify",
            json={"email_content": email_content}
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"Reclassified as: {result.get('category', 'Unknown')}")
            st.json(result)
        else:
            st.error("Reclassification failed")
    
    except Exception as e:
        st.error(f"Error: {e}")

def find_similar_emails(email: Dict[str, Any]):
    """Find similar emails"""
    
    try:
        # Use RAG search to find similar emails
        query = f"{email.get('subject', '')} {email.get('snippet', '')}"[:100]
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query, "limit": 5}
        )
        
        if response.status_code == 200:
            result = response.json()
            similar_emails = result.get('sources', [])
            
            if similar_emails:
                st.markdown("### 🔍 Similar Emails")
                for similar in similar_emails:
                    with st.expander(f"Similarity: {similar.get('similarity_score', 0):.2f}"):
                        st.write(similar.get('content', 'No content'))
                        st.json(similar.get('metadata', {}))
            else:
                st.info("No similar emails found")
        else:
            st.error("Search failed")
    
    except Exception as e:
        st.error(f"Error: {e}")

def delete_email(email: Dict[str, Any]):
    """Delete an email"""
    
    try:
        email_id = email.get('id')
        if email_id:
            response = requests.delete(f"{API_BASE_URL}/emails/{email_id}")
            
            if response.status_code == 200:
                st.success("Email deleted successfully")
                st.session_state.selected_email = None
                st.session_state.selected_email_data = None
                st.session_state.confirm_delete = False
                st.rerun()
            else:
                st.error("Deletion failed")
        else:
            st.error("Cannot delete: No email ID")
    
    except Exception as e:
        st.error(f"Error: {e}")

def extract_key_information(email: Dict[str, Any]):
    """Extract key information from email"""
    
    try:
        # This would call the LLM to extract structured information
        content = email.get('snippet', '') or email.get('body', '')
        
        # For now, show a simple analysis
        st.markdown("### 📊 Extracted Information")
        
        # Basic analysis
        info = {
            "Word Count": len(content.split()),
            "Character Count": len(content),
            "Contains Phone": bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)),
            "Contains Email": bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
            "Contains URL": bool(re.search(r'http[s]?://\S+', content)),
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            for key, value in list(info.items())[:3]:
                st.metric(key, value)
        
        with col2:
            for key, value in list(info.items())[3:]:
                st.metric(key, "Yes" if value else "No")
        
        # Keywords
        words = content.lower().split()
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        if keywords:
            from collections import Counter
            keyword_counts = Counter(keywords).most_common(10)
            
            st.markdown("**Top Keywords:**")
            for word, count in keyword_counts:
                st.write(f"• {word}: {count}")
    
    except Exception as e:
        st.error(f"Information extraction failed: {e}")
