from dataclasses import dataclass
from typing import Optional


@dataclass
class RawItem:
    """单条原始内容，来自任意信息源"""

    source_name: str
    source_type: str  # rss | email | twitter
    title: str
    content: str
    link: Optional[str] = None
    published: Optional[str] = None
