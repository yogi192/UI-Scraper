#!/usr/bin/env python3
"""
Add test business data to MongoDB for demonstration purposes
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import random

# Sample Dominican Republic businesses
SAMPLE_BUSINESSES = [
    {
        "name": "Supermercado Nacional",
        "address": "Av. 27 de Febrero, Santo Domingo",
        "phone": "809-565-5555",
        "category": "Supermarket",
        "website": "https://www.nacional.com.do",
        "email": "info@nacional.com.do",
        "description": "Leading supermarket chain in Dominican Republic",
        "source_url": "https://example.com/nacional",
        "source_name": "Test Data"
    },
    {
        "name": "Restaurant El Conuco",
        "address": "Calle Casimiro de Moya, Santo Domingo",
        "phone": "809-686-0129",
        "category": "Restaurant",
        "website": "https://elconuco.com.do",
        "description": "Traditional Dominican cuisine restaurant",
        "source_url": "https://example.com/elconuco",
        "source_name": "Test Data"
    },
    {
        "name": "Blue Mall Punta Cana",
        "address": "Carretera Bávaro, Punta Cana",
        "phone": "809-466-0505",
        "category": "Shopping Mall",
        "website": "https://bluemall.com.do",
        "description": "Premium shopping mall in Punta Cana",
        "source_url": "https://example.com/bluemall",
        "source_name": "Test Data"
    },
    {
        "name": "Hotel Barceló Santo Domingo",
        "address": "Av. Máximo Gómez, Santo Domingo",
        "phone": "809-563-5000",
        "category": "Hotel",
        "website": "https://www.barcelo.com",
        "email": "santodomingo@barcelo.com",
        "description": "5-star hotel in the heart of Santo Domingo",
        "source_url": "https://example.com/barcelo",
        "source_name": "Test Data"
    },
    {
        "name": "Farmacia Carol",
        "address": "Multiple locations in Santo Domingo",
        "phone": "809-565-2222",
        "category": "Pharmacy",
        "website": "https://farmaciacarol.com",
        "description": "Popular pharmacy chain",
        "source_url": "https://example.com/carol",
        "source_name": "Test Data"
    },
    {
        "name": "La Sirena",
        "address": "Av. Winston Churchill, Santo Domingo",
        "phone": "809-472-4444",
        "category": "Department Store",
        "website": "https://lasirena.com.do",
        "description": "Major retail department store chain",
        "source_url": "https://example.com/lasirena",
        "source_name": "Test Data"
    },
    {
        "name": "Banco Popular Dominicano",
        "address": "Torre Popular, Av. John F. Kennedy",
        "phone": "809-544-5000",
        "category": "Bank",
        "website": "https://www.popularenlinea.com",
        "email": "servicio@bpd.com.do",
        "description": "Leading commercial bank in Dominican Republic",
        "source_url": "https://example.com/popular",
        "source_name": "Test Data"
    },
    {
        "name": "Plaza Lama",
        "address": "Av. Duarte, Santiago",
        "phone": "809-582-1234",
        "category": "Department Store",
        "website": "https://plazalama.com.do",
        "description": "Electronics and home appliances store",
        "source_url": "https://example.com/plazalama",
        "source_name": "Test Data"
    },
    {
        "name": "Caribbean Cinemas",
        "address": "Ágora Mall, Santo Domingo",
        "phone": "809-372-1000",
        "category": "Entertainment",
        "website": "https://caribbeancinemas.com",
        "description": "Movie theater chain",
        "source_url": "https://example.com/caribbean",
        "source_name": "Test Data"
    },
    {
        "name": "Hospital General Plaza de la Salud",
        "address": "Av. Ortega y Gasset, Santo Domingo",
        "phone": "809-565-7477",
        "category": "Hospital",
        "website": "https://www.hgps.org.do",
        "email": "info@hgps.org.do",
        "description": "Modern medical facility",
        "source_url": "https://example.com/hgps",
        "source_name": "Test Data"
    }
]

async def add_test_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client.ui_scraper
    collection = db.businesses
    
    # Check if we already have test data
    existing = await collection.count_documents({"source_name": "Test Data"})
    if existing > 0:
        print(f"Test data already exists ({existing} records). Skipping...")
        return
    
    # Add created_at and updated_at timestamps
    for business in SAMPLE_BUSINESSES:
        business["created_at"] = datetime.utcnow()
        business["updated_at"] = datetime.utcnow()
        business["rating"] = f"{random.randint(35, 50)/10:.1f}"
        business["location"] = {
            "lat": 18.4861 + random.uniform(-2, 2),
            "lng": -69.9312 + random.uniform(-2, 2)
        }
    
    # Insert test data
    result = await collection.insert_many(SAMPLE_BUSINESSES)
    print(f"Successfully added {len(result.inserted_ids)} test businesses to the database!")
    
    # Show some stats
    total = await collection.count_documents({})
    categories = await collection.distinct("category")
    print(f"\nDatabase now contains:")
    print(f"- Total businesses: {total}")
    print(f"- Categories: {', '.join(categories)}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_test_data())