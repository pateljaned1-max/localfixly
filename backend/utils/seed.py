import sqlite3
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, init_db
from auth import hash_password

CATEGORIES = [
    {"name": "Plumber", "slug": "plumber", "icon": "🔧", "description": "Pipe leaks, tap repair, drain cleaning, fitting installation"},
    {"name": "Electrician", "slug": "electrician", "icon": "⚡", "description": "Wiring, short circuits, switchboards, fan & light installation"},
    {"name": "Cleaner", "slug": "cleaner", "icon": "🧹", "description": "Deep home cleaning, sofa, kitchen, and bathroom sanitation"},
    {"name": "Carpenter", "slug": "carpenter", "icon": "🪚", "description": "Furniture repair, custom woodwork, door & lock fitting"},
    {"name": "Painter", "slug": "painter", "icon": "🎨", "description": "Interior & exterior wall painting, touch-ups, waterproofing"},
    {"name": "AC Repair", "slug": "ac-repair", "icon": "❄️", "description": "AC servicing, gas refilling, cooling fix, installation"},
    {"name": "Mechanic", "slug": "mechanic", "icon": "🚗", "description": "Car & bike emergency repair, battery jumpstart, brake service"},
    {"name": "Property Dealer", "slug": "property-dealer", "icon": "🏠", "description": "Rental assistance, property verification, real estate advisory"},
    {"name": "Locksmith", "slug": "locksmith", "icon": "🔑", "description": "Emergency key unlocking, safe opening, high-security lock install"},
    {"name": "Appliance Repair", "slug": "appliance-repair", "icon": "📺", "description": "Washing machine, refrigerator, TV, microwave troubleshooting"},
    {"name": "Packers & Movers", "slug": "packers-movers", "icon": "📦", "description": "House shifting, heavy item relocation, safe packaging"},
    {"name": "Computer Repair", "slug": "computer-repair", "icon": "💻", "description": "Laptop screen replacement, OS install, virus cleanup, hardware upgrade"}
]

# Base location centered around New Delhi / Central Metro (28.6139, 77.2090)
# Can easily search near this lat/lng or any custom coordinates
PROVIDERS_DATA = [
    {
        "name": "Rajesh Kumar",
        "email": "rajesh.plumber@example.com",
        "phone": "+91 98765 43210",
        "password": "Password123!",
        "business_name": "Apex Plumbing Solutions",
        "description": "Licensed plumber with 8+ years experience fixing urgent leaks, burst pipes, and bathroom fixture setups.",
        "experience_years": 8,
        "lat": 28.6145,
        "lng": 77.2095,
        "address": "Connaught Place, Central City",
        "service_radius": 15.0,
        "availability": "available",
        "pricing_note": "$25 / hr base charge",
        "starting_price": 25.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["plumber", "appliance-repair"],
        "hours": [(0, "08:00", "20:00", 0), (1, "08:00", "20:00", 0), (2, "08:00", "20:00", 0), (3, "08:00", "20:00", 0), (4, "08:00", "20:00", 0), (5, "08:00", "20:00", 0), (6, "09:00", "17:00", 0)]
    },
    {
        "name": "Amit Sharma",
        "email": "amit.elec@example.com",
        "phone": "+91 98123 45678",
        "password": "Password123!",
        "business_name": "Sharma Electricals & Emergency Repairs",
        "description": "Fast response certified electrician. Available for urgent short-circuit fixes, MCB tripping, and heavy appliance wiring.",
        "experience_years": 10,
        "lat": 28.6200,
        "lng": 77.2150,
        "address": "Barakhamba Road, Central City",
        "service_radius": 12.0,
        "availability": "available",
        "pricing_note": "$30 inspection + repair",
        "starting_price": 30.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["electrician", "ac-repair"],
        "hours": [(0, "00:00", "23:59", 0), (1, "08:00", "22:00", 0), (2, "08:00", "22:00", 0), (3, "08:00", "22:00", 0), (4, "08:00", "22:00", 0), (5, "08:00", "22:00", 0), (6, "08:00", "22:00", 0)]
    },
    {
        "name": "Priya Verma",
        "email": "priya.clean@example.com",
        "phone": "+91 97111 22233",
        "password": "Password123!",
        "business_name": "Sparkle Clean Home Services",
        "description": "Eco-friendly deep cleaning experts for homes, kitchens, and office spaces. Guaranteed spotless finish.",
        "experience_years": 5,
        "lat": 28.6080,
        "lng": 77.2010,
        "address": "Janpath, Central City",
        "service_radius": 10.0,
        "availability": "available",
        "pricing_note": "$45 flat per room",
        "starting_price": 45.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["cleaner"],
        "hours": [(0, "09:00", "18:00", 1), (1, "09:00", "18:00", 0), (2, "09:00", "18:00", 0), (3, "09:00", "18:00", 0), (4, "09:00", "18:00", 0), (5, "09:00", "18:00", 0), (6, "09:00", "18:00", 0)]
    },
    {
        "name": "Vikram Singh",
        "email": "vikram.carpenter@example.com",
        "phone": "+91 99887 76655",
        "password": "Password123!",
        "business_name": "Royal Craft Carpentry",
        "description": "Master carpenter specializing in custom furniture repair, modular cabinet assembly, and high-security door locks.",
        "experience_years": 12,
        "lat": 28.6250,
        "lng": 77.1980,
        "address": "Pusa Road, Central City",
        "service_radius": 20.0,
        "availability": "busy",
        "pricing_note": "$35 base visit fee",
        "starting_price": 35.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["carpenter", "locksmith"],
        "hours": [(0, "10:00", "18:00", 0), (1, "09:00", "19:00", 0), (2, "09:00", "19:00", 0), (3, "09:00", "19:00", 0), (4, "09:00", "19:00", 0), (5, "09:00", "19:00", 0), (6, "10:00", "16:00", 0)]
    },
    {
        "name": "Sanjay Kapoor",
        "email": "sanjay.ac@example.com",
        "phone": "+91 98990 11223",
        "password": "Password123!",
        "business_name": "CoolBreeze AC & Appliance Care",
        "description": "24/7 HVAC technician team for split/window AC servicing, gas charging, compressor repair, and fridge maintenance.",
        "experience_years": 7,
        "lat": 28.5950,
        "lng": 77.2200,
        "address": "Khan Market, Central City",
        "service_radius": 15.0,
        "availability": "available",
        "pricing_note": "$20 service charge",
        "starting_price": 20.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["ac-repair", "appliance-repair"],
        "hours": [(0, "08:00", "21:00", 0), (1, "08:00", "21:00", 0), (2, "08:00", "21:00", 0), (3, "08:00", "21:00", 0), (4, "08:00", "21:00", 0), (5, "08:00", "21:00", 0), (6, "08:00", "21:00", 0)]
    },
    {
        "name": "Sunil Locksmith",
        "email": "sunil.keys@example.com",
        "phone": "+91 97777 88899",
        "password": "Password123!",
        "business_name": "QuickKey 24x7 Emergency Locksmith",
        "description": "Locked out of your home or car? Mobile van equipped with key cutting and non-destructive lock picking tools.",
        "experience_years": 9,
        "lat": 28.6300,
        "lng": 77.2100,
        "address": "Paharganj, Central City",
        "service_radius": 25.0,
        "availability": "available",
        "pricing_note": "$40 emergency callout",
        "starting_price": 40.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["locksmith"],
        "hours": [(0, "00:00", "23:59", 0), (1, "00:00", "23:59", 0), (2, "00:00", "23:59", 0), (3, "00:00", "23:59", 0), (4, "00:00", "23:59", 0), (5, "00:00", "23:59", 0), (6, "00:00", "23:59", 0)]
    },
    {
        "name": "Rohan Mehta",
        "email": "rohan.tech@example.com",
        "phone": "+91 96543 21098",
        "password": "Password123!",
        "business_name": "GeekFix Computer & IT Care",
        "description": "On-site laptop and desktop troubleshooting, malware removal, SSD speed upgrades, and network configuration.",
        "experience_years": 6,
        "lat": 28.6100,
        "lng": 77.2250,
        "address": "Pragati Maidan, Central City",
        "service_radius": 15.0,
        "availability": "offline",
        "pricing_note": "$30 diagnostic fee",
        "starting_price": 30.0,
        "verified": 0,
        "verification_status": "pending",
        "categories": ["computer-repair"],
        "hours": [(0, "10:00", "19:00", 1), (1, "10:00", "19:00", 0), (2, "10:00", "19:00", 0), (3, "10:00", "19:00", 0), (4, "10:00", "19:00", 0), (5, "10:00", "19:00", 0), (6, "10:00", "19:00", 0)]
    },
    {
        "name": "Manoj Auto Repair",
        "email": "manoj.auto@example.com",
        "phone": "+91 95432 10987",
        "password": "Password123!",
        "business_name": "CityRoad Mobile Mechanic & Towing",
        "description": "Mobile auto workshop for flat tire replacement, battery revival, oil changes, and roadside breakdown assistance.",
        "experience_years": 11,
        "lat": 28.6000,
        "lng": 77.1900,
        "address": "Dhaula Kuan, Central City",
        "service_radius": 30.0,
        "availability": "available",
        "pricing_note": "$50 roadside visit",
        "starting_price": 50.0,
        "verified": 1,
        "verification_status": "approved",
        "categories": ["mechanic"],
        "hours": [(0, "06:00", "23:00", 0), (1, "06:00", "23:00", 0), (2, "06:00", "23:00", 0), (3, "06:00", "23:00", 0), (4, "06:00", "23:00", 0), (5, "06:00", "23:00", 0), (6, "06:00", "23:00", 0)]
    }
]

CUSTOMERS_DATA = [
    {"name": "Ananya Sharma", "email": "customer@example.com", "phone": "+91 99900 11122", "password": "Password123!"},
    {"name": "Rahul Verma", "email": "rahul.customer@example.com", "phone": "+91 98888 77766", "password": "Password123!"},
    {"name": "Sneha Gupta", "email": "sneha.customer@example.com", "phone": "+91 97777 66655", "password": "Password123!"}
]

ADMIN_DATA = {
    "name": "LocalFix Admin",
    "email": "admin@example.com",
    "phone": "+91 90000 00000",
    "password": "AdminPassword123!"
}

def seed_database():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    print("Seeding database...")

    # 1. Categories
    cur.execute("DELETE FROM categories;")
    for idx, cat in enumerate(CATEGORIES, start=1):
        cur.execute(
            "INSERT INTO categories (name, slug, icon, description, active, sort_order) VALUES (?, ?, ?, ?, 1, ?);",
            (cat["name"], cat["slug"], cat["icon"], cat["description"], idx)
        )
    category_map = {}
    for row in cur.execute("SELECT id, slug FROM categories;").fetchall():
        category_map[row["slug"]] = row["id"]

    # 2. Admin User
    cur.execute("DELETE FROM users WHERE role = 'admin';")
    admin_pw_hash = hash_password(ADMIN_DATA["password"])
    cur.execute(
        "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, 'admin');",
        (ADMIN_DATA["name"], ADMIN_DATA["email"], ADMIN_DATA["phone"], admin_pw_hash)
    )

    # 3. Customer Users
    cur.execute("DELETE FROM users WHERE role = 'customer';")
    customer_ids = []
    for cust in CUSTOMERS_DATA:
        pw_hash = hash_password(cust["password"])
        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, 'customer');",
            (cust["name"], cust["email"], cust["phone"], pw_hash)
        )
        customer_ids.append(cur.lastrowid)

    # 4. Provider Users & Profiles
    cur.execute("DELETE FROM users WHERE role = 'provider';")
    provider_id_list = []

    for pdata in PROVIDERS_DATA:
        pw_hash = hash_password(pdata["password"])
        cur.execute(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, 'provider');",
            (pdata["name"], pdata["email"], pdata["phone"], pw_hash)
        )
        user_id = cur.lastrowid

        cur.execute(
            """INSERT INTO providers 
               (user_id, business_name, description, experience_years, latitude, longitude, address_text, 
                service_radius_km, availability_status, pricing_note, starting_price, verified, verification_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            (user_id, pdata["business_name"], pdata["description"], pdata["experience_years"],
             pdata["lat"], pdata["lng"], pdata["address"], pdata["service_radius"],
             pdata["availability"], pdata["pricing_note"], pdata["starting_price"],
             pdata["verified"], pdata["verification_status"])
        )
        provider_id = cur.lastrowid
        provider_id_list.append((provider_id, user_id, pdata["name"]))

        # Link categories
        for cat_slug in pdata["categories"]:
            if cat_slug in category_map:
                cur.execute(
                    "INSERT INTO provider_categories (provider_id, category_id) VALUES (?, ?);",
                    (provider_id, category_map[cat_slug])
                )

        # Working hours
        for h in pdata["hours"]:
            cur.execute(
                "INSERT INTO provider_hours (provider_id, day_of_week, open_time, close_time, is_closed) VALUES (?, ?, ?, ?, ?);",
                (provider_id, h[0], h[1], h[2], h[3])
            )

    # 5. Bookings & Reviews Seed Data
    cur.execute("DELETE FROM bookings;")
    cur.execute("DELETE FROM reviews;")
    cur.execute("DELETE FROM reports;")

    cust1 = customer_ids[0]
    cust2 = customer_ids[1] if len(customer_ids) > 1 else cust1

    prov1_id = provider_id_list[0][0] # Rajesh Plumber
    prov2_id = provider_id_list[1][0] # Amit Electrician
    prov3_id = provider_id_list[2][0] # Priya Cleaner

    # Completed booking 1 -> reviewed
    cur.execute(
        """INSERT INTO bookings 
           (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, preferred_date, preferred_time, status)
           VALUES (?, ?, ?, 'Leaking kitchen tap and sink pipe clogging issue', 28.6139, 77.2090, 'Connaught Place Flat 4B', '2026-08-01', '10:00 AM', 'completed');""",
        (cust1, prov1_id, category_map["plumber"])
    )
    b1_id = cur.lastrowid
    cur.execute(
        "INSERT INTO reviews (booking_id, customer_id, provider_id, rating, review) VALUES (?, ?, ?, 5, 'Rajesh arrived in 20 minutes, super polite and fixed the leaking tap quickly. Highly recommended!');",
        (b1_id, cust1, prov1_id)
    )

    # Completed booking 2 -> reviewed
    cur.execute(
        """INSERT INTO bookings 
           (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, preferred_date, preferred_time, status)
           VALUES (?, ?, ?, 'Main switchboard sparking and MCB tripping', 28.6180, 77.2120, 'Barakhamba Road Apt 12', '2026-08-03', '02:00 PM', 'completed');""",
        (cust2, prov2_id, category_map["electrician"])
    )
    b2_id = cur.lastrowid
    cur.execute(
        "INSERT INTO reviews (booking_id, customer_id, provider_id, rating, review) VALUES (?, ?, ?, 5, 'Very knowledgeable electrician. Explained the overload issue and replaced the blown fuse safely.');",
        (b2_id, cust2, prov2_id)
    )

    # Pending booking (For provider Rajesh to view in dashboard inbox)
    cur.execute(
        """INSERT INTO bookings 
           (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, preferred_date, preferred_time, status)
           VALUES (?, ?, ?, 'Bathroom flush tank valve broken, water running continuously', 28.6140, 77.2085, 'Janpath Enclave House 14', '2026-08-08', '11:00 AM', 'pending');""",
        (cust1, prov1_id, category_map["plumber"])
    )

    # Accepted booking (In active state)
    cur.execute(
        """INSERT INTO bookings 
           (customer_id, provider_id, category_id, description, location_lat, location_lng, address_text, preferred_date, preferred_time, status)
           VALUES (?, ?, ?, 'Full 3BHK deep cleaning before housewarming event', 28.6080, 77.2010, 'Janpath Block C', '2026-08-09', '09:00 AM', 'accepted');""",
        (cust2, prov3_id, category_map["cleaner"])
    )

    # Recalculate average ratings and review counts for providers
    cur.execute("""
        UPDATE providers 
        SET avg_rating = (
            SELECT COALESCE(ROUND(AVG(rating), 1), 0.0) FROM reviews WHERE reviews.provider_id = providers.id
        ),
        review_count = (
            SELECT COUNT(*) FROM reviews WHERE reviews.provider_id = providers.id
        );
    """)

    conn.commit()
    conn.close()

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
