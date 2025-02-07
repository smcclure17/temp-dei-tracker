from datetime import datetime
import pydantic


class ScrapeResult(pydantic.BaseModel):
    id: str
    url: str
    similarity: float
    """cosine similarity to the previous snapshot"""
    content: str
    timestamp: str
    content_html: str | None = None
    title: str | None = None
    screenshot_url: str | None = None
    old_screenshot_url: str | None = None
    old_timestamp: str | None = None
    """screenshot of previous snapshot. used for helping compare diffs"""

    def __eq__(self, value):
        if not isinstance(value, ScrapeResult):
            raise ValueError("Cannot compare")
        return self.similarity == value.similarity

    def __gt__(self, value):
        if not isinstance(value, ScrapeResult):
            raise ValueError("Cannot compare")
        return self.similarity > value.similarity


class ScrapeResultWithoutContent(pydantic.BaseModel):
    id: str
    url: str
    similarity: float
    """cosine similarity to the previous snapshot"""
    timestamp: str
    title: str | None = None
    screenshot_url: str | None = None
    old_screenshot_url: str | None = None
    old_timestamp: str | None = None
    """screenshot of previous snapshot. used for helping compare diffs"""

    def __eq__(self, value):
        if not isinstance(value, ScrapeResultWithoutContent):
            raise ValueError("Cannot compare")
        return self.similarity == value.similarity

    def __gt__(self, value):
        if not isinstance(value, ScrapeResultWithoutContent):
            raise ValueError("Cannot compare")
        return self.similarity > value.similarity

    @classmethod
    def from_scrape_result(cls, res: ScrapeResult) -> "ScrapeResultWithoutContent":
        return cls(**res.model_dump(exclude=["content", "content_html"]))
