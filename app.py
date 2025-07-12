%%writefile app.py

import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 1. UTILITY & TOOL DEFINITIONS ---

SOCIAL_PLATFORMS = {
    'linkedin.com': 'LinkedIn', 'twitter.com': 'Twitter', 'facebook.com': 'Facebook',
    'instagram.com': 'Instagram', 'youtube.com': 'YouTube'
}

def scrape_contact_info(url: str) -> dict:
    """
    Completely rebuilt scraper that is much more accurate and less prone to false positives.
    """
    if not url.startswith('http'):
        url = 'https://' + url
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    found_info = {
        "email": set(), "phone": set(), "social_links": {}, "contact_page": set(),
        "meta_title": "Not found", "meta_description": "Not found"
    }

    try:
        response = requests.get(url, headers=headers, timeout=100)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        # --- Scrape meta tags for better context ---
        if soup.title and soup.title.string:
            found_info["meta_title"] = soup.title.string.strip()
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            found_info["meta_description"] = meta_desc.get('content').strip()

        # Find all links on the page
        all_links = soup.find_all('a', href=True)

        for a in all_links:
            href = a['href']
            # Find direct email addresses
            if href.startswith('mailto:'):
                found_info["email"].add(href.replace('mailto:', ''))

            # Stricter check for social media and contact pages
            full_url = urljoin(base_url, href)
            parsed_full_url = urlparse(full_url)
            domain = parsed_full_url.netloc.lower().replace('www.', '')
            path = parsed_full_url.path.lower()

            # Social media: Must match the domain
            if domain in SOCIAL_PLATFORMS:
                platform_name = SOCIAL_PLATFORMS[domain]
                if platform_name not in found_info["social_links"]: # Add only the first unique link
                    found_info["social_links"][platform_name] = full_url

            # Contact page: Must have 'contact' or 'help' in the URL path
            if '/contact' in path or '/help' in path:
                found_info["contact_page"].add(full_url)

        # Fallback regex search for emails and phones
        page_text = soup.get_text()
        found_info["email"].update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text))
        found_info["phone"].update(re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text))

    except requests.RequestException as e:
        st.warning(f"Could not scrape {url}: {e}")

    final_output = {
        "Email Address": list(found_info["email"])[0] if found_info["email"] else "Not found",
        "Phone Number": list(found_info["phone"])[0] if found_info["phone"] else "Not found",
        "Social Media": found_info["social_links"] if found_info["social_links"] else "Not found",
        "Contact Form Page": list(found_info["contact_page"])[0] if found_info["contact_page"] else "Not found",
        "Website Title": found_info["meta_title"],
        "Website Description": found_info["meta_description"]
    }    
    return final_output


PLATFORM_BLACKLIST = [
    'wikipedia', 'crunchbase', 'bloomberg', 'reuters', 'github', 'zoominfo', 
    'forbes', 'techcrunch', 'medium', 'news', 'jobs', 'careers', 'owler'
]

def clean_company_name(name: str) -> str:
    name = name.lower()
    suffixes = ['inc', 'llc', 'ltd', 'corp', 'corporation', 'gmbh']
    for suffix in suffixes:
        name = name.replace(f'.{suffix}', '').replace(f',{suffix}', '').replace(suffix, '')
    name = re.sub(r'[\s.,-]', '', name)
    return name

def find_best_url(company_name: str, search_results: list) -> str | None:
    """
    Finds the most likely official URL from search results using a scoring system.
    It heavily prioritizes URLs where the domain contains the company name.
    """
    clean_name = clean_company_name(company_name)
    best_score = -1
    best_url = None

    # This blacklist is for non-corporate sites like news, directories, etc.
    # Social media is handled by the main scraper, so it's not needed here.
    NON_CORPORATE_BLACKLIST = [
        'wikipedia', 'crunchbase', 'bloomberg', 'reuters', 'github', 'zoominfo', 
        'forbes', 'techcrunch', 'medium', 'news', 'jobs', 'careers', 'owler', 'apollo.io'
    ]

    for result in search_results:
        url = result.get('url')
        title = result.get('title', '')
        if not url:
            continue

        current_score = 0
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower().replace('www.', '')

            # --- HEURISTIC SCORING ---

            # 1. Penalize heavily if it's a known non-corporate platform.
            if any(platform in domain for platform in NON_CORPORATE_BLACKLIST):
                current_score -= 100

            # 2. **HIGHEST REWARD**: If the clean company name is a part of the domain.
            # This is the logic that worked well before and is now prioritized.
            # Example: 'wipro' in 'wipro.com' -> TRUE
            if clean_name in domain:
                current_score += 100
            
            # 3. Small bonus if the company name is in the page title.
            # This helps break ties.
            if clean_name in title.lower():
                current_score += 10
            
            # Update the best URL if the current one has a higher score
            if current_score > best_score:
                best_score = current_score
                best_url = url
        
        except Exception:
            # If any URL is malformed, just skip it.
            continue
    
    # Return the URL that scored the highest.
    return best_url

PITCH_TEMPLATES = {
    "Formal": "a professional and respectful tone", "Casual": "a friendly, approachable tone",
    "Direct & Punchy": "a direct, to-the-point tone with a sense of urgency", "Follow-up": "a gentle, concise follow-up tone"
}
st.set_page_config(page_title="Sales Assistant Agent", layout="wide")
st.title("AI Sales Assistant Agent")
with st.sidebar:
    st.header("Configuration")
    gemini_api_key = st.text_input("Gemini API Key:", type="password", key="gemini_api_key")
    tavily_api_key = st.text_input("Tavily API Key:", type="password", key="tavily_api_key")
    st.markdown("---"); st.subheader("Your Information")
    user_name = st.text_input("Your Name:", placeholder="e.g., Jane Doe", key="user_name")
    user_title = st.text_input("Your Company/Title:", placeholder="e.g., Founder, Innovate Inc.", key="user_title")
    st.markdown("---"); st.subheader("Pitch Settings")
    pitch_tone = st.selectbox("Select Pitch Tone:", options=list(PITCH_TEMPLATES.keys()), key="pitch_tone")

company_name = st.text_input("Enter Company Name to research:", key="company_name")
if st.button("Generate Email"):
    if not all([gemini_api_key, tavily_api_key, company_name]):
        st.warning("Please enter your API keys and a company name.")
    else:
        with st.spinner("Executing sales agent workflow..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini_api_key, temperature=0.7)  #please please if required toggle the 
                search_tool = TavilySearchResults(tavily_api_key=tavily_api_key, max_results=5)

                st.write("Step 1: Finding official website...")
                search_results = search_tool.invoke(f"official website homepage for {company_name}")
                website_url = find_best_url(company_name, search_results)
                if not website_url: st.error(f"Could not find a reliable website for '{company_name}'."); st.stop()
                
                website_url = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"
                st.write(f"Found and cleaned URL: {website_url}")

                st.write("Step 2: Performing hyper-scrape for context and contacts...")
                contact_info = scrape_contact_info(website_url)

                # --- THE DEFINITIVE, HYPER-PERSONALIZED PROMPT ---
                prompt_template = ChatPromptTemplate.from_template(
                    """
                    **TASK:** Generate a complete, ready-to-send cold email pitching an invented B2B AI automation service.

                    **CORE INSTRUCTIONS:**
                    1.  **HYPER-PERSONALIZE THE OPENING:** Your first sentence MUST be a specific, compelling observation based on the "Website Title" and "Website Description" provided below. Do NOT use generic openings like "I was looking at your website." Instead, connect their stated mission to a problem your invented service can solve.
                    2.  **INVENT A RELEVANT AUTOMATION SERVICE:** Create a plausible AI service that solves a problem relevant to the target company. Do NOT use generic placeholders.
                    3.  **WRITE IN PROSE ONLY (NO BULLET POINTS):** The entire email body must be in natural paragraphs. Do NOT use lists. Weave the benefits smoothly into the text.
                    4.  **SIGN-OFF CORRECTLY:** Use the provided sender name and title.
                    5.  **FORMAT:** Start with a compelling subject line: 'Subject: Your Subject Here'.

                    **CONTEXT FOR PERSONALIZATION:**
                    - **Website Title:** {website_title}
                    - **Website Description:** {website_description}

                    **EMAIL DETAILS:**
                    - **Target Company:** {company_name}
                    - **Sender Name:** {user_name}
                    - **Sender Title/Company:** {user_title}
                    - **Desired Tone:** {pitch_style}

                    Execute the task now.
                    """
                )

                st.write("Step 3: Drafting hyper-personalized email...")
                email_generation_chain = prompt_template | llm | StrOutputParser()
                email_text = email_generation_chain.invoke({
                    "company_name": company_name, "website_title": contact_info["Website Title"],
                    "website_description": contact_info["Website Description"], "user_name": user_name,
                    "user_title": user_title, "pitch_style": PITCH_TEMPLATES[pitch_tone]
                })

                st.subheader("Agent Finished: Email Draft Ready")
                st.text_area("Generated Email", email_text, height=400, key="email_text_area")
                escaped_text = json.dumps(email_text)
                button_html = f"""<style>.copy-btn-container{{...}}</style><div class="copy-btn-container"><button ...>...</button></div>"""
                components.html(button_html, height=40)

                with st.expander("View Agent's Findings", expanded=True):
                    st.json(contact_info)

            except Exception as e:
                st.error(f"An error occurred: {e}")
