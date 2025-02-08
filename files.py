from datetime import datetime
import pathlib
import aiohttp
import crawl4ai
import asyncio
from typing import List
from tracker import sitemaps


FILES_PATH = pathlib.Path("/mnt/s3/cfpb-files")
# FILES_PATH = pathlib.Path("data") / "cfpb-files"
# FILES_PATH.mkdir(exist_ok=True)


async def process_page(page: crawl4ai.CrawlResult):
    if "internal" not in page.links:
        print("No internal files!")
        return []

    internal_links = page.links["internal"]
    files = []
    for link in internal_links:
        href = link["href"]
        if "files.consumerfinance.gov" in href:
            files.append(href)
    await download_files(urls=files)


async def download_file(session: aiohttp.ClientSession, url: str):
    filename = url.split("/")[-1]
    try:
        async with session.get(url) as response:
            if response.status == 200:
                res = await response.read()
                (FILES_PATH / filename).write_bytes(res)
                print(f"saved file {filename}")
            else:
                print(f"Failed to download {url}: HTTP {response.status}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


async def download_files(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [download_file(session, url) for url in urls]
        await asyncio.gather(*tasks)


async def process_urls(urls) -> List:
    """
    Concurrently scrape and process all URLs.
    """
    async with crawl4ai.AsyncWebCrawler() as crawler:
        run_config = crawl4ai.CrawlerRunConfig(stream=True)
        tasks = []

        async for page in await crawler.arun_many(urls, config=run_config):
            tasks.append(asyncio.create_task(process_page(page)))

    results = await asyncio.gather(*tasks)
    return results


async def main():
    site_map_urls = ["https://www.consumerfinance.gov/sitemap.xml"]
    urls = []
    updated_after = datetime(2025, 1, 3)

    print(f"Fetching updates since: {updated_after}")
    for sitemap in site_map_urls:
        res = await sitemaps.get_updated_urls_from_map(
            sitemap, updated_after=updated_after
        )
        urls.extend(res)

    print(f"Updating {len(urls)} urls.")
    results = await process_urls(urls=urls)


if __name__ == "__main__":
    asyncio.run(main())
