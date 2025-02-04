import shutil
import subprocess
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
if "processing" not in st.session_state:
    st.session_state.processing = False
if "results" not in st.session_state:
    st.session_state.results = []

ROOT = pathlib.Path("data")
ROOT.mkdir(exist_ok=True)
(ROOT / "baseline").mkdir(exist_ok=True)

URLS = [
    "https://fenwayhealth.org/the-fenway-institute/",
    "https://www.childrenshospital.org/programs/gender-multispecialty-service",
    "https://www.massgeneralbrigham.org/en/about/diversity-equity-and-inclusion",
    "https://bilh.org/about/dei",
    "https://www.childrenshospital.org/departments/psychiatry/diversity-equity-inclusion",
    "https://www.childrenshospital.org/about-us/lgbtq-equality",
    "https://www.bmc.org/about-bmc/diversity-equity-and-inclusion",
    "https://www.dana-farber.org/about/inclusion-diversity-equity",
    "https://dicp.hms.harvard.edu/",
    "https://medicine.tufts.edu/about/school-medicine/diversity-equity-inclusion",
    "https://www.bumc.bu.edu/camed/about/anti-racism-resources/",
    "https://hms.harvard.edu/about-hms/campus-culture/diversity-inclusion/anti-racism-initiatives",
    "https://www.massgeneralbrigham.org/en/about/diversity-equity-and-inclusion/united-against-racism",
    "https://mapublichealth.org/health-equity-policy-framework/",
    "https://www.mhalink.org/dei/",
    "https://www.mass.gov/orgs/maternal-mortality-and-morbidity-review",
    "https://www.bmc.org/health-equity-accelerator",
    "https://www.massgeneral.org/about/diversity-inclusion",
    "https://domdei.brighamandwomens.org/",
    "https://careers.bluecrossma.org/us/en/diversity-equity-inclusion ",
    "https://fxb.harvard.edu/racial-justice/racial-justice-program/",
    "https://fxb.harvard.edu/",
    "https://www.bu.edu/diversity/",
    "https://www.bc.edu/bc-web/offices/human-resources/sites/oid.html",
    "https://mitsloan.mit.edu/diversity/our-mission",
    "https://hr.mit.edu/diversity-equity-inclusion",
    "https://hr.mit.edu/staff/Diversity%2C-Equity%2C-and-Inclusion",
    "https://edib.harvard.edu/",
    "https://www.suffolk.edu/about/diversity-equity-and-inclusion",
    "https://as.tufts.edu/about/diversity-equity-inclusion-justice",
    "https://www.umass.edu/diversity/",
    "https://www.unh.edu/diversity-inclusion/",
    "https://web.uri.edu/diversity/",
    "https://www.uvm.edu/ie",
    "https://diversity.uconn.edu/",
    "https://umaine.edu/diversity-and-inclusion/",
    "https://www.snhu.edu/about-us/diversity-and-inclusion",
    "https://oied.brown.edu/",
    "https://ide.dartmouth.edu/",
    "https://your.yale.edu/community/diversity-and-inclusion",
    "https://belonging.northeastern.edu/",
    "https://www.holycross.edu/campus-life/diversity-and-inclusion",
    "https://www.wellesley.edu/about-us/inclusive-excellence",
    "https://www.fidelity.com/about-fidelity/our-company/diversityandinclusion",
    "https://www.libertymutualgroup.com/about-lm/corporate-information/diversity-equity-inclusion/our-commitment-diversity-equity-inclusion",
    "https://www.johnhancock.com/about-us/diversity-equity-inclusion.html",
    "https://www.statestreet.com/us/en/asset-manager/about/sustainability/global-inclusion-diversity-equity",
    "https://www.massbio.org/dei/",
    "https://www.glad.org/",
    "https://healthequitycompact.org/",
    "https://www.boston.gov/government/cabinets/boston-public-health-commission",
    "https://www.cambridgema.gov/Departments/officeofequityandinclusion",
    "https://www.cambridgema.gov/Departments/officeofequityandinclusion/interactiveequityandinclusiondashboard",
    "https://www.bostonpublicschools.org/bps-departments/civil-rights/about",
    "https://www.bostonpublicschools.org/about-bps/office-of-the-superintendent/ana-tavares",
    "https://www.bostonpublicschools.org/school-committee/task-force-groups/opportunity-and-achievements-gaps-task-force",
    "https://sites.google.com/bostonpublicschools.org/ogequityandclsptoolkit/racial-equity-planning-tool",
    "https://www.bostonpublicschools.org/bps-departments/multilingual-and-multicultural-education/equity-accountability",
    "https://www.bostonpublicschools.org/about-bps/office-of-the-superintendent/dr-mariel-novas",
    "https://www.worcesterschools.org/page/equity-office",
    "https://www.springfieldpublicschools.com/about/diversity__equity__and_inclusion",
    "https://www.boston.gov/government/cabinets/boston-public-health-commission/racial-justice-and-health-equity",
    "https://www.bostonpublicschools.org/archive/division-of-equity-and-strategy/office-of-equity",
    "https://www.bostonpublicschools.org/about-bps/office-of-the-superintendent/organizational-chart",
    "https://www.mass.gov/info-details/sdo-certified-diverse-business-dashboard",
    "https://www.mass.gov/orgs/office-of-health-equity-and-community-engagement",
    "https://masshpc.gov/health-equity",
    "https://www.mass.gov/advancing-health-equity-in-ma",
    "https://www.bostonplans.org/about-us/divisions/diversity-equity-and-inclusion",
    "https://www.boston.gov/government/cabinets/equity-and-inclusion-cabinet",
    "https://www.bostonplans.org/projects/standards/dei-in-development-policy ",
    "https://www.boston.gov/government/cabinets/economic-opportunity-and-inclusion",
    "https://www.boston.gov/departments/equity-and-inclusion-cabinet/racial-justice ",
    "https://www.boston.gov/departments/economic-opportunity-and-inclusion/economic-opportunity-and-inclusion-programs ",
    "https://www.boston.gov/departments/city-council/civil-rights-racial-equity-and-immigrant-advancement",
    "https://www.boston.gov/departments/supplier-diversity ",
    "https://www.doe.mass.edu/csi/diverse-workforce/default.html",
    "https://www.doe.mass.edu/csi/dei.html",
    "https://www.doe.mass.edu/csi/equitable-stu-access.html",
]


def url_to_name(url: str) -> str:
    return (
        url.split("https://")[1].replace("/", "-").replace("www.", "").replace(":", "")
    )


def chatgpt_compare(openai_client: openai.OpenAI, baseline: str, updated: str) -> str:
    prompt = f"""We are tracking changes in DEI and LGBT language in websites. We are particularly concerned
    with removals of references to diversity. Please compare the two website content, formatted as markdown.

    Has any content changed between the two versions? If yes, return "Yes" and then a list of changes. If no
    changes, return "No". Focus on content not formatting.

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

                results.append(
                    {
                        "url": page.url,
                        "status": "Success",
                        "comparison": comparison,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "url": page.url,
                        "status": "Error",
                        "comparison": str(e),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    return results


def main():
    playwright_path = shutil.which("playwright")
    if playwright_path:
        subprocess.run([playwright_path, "install"], check=True)
    else:
        print("Playwright not found. Make sure it is installed and available in PATH.")

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
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
