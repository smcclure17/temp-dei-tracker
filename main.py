import re
import crawl4ai
import asyncio
from typing import List
from tracker import aws_helpers, change_detection, slack, storage
from tracker import sitemaps
from tracker.models import ScrapeResult, ScrapeResultWithoutContent


ARCHIVE = True
CHANGE_THRESH = 0.97
SCREENSHOT = True
COMPARE_TO_OLDEST = True


S3_BUCKET = "bgmp-dei-tracker"


async def process_page(page: crawl4ai.CrawlResult):
    data_path = storage.get_path_for_url(page.url)
    id = storage.url_to_id(page.url)

    if data_path.exists():
        old_snapshot = storage.get_previous_snapshot(data_path, COMPARE_TO_OLDEST)
        similarity = change_detection.get_cosine_similarity(
            old_snapshot.content, page.markdown
        )
        old_screenshot_url = old_snapshot.screenshot_url
        old_timestamp = old_snapshot.timestamp
    else:
        print("Initializing new data...")
        similarity = 999  # placeholder
        old_screenshot_url = None
        old_timestamp = None

    def _get_html_title(html: str):
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        return match.group(1) if match else None

    screenshot_url = None
    if SCREENSHOT:
        sc_file_name = f"{id}-{storage.DATETIME}.png"
        screenshot_url = await aws_helpers.upload_png_to_s3_async(
            page.screenshot, S3_BUCKET, sc_file_name
        )

    res = ScrapeResult(
        id=id,
        url=page.url,
        title=_get_html_title(page.html),
        content=page.markdown,
        content_html=page.html,
        screenshot_url=screenshot_url,
        timestamp=storage.DATETIME,
        similarity=similarity,
        old_screenshot_url=old_screenshot_url,
        old_timestamp=old_timestamp,
    )
    save_data(res)  # persist with content
    return ScrapeResultWithoutContent.from_scrape_result(res)  # drop content


async def process_urls(urls) -> List[ScrapeResult]:
    """
    Concurrently scrape and process all URLs.
    """
    async with crawl4ai.AsyncWebCrawler() as crawler:
        run_config = crawl4ai.CrawlerRunConfig(screenshot=SCREENSHOT, stream=True)
        tasks = []

        async for page in await crawler.arun_many(urls, config=run_config):
            tasks.append(asyncio.create_task(process_page(page)))

    results = await asyncio.gather(*tasks)
    return results


def save_data(result: ScrapeResult):
    data_path = storage.get_path_for_url(result.url)
    data_path.mkdir(exist_ok=True)
    storage.save_current_data(data_path, result)
    if ARCHIVE:
        storage.save_archive_data(data_path, result)


async def main():
    site_map_urls = ["https://www.consumerfinance.gov/sitemap.xml"]
    urls = []
    updated_after = storage.get_last_update_time()

    print(f"Fetching updates since: {updated_after}")
    for sitemap in site_map_urls:
        res = await sitemaps.get_updated_urls_from_map(
            sitemap, updated_after=updated_after
        )
        urls.extend(res)

    print(f"Updating {len(urls)} urls.")
    results = await process_urls(urls=urls)

    slack.send_slack_alerts(results=results, change_threshold=CHANGE_THRESH)
    storage.persist_update_time()


if __name__ == "__main__":
    asyncio.run(main())
