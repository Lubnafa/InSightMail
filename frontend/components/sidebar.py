"""
Streamlit sidebar component
"""
import streamlit as st

def render_sidebar() -> str:
    """Render sidebar navigation"""
    
    with st.sidebar:
        st.title("📧 InSightMail")
        st.markdown("---")
        
        # Navigation
        pages = [
            "Dashboard",
            "Email Upload", 
            "Job Pipeline",
            "Email Viewer",
            "Ask My Inbox",
            "Analytics"
        ]
        
        # Page icons
        page_icons = {
            "Dashboard": "📊",
            "Email Upload": "📤",
            "Job Pipeline": "🔄", 
            "Email Viewer": "📋",
            "Ask My Inbox": "🔍",
            "Analytics": "📈"
        }
        
        selected_page = st.radio(
            "Navigation",
            pages,
            format_func=lambda x: f"{page_icons.get(x, '📄')} {x}",
            key="nav_radio"
        )
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        
        # Add some placeholder metrics that will be updated
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Today", "0", delta="0")
        with col2:
            st.metric("This Week", "0", delta="0")
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Settings")
        
        # Theme toggle (placeholder)
        st.checkbox("Dark Mode", value=False, disabled=True, help="Coming soon!")
        
        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        if auto_refresh:
            st.text("Refreshing every 30s")
        
        # Model selection
        st.selectbox(
            "LLM Model",
            ["mistral:7b", "phi3:mini", "llama3.2:3b"],
            index=0,
            help="Select which local model to use"
        )
        
        st.markdown("---")
        
        # Help section
        with st.expander("📖 Help & Tips"):
            st.markdown("""
            **Getting Started:**
            1. Upload Gmail exports via "Email Upload"
            2. Wait for processing to complete
            3. View results in "Job Pipeline"
            4. Use "Ask My Inbox" to search
            
            **Tips:**
            - Upload multiple Gmail accounts
            - Check "Analytics" for insights
            - Use specific keywords in search
            """)
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #666; font-size: 0.8em;'>
                InSightMail v1.0<br>
                🤖 Powered by Local AI
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        return selected_page

