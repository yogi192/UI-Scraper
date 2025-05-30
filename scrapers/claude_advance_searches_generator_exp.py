import os, sys
from urllib.parse import quote_plus, urlencode
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SearchType(Enum):
    BUSINESSES = "businesses"
    RESTAURANTS = "restaurants" 
    ATTRACTIONS = "attractions"
    SERVICES = "services"
    HOTELS = "hotels"
    GENERAL = "general"

class TimeFilter(Enum):
    ANY_TIME = ""
    PAST_HOUR = "qdr:h"
    PAST_24H = "qdr:d"
    PAST_WEEK = "qdr:w"
    PAST_MONTH = "qdr:m"
    PAST_YEAR = "qdr:y"

@dataclass
class SearchConfig:
    search_term: str
    search_type: SearchType = SearchType.GENERAL
    num_results: int = 100
    language: str = 'lang_es'  # Spanish for DR
    country: str = 'countryDO'
    location: str = 'Dominican Republic'
    time_filter: TimeFilter = TimeFilter.ANY_TIME
    file_type: Optional[str] = None  # pdf, doc, xls, etc.
    exact_phrase: Optional[str] = None
    exclude_words: Optional[List[str]] = None
    include_words: Optional[List[str]] = None
    site_restrict: Optional[str] = None
    related_site: Optional[str] = None
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None

class AdvancedGoogleSearchGenerator:
    def __init__(self):
        self.base_url = "https://www.google.com/search"
        
        # Dominican Republic specific keywords for different categories
        self.dr_keywords = {
            SearchType.BUSINESSES: [
                "empresas", "negocios", "directorio empresarial", "compañías", 
                "industrias", "comercios", "pymes", "negocio dominicano"
            ],
            SearchType.RESTAURANTS: [
                "restaurantes", "comida", "gastronomía", "cocina dominicana",
                "donde comer", "comedor", "cafetería", "bar restaurante"
            ],
            SearchType.ATTRACTIONS: [
                "lugares turísticos", "atracciones", "turismo", "que visitar",
                "sitios de interés", "monumentos", "playas", "parques"
            ],
            SearchType.SERVICES: [
                "servicios", "profesionales", "técnicos", "reparaciones",
                "consultores", "servicios profesionales", "proveedores"
            ],
            SearchType.HOTELS: [
                "hoteles", "hospedaje", "alojamiento", "resort", "pensión",
                "apart hotel", "posada", "villa"
            ]
        }
        
        # Dominican specific domains and sites
        self.dr_domains = [
            "site:.do", "site:tripadvisor.com.do", "site:paginasamarillas.com.do",
            "site:listindiario.com", "site:diariolibre.com", "site:elcaribe.com.do",
            "site:dominicanaonline.org", "site:godominicanrepublic.com"
        ]
        
        # Common Dominican cities for location-specific searches
        self.dr_cities = [
            "Santo Domingo", "Santiago", "Puerto Plata", "La Romana", 
            "San Pedro de Macorís", "Punta Cana", "Boca Chica", "Samaná",
            "Barahona", "Monte Cristi", "Higüey", "Mao", "Bonao"
        ]

    def _build_search_query(self, config: SearchConfig) -> str:
        """Build the main search query with operators"""
        query_parts = []
        
        # Main search term
        base_term = config.search_term.strip()
        
        # Add exact phrase if specified
        if config.exact_phrase:
            query_parts.append(f'"{config.exact_phrase}"')
        
        # Add category-specific keywords
        if config.search_type != SearchType.GENERAL:
            category_keywords = self.dr_keywords.get(config.search_type, [])
            # Pick 2-3 most relevant keywords to avoid query bloat
            selected_keywords = category_keywords[:2]
            for keyword in selected_keywords:
                query_parts.append(f'"{keyword}"')
        
        # Add location context
        query_parts.append(f'"{config.location}"')
        
        # Include additional words (OR logic)
        if config.include_words:
            include_phrase = " OR ".join([f'"{word}"' for word in config.include_words])
            query_parts.append(f"({include_phrase})")
        
        # Exclude words
        if config.exclude_words:
            for word in config.exclude_words:
                query_parts.append(f'-"{word}"')
        
        # Add base search term
        query_parts.insert(0, base_term)
        
        return " ".join(query_parts)

    def _build_site_operators(self, config: SearchConfig) -> List[str]:
        """Build site-specific operators"""
        site_operators = []
        
        # Primary site restriction
        if config.site_restrict:
            site_operators.append(f"site:{config.site_restrict}")
        
        # Related site
        if config.related_site:
            site_operators.append(f"related:{config.related_site}")
        
        # Include specific domains
        if config.include_domains:
            domain_group = " OR ".join([f"site:{domain}" for domain in config.include_domains])
            site_operators.append(f"({domain_group})")
        
        # Exclude domains
        if config.exclude_domains:
            for domain in config.exclude_domains:
                site_operators.append(f"-site:{domain}")
        
        return site_operators

    def generate_search_url(self, config: SearchConfig) -> str:
        """Generate advanced Google search URL"""
        # Build main query
        main_query = self._build_search_query(config)
        
        # Add site operators
        site_operators = self._build_site_operators(config)
        if site_operators:
            main_query += " " + " ".join(site_operators)
        
        # Add file type filter
        if config.file_type:
            main_query += f" filetype:{config.file_type}"
        
        # Build URL parameters
        params = {
            'q': main_query,
            'num': min(config.num_results, 100),  # Google limits to 100
            'lr': config.language,
            'cr': config.country,
            'gl': 'DO',  # Geolocation for Dominican Republic
            'hl': 'es'   # Interface language Spanish
        }
        
        # Add time filter
        if config.time_filter != TimeFilter.ANY_TIME:
            params['tbs'] = config.time_filter.value
        
        # Build final URL
        encoded_params = urlencode(params, quote_via=quote_plus)
        return f"{self.base_url}?{encoded_params}"

    def generate_specialized_urls(self, 
                                base_search: str, 
                                search_types: List[SearchType] = None,
                                cities: List[str] = None) -> List[Dict[str, str]]:
        """Generate multiple specialized search URLs"""
        
        if search_types is None:
            search_types = [SearchType.BUSINESSES, SearchType.RESTAURANTS, 
                           SearchType.ATTRACTIONS, SearchType.SERVICES]
        
        if cities is None:
            cities = self.dr_cities[:5]  # Top 5 cities
        
        urls = []
        
        # Generate URLs for each search type
        for search_type in search_types:
            config = SearchConfig(
                search_term=base_search,
                search_type=search_type,
                location="República Dominicana",
                include_domains=[".do"],
                exclude_domains=["facebook.com", "instagram.com", "twitter.com"]
            )
            
            url = self.generate_search_url(config)
            urls.append({
                'type': search_type.value,
                'location': 'General DR',
                'url': url,
                'description': f"Search for {search_type.value} related to '{base_search}' in Dominican Republic"
            })
        
        # Generate city-specific URLs for top search type
        primary_type = search_types[0] if search_types else SearchType.BUSINESSES
        for city in cities[:3]:  # Limit to top 3 cities
            config = SearchConfig(
                search_term=base_search,
                search_type=primary_type,
                location=city,
                include_domains=[".do"]
            )
            
            url = self.generate_search_url(config)
            urls.append({
                'type': f"{primary_type.value}_city",
                'location': city,
                'url': url,
                'description': f"Search for {primary_type.value} related to '{base_search}' in {city}"
            })
        
        return urls

    def generate_directory_focused_urls(self, search_term: str) -> List[Dict[str, str]]:
        """Generate URLs specifically for finding business directories"""
        directory_configs = [
            {
                'name': 'Dominican Business Directories',
                'config': SearchConfig(
                    search_term=search_term,
                    search_type=SearchType.BUSINESSES,
                    include_words=["directorio", "empresas", "listado", "guía"],
                    include_domains=[".do", "paginasamarillas.com.do"],
                    exclude_words=["facebook", "instagram"]
                )
            },
            {
                'name': 'Tourism and Attraction Listings',
                'config': SearchConfig(
                    search_term=search_term,
                    search_type=SearchType.ATTRACTIONS,
                    include_words=["guía turística", "lugares", "directorio turístico"],
                    site_restrict="godominicanrepublic.com"
                )
            },
            {
                'name': 'Restaurant and Food Directories',
                'config': SearchConfig(
                    search_term=search_term,
                    search_type=SearchType.RESTAURANTS,
                    include_words=["directorio", "restaurantes", "donde comer"],
                    exclude_words=["delivery", "domicilio"]
                )
            }
        ]
        
        urls = []
        for item in directory_configs:
            url = self.generate_search_url(item['config'])
            urls.append({
                'type': 'directory',
                'name': item['name'],
                'url': url,
                'description': f"Specialized search for {item['name'].lower()}"
            })
        
        return urls


# Example usage and testing
if __name__ == "__main__":
    generator = AdvancedGoogleSearchGenerator()
    
    # Example 1: Basic specialized search
    print("=== Basic Search ===")
    config = SearchConfig(
        search_term="hotel toachi",
        search_type=SearchType.HOTELS,
        location="Santo Domingo",
        include_domains=[".do"]
    )
    url = generator.generate_search_url(config)
    print(url)
    
    # Example 2: Multiple specialized URLs
    print("\n=== Specialized URLs ===")
    urls = generator.generate_specialized_urls("restaurantes zona colonial")
    for item in urls[:3]:  # Show first 3
        print(f"{item['type']} ({item['location']}): {item['url']}")
    
    # Example 3: Directory-focused URLs
    print("\n=== Directory URLs ===")
    directory_urls = generator.generate_directory_focused_urls("negocios santo domingo")
    for item in directory_urls:
        print(f"{item['name']}: {item['url']}")