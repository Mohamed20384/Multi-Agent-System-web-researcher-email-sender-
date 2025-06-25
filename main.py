import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Type
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import markdown

# Load environment variables
load_dotenv()

os.environ["CREWAI_EMBEDDING_PROVIDER"] = "local"
os.environ["CREWAI_EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["CHROMA_OPENAI_API_KEY"] = "fake-key"  # ✅ Workaround
os.environ["CREWAI_STORAGE_DISABLED"] = "true"  # Prevent DB errors (optional)

from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool

# Try to import SerperDevTool, with fallback
try:
    from crewai_tools import SerperDevTool
    SERPER_AVAILABLE = True
except ImportError:
    SERPER_AVAILABLE = False
    # Create custom search tool as fallback
    import requests
    
    class SearchInput(BaseModel):
        search_query: str = Field(..., description="Search query to execute")
    
    class SerperDevTool(BaseTool):
        name: str = "Search the internet"
        description: str = "Search the internet for information"
        args_schema: Type[BaseModel] = SearchInput
        
        def _run(self, search_query: str) -> str:
            """Search using Serper API"""
            try:
                url = "https://google.serper.dev/search"
                payload = {"q": search_query}
                headers = {
                    "X-API-KEY": os.getenv("SERPER_API_KEY"),
                    "Content-Type": "application/json"
                }
                response = requests.post(url, json=payload, headers=headers)
                results = response.json()
                
                # Format results
                formatted_results = []
                if "organic" in results:
                    for result in results["organic"][:5]:
                        formatted_results.append(f"Title: {result.get('title', '')}\nLink: {result.get('link', '')}\nSnippet: {result.get('snippet', '')}\n---")
                
                return "\n".join(formatted_results) if formatted_results else "No results found"
            except Exception as e:
                return f"Search failed: {str(e)}"

import streamlit as st

# Custom Email Tool
class EmailInput(BaseModel):
    """Input schema for EmailTool."""
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content in Markdown format")

class EmailTool(BaseTool):
    name: str = "Send Email"
    description: str = "Send emails via SMTP. Use this to send email notifications, reports, or summaries."
    args_schema: Type[BaseModel] = EmailInput

    def _run(self, to_email: str, subject: str, body: str) -> str:
        """Send email using SMTP with Markdown converted to HTML"""
        try:
            # Load credentials
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv("EMAIL_USER")
            sender_password = os.getenv("EMAIL_PASS")

            if not sender_email or not sender_password:
                return "❌ Email credentials not found in environment variables"

            # Convert Markdown body to HTML
            html_body = markdown.markdown(body)

            # Wrap with basic HTML styling
            html_template = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {html_body}
              </body>
            </html>
            """

            # Construct the email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_template, 'html'))

            # Send the email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()

            return f"✅ Email sent successfully to {to_email}"

        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"

# Page configuration
st.set_page_config(
    page_title="AI Research Crew Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Embedded CSS for improved UI
st.markdown("""
<style>
/* Main header styling */
            
.stApp {
    background-color: transparent !important;
}

section.main {
    background-color: transparent !important;
}

div.block-container {
    background-color: transparent !important;
    padding-top: 2rem;
}
            
.header {
    background: linear-gradient(45deg, #6e48aa, #9d50bb);
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header h1 {
    margin: 0;
    font-size: 2.5rem;
}
.header p {
    margin: 0.5rem 0 0;
    font-size: 1.1rem;
    opacity: 0.9;
}

.status-card {
    background: rgba(110, 72, 170, 0.1) !important;  /* Semi-transparent purple */
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid #6e48aa;
    backdrop-filter: blur(5px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-card h3 {
    margin-top: 0;
    color: #6e48aa !important;
}

.status-card p {
    color: #e0e0e0 !important;  /* Light gray text */
    margin: 0.5rem 0;
}

/* Button styling */
.stButton>button {
    border: 2px solid #6e48aa;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    transition: all 0.3s;
}
.stButton>button:hover {
    background-color: #6e48aa;
    color: white;
}

/* Expander styling */
.st-expander {
    border: 1px solid #eee;
    border-radius: 8px;
    padding: 1rem;
}
.st-expander .stMarkdown {
    margin-bottom: 0.5rem;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}
.stTabs [data-baseweb="tab"] {
    padding: 8px 16px;
    border-radius: 4px 4px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: #6e48aa;
    color: white;
}

/* Progress bar styling */
.stProgress > div > div > div {
    background-color: #9d50bb;
}

/* Input field styling */
.stTextInput>div>div>input {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 8px 12px;
}
</style>
""", unsafe_allow_html=True)

# Main header with gradient
st.markdown("""
<div class="header">
    <h1>AI Research Pro 🔍</h1>
    <h4>Advanced Multi Agent System</h4>
    <p>web research, summarization & email reporting</p>
</div>
""", unsafe_allow_html=True)

# Main columns layout
col1, col2 = st.columns([2, 1])

with col1:
    # Research configuration in an expandable card
    with st.expander("🔧 Research Configuration", expanded=True):
        topic = st.text_input(
            "**Research Topic**",
            "Latest AI developments in 2025",
            help="Enter the topic you want to research"
        )
        
        recipient_email = st.text_input(
            "**Email Recipient**",
            "recipient@example.com",
            help="Where to send the research report"
        )
        
        col1a, col1b = st.columns(2)
        with col1a:
            num_results = st.slider(
                "**Number of search results**",
                3, 10, 5,
                help="How many sources to include in the research"
            )
        with col1b:
            email_format = st.selectbox(
                "**Report Format**",
                ["Summary Report", "Detailed Analysis", "Executive Brief"],
                help="Choose the format for the final report"
            )
    
    # Run button with better styling
    run_button = st.button(
        "🚀 Launch Research Crew", 
        use_container_width=True,
        help="Start the research process"
    )

with col2:
    # Features card only
    st.markdown("""
    <div class="status-card">
        <h3>📊 Features</h3>
        <p>• Web Search with Serper API</p>
        <p>• AI-Powered Summarization</p>
        <p>• Automated Email Delivery</p>
        <p>• Multiple Report Formats</p>
        <p>• Memory-Enabled Agents</p>
    </div>
    """, unsafe_allow_html=True)

# Results section
if run_button:
    if not topic or not recipient_email:
        st.error("⚠️ Please fill in all required fields!")
    else:
        with st.spinner("🚀 Assembling AI research team... This may take a few moments"):
            
            # Progress bar
            progress_bar = st.progress(0)
            
            # 1. Set up LLM
            progress_bar.progress(10)
            gemini_llm = LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.7,
            )

            # 2. Initialize Tools
            progress_bar.progress(20)
            search_tool = SerperDevTool()
            email_tool = EmailTool()

            # 3. Define Advanced Agents
            progress_bar.progress(30)
            web_researcher = Agent(
                role="Senior Web Research Specialist",
                goal=f"Conduct comprehensive web research on: {topic}",
                backstory="""You are an expert web researcher with advanced skills in finding, 
                analyzing, and extracting valuable information from online sources. You excel at 
                identifying credible sources, fact-checking, and gathering comprehensive data on any topic.""",
                tools=[search_tool],
                llm=gemini_llm,
                verbose=True,
                max_iter=3
            )

            content_summarizer = Agent(
                role="Content Analysis & Summarization Expert",
                goal="Create intelligent summaries and analysis from research data",
                backstory="""You are a skilled content analyst who specializes in synthesizing 
                complex information into clear, actionable insights. You excel at identifying key 
                trends, extracting important details, and presenting information in various formats 
                tailored to different audiences.""",
                llm=gemini_llm,
                verbose=True,
                max_iter=2
            )

            email_coordinator = Agent(
                role="Email Communication Specialist",
                goal="Send professional email reports with research findings",
                backstory="""You are a professional communication specialist who excels at 
                crafting clear, engaging emails that effectively communicate research findings 
                and insights to various stakeholders.""",
                tools=[email_tool],
                llm=gemini_llm,
                verbose=True,
                max_iter=2
            )

            # 4. Define Advanced Tasks
            progress_bar.progress(50)
            research_task = Task(
                description=f"""
                Conduct comprehensive web research on: {topic}
                
                Requirements:
                - Search for the most recent and relevant information
                - Focus on credible sources and authoritative content
                - Gather at least {num_results} different perspectives or sources
                - Include current trends, developments, and expert opinions
                - Note publication dates and source credibility
                
                Provide detailed findings with source citations.
                """,
                expected_output=f"Comprehensive research report with {num_results}+ sources, key findings, trends, and credible citations",
                agent=web_researcher
            )

            summarization_task = Task(
                description=f"""
                Analyze the research findings and create a {email_format.lower()} based on the web research results.
                
                Format Requirements for {email_format}:
                {"- Executive summary with key points and recommendations" if email_format == "Executive Brief" else ""}
                {"- Detailed analysis with supporting evidence and implications" if email_format == "Detailed Analysis" else ""}
                {"- Concise summary with main findings and actionable insights" if email_format == "Summary Report" else ""}
                
                Structure:
                1. Key Findings (3-5 main points)
                2. Current Trends & Developments  
                3. Expert Insights & Opinions
                4. Implications & Recommendations
                5. Sources & References
                
                Make it professional, well-organized, and actionable.
                """,
                expected_output=f"Well-structured {email_format.lower()} with clear sections, key insights, and professional formatting suitable for email",
                agent=content_summarizer,
                context=[research_task]
            )

            email_task = Task(
                description=f"""
                Send a professional email with the research summary to: {recipient_email}
                
                Email Requirements:
                - Subject: "Research Report: {topic} - {email_format}"
                - Professional greeting and closing
                - Include the complete summarized research findings
                - Format the content clearly with proper structure
                - Add a note about the AI research methodology
                - Maintain professional tone throughout
                
                Send the email and confirm delivery.
                """,
                expected_output=f"Confirmation that professional research email was successfully sent to {recipient_email}",
                agent=email_coordinator,
                context=[summarization_task]
            )

            # 5. Run the Advanced Crew
            progress_bar.progress(70)
            crew = Crew(
                agents=[web_researcher, content_summarizer, email_coordinator],
                tasks=[research_task, summarization_task, email_task],
                verbose=True,
                memory=True  # Enable memory for better context sharing
            )

            try:
                result = crew.kickoff()
                progress_bar.progress(100)
                
                # Success notification
                st.balloons()
                st.success("✨ Research completed successfully!")
                
                # Results display in tabs
                tab1, tab2, tab3 = st.tabs(["Research Findings", "Analysis Summary", "Email Status"])
                
                with tab1:
                    if hasattr(result, 'tasks_output') and len(result.tasks_output) > 0:
                        st.subheader("🔍 Web Research Results")
                        st.markdown(result.tasks_output[0].raw)
                    else:
                        st.info("No research results available")
                
                with tab2:
                    if hasattr(result, 'tasks_output') and len(result.tasks_output) > 1:
                        st.subheader("📊 Content Analysis")
                        st.markdown(result.tasks_output[1].raw)
                    else:
                        st.info("No summary available")
                
                with tab3:
                    if hasattr(result, 'tasks_output') and len(result.tasks_output) > 2:
                        st.subheader("📧 Email Delivery")
                        st.markdown(result.tasks_output[2].raw)
                    else:
                        st.info("No email status available")

                # Download buttons
                st.subheader("📥 Download Reports")
                dl_col1, dl_col2 = st.columns(2)
                
                with dl_col1:
                    if hasattr(result, 'tasks_output') and len(result.tasks_output) > 0:
                        st.download_button(
                            label="Download Research Report (MD)",
                            data=result.tasks_output[0].raw,
                            file_name=f"research_report_{topic.replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                
                with dl_col2:
                    if hasattr(result, 'tasks_output') and len(result.tasks_output) > 1:
                        st.download_button(
                            label="Download Summary (MD)",
                            data=result.tasks_output[1].raw,
                            file_name=f"summary_{topic.replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

            except Exception as e:
                progress_bar.progress(0)
                st.error(f"❌ An error occurred: {str(e)}")
                st.info("Please check your API keys and internet connection.")

# Footer
st.markdown("""
<hr style="margin: 2rem 0; border: none; height: 1px; background-color: #eee;"/>
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>AI Research Crew Pro • Powered by CrewAI and Gemini</p>
</div>
""", unsafe_allow_html=True)