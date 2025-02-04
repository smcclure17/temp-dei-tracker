import streamlit as st
import openai
import crawl4ai
import asyncio
import pathlib
from typing import List
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Website Content Monitor", layout="wide")

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = []

ROOT = pathlib.Path("data")
ROOT.mkdir(exist_ok=True)
(ROOT / "baseline").mkdir(exist_ok=True)

URLS = [
    "https://www.mass.gov/info-details/sdo-certified-diverse-business-dashboard",
    "https://www.mass.gov/orgs/office-of-health-equity-and-community-engagement",
    "https://masshpc.gov/health-equity",
    "https://www.mass.gov/advancing-health-equity-in-ma",
    "https://www.bostonplans.org/about-us/divisions/diversity-equity-and-inclusion",
    "https://www.boston.gov/government/cabinets/equity-and-inclusion-cabinet",
    "https://www.bostonplans.org/projects/standards/dei-in-development-policy",
    "https://www.boston.gov/government/cabinets/economic-opportunity-and-inclusion",
    "https://www.boston.gov/departments/equity-and-inclusion-cabinet/racial-justice",
    "https://www.boston.gov/departments/economic-opportunity-and-inclusion/economic-opportunity-and-inclusion-programs",
    "https://www.boston.gov/departments/city-council/civil-rights-racial-equity-and-immigrant-advancement",
    "https://www.boston.gov/departments/supplier-diversity",
    "https://www.doe.mass.edu/csi/diverse-workforce/default.html",
    "https://www.doe.mass.edu/csi/dei.html",
    "https://www.doe.mass.edu/csi/equitable-stu-access.html",
]

def url_to_name(url: str) -> str:
    return url.split("https://")[1].replace("/", "-").replace("www.", "").replace(":", "")

def chatgpt_compare(openai_client: openai.OpenAI, baseline: str, updated: str) -> str:
    prompt = f"""We are tracking changes in DEI and LGBT language in websites. We are particularly concerned
    with removals of references to diversity. Please compare the two website content, formatted as markdown.

    If there are no changes, say "no changes", else, return a summary of what has been changed

    before:
    ```
    {baseline}
    ```

    after:
    ```
    {updated}
    ```
    """

    chat_completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return chat_completion.choices[0].message.content

async def process_urls(api_key: str) -> List[dict]:
    results = []
    run_config = crawl4ai.CrawlerRunConfig(screenshot=True, pdf=True)
    
    openai_client = openai.OpenAI(api_key=api_key)

    async with crawl4ai.AsyncWebCrawler() as crawler:
        pages = await crawler.arun_many(URLS, config=run_config)

        for page in pages:
            url_dir_name = url_to_name(page.url)
            baseline_path = ROOT / "baseline" / url_dir_name / "content.md"
            
            try:
                if baseline_path.exists():
                    baseline = baseline_path.read_text()
                    print("comparing for", baseline_path)
                    comparison = chatgpt_compare(openai_client, baseline, page.markdown)
                else:
                    # Create baseline if it doesn't exist
                    baseline_path.parent.mkdir(exist_ok=True)
                    baseline_path.write_text(page.markdown)
                    comparison = "Baseline created"
                
                results.append({
                    "url": page.url,
                    "status": "Success",
                    "comparison": comparison,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                results.append({
                    "url": page.url,
                    "status": "Error",
                    "comparison": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    return results

def main():
    st.title("Website Content Update Tracker")
    
    # API Key input
    api_key = st.text_input("Enter OpenAI API Key:", type="password")
    
    if st.button("Start Processing"):
        if not api_key:
            st.error("Please enter an OpenAI API key")
            return
            
        st.session_state.processing = True
        
        with st.spinner("Processing URLs..."):
            try:
                results = asyncio.run(process_urls(api_key))
                st.session_state.results = results
                st.session_state.processing = False
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.processing = False
                return
    
    if not st.session_state.processing and not st.session_state.results:
        st.subheader("URLs to be checked:")
        for url in URLS:
            st.write(f"• {url}")

    # Display results
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df)
        
        # Download results
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results",
            data=csv,
            file_name="content_monitor_results.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()