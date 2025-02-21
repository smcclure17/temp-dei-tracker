from datetime import datetime
import asyncio
import aiohttp
import xml.etree.ElementTree as ET


class NotFoundError(Exception):
    pass


async def _fetch_sitemap(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        if response.status in {404, 403}:
            raise NotFoundError(url)
        response.raise_for_status()
        return await response.text()


async def _parse_sitemap(
    session: aiohttp.ClientSession, xml_content: str, updated_after: datetime
):
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return []

    urls = []
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"

    tasks = []
    for url_elem in root.findall(f"{namespace}url"):
        loc_elem = url_elem.find(f"{namespace}loc")
        lastmod_elem = url_elem.find(f"{namespace}lastmod")

        if loc_elem is not None and lastmod_elem is not None:
            try:
                lastmod_date = datetime.fromisoformat(lastmod_elem.text)
                if lastmod_date > updated_after:
                    urls.append(loc_elem.text)
            except ValueError:
                print(f"Invalid date format in <lastmod>: {lastmod_elem.text}")
        elif loc_elem is not None:
            print(f"Missing <lastmod> tag for {loc_elem.text}, fetching anyway")
            urls.append(loc_elem.text)

    for elem in root.findall(f"{namespace}sitemap/{namespace}loc"):
        sub_sitemap = elem.text
        print(f"Fetching sub-sitemap: {sub_sitemap}")
        tasks.append(_get_all_urls(session, sub_sitemap, updated_after))

    sub_urls = await asyncio.gather(*tasks)
    for sublist in sub_urls:
        urls.extend(sublist)

    return urls


async def _get_all_urls(
    session: aiohttp.ClientSession, sitemap_url: str, updated_after: datetime
):
    try:
        xml_content = await _fetch_sitemap(session, sitemap_url)
    except NotFoundError as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return []
    return await _parse_sitemap(session, xml_content, updated_after)


async def get_updated_urls_from_map(sitemap_index_url: str, updated_after: datetime):
    """List all urls from a sitemap that have been modified after the given timestamp"""
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    ) as session:
        return await _get_all_urls(session, sitemap_index_url, updated_after)
