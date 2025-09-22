
import json
from typing import List, Dict, Optional

class Category:
    def __init__(self, data: Dict):
        self.id: int = data.get("id")
        self.name: str = data.get("name")
        self.parent_id: Optional[int] = data.get("parent_id")
        self.subcategories: List[Category] = [Category(sub) for sub in data.get("subcategories", [])]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "subcategories": [sub.to_dict() for sub in self.subcategories],
        }

class CategoryService:
    def __init__(self, api_client):
        self.api_client = api_client
        self.categories: List[Category] = []

    def load_categories(self) -> None:
        """Loads categories from the Wallapop API."""
        response = self.api_client.get("../categories", params={"context": "search"})
        if response and response.status_code == 200:
            data = response.json()
            self.categories = [Category(cat) for cat in data.get("categories", [])]
        else:
            # Handle error
            self.categories = []

    def get_categories_as_json(self) -> str:
        """Returns the loaded categories as a JSON string."""
        return json.dumps([cat.to_dict() for cat in self.categories])

    def find_category_by_id(self, category_id: int, categories: List[Category] = None) -> Optional[Category]:
        """Finds a category by its ID in the category tree."""
        if categories is None:
            categories = self.categories

        for category in categories:
            if category.id == category_id:
                return category
            
            found_in_sub = self.find_category_by_id(category_id, category.subcategories)
            if found_in_sub:
                return found_in_sub
        
        return None
