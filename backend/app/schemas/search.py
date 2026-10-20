from typing import List, Optional

from pydantic import BaseModel, Field


class SearchMenuItemOut(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    price: float = 0.0
    image_url: Optional[str] = None
    is_available: bool = True
    average_rating: float = 0.0
    total_reviews: int = 0
    category_name: Optional[str] = None
    category_slug: Optional[str] = None


class SearchCategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    image_url: Optional[str] = None


class SearchSuggestionItem(BaseModel):
    text: str
    kind: str = "term"
    slug: Optional[str] = None


class SearchResultsOut(BaseModel):
    query: str = ""
    items: List[SearchMenuItemOut] = Field(default_factory=list)
    categories: List[SearchCategoryOut] = Field(default_factory=list)
    suggestions: List[SearchSuggestionItem] = Field(default_factory=list)
    total: int = 0


class SearchSuggestOut(BaseModel):
    query: str = ""
    suggestions: List[SearchSuggestionItem] = Field(default_factory=list)