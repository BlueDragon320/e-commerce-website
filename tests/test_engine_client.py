from unittest.mock import patch, MagicMock
import pytest
import requests
from app.engine_client import RankingEngineClient

def test_engine_client_init(app):
    """Test client initialization and default properties."""
    with app.app_context():
        client = RankingEngineClient()
        assert client.base_url == "http://localhost:5000"
        assert client.company_id == 1
        assert client.timeout == 3.0

def test_health_check_online(app):
    """Test health check when engine is reachable."""
    with app.app_context():
        client = RankingEngineClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'status': 'success',
            'company_name': 'TechMart Electronics',
            'categories': [{'category_id': 1}]
        }
        with patch('requests.get', return_value=mock_resp):
            health = client.health_check()
            assert health['status'] == 'online'
            assert health['company_id'] == 1
            assert health['latency_ms'] is not None

def test_health_check_offline(app):
    """Test health check when engine is unreachable."""
    with app.app_context():
        client = RankingEngineClient()
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Connection refused")):
            health = client.health_check()
            assert health['status'] == 'offline'
            assert health['latency_ms'] is None
            assert 'Connection refused' in health['error']

def test_get_categories_online(app):
    """Test categories retrieval when engine responds."""
    with app.app_context():
        client = RankingEngineClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'status': 'success',
            'categories': [{'category_id': 1, 'name': 'Wireless Earbuds'}]
        }
        with patch('requests.get', return_value=mock_resp):
            data = client.get_categories()
            assert data['status'] == 'success'
            assert data['engine_status'] == 'online'
            assert len(data['categories']) == 1

def test_get_categories_offline_fallback(app):
    """Test categories retrieval fallback when engine is offline."""
    with app.app_context():
        client = RankingEngineClient()
        with patch('requests.get', side_effect=requests.exceptions.ConnectTimeout()):
            data = client.get_categories()
            assert data['status'] == 'success'
            assert data['engine_status'] == 'offline'
            assert len(data['categories']) > 0

def test_search_offline_fallback(app):
    """
    Critical requirement: If connection fails or returns error,
    fallback gracefully to local database search and flag engine_status='offline'.
    """
    with app.app_context():
        client = RankingEngineClient()
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Engine down")):
            res = client.search(query="VS102")
            assert res['status'] == 'success'
            assert res['engine_status'] == 'offline'
            assert res['fallback'] is True
            assert res['total_results'] >= 1
            first = res['results'][0]
            assert "VS102" in first['name']
            assert 'composite_score' in first
            assert 'attributes' in first

def test_search_with_custom_weights(app):
    """Test dynamic custom weights passed to engine search."""
    with app.app_context():
        client = RankingEngineClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'status': 'success',
            'results': [
                {
                    'rank': 1,
                    'product_id': 1,
                    'name': 'OnePlus Nord Buds 2',
                    'composite_score': 0.88,
                    'score_pct': '88.00%',
                    'is_sponsored': False,
                    'attributes': {}
                }
            ]
        }
        custom_weights = {
            'Battery Life (hours)': 50.0,
            'Price (INR)': 30.0,
            'Rating': 10.0,
            'Active Noise Cancelling': 10.0
        }
        with patch('requests.post', return_value=mock_resp) as mock_post:
            res = client.search(category_id=1, custom_weights=custom_weights)
            assert res['status'] == 'success'
            assert res['engine_status'] == 'online'
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs['json']['custom_weights'] == custom_weights

def test_product_breakdown_fallback(app):
    """Test product breakdown when engine is offline."""
    with app.app_context():
        client = RankingEngineClient()
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError()):
            # Test with local product id 1
            breakdown = client.get_product_breakdown(1)
            assert breakdown['status'] == 'success'
            assert breakdown['engine_status'] == 'offline'
            assert 'score_breakdown' in breakdown
            assert len(breakdown['score_breakdown']) == 4
            assert breakdown['composite_score'] > 0

def test_enrich_with_local_products_image_sync_existing(app):
    """Test that when engine returns image_url, existing local product is updated and committed."""
    with app.app_context():
        from app import db
        from app.models import Product
        client = RankingEngineClient()
        prod = db.session.get(Product, 1)
        original_img = prod.image_url
        new_engine_img = "https://images.unsplash.com/photo-test-engine-image?w=800"

        results = [{
            'product_id': 1,
            'name': prod.name,
            'image_url': new_engine_img,
            'attributes': {'Price': 1999.0}
        }]
        with patch.dict(app.config, {'TESTING': False}):
            client._enrich_with_local_products(results)

        assert results[0]['image_url'] == new_engine_img
        updated_prod = db.session.get(Product, 1)
        assert updated_prod.image_url == new_engine_img

        # Restore original image
        updated_prod.image_url = original_img
        db.session.commit()

def test_enrich_with_local_products_auto_create_missing(app):
    """Test that missing product with engine image_url is auto-created in local database."""
    with app.app_context():
        from app import db
        from app.models import Product
        client = RankingEngineClient()
        test_id = 99999
        # Ensure not existing
        existing = db.session.get(Product, test_id)
        if existing:
            db.session.delete(existing)
            db.session.commit()

        engine_img = "https://images.unsplash.com/photo-new-headphones-123?w=800"
        results = [{
            'product_id': test_id,
            'name': 'Auto Created Engine Product',
            'category_name': 'Headphones',
            'image_url': engine_img,
            'attributes': {'Price': 3499.0, 'Rating': 4.5}
        }]
        with patch.dict(app.config, {'TESTING': False}):
            client._enrich_with_local_products(results)

        assert results[0]['image_url'] == engine_img
        new_prod = db.session.get(Product, test_id)
        assert new_prod is not None
        assert new_prod.name == 'Auto Created Engine Product'
        assert new_prod.image_url == engine_img
        assert new_prod.price == 3499.0

        # Clean up
        db.session.delete(new_prod)
        db.session.commit()

def test_sync_product_to_engine_payload_includes_image(app):
    """Test that sync_product_to_engine includes image_url in payload sent to engine."""
    with app.app_context():
        client = RankingEngineClient()
        test_prod = {
            'id': 1,
            'name': 'Sync Test Product',
            'price': 1499.0,
            'rating': 4.1,
            'image_url': 'https://example.com/test-image.jpg'
        }
        with patch.dict(app.config, {'TESTING': False}):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            with patch('requests.post', return_value=mock_resp) as mock_post:
                res = client.sync_product_to_engine(test_prod)
                assert res is not None
                mock_post.assert_called_once()
                call_json = mock_post.call_args[1]['json']
                assert call_json['image_url'] == 'https://example.com/test-image.jpg'
                assert call_json['price'] == 1499.0

# -----------------------------------------------------------------------------
# Live Integration Tests with Weighted Ranking Engine on Port 5000
# -----------------------------------------------------------------------------

def _engine_online():
    try:
        r = requests.get('http://localhost:5000/api/v1/health', timeout=0.5)
        return r.status_code == 200
    except Exception:
        return False

@pytest.mark.skipif(not _engine_online(), reason="Live ranking engine not running on localhost:5000")
def test_live_engine_health_and_company(app):
    """Verify live integration with port 5000: health check and company name."""
    with app.app_context():
        client = RankingEngineClient()
        health = client.health_check()
        assert health['status'] == 'online'
        assert health['company_id'] == 1
        assert health['company_name'] == 'Noise Official'
        assert health['latency_ms'] is not None

@pytest.mark.skipif(not _engine_online(), reason="Live ranking engine not running on localhost:5000")
def test_live_engine_categories_noise(app):
    """Verify live categories on port 5000 match official Noise categories."""
    with app.app_context():
        client = RankingEngineClient()
        data = client.get_categories()
        assert data['status'] == 'success'
        assert data['engine_status'] == 'online'
        assert data['company_name'] == 'Noise Official'
        cat_names = [c['name'] for c in data['categories']]
        expected_cats = ['Wireless Earbuds', 'Smartwatches', 'Neckbands', 'Headphones', 'Smart Eyewear']
        for expected in expected_cats:
            assert expected in cat_names, f"Expected category '{expected}' in {cat_names}"

@pytest.mark.skipif(not _engine_online(), reason="Live ranking engine not running on localhost:5000")
def test_live_engine_search_noise_products(app):
    """Verify live search on port 5000 returns Noise products with ranks and composite scores."""
    with app.app_context():
        client = RankingEngineClient()
        # Search all
        res = client.search(limit=20)
        assert res['status'] == 'success'
        assert res['engine_status'] == 'online'
        assert len(res['results']) >= 16
        
        # Verify specific Noise products exist in results
        names = [p['name'] for p in res['results']]
        assert any('VS102' in n for n in names)
        assert any('Ultra 3' in n for n in names)
        assert any('Air Buds Pro 2' in n for n in names)
        
        # Verify rank and composite scores
        for item in res['results']:
            assert 'rank' in item
            assert item['rank'] >= 1
            assert 'composite_score' in item
            assert item['composite_score'] > 0
            assert 'attributes' in item

@pytest.mark.skipif(not _engine_online(), reason="Live ranking engine not running on localhost:5000")
def test_live_engine_category_filtering(app):
    """Verify live category-specific search returns matching Noise category products."""
    with app.app_context():
        client = RankingEngineClient()
        cats = client.get_categories().get('categories', [])
        earbuds_cat = next((c for c in cats if 'Earbud' in c['name']), None)
        assert earbuds_cat is not None
        cat_id = earbuds_cat['category_id']

        res = client.search(category_id=cat_id)
        assert res['status'] == 'success'
        assert len(res['results']) == 7
        for p in res['results']:
            assert p['category_name'] == 'Wireless Earbuds'

