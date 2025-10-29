"""
RAG search component for "Ask My Inbox" functionality
"""
import streamlit as st
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.express as px

# API Configuration
API_BASE_URL = "http://localhost:8000"

def render_rag_search():
    """Render RAG search interface"""
    
    st.header("🔍 Ask My Inbox")
    st.markdown("Search through your emails using natural language queries powered by AI.")
    
    # Initialize session state
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    # Quick start examples
    render_example_queries()
    
    # Main search interface
    render_search_interface()
    
    # Search results
    if st.session_state.search_results:
        render_search_results()
    
    # Search history
    render_search_history()

def render_example_queries():
    """Render example query suggestions"""
    
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        **Try these example queries:**
        
        **Job Search Progress:**
        - "How many interviews did I have this month?"
        - "Show me all rejection emails"
        - "What companies have I applied to?"
        - "Find emails about salary negotiations"
        
        **Follow-ups:**
        - "Which applications need follow-up?"
        - "Show me unanswered recruiter emails"
        - "Find interviews from last week"
        
        **Company Research:**
        - "What did Google recruiters say?"  
        - "Show me all emails from tech companies"
        - "Find emails mentioning remote work"
        
        **Timeline & Analysis:**
        - "What happened in my job search this week?"
        - "Show me my interview performance feedback"
        - "Find emails about job offers"
        """)
        
        # Quick query buttons
        st.markdown("**Quick Queries:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Job search summary", key="quick_summary"):
                run_search("Summarize my job search progress this month")
        
        with col2:
            if st.button("📧 Pending follow-ups", key="quick_followups"):
                run_search("Which emails need follow-up or response?")
        
        with col3:
            if st.button("🎯 Recent interviews", key="quick_interviews"):
                run_search("Show me interview emails from the last 30 days")

def render_search_interface():
    """Render main search interface"""
    
    st.subheader("🔎 Search Your Emails")
    
    # Search input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "",
            placeholder="Ask anything about your job search emails...",
            key="search_query",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Search on Enter or button click
    if search_button or (query and st.session_state.get('last_query') != query):
        if query.strip():
            run_search(query)
            st.session_state.last_query = query
    
    # Advanced search options
    with st.expander("⚙️ Advanced Options", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_results = st.slider(
                "Number of results",
                min_value=5,
                max_value=50,
                value=10,
                key="num_results"
            )
            
            search_type = st.selectbox(
                "Search type",
                ["Semantic (AI-powered)", "Keyword matching", "Hybrid"],
                index=0,
                key="search_type"
            )
        
        with col2:
            category_filter = st.multiselect(
                "Filter by category",
                ["Application Sent", "Recruiter Response", "Interview", "Offer", "Rejection", "Other"],
                key="category_filter"
            )
            
            date_range = st.selectbox(
                "Date range",
                ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "This year"],
                key="date_range_filter"
            )

def run_search(query: str):
    """Execute search query"""
    
    with st.spinner("🔍 Searching your emails..."):
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "limit": st.session_state.get('num_results', 10)
            }
            
            # Add filters if specified
            if st.session_state.get('category_filter'):
                search_params['categories'] = st.session_state.category_filter
            
            # Make API call
            response = requests.post(
                f"{API_BASE_URL}/query",
                json=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Store results and add to history
                st.session_state.search_results = results
                add_to_search_history(query, results)
                
                st.success(f"✅ Found {len(results.get('sources', []))} relevant emails")
                
            else:
                st.error(f"Search failed: HTTP {response.status_code}")
                st.session_state.search_results = None
        
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            st.session_state.search_results = None

def render_search_results():
    """Render search results"""
    
    results = st.session_state.search_results
    
    if not results:
        return
    
    st.subheader("🎯 Search Results")
    
    # AI-generated answer
    if results.get('answer'):
        st.markdown("### 🤖 AI Answer")
        st.info(results['answer'])
        st.markdown("---")
    
    # Source emails
    sources = results.get('sources', [])
    
    if not sources:
        st.warning("No relevant emails found")
        return
    
    st.markdown(f"### 📧 Relevant Emails ({len(sources)})")
    
    # Results display options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        view_mode = st.radio(
            "View mode",
            ["Detailed", "Compact", "List only"],
            horizontal=True,
            key="results_view_mode"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Relevance", "Date", "Category"],
            key="results_sort"
        )
    
    # Sort results
    if sort_by == "Date":
        sources = sorted(sources, key=lambda x: x.get('metadata', {}).get('date', ''), reverse=True)
    elif sort_by == "Category":
        sources = sorted(sources, key=lambda x: x.get('metadata', {}).get('category', ''))
    # Relevance is default order from API
    
    # Display results
    for i, source in enumerate(sources):
        render_search_result(source, i, view_mode)
    
    # Export results
    if st.button("📥 Export Results", help="Export search results as JSON"):
        export_search_results(results)

def render_search_result(source: Dict[str, Any], index: int, view_mode: str):
    """Render individual search result"""
    
    metadata = source.get('metadata', {})
    content = source.get('content', 'No content')
    similarity = source.get('similarity_score', 0)
    
    # Create expandable result
    with st.expander(
        f"📧 {metadata.get('subject', 'No Subject')[:60]}... (Relevance: {similarity:.2f})",
        expanded=(view_mode == "Detailed" and index < 3)
    ):
        
        # Metadata row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**From:** {metadata.get('sender', 'Unknown')}")
            st.write(f"**Category:** {metadata.get('category', 'Other')}")
        
        with col2:
            date = metadata.get('date', '')
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    st.write(f"**Date:** {date_obj.strftime('%Y-%m-%d')}")
                except:
                    st.write(f"**Date:** {date[:10]}")
            
            st.write(f"**Account:** {metadata.get('account', 'Unknown')}")
        
        with col3:
            st.metric("Relevance", f"{similarity:.2f}")
            
            # Quick actions
            if st.button("🔍 View Full", key=f"view_full_{index}"):
                view_full_email(metadata.get('email_id'))
        
        # Content preview
        if view_mode in ["Detailed", "Compact"]:
            st.markdown("**Content:**")
            
            # Highlight search terms (basic implementation)
            query = st.session_state.search_results.get('query', '')
            highlighted_content = highlight_search_terms(content, query)
            
            if view_mode == "Detailed":
                st.markdown(highlighted_content)
            else:
                # Compact view - show first 200 chars
                st.markdown(highlighted_content[:200] + "..." if len(highlighted_content) > 200 else highlighted_content)
        
        st.markdown("---")

def highlight_search_terms(content: str, query: str) -> str:
    """Highlight search terms in content"""
    
    if not query or len(query) < 3:
        return content
    
    # Simple highlighting - in a real app, you'd want more sophisticated highlighting
    import re
    
    # Extract meaningful words from query
    query_words = [word.strip().lower() for word in query.split() if len(word) > 2]
    
    highlighted = content
    for word in query_words:
        # Case-insensitive replacement with highlighting
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        highlighted = pattern.sub(f"**{word.upper()}**", highlighted)
    
    return highlighted

def add_to_search_history(query: str, results: Dict[str, Any]):
    """Add search to history"""
    
    search_entry = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'num_results': len(results.get('sources', [])),
        'has_answer': bool(results.get('answer'))
    }
    
    # Add to beginning of history
    st.session_state.search_history.insert(0, search_entry)
    
    # Keep only last 20 searches
    st.session_state.search_history = st.session_state.search_history[:20]

def render_search_history():
    """Render search history"""
    
    if not st.session_state.search_history:
        return
    
    with st.expander(f"📚 Search History ({len(st.session_state.search_history)})", expanded=False):
        
        for i, search in enumerate(st.session_state.search_history):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Make search clickable to re-run
                if st.button(
                    f"🔍 {search['query']}",
                    key=f"history_{i}",
                    help="Click to re-run this search"
                ):
                    run_search(search['query'])
            
            with col2:
                try:
                    timestamp = datetime.fromisoformat(search['timestamp'])
                    st.write(timestamp.strftime('%m/%d %H:%M'))
                except:
                    st.write("Recent")
            
            with col3:
                st.write(f"{search['num_results']} results")
        
        # Clear history
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.search_history = []
            st.rerun()

def view_full_email(email_id: Optional[str]):
    """View full email details"""
    
    if not email_id:
        st.error("Cannot view email: No ID provided")
        return
    
    try:
        response = requests.get(f"{API_BASE_URL}/emails", params={'email_id': email_id})
        
        if response.status_code == 200:
            emails = response.json().get('emails', [])
            if emails:
                email = emails[0]
                
                # Store in session state for email viewer
                st.session_state.selected_email_data = email
                st.session_state.current_page = "Email Viewer"
                
                st.success("Switching to Email Viewer...")
                st.rerun()
            else:
                st.error("Email not found")
        else:
            st.error("Failed to load email")
    
    except Exception as e:
        st.error(f"Error loading email: {e}")

def export_search_results(results: Dict[str, Any]):
    """Export search results"""
    
    try:
        # Prepare export data
        export_data = {
            'query': results.get('query', ''),
            'timestamp': datetime.now().isoformat(),
            'answer': results.get('answer', ''),
            'num_sources': len(results.get('sources', [])),
            'sources': []
        }
        
        # Add source data
        for source in results.get('sources', []):
            export_data['sources'].append({
                'content': source.get('content', ''),
                'metadata': source.get('metadata', {}),
                'similarity_score': source.get('similarity_score', 0)
            })
        
        # Convert to JSON
        json_str = json.dumps(export_data, indent=2)
        
        # Provide download
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.success("✅ Export ready for download!")
    
    except Exception as e:
        st.error(f"Export failed: {e}")

def render_search_analytics():
    """Render search analytics (if enough history)"""
    
    history = st.session_state.search_history
    
    if len(history) < 5:
        return
    
    with st.expander("📊 Search Analytics", expanded=False):
        
        # Query patterns
        all_queries = [search['query'].lower() for search in history]
        
        # Word frequency
        from collections import Counter
        all_words = []
        for query in all_queries:
            words = [word for word in query.split() if len(word) > 2]
            all_words.extend(words)
        
        if all_words:
            word_counts = Counter(all_words).most_common(10)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Most Searched Terms:**")
                for word, count in word_counts:
                    st.write(f"• {word}: {count}")
            
            with col2:
                # Simple bar chart
                if len(word_counts) > 0:
                    words, counts = zip(*word_counts)
                    
                    import pandas as pd
                    df = pd.DataFrame({'Word': words, 'Count': counts})
                    
                    fig = px.bar(df, x='Word', y='Count', title='Search Term Frequency')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Search success rate
        successful_searches = len([s for s in history if s['num_results'] > 0])
        success_rate = (successful_searches / len(history)) * 100
        
        st.metric("Search Success Rate", f"{success_rate:.1f}%")

# Add analytics to the main render function
def render_rag_search():
    """Render RAG search interface"""
    
    st.header("🔍 Ask My Inbox")
    st.markdown("Search through your emails using natural language queries powered by AI.")
    
    # Initialize session state
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    # Quick start examples
    render_example_queries()
    
    # Main search interface
    render_search_interface()
    
    # Search results
    if st.session_state.search_results:
        render_search_results()
    
    # Search history and analytics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_search_history()
    
    with col2:
        render_search_analytics()
