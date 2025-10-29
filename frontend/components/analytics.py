"""
Analytics and insights component for job search data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np

# API Configuration
API_BASE_URL = "http://localhost:8000"

def render_analytics():
    """Render analytics dashboard"""
    
    st.header("📈 Job Search Analytics")
    st.markdown("Deep insights into your job search performance and trends.")
    
    # Load data
    emails = load_email_data()
    if not emails:
        st.info("No data available for analysis. Upload some emails first!")
        return
    
    # Time period selector
    time_period = render_time_selector()
    
    # Filter emails by time period
    filtered_emails = filter_emails_by_period(emails, time_period)
    
    if not filtered_emails:
        st.warning(f"No emails found in the selected time period ({time_period})")
        return
    
    # Main analytics sections
    render_overview_metrics(filtered_emails)
    render_trend_analysis(filtered_emails)
    render_category_analysis(filtered_emails)
    render_performance_metrics(filtered_emails)
    render_company_analysis(filtered_emails)
    render_timing_analysis(filtered_emails)
    render_predictive_insights(filtered_emails)

def load_email_data() -> List[Dict[str, Any]]:
    """Load all email data"""
    try:
        response = requests.get(f"{API_BASE_URL}/emails", params={'limit': 1000})
        if response.status_code == 200:
            return response.json().get('emails', [])
        return []
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return []

def render_time_selector() -> str:
    """Render time period selector"""
    
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        time_period = st.selectbox(
            "📅 Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All time"],
            index=2  # Default to last 90 days
        )
    
    with col2:
        # Custom date range option
        if st.checkbox("Custom range"):
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=90))
            end_date = st.date_input("To", value=datetime.now())
            time_period = f"Custom: {start_date} to {end_date}"
    
    with col3:
        # Refresh data button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    return time_period

def filter_emails_by_period(emails: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
    """Filter emails by time period"""
    
    if period == "All time":
        return emails
    
    now = datetime.now()
    
    if period == "Last 7 days":
        cutoff = now - timedelta(days=7)
    elif period == "Last 30 days":
        cutoff = now - timedelta(days=30)
    elif period == "Last 90 days":
        cutoff = now - timedelta(days=90)
    elif period == "Last 6 months":
        cutoff = now - timedelta(days=180)
    elif period == "Last year":
        cutoff = now - timedelta(days=365)
    elif period.startswith("Custom:"):
        # Handle custom date range
        try:
            date_part = period.replace("Custom: ", "")
            start_str, end_str = date_part.split(" to ")
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
            
            return [
                email for email in emails
                if email.get('date_received') and
                start_date <= datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')) <= end_date
            ]
        except:
            return emails
    else:
        return emails
    
    return [
        email for email in emails
        if email.get('date_received') and
        datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')) >= cutoff
    ]

def render_overview_metrics(emails: List[Dict[str, Any]]):
    """Render overview metrics"""
    
    st.subheader("📊 Overview Metrics")
    
    # Calculate key metrics
    total_emails = len(emails)
    categories = {}
    for email in emails:
        category = email.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    applications = categories.get('Application Sent', 0)
    responses = categories.get('Recruiter Response', 0)
    interviews = categories.get('Interview', 0)
    offers = categories.get('Offer', 0)
    rejections = categories.get('Rejection', 0)
    
    # Display metrics in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📧 Total Emails", total_emails)
        st.metric("📤 Applications", applications)
    
    with col2:
        response_rate = (responses/applications*100) if applications > 0 else 0
        st.metric("💬 Responses", responses, delta=f"{response_rate:.1f}%")
    
    with col3:
        interview_rate = (interviews/applications*100) if applications > 0 else 0
        st.metric("🎯 Interviews", interviews, delta=f"{interview_rate:.1f}%")
    
    with col4:
        offer_rate = (offers/applications*100) if applications > 0 else 0
        st.metric("🎉 Offers", offers, delta=f"{offer_rate:.1f}%")
    
    with col5:
        rejection_rate = (rejections/applications*100) if applications > 0 else 0
        st.metric("❌ Rejections", rejections, delta=f"{rejection_rate:.1f}%")
    
    # Conversion funnel visualization
    st.markdown("### 🔄 Conversion Funnel")
    
    funnel_data = [
        ('Applications Sent', applications, '#1f77b4'),
        ('Responses Received', responses, '#ff7f0e'),
        ('Interviews Scheduled', interviews, '#2ca02c'),
        ('Offers Received', offers, '#d62728')
    ]
    
    fig = go.Figure()
    
    for i, (stage, count, color) in enumerate(funnel_data):
        percentage = (count/applications*100) if applications > 0 else 0
        
        fig.add_trace(go.Funnel(
            y=[stage],
            x=[count],
            textinfo="value+percent initial",
            textposition="inside",
            marker=dict(color=color),
            connector=dict(line=dict(color='rgb(63, 63, 63)', dash='dot', width=3))
        ))
    
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def render_trend_analysis(emails: List[Dict[str, Any]]):
    """Render trend analysis"""
    
    st.subheader("📈 Trend Analysis")
    
    # Prepare time series data
    email_df = pd.DataFrame(emails)
    if email_df.empty or 'date_received' not in email_df.columns:
        st.info("No date information available for trend analysis")
        return
    
    # Convert dates
    email_df['date'] = pd.to_datetime(email_df['date_received'], errors='coerce')
    email_df = email_df.dropna(subset=['date'])
    
    if email_df.empty:
        st.info("No valid dates found for trend analysis")
        return
    
    # Group by date and category
    email_df['date_only'] = email_df['date'].dt.date
    
    # Daily activity
    daily_activity = email_df.groupby(['date_only', 'category']).size().reset_index(name='count')
    
    # Create time series chart
    fig = px.line(
        daily_activity,
        x='date_only',
        y='count',
        color='category',
        title='Daily Email Activity by Category',
        labels={'date_only': 'Date', 'count': 'Number of Emails'}
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Weekly aggregation
    col1, col2 = st.columns(2)
    
    with col1:
        # Weekly totals
        email_df['week'] = email_df['date'].dt.to_period('W')
        weekly_totals = email_df.groupby('week').size()
        
        fig_weekly = px.bar(
            x=[str(w) for w in weekly_totals.index],
            y=weekly_totals.values,
            title='Weekly Email Volume',
            labels={'x': 'Week', 'y': 'Number of Emails'}
        )
        fig_weekly.update_layout(height=300)
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    with col2:
        # Day of week analysis
        email_df['day_of_week'] = email_df['date'].dt.day_name()
        day_counts = email_df['day_of_week'].value_counts()
        
        # Reorder by actual day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = day_counts.reindex([day for day in day_order if day in day_counts.index])
        
        fig_days = px.bar(
            x=day_counts.index,
            y=day_counts.values,
            title='Activity by Day of Week',
            labels={'x': 'Day', 'y': 'Number of Emails'}
        )
        fig_days.update_layout(height=300)
        st.plotly_chart(fig_days, use_container_width=True)

def render_category_analysis(emails: List[Dict[str, Any]]):
    """Render category analysis"""
    
    st.subheader("🏷️ Category Analysis")
    
    # Category distribution
    categories = {}
    for email in emails:
        category = email.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            values=list(categories.values()),
            names=list(categories.keys()),
            title='Email Distribution by Category'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Category performance metrics
        st.markdown("**Category Insights:**")
        
        total_emails = len(emails)
        applications = categories.get('Application Sent', 0)
        
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count/total_emails*100) if total_emails > 0 else 0
            
            # Calculate conversion if it's applications
            conversion_text = ""
            if category == 'Application Sent' and applications > 0:
                responses = categories.get('Recruiter Response', 0)
                interviews = categories.get('Interview', 0)
                conversion_text = f" → {(responses/applications*100):.1f}% response rate"
            
            st.write(f"• **{category}**: {count} ({percentage:.1f}%){conversion_text}")

def render_performance_metrics(emails: List[Dict[str, Any]]):
    """Render performance metrics"""
    
    st.subheader("🎯 Performance Metrics")
    
    # Calculate advanced metrics
    categories = {}
    for email in emails:
        category = email.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    applications = categories.get('Application Sent', 0)
    responses = categories.get('Recruiter Response', 0)
    interviews = categories.get('Interview', 0)
    offers = categories.get('Offer', 0)
    rejections = categories.get('Rejection', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Conversion Rates")
        
        if applications > 0:
            response_rate = responses / applications
            interview_rate = interviews / applications
            offer_rate = offers / applications
            
            # Response rate gauge
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=response_rate * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Response Rate (%)"},
                delta={'reference': 20},  # Industry benchmark
                gauge={
                    'axis': {'range': [None, 50]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 10], 'color': "lightgray"},
                        {'range': [10, 25], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 20
                    }
                }
            ))
            
            fig_gauge.update_layout(height=250)
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("No applications found for conversion analysis")
    
    with col2:
        st.markdown("### ⏱️ Response Times")
        
        # Calculate average response times (simplified)
        response_times = []
        for email in emails:
            if email.get('category') == 'Recruiter Response':
                # This is a simplified calculation
                # In a real app, you'd match responses to applications
                response_times.append(5)  # Placeholder
        
        if response_times:
            avg_response_time = np.mean(response_times)
            st.metric("Avg Response Time", f"{avg_response_time:.1f} days")
            st.metric("Fastest Response", f"{min(response_times)} days")
            st.metric("Slowest Response", f"{max(response_times)} days")
        else:
            st.info("No response time data available")
    
    with col3:
        st.markdown("### 🏆 Success Scores")
        
        # Calculate success score based on various factors
        success_score = 0
        max_score = 100
        
        if applications > 0:
            # Response rate contribution (40 points max)
            response_contribution = min((responses/applications) * 200, 40)
            success_score += response_contribution
            
            # Interview rate contribution (35 points max)
            interview_contribution = min((interviews/applications) * 350, 35)
            success_score += interview_contribution
            
            # Offer rate contribution (25 points max)
            offer_contribution = min((offers/applications) * 500, 25)
            success_score += offer_contribution
        
        st.metric("Overall Success Score", f"{success_score:.0f}/100")
        
        # Success level
        if success_score >= 80:
            st.success("🌟 Excellent performance!")
        elif success_score >= 60:
            st.info("👍 Good performance")
        elif success_score >= 40:
            st.warning("📈 Room for improvement")
        else:
            st.error("🎯 Focus on optimization")

def render_company_analysis(emails: List[Dict[str, Any]]):
    """Render company analysis"""
    
    st.subheader("🏢 Company Analysis")
    
    # Extract companies from email senders
    companies = {}
    company_categories = {}
    
    for email in emails:
        sender = email.get('sender', '')
        category = email.get('category', 'Other')
        
        # Simple company extraction from email domain
        if '@' in sender:
            domain = sender.split('@')[1].lower()
            # Remove common domain parts
            company = domain.replace('.com', '').replace('.org', '').replace('.net', '')
            company = company.replace('mail.', '').replace('www.', '')
            
            if company:
                companies[company] = companies.get(company, 0) + 1
                
                if company not in company_categories:
                    company_categories[company] = {}
                company_categories[company][category] = company_categories[company].get(category, 0) + 1
    
    if not companies:
        st.info("No company data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top companies by email volume
        st.markdown("### 📈 Most Active Companies")
        
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_companies:
            companies_df = pd.DataFrame(top_companies, columns=['Company', 'Emails'])
            
            fig_companies = px.bar(
                companies_df,
                x='Emails',
                y='Company',
                orientation='h',
                title='Email Volume by Company'
            )
            fig_companies.update_layout(height=400)
            st.plotly_chart(fig_companies, use_container_width=True)
    
    with col2:
        # Company engagement analysis
        st.markdown("### 🎯 Company Engagement")
        
        for company, total_emails in top_companies[:5]:
            categories = company_categories.get(company, {})
            
            # Calculate engagement score
            applications = categories.get('Application Sent', 0)
            responses = categories.get('Recruiter Response', 0)
            interviews = categories.get('Interview', 0)
            offers = categories.get('Offer', 0)
            
            engagement_score = 0
            if applications > 0:
                engagement_score = ((responses + interviews * 2 + offers * 3) / applications) * 100
            
            with st.expander(f"{company.title()} ({total_emails} emails)"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write(f"Applications: {applications}")
                    st.write(f"Responses: {responses}")
                
                with col_b:
                    st.write(f"Interviews: {interviews}")
                    st.write(f"Offers: {offers}")
                
                if engagement_score > 0:
                    st.metric("Engagement Score", f"{engagement_score:.1f}")

def render_timing_analysis(emails: List[Dict[str, Any]]):
    """Render timing analysis"""
    
    st.subheader("⏰ Timing Analysis")
    
    email_df = pd.DataFrame(emails)
    if email_df.empty or 'date_received' not in email_df.columns:
        st.info("No timing data available")
        return
    
    # Convert dates
    email_df['date'] = pd.to_datetime(email_df['date_received'], errors='coerce')
    email_df = email_df.dropna(subset=['date'])
    
    if email_df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Hour of day analysis
        email_df['hour'] = email_df['date'].dt.hour
        hourly_activity = email_df.groupby('hour').size()
        
        fig_hourly = px.bar(
            x=hourly_activity.index,
            y=hourly_activity.values,
            title='Email Activity by Hour of Day',
            labels={'x': 'Hour (24-hour format)', 'y': 'Number of Emails'}
        )
        fig_hourly.update_layout(height=300)
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        # Month analysis
        email_df['month'] = email_df['date'].dt.month_name()
        monthly_activity = email_df['month'].value_counts()
        
        # Reorder by calendar months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        monthly_activity = monthly_activity.reindex([m for m in month_order if m in monthly_activity.index])
        
        fig_monthly = px.bar(
            x=monthly_activity.index,
            y=monthly_activity.values,
            title='Email Activity by Month',
            labels={'x': 'Month', 'y': 'Number of Emails'}
        )
        fig_monthly.update_layout(height=300)
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Best times insights
    st.markdown("### 💡 Timing Insights")
    
    # Peak activity hours
    peak_hour = hourly_activity.idxmax()
    peak_count = hourly_activity.max()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Peak Activity Hour", f"{peak_hour}:00", f"{peak_count} emails")
    
    with col2:
        # Business hours activity (9 AM - 5 PM)
        business_hours = hourly_activity[9:17].sum()
        total_emails = hourly_activity.sum()
        business_percentage = (business_hours/total_emails*100) if total_emails > 0 else 0
        st.metric("Business Hours Activity", f"{business_percentage:.1f}%")
    
    with col3:
        # Weekend activity
        weekend_activity = email_df[email_df['date'].dt.dayofweek.isin([5, 6])].shape[0]
        weekend_percentage = (weekend_activity/len(email_df)*100) if len(email_df) > 0 else 0
        st.metric("Weekend Activity", f"{weekend_percentage:.1f}%")

def render_predictive_insights(emails: List[Dict[str, Any]]):
    """Render predictive insights and recommendations"""
    
    st.subheader("🔮 Predictive Insights & Recommendations")
    
    # Calculate trends
    categories = {}
    for email in emails:
        category = email.get('category', 'Other')
        categories[category] = categories.get(category, 0) + 1
    
    applications = categories.get('Application Sent', 0)
    responses = categories.get('Recruiter Response', 0)
    interviews = categories.get('Interview', 0)
    offers = categories.get('Offer', 0)
    rejections = categories.get('Rejection', 0)
    
    # Generate insights
    insights = []
    recommendations = []
    
    # Response rate analysis
    if applications > 0:
        response_rate = responses / applications
        
        if response_rate < 0.1:
            insights.append("🔴 Low response rate detected (< 10%)")
            recommendations.append("• Improve application quality and personalization")
            recommendations.append("• Review job matching criteria")
        elif response_rate > 0.3:
            insights.append("🟢 Excellent response rate (> 30%)")
            recommendations.append("• Continue current application strategy")
    
    # Interview conversion
    if responses > 0:
        interview_conversion = interviews / responses
        
        if interview_conversion < 0.2:
            insights.append("🟡 Low interview conversion from responses")
            recommendations.append("• Improve follow-up timing and quality")
            recommendations.append("• Enhance networking and relationship building")
    
    # Offer conversion
    if interviews > 0:
        offer_conversion = offers / interviews
        
        if offer_conversion < 0.1:
            insights.append("🔴 Low offer conversion from interviews")
            recommendations.append("• Practice interview skills")
            recommendations.append("• Research companies and roles more thoroughly")
        elif offer_conversion > 0.2:
            insights.append("🟢 Strong interview performance")
    
    # Timing insights
    email_df = pd.DataFrame(emails)
    if not email_df.empty and 'date_received' in email_df.columns:
        email_df['date'] = pd.to_datetime(email_df['date_received'], errors='coerce')
        email_df = email_df.dropna(subset=['date'])
        
        if not email_df.empty:
            # Recent activity trend
            last_week = email_df[email_df['date'] >= (datetime.now() - timedelta(days=7))]
            prev_week = email_df[
                (email_df['date'] >= (datetime.now() - timedelta(days=14))) &
                (email_df['date'] < (datetime.now() - timedelta(days=7)))
            ]
            
            if len(last_week) < len(prev_week) * 0.8:
                insights.append("📉 Job search activity has decreased recently")
                recommendations.append("• Increase daily application targets")
                recommendations.append("• Set up job alerts for consistent pipeline")
    
    # Display insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Key Insights")
        
        if insights:
            for insight in insights:
                st.write(insight)
        else:
            st.info("Keep applying to generate more insights!")
    
    with col2:
        st.markdown("### 💡 Recommendations")
        
        if recommendations:
            for rec in recommendations:
                st.write(rec)
        else:
            st.success("Great job! Keep up the current strategy.")
    
    # Projected outcomes
    if applications >= 10:  # Need sufficient data for projections
        st.markdown("### 📊 Projected Outcomes")
        
        current_response_rate = responses / applications if applications > 0 else 0
        current_interview_rate = interviews / applications if applications > 0 else 0
        current_offer_rate = offers / applications if applications > 0 else 0
        
        # Project next 30 days assuming similar activity
        projected_apps = max(1, int(applications * 0.3))  # 30% of current monthly rate
        projected_responses = int(projected_apps * current_response_rate)
        projected_interviews = int(projected_apps * current_interview_rate)
        projected_offers = int(projected_apps * current_offer_rate)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Projected Applications", projected_apps, "next 30 days")
        
        with col2:
            st.metric("Expected Responses", projected_responses)
        
        with col3:
            st.metric("Expected Interviews", projected_interviews)
        
        with col4:
            st.metric("Expected Offers", projected_offers)
