from typing import List, Optional

class ApiImageUrls:
    def __init__(self, small: str, medium: str, big: str):
        self.small = small
        self.medium = medium
        self.big = big

class ApiImage:
    def __init__(self, id: str, urls: ApiImageUrls, average_color: str):
        self.id = id
        self.urls = urls
        self.average_color = average_color

class ApiLocation:
    def __init__(self, latitude: float, longitude: float, postal_code: str, city: str, country_code: str, region: Optional[str] = None, region2: Optional[str] = None):
        self.latitude = latitude
        self.longitude = longitude
        self.postal_code = postal_code
        self.city = city
        self.country_code = country_code
        self.region = region
        self.region2 = region2

class ApiPrice:
    def __init__(self, amount: float, currency: str):
        self.amount = amount
        self.currency = currency

class ApiShipping:
    def __init__(self, item_is_shippable: bool, user_allows_shipping: bool, cost_configuration_id: Optional[str] = None):
        self.item_is_shippable = item_is_shippable
        self.user_allows_shipping = user_allows_shipping
        self.cost_configuration_id = cost_configuration_id

class ApiTaxonomy:
    def __init__(self, id: int, name: str, icon: Optional[str] = None):
        self.id = id
        self.name = name
        self.icon = icon

class ApiDiscount:
    def __init__(self, percentage: float, previous_price: ApiPrice):
        self.percentage = percentage
        self.previous_price = previous_price

class ApiSearchItem:
    def __init__(self,
                 id: str,
                 title: str,
                 description: str,
                 price: ApiPrice,
                 category_id: int,
                 user_id: str,
                 created_at: int,
                 modified_at: int,
                 web_slug: str,
                 images: List[ApiImage],
                 location: ApiLocation,
                 shipping: ApiShipping,
                 taxonomy: List[ApiTaxonomy],
                 is_refurbished: bool,
                 is_favoriteable: bool,
                 is_top_profile: bool,
                 has_warranty: bool,
                 reserved: bool,
                 favorited: bool,
                 bump: dict,
                 discount: Optional[ApiDiscount] = None):
        self.id = id
        self.title = title
        self.description = description
        self.price = price
        self.category_id = category_id
        self.user_id = user_id
        self.created_at = created_at
        self.modified_at = modified_at
        self.web_slug = web_slug
        self.images = images
        self.location = location
        self.shipping = shipping
        self.taxonomy = taxonomy
        self.is_refurbished = is_refurbished
        self.is_favoriteable = is_favoriteable
        self.is_top_profile = is_top_profile
        self.has_warranty = has_warranty
        self.reserved = reserved
        self.favorited = favorited
        self.bump = bump
        self.discount = discount
