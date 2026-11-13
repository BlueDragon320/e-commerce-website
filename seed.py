"""
seed.py — Populate Noise E-Commerce site catalog with 16+ Noise electronics,
realistic specs in INR, battery life, ANC, ratings, and mock orders.
"""
from datetime import datetime, timedelta, timezone
import random
from slugify import slugify
from app import create_app, db
from app.models import Product, Order, OrderItem, CartItem

def seed():
    app = create_app('development')
    with app.app_context():
        print("🌱 Seeding Noise E-Commerce Database...")
        db.drop_all()
        db.create_all()

        products_data = [
            # 1. Flagship Smartwatch
            {
                "name": "Noise ColorFit Ultra 3",
                "category": "Smartwatches",
                "price": 2999.0,
                "original_price": 7999.0,
                "battery_life": 168.0,  # 7 days
                "anc": False,
                "rating": 4.5,
                "review_count": 1840,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://www.gonoise.com/cdn/shop/files/NoiseColorFitUltra3-BlackEliteEdition_1_grande.png?v=1695122129",
                "description": "Premium 1.96'' AMOLED display smartwatch with Tru Sync Bluetooth calling, functional crown, and 100+ sports modes.",
                "specs": {
                    "Display": "1.96'' AMOLED (410x502)",
                    "Calling": "Bluetooth Tru Sync v5.3",
                    "Battery": "Up to 7 days (168 hours)",
                    "Water Resistance": "IP68 Water Resistant",
                    "Health Tracking": "24/7 Heart Rate, SpO2, Sleep Tracker"
                }
            },
            # 2. AMOLED Metallic Smartwatch
            {
                "name": "NoiseFit Halo",
                "category": "Smartwatches",
                "price": 2499.0,
                "original_price": 6999.0,
                "battery_life": 168.0,
                "anc": False,
                "rating": 4.4,
                "review_count": 1420,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://www.gonoise.com/cdn/shop/files/1_1_b18f77db-5fef-4698-9902-a48fec2b8efa_grande.png?v=1704963291",
                "description": "Round dial 1.43'' AMOLED smartwatch with premium metallic build, always-on display, and intelligent gesture control.",
                "specs": {
                    "Display": "1.43'' Round AMOLED",
                    "Casing": "Metallic Finish Alloy",
                    "Battery": "7 days typical usage",
                    "Voice Assistant": "AI Voice Assistant support",
                    "Sensors": "Heart Rate, Blood Oxygen, Stress Level"
                }
            },
            # 3. Budget Bestseller Smartwatch
            {
                "name": "Noise ColorFit Icon 2",
                "category": "Smartwatches",
                "price": 1499.0,
                "original_price": 4999.0,
                "battery_life": 120.0,  # 5 days
                "anc": False,
                "rating": 4.2,
                "review_count": 2890,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://www.gonoise.com/cdn/shop/products/Icon2-5_grande.png?v=1681610912",
                "description": "Vibrant 1.8'' LCD display with clear Bluetooth calling, built-in games, and 60+ sports tracking modes.",
                "specs": {
                    "Display": "1.8'' TFT LCD 500 nits",
                    "Battery": "5 days (120 hours)",
                    "Waterproof": "IP67 dust and water resistant",
                    "Special": "Built-in mini arcade games"
                }
            },
            # 4. Premium AMOLED Digital Crown
            {
                "name": "Noise ColorFit Pro 4 Alpha",
                "category": "Smartwatches",
                "price": 3499.0,
                "original_price": 8999.0,
                "battery_life": 168.0,
                "anc": False,
                "rating": 4.6,
                "review_count": 920,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/1_0ba84c50-3527-4c98-b643-f3f4f3075c27.png?v=1686911647",
                "description": "Flagship 1.78'' AMOLED smartwatch with 60Hz refresh rate, digital rotary crown, and palm-to-turn-off display.",
                "specs": {
                    "Display": "1.78'' AMOLED 60Hz",
                    "Crown": "Fully functional digital crown",
                    "Battery": "7 days battery life",
                    "Sensors": "Optical Heart Rate, Accel, SpO2"
                }
            },
            # 5. Women's Luxury Smartwatch
            {
                "name": "Noise Diva Smartwatch",
                "category": "Smartwatches",
                "price": 2999.0,
                "original_price": 5999.0,
                "battery_life": 96.0,  # 4 days
                "anc": False,
                "rating": 4.4,
                "review_count": 640,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/Artboard19_result_5250da54-389e-4afa-a440-870f0bae2459.webp?v=1776673795",
                "description": "Diamond-cut decorative bezel smartwatch with 1.1'' AMOLED display, mesh straps, and dedicated female cycle tracking.",
                "specs": {
                    "Display": "1.1'' AMOLED Diamond Cut",
                    "Strap": "Milanese Metal Mesh",
                    "Battery": "4 days (96 hours)",
                    "Health": "Female cycle tracker, Heart Rate"
                }
            },
            # 6. Ultra Budget Earbuds
            {
                "name": "Noise Buds VS102",
                "category": "Wireless Earbuds",
                "price": 1099.0,
                "original_price": 2999.0,
                "battery_life": 50.0,
                "anc": False,
                "rating": 4.1,
                "review_count": 3520,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/1_9e839f18-7b82-4b71-ab98-471982ca91ef.png?v=1682439948",
                "description": "Ergonomic Flybird design earbuds with 50-hour continuous playback, 11mm dynamic drivers, and Type-C fast charging.",
                "specs": {
                    "Playtime": "50 Hours total playback",
                    "Drivers": "11mm Dynamic Bass Drivers",
                    "Fast Charge": "10 mins charge = 120 mins playtime",
                    "Resistance": "IPX5 Water Resistant"
                }
            },
            # 7. Long Playtime Quad Mic Earbuds
            {
                "name": "Noise Buds VS404",
                "category": "Wireless Earbuds",
                "price": 1299.0,
                "original_price": 3499.0,
                "battery_life": 45.0,
                "anc": False,
                "rating": 4.3,
                "review_count": 2180,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://www.gonoise.com/cdn/shop/files/image_2023_09_19T10_11_28_596Z_grande.png?v=1695119844",
                "description": "Quad Mic Environmental Noise Cancellation (ENC) wireless earbuds with 3 EQ modes and ultra-clear voice calls.",
                "specs": {
                    "Playtime": "45 Hours battery life",
                    "Microphones": "Quad Mic ENC System",
                    "Latency": "HyperSync Low Latency",
                    "Modes": "Bass, Balanced, and Vocal EQ"
                }
            },
            # 8. Flagship ANC Earbuds
            {
                "name": "Noise Air Buds Pro 2 with ANC",
                "category": "Wireless Earbuds",
                "price": 2499.0,
                "original_price": 6999.0,
                "battery_life": 40.0,
                "anc": True,
                "rating": 4.5,
                "review_count": 1650,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/3.74_copy_result.webp?v=1744177541",
                "description": "Active Noise Cancellation up to 40dB with Transparency mode, 10mm drivers, and precision dual-mic calling algorithms.",
                "specs": {
                    "ANC Depth": "Up to -40dB Hybrid ANC",
                    "Playtime": "40 Hours with Charging Case",
                    "Transparency Mode": "Supported ambient awareness",
                    "Drivers": "10mm Titanium Composite"
                }
            },
            # 9. Gaming Earbuds with RGB
            {
                "name": "Noise Buds Combat",
                "category": "Wireless Earbuds",
                "price": 1399.0,
                "original_price": 3999.0,
                "battery_life": 45.0,
                "anc": False,
                "rating": 4.2,
                "review_count": 1120,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/Black-Combat-Carousel-500x500-1.png?v=1673874381",
                "description": "Dedicated gaming earbuds with 45ms ultra-low latency, breathing RGB lights, and 13mm speaker drivers.",
                "specs": {
                    "Gaming Latency": "45ms Ultra-low gaming latency",
                    "Lighting": "Breathing RGB LED on case & pods",
                    "Playtime": "45 Hours total playtime",
                    "Drivers": "13mm deep bass drivers"
                }
            },
            # 10. Compact Classic Earbuds
            {
                "name": "Noise Buds VS201 V2",
                "category": "Wireless Earbuds",
                "price": 1199.0,
                "original_price": 2999.0,
                "battery_life": 36.0,
                "anc": False,
                "rating": 4.0,
                "review_count": 1890,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/b3.png?v=1627585394",
                "description": "Dual equalizer earbuds with full touch controls, lightweight fit, and Bluetooth 5.1 instant pairing.",
                "specs": {
                    "Playtime": "36 Hours playtime",
                    "Equalizer": "Dual EQ Modes (Bass / Normal)",
                    "Controls": "Full Touch Controls",
                    "Waterproof": "IPX4 splash resistant"
                }
            },
            # 11. Ultra Premium Studio ANC Earbuds
            {
                "name": "Noise Master Buds",
                "category": "Wireless Earbuds",
                "price": 3999.0,
                "original_price": 9999.0,
                "battery_life": 48.0,
                "anc": True,
                "rating": 4.7,
                "review_count": 780,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/Artboard9_result_e8b91d73-7a1a-4375-a0ce-f6a825fad7e2.webp?v=1773898750",
                "description": "Audiophile grade Hi-Res wireless audio earbuds with 45dB Active Noise Cancellation and 6-mic studio voice processing.",
                "specs": {
                    "Audio Codec": "Hi-Res LDAC & AAC support",
                    "ANC": "45dB Adaptive Active Noise Cancellation",
                    "Mics": "6-Mic System with ENC & Wind Shield",
                    "Battery": "48 Hours playtime (wireless charging)"
                }
            },
            # 12. Wireless Neckband
            {
                "name": "Noise Tune Charge",
                "category": "Neckbands",
                "price": 999.0,
                "original_price": 2499.0,
                "battery_life": 35.0,
                "anc": False,
                "rating": 4.2,
                "review_count": 2740,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/Artboard1_f25c5842-36c2-4588-a9b3-f6482b5e28c1.png?v=1627585694",
                "description": "Wireless magnetic neckband with dedicated bass booster button, Qualcomm chipset, and 35 hours battery life.",
                "specs": {
                    "Playtime": "35 Hours continuous playback",
                    "Bass Booster": "Dedicated physical bass booster switch",
                    "Charging": "Type-C Fast Charging",
                    "Magnetic Earbuds": "Magnetic clip lock on buds"
                }
            },
            # 13. Marathon Battery Neckband
            {
                "name": "Noise Flair XL",
                "category": "Neckbands",
                "price": 1299.0,
                "original_price": 3999.0,
                "battery_life": 80.0,
                "anc": False,
                "rating": 4.4,
                "review_count": 1390,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/2.1699.png?v=1656585389",
                "description": "Marathon battery neckband delivering up to 80 hours playtime, environmental noise cancellation, and vibration call alerts.",
                "specs": {
                    "Battery": "Huge 80 Hours non-stop playtime",
                    "Vibration": "Built-in incoming call vibration alert",
                    "Fast Charge": "10 mins charge = 15 hours playback",
                    "Drivers": "10mm Titanium-coated drivers"
                }
            },
            # 14. Open-Ear Audio Pods
            {
                "name": "Noise Pure Pods",
                "category": "Wireless Earbuds",
                "price": 2999.0,
                "original_price": 6999.0,
                "battery_life": 80.0,
                "anc": False,
                "rating": 4.3,
                "review_count": 860,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/5_78ab6c3d-0bf3-495b-9580-c640e5cf459d.webp?v=1720444316",
                "description": "Revolutionary AirWave technology open-ear wireless pods for zero ear fatigue, natural ambient listening, and 80h battery.",
                "specs": {
                    "Technology": "AirWave Open-Ear Sound Diffusion",
                    "Comfort": "Zero in-ear pressure earhooks",
                    "Battery": "80 Hours total playtime with dock",
                    "Calls": "Quad Mic directional ENC"
                }
            },
            # 15. Wireless Over-Ear Headphones
            {
                "name": "Noise Two Wireless Headphones",
                "category": "Headphones",
                "price": 1799.0,
                "original_price": 4999.0,
                "battery_life": 50.0,
                "anc": False,
                "rating": 4.2,
                "review_count": 690,
                "is_featured": False,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/1_3941f406-f4ff-4692-8ef4-6719497a0f56.webp?v=1720759157",
                "description": "Ergonomic foldable over-ear headphones with 40mm drivers, dual pairing capability, and plush protein leather earcups.",
                "specs": {
                    "Drivers": "40mm High Definition Drivers",
                    "Playtime": "50 Hours battery reserve",
                    "Connectivity": "Bluetooth 5.3 + 3.5mm AUX Backup",
                    "Form Factor": "Foldable compact design"
                }
            },
            # 16. Smart Audio Sunglasses
            {
                "name": "Noise i1 Smart Glasses",
                "category": "Smart Eyewear",
                "price": 4999.0,
                "original_price": 9999.0,
                "battery_life": 9.0,
                "anc": False,
                "rating": 4.1,
                "review_count": 420,
                "is_featured": True,
                "in_stock": True,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/S1_57e9472f-ddeb-4b8d-b74c-2ef1bf551ab1.png?v=1682400943",
                "description": "Cutting edge audio sunglasses with polarized UVA/UVB protection, open-ear directional sound, and Siri/Google voice control.",
                "specs": {
                    "Lenses": "Interchangeable Polarized UV400 Lenses",
                    "Audio": "Open-ear directional acoustic speakers",
                    "Playtime": "9 Hours audio playback on single charge",
                    "Controls": "Touch controls on temple stems"
                }
            }
        ]

        created_products = []
        for pdata in products_data:
            prod = Product(
                name=pdata['name'],
                slug=slugify(pdata['name']),
                category=pdata['category'],
                price=pdata['price'],
                original_price=pdata['original_price'],
                battery_life=pdata['battery_life'],
                anc=pdata['anc'],
                rating=pdata['rating'],
                review_count=pdata['review_count'],
                image_url=pdata['image_url'],
                description=pdata['description'],
                in_stock=pdata['in_stock'],
                is_featured=pdata['is_featured']
            )
            prod.specs = pdata['specs']
            db.session.add(prod)
            created_products.append(prod)

        db.session.commit()
        print(f"✅ Created {len(created_products)} Noise electronics products.")

        # Seed sample orders so Admin Dashboard has real metrics immediately
        print("📦 Seeding sample orders for Admin Dashboard...")
        sample_customers = [
            ("Aarav Sharma", "aarav.sharma@example.com", "Flat 402, Green Glen Layout, Bellandur, Bangalore - 560103"),
            ("Priya Nair", "priya.nair@example.com", "House 12, Anna Nagar West, Chennai - 600040"),
            ("Rohan Mehta", "rohan.mehta@example.com", "B-204, Lodha Splendora, Ghodbunder Rd, Thane, Mumbai - 400615"),
            ("Sneha Roy", "sneha.roy@example.com", "Sector 62, Noida, Uttar Pradesh - 201309"),
            ("Kavita Patel", "kavita.patel@example.com", "Vastrapur Lake Road, Ahmedabad - 380015"),
            ("Aditya Verma", "aditya.v@example.com", "Banjara Hills Road No 10, Hyderabad - 500034")
        ]

        for i, (name, email, addr) in enumerate(sample_customers, 1):
            chosen_prods = random.sample(created_products, k=random.randint(1, 3))
            subtotal = sum(p.price for p in chosen_prods)
            gst = round(subtotal * 0.18, 2)
            shipping = 0.0 if subtotal >= 999 else 99.0
            total = round(subtotal + gst + shipping, 2)

            order = Order(
                order_number=f"NOISE-{int(datetime.now(timezone.utc).timestamp()) - (i * 3600 * 6)}-{random.randint(1000, 9999)}",
                customer_name=name,
                customer_email=email,
                address=addr,
                subtotal=subtotal,
                shipping_fee=shipping,
                gst_amount=gst,
                total_amount=total,
                status=random.choice(['completed', 'completed', 'completed', 'processing']),
                created_at=datetime.now(timezone.utc) - timedelta(days=i * 2, hours=random.randint(1, 10))
            )
            db.session.add(order)
            db.session.flush()

            for p in chosen_prods:
                item = OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    quantity=1,
                    unit_price=p.price
                )
                db.session.add(item)

        db.session.commit()
        print(f"✅ Seeded {len(sample_customers)} realistic sample orders with line items.")
        print("🎉 Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
