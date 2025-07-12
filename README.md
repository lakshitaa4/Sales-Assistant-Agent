# AI Sales Assistant Agent
---------------------------

This is an intelligent sales email generator that automatically scrapes company data and crafts **hyper-personalized cold emails** using **Gemini Pro** and **LangChain**.

* * * * *

### Features:

-   Accepts **company name**, your **name**, and your **company/title**

-   Uses **Tavily API** to find the **official company website**

-   Scrapes:

    -   Contact Email & Phone

    -   Social Media Links

    -   Website Title & Description (for personalized prompts)

-   Feeds context to **Gemini Pro** LLM via **LangChain**

-   Generates **pitch-perfect cold emails** in 4 tones:

    -   Formal

    -   Casual

    -   Direct & Punchy

    -   Follow-up

-   Clean UI with **Streamlit**

-   Optional: Add to clipboard with a single click

* * * * *

### Tech Stack

-   LangChain

-   Gemini LLM API

-   Tavily Search API

-   BeautifulSoup4

-   Streamlit

* * * * *

How to Run This Project
--------------------------

### Step 1: Get API Keys

#### Gemini (Google AI)

1.  Visit: [Google AI Studio](https://aistudio.google.com/)

2.  Log in and click "Get API Key"

3.  Copy the key

#### Tavily

1.  Go to: [Tavily](https://app.tavily.com)

2.  Sign up and open the Dashboard

3.  Generate a new key and copy it

* * * * *

### Step 2: Install and Run

1.  Clone the repository:

`git clone https://github.com/lakshitaa4/Sales-Assistant-Agent.git`<br />
`cd Sales-Assistant-Agent`

2.  Install dependencies:

`pip install -r requirements.txt`

3.  Start the app:

`streamlit run app.py`

4.  Enter:

    -   Gemini API key

    -   Tavily API key

    -   Your name and company

    -   Target company to research

    -   Select tone → Click "Generate Email"

* * * * *

requirements.txt
-------------------

`streamlit
langchain
langchain-google-genai
tavily-python
beautifulsoup4
requests
lxml
langchain-community`

* * * * *

Project Structure
--------------------

`├── app.py                # Main app file` <br />
`├── requirements.txt      # Dependencies` <br />
`├── README.md             # Docs (you'll convert this!)` <br />

* * * * *

Sample Output
----------------

### Input:

-   Company: Mahindra

-   Tone: Direct & Punchy

-   Your Name: Lakshita

-   Your Company Name: <br /> For example: Garage AI

### Output:

-   Subject: Accelerating Mahindra's Rise with AI Efficiency

-   Scraped Email: support@mahindra.in

-   Scraped Contact Page: <https://mahindra.com/contact-us>

-   Email Body:

    > "Given Mahindra's dedication to enabling people to 'Rise' through innovation, our AI platform, **SynergyAI**, can detect opportunities for internal synergy across subsidiaries and enable smarter resource planning..."

* * * * *

Future Improvements
----------------------

-   Session memory to store email history

-   Export to PDF / Gmail integration

-   Deploy via Hugging Face or Streamlit Cloud

* * * * *

Built By
--------------

**Lakshita Soni**

-   LinkedIn: [linkedin.com/in/lakshita-soni-b3268b2a5](https://linkedin.com/in/lakshita-soni-b3268b2a5)

-   GitHub: [github.com/lakshitaa4](https://github.com/lakshitaa4)

* * * * *

📜 License
----------

MIT -- Free for personal and commercial use. Credit is appreciated.
