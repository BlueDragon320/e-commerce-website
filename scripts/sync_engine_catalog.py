#!/usr/bin/env python3
"""
scripts/sync_engine_catalog.py
Synchronize the Weighted Ranking Engine database (port 5000) with the complete Noise product catalog.
Sets Company 1 as 'Noise Official', creates 5 categories:
  - Wireless Earbuds (ID 4)
  - Smartwatches (ID 5)
  - Neckbands (ID 6)
  - Headphones (ID 7) - containing Noise Two Wireless Headphones
  - Smart Eyewear (ID 8)
Registers attributes with calibrated weights (summing to 100%), seeds all 16 Noise products with
attribute values, recomputes composite scores, and sets sponsored placement.
Noise Official is the sole tenant.
"""
import sys
import os
from datetime import date, datetime, timedelta, timezone

# Prevent bytecode compilation
sys.dont_write_bytecode = True

def resolve_engine_dir():
    """Dynamically resolve the Product-Catalogue-Ranked-Search directory."""
    candidates = [
        os.environ.get('RANKING_ENGINE_DIR'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Product-Catalogue-Ranked-Search')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Product-Catalogue-Ranked-Search')),
        '/home/blue/mini-pjct/Product-Catalogue-Ranked-Search',
        '/home/blue/Collage-Mini-Project/Product-Catalogue-Ranked-Search',
        '/home/blue/MiniProject/weighted-ranking-engine',
    ]
    for c in candidates:
        if c and os.path.isdir(c) and os.path.isfile(os.path.join(c, 'app', 'models.py')):
            return os.path.abspath(c)

    for p in sys.path:
        if p and os.path.isdir(p) and os.path.isfile(os.path.join(p, 'app', 'models.py')):
            return os.path.abspath(p)

    raise RuntimeError("Could not dynamically resolve Product-Catalogue-Ranked-Search directory.")

ENGINE_DIR = resolve_engine_dir()
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from app import create_app, db
from app.models import Company, Category, Attribute, Product, ProductAttrValue, SponsoredPlacement, SearchLog, User
from app.ranking.engine import recompute_category_scores

def sync():
    print(f"📁 Ranking Engine Directory resolved to: {ENGINE_DIR}")
    app = create_app('development')
    with app.app_context():
        print("⚡ Synchronizing Weighted Ranking Engine catalog...")

        # -------------------------------------------------------------
        # 1. Super Admin (Platform Operator without tenant lock)
        # -------------------------------------------------------------
        superadmin = User.query.filter_by(username='admin').first()
        if not superadmin:
            superadmin = User(
                username='admin',
                email='admin@rankengine.io',
                company_id=None,
                is_admin=True,
                is_superadmin=True
            )
            superadmin.set_password('admin123')
            db.session.add(superadmin)
            print("  ✓ Platform Superadmin account provisioned (admin / admin123)")
        else:
            superadmin.is_admin = True
            superadmin.is_superadmin = True
            superadmin.set_password('admin123')
        db.session.commit()

        # -------------------------------------------------------------
        # 2. Company 1: Noise Official & Manager (techmart_admin)
        # -------------------------------------------------------------
        company1 = db.session.get(Company, 1)
        if not company1:
            company1 = Company(company_id=1, name='Noise Official')
            db.session.add(company1)
        else:
            company1.name = 'Noise Official'
        db.session.commit()

        # Manager for Company 1
        techmart_manager = User.query.filter_by(username='techmart_admin').first()
        if not techmart_manager:
            techmart_manager = User(
                username='techmart_admin',
                email='admin@techmart.com',
                company_id=1,
                is_admin=True,
                is_superadmin=False
            )
            techmart_manager.set_password('company123')
            db.session.add(techmart_manager)
            print("  ✓ Tenant 1 Manager provisioned (techmart_admin / company123)")
        else:
            techmart_manager.company_id = 1
            techmart_manager.set_password('company123')
        db.session.commit()

        # -------------------------------------------------------------
        # 4. Clean up old Company 1 data (Only Company 1, preserving Company 2)
        # -------------------------------------------------------------
        old_cats = Category.query.filter_by(company_id=1).all()
        old_cat_ids = [c.category_id for c in old_cats]

        if old_cat_ids:
            old_prods = Product.query.filter(Product.category_id.in_(old_cat_ids)).all()
            old_prod_ids = [p.product_id for p in old_prods]
            
            if old_prod_ids:
                SponsoredPlacement.query.filter(SponsoredPlacement.product_id.in_(old_prod_ids)).delete(synchronize_session=False)
                ProductAttrValue.query.filter(ProductAttrValue.product_id.in_(old_prod_ids)).delete(synchronize_session=False)
                Product.query.filter(Product.product_id.in_(old_prod_ids)).delete(synchronize_session=False)

            SearchLog.query.filter(SearchLog.category_id.in_(old_cat_ids)).delete(synchronize_session=False)
            Attribute.query.filter(Attribute.category_id.in_(old_cat_ids)).delete(synchronize_session=False)
            Category.query.filter(Category.category_id.in_(old_cat_ids)).delete(synchronize_session=False)
            db.session.commit()
            db.session.expunge_all()
            print(f"  ✓ Purged previous Company 1 records (Categories: {old_cat_ids})")

        # -------------------------------------------------------------
        # 5. Create the 5 Official Categories for Noise Official
        # Explicit Category IDs: 4 (Earbuds), 5 (Smartwatches), 6 (Neckbands), 7 (Headphones), 8 (Eyewear)
        # -------------------------------------------------------------
        category_configs = {
            'Wireless Earbuds': {
                'id': 4,
                'display_attr_1': 'Battery Life (hours)',
                'display_attr_2': 'Active Noise Cancelling',
                'attrs': [
                    {'name': 'Battery Life (hours)', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 100.0, 'weight': 35.0, 'lower_is_better': False},
                    {'name': 'Price (INR)', 'data_type': 'numeric', 'min_value': 500.0, 'max_value': 15000.0, 'weight': 35.0, 'lower_is_better': True},
                    {'name': 'Rating', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 5.0, 'weight': 15.0, 'lower_is_better': False},
                    {'name': 'Active Noise Cancelling', 'data_type': 'binary', 'min_value': 0.0, 'max_value': 1.0, 'weight': 15.0, 'lower_is_better': False}
                ]
            },
            'Smartwatches': {
                'id': 5,
                'display_attr_1': 'Battery Life (hours)',
                'display_attr_2': 'Rating',
                'attrs': [
                    {'name': 'Battery Life (hours)', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 300.0, 'weight': 35.0, 'lower_is_better': False},
                    {'name': 'Price (INR)', 'data_type': 'numeric', 'min_value': 1000.0, 'max_value': 15000.0, 'weight': 35.0, 'lower_is_better': True},
                    {'name': 'Rating', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 5.0, 'weight': 30.0, 'lower_is_better': False}
                ]
            },
            'Neckbands': {
                'id': 6,
                'display_attr_1': 'Battery Life (hours)',
                'display_attr_2': 'Active Noise Cancelling',
                'attrs': [
                    {'name': 'Battery Life (hours)', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 120.0, 'weight': 35.0, 'lower_is_better': False},
                    {'name': 'Price (INR)', 'data_type': 'numeric', 'min_value': 500.0, 'max_value': 10000.0, 'weight': 35.0, 'lower_is_better': True},
                    {'name': 'Rating', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 5.0, 'weight': 15.0, 'lower_is_better': False},
                    {'name': 'Active Noise Cancelling', 'data_type': 'binary', 'min_value': 0.0, 'max_value': 1.0, 'weight': 15.0, 'lower_is_better': False}
                ]
            },
            'Headphones': {
                'id': 7,
                'display_attr_1': 'Battery Life (hours)',
                'display_attr_2': 'Active Noise Cancelling',
                'attrs': [
                    {'name': 'Battery Life (hours)', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 100.0, 'weight': 35.0, 'lower_is_better': False},
                    {'name': 'Price (INR)', 'data_type': 'numeric', 'min_value': 500.0, 'max_value': 15000.0, 'weight': 35.0, 'lower_is_better': True},
                    {'name': 'Rating', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 5.0, 'weight': 15.0, 'lower_is_better': False},
                    {'name': 'Active Noise Cancelling', 'data_type': 'binary', 'min_value': 0.0, 'max_value': 1.0, 'weight': 15.0, 'lower_is_better': False}
                ]
            },
            'Smart Eyewear': {
                'id': 8,
                'display_attr_1': 'Battery Life (hours)',
                'display_attr_2': 'Rating',
                'attrs': [
                    {'name': 'Battery Life (hours)', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 24.0, 'weight': 35.0, 'lower_is_better': False},
                    {'name': 'Price (INR)', 'data_type': 'numeric', 'min_value': 1000.0, 'max_value': 15000.0, 'weight': 35.0, 'lower_is_better': True},
                    {'name': 'Rating', 'data_type': 'numeric', 'min_value': 0.0, 'max_value': 5.0, 'weight': 30.0, 'lower_is_better': False}
                ]
            }
        }

        created_cats = {}
        attr_objs = {}

        for cat_name, conf in category_configs.items():
            cat = Category(
                category_id=conf['id'],
                name=cat_name,
                company_id=1,
                display_attr_1=conf.get('display_attr_1'),
                display_attr_2=conf.get('display_attr_2')
            )
            db.session.add(cat)
            db.session.flush()
            created_cats[cat_name] = cat

            attr_objs[cat_name] = {}
            for attr_def in conf['attrs']:
                attr = Attribute(
                    category_id=cat.category_id,
                    name=attr_def['name'],
                    data_type=attr_def['data_type'],
                    min_value=attr_def['min_value'],
                    max_value=attr_def['max_value'],
                    weight=attr_def['weight'],
                    lower_is_better=attr_def['lower_is_better']
                )
                db.session.add(attr)
                db.session.flush()
                attr_objs[cat_name][attr_def['name']] = attr

        db.session.commit()
        for cat_name, cat in created_cats.items():
            print(f"  ✓ Category created: '{cat_name}' (ID: {cat.category_id}) with {len(attr_objs[cat_name])} attributes")

        # -------------------------------------------------------------
        # 6. Catalog Products (16 Noise products matching Storefront)
        # -------------------------------------------------------------
        products_data = [
            # Smartwatches (Category ID 5)
            {
                "name": "Noise ColorFit Ultra 3",
                "category": "Smartwatches",
                "price": 2999.0,
                "battery": 168.0,
                "rating": 4.5,
                "anc": 0.0,
                "hits": 184,
                "image_url": "https://www.gonoise.com/cdn/shop/files/NoiseColorFitUltra3-BlackEliteEdition_1_grande.png?v=1695122129"
            },
            {
                "name": "NoiseFit Halo",
                "category": "Smartwatches",
                "price": 2499.0,
                "battery": 168.0,
                "rating": 4.4,
                "anc": 0.0,
                "hits": 142,
                "image_url": "https://www.gonoise.com/cdn/shop/files/1_1_b18f77db-5fef-4698-9902-a48fec2b8efa_grande.png?v=1704963291"
            },
            {
                "name": "Noise ColorFit Icon 2",
                "category": "Smartwatches",
                "price": 1499.0,
                "battery": 120.0,
                "rating": 4.2,
                "anc": 0.0,
                "hits": 289,
                "image_url": "https://www.gonoise.com/cdn/shop/products/Icon2-5_grande.png?v=1681610912"
            },
            {
                "name": "Noise ColorFit Pro 4 Alpha",
                "category": "Smartwatches",
                "price": 3499.0,
                "battery": 168.0,
                "rating": 4.6,
                "anc": 0.0,
                "hits": 92,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/1_0ba84c50-3527-4c98-b643-f3f4f3075c27.png?v=1686911647"
            },
            {
                "name": "Noise Diva Smartwatch",
                "category": "Smartwatches",
                "price": 2999.0,
                "battery": 96.0,
                "rating": 4.4,
                "anc": 0.0,
                "hits": 64,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/Artboard19_result_5250da54-389e-4afa-a440-870f0bae2459.webp?v=1776673795"
            },
            
            # Wireless Earbuds (Category ID 4)
            {
                "name": "Noise Buds VS102",
                "category": "Wireless Earbuds",
                "price": 1099.0,
                "battery": 50.0,
                "rating": 4.1,
                "anc": 0.0,
                "hits": 352,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/1_9e839f18-7b82-4b71-ab98-471982ca91ef.png?v=1682439948"
            },
            {
                "name": "Noise Buds VS404",
                "category": "Wireless Earbuds",
                "price": 1299.0,
                "battery": 45.0,
                "rating": 4.3,
                "anc": 0.0,
                "hits": 218,
                "image_url": "https://www.gonoise.com/cdn/shop/files/image_2023_09_19T10_11_28_596Z_grande.png?v=1695119844"
            },
            {
                "name": "Noise Air Buds Pro 2 with ANC",
                "category": "Wireless Earbuds",
                "price": 2499.0,
                "battery": 40.0,
                "rating": 4.5,
                "anc": 1.0,
                "hits": 165,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/3.74_copy_result.webp?v=1744177541"
            },
            {
                "name": "Noise Buds Combat",
                "category": "Wireless Earbuds",
                "price": 1399.0,
                "battery": 45.0,
                "rating": 4.2,
                "anc": 0.0,
                "hits": 112,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/Black-Combat-Carousel-500x500-1.png?v=1673874381"
            },
            {
                "name": "Noise Buds VS201 V2",
                "category": "Wireless Earbuds",
                "price": 1199.0,
                "battery": 36.0,
                "rating": 4.0,
                "anc": 0.0,
                "hits": 189,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/b3.png?v=1627585394"
            },
            {
                "name": "Noise Master Buds",
                "category": "Wireless Earbuds",
                "price": 3999.0,
                "battery": 48.0,
                "rating": 4.7,
                "anc": 1.0,
                "hits": 78,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/Artboard9_result_e8b91d73-7a1a-4375-a0ce-f6a825fad7e2.webp?v=1773898750"
            },
            {
                "name": "Noise Pure Pods",
                "category": "Wireless Earbuds",
                "price": 2999.0,
                "battery": 80.0,
                "rating": 4.3,
                "anc": 0.0,
                "hits": 86,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/5_78ab6c3d-0bf3-495b-9580-c640e5cf459d.webp?v=1720444316"
            },

            # Neckbands (Category ID 6)
            {
                "name": "Noise Tune Charge",
                "category": "Neckbands",
                "price": 999.0,
                "battery": 35.0,
                "rating": 4.2,
                "anc": 0.0,
                "hits": 274,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/Artboard1_f25c5842-36c2-4588-a9b3-f6482b5e28c1.png?v=1627585694"
            },
            {
                "name": "Noise Flair XL",
                "category": "Neckbands",
                "price": 1299.0,
                "battery": 80.0,
                "rating": 4.4,
                "anc": 0.0,
                "hits": 139,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/2.1699.png?v=1656585389"
            },

            # Headphones (Category ID 7)
            {
                "name": "Noise Two Wireless Headphones",
                "category": "Headphones",
                "price": 1799.0,
                "battery": 50.0,
                "rating": 4.2,
                "anc": 0.0,
                "hits": 69,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/files/1_3941f406-f4ff-4692-8ef4-6719497a0f56.webp?v=1720759157"
            },

            # Smart Eyewear (Category ID 8)
            {
                "name": "Noise i1 Smart Glasses",
                "category": "Smart Eyewear",
                "price": 4999.0,
                "battery": 9.0,
                "rating": 4.1,
                "anc": 0.0,
                "hits": 42,
                "image_url": "https://cdn.shopify.com/s/files/1/0997/6284/products/S1_57e9472f-ddeb-4b8d-b74c-2ef1bf551ab1.png?v=1682400943"
            }
        ]

        created_products = []
        air_buds_pro_product = None

        for p_data in products_data:
            cat_name = p_data['category']
            cat = created_cats[cat_name]

            prod = Product(
                name=p_data['name'],
                category_id=cat.category_id,
                search_count=p_data['hits'],
                image_url=p_data.get('image_url')
            )
            db.session.add(prod)
            db.session.flush()
            created_products.append(prod)

            if prod.name == "Noise Air Buds Pro 2 with ANC":
                air_buds_pro_product = prod

            # Add attribute values
            cat_attrs = attr_objs[cat_name]
            for attr_name, attr_model in cat_attrs.items():
                if attr_name == 'Battery Life (hours)':
                    val = p_data['battery']
                elif attr_name == 'Price (INR)':
                    val = p_data['price']
                elif attr_name == 'Rating':
                    val = p_data['rating']
                elif attr_name == 'Active Noise Cancelling':
                    val = p_data['anc']
                else:
                    val = 0.0

                pav = ProductAttrValue(
                    product_id=prod.product_id,
                    attribute_id=attr_model.attribute_id,
                    raw_value=val
                )
                db.session.add(pav)

        db.session.commit()
        print(f"  ✓ 16 Noise products and attribute measurements registered across 5 categories.")

        # -------------------------------------------------------------
        # 7. Recompute composite scores for all categories
        # -------------------------------------------------------------
        for cat_name, cat in created_cats.items():
            recompute_category_scores(cat.category_id, db.session, Product, Attribute, ProductAttrValue)
            print(f"  ✓ Recomputed composite scores for category '{cat_name}' (ID: {cat.category_id})")

        # -------------------------------------------------------------
        # 8. Add active sponsored placement for Noise Air Buds Pro 2 with ANC
        # -------------------------------------------------------------
        if air_buds_pro_product:
            sp = SponsoredPlacement(
                product_id=air_buds_pro_product.product_id,
                slot_position=1,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                is_active=True
            )
            db.session.add(sp)
            db.session.commit()
            print(f"  ✓ Sponsored placement created for '{air_buds_pro_product.name}' at slot 1")

        # -------------------------------------------------------------
        # 9. Add seed search logs for insights
        # -------------------------------------------------------------
        search_queries = [
            ("ear phones", created_cats['Wireless Earbuds'].category_id, 7),
            ("earbuds", created_cats['Wireless Earbuds'].category_id, 7),
            ("smart watch", created_cats['Smartwatches'].category_id, 5),
            ("anc earbuds", created_cats['Wireless Earbuds'].category_id, 2),
            ("noise smart watch", created_cats['Smartwatches'].category_id, 5),
            ("wireless neckband", created_cats['Neckbands'].category_id, 2),
            ("noise headphones", created_cats['Headphones'].category_id, 1),
            ("smart glasses", created_cats['Smart Eyewear'].category_id, 1)
        ]
        for q_text, cid, r_cnt in search_queries:
            slog = SearchLog(
                query_text=q_text,
                category_id=cid,
                results_count=r_cnt,
                searched_at=datetime.now(timezone.utc) - timedelta(minutes=10)
            )
            db.session.add(slog)
        db.session.commit()
        print("  ✓ Analytics search logs generated.")

        print("\n🎉 Sync completed successfully! 16 Noise products indexed across 5 categories.")
        print(f"   Platform Superadmin : admin / admin123 (Inspect all categories)")
        print(f"   Tenant ('Noise Official'): techmart_admin / company123, noise_admin / company123 (Categories: 4, 5, 6, 7, 8)")

if __name__ == '__main__':
    sync()
