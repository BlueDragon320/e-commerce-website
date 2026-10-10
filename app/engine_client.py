import re
import difflib
import time
import logging
import requests
from flask import current_app, has_app_context
from app import db

logger = logging.getLogger(__name__)

# Category synonyms and natural language intent dictionaries
CATEGORY_SYNONYMS = {
    4: {
        'name': 'Wireless Earbuds',
        'synonyms': {
            'earphone', 'earphones', 'ear phone', 'ear phones',
            'earfone', 'earfones', 'ear pod', 'ear pods',
            'earpod', 'earpods', 'ear bud', 'ear buds',
            'earbud', 'earbuds', 'erbuds', 'earbds', 'erphones',
            'bud', 'buds', 'tws', 'airpod', 'airpods',
            'air pod', 'air pods', 'wireless earbuds', 'wireless buds',
            'audio', 'sound', 'pure pods'
        }
    },
    5: {
        'name': 'Smartwatches',
        'synonyms': {
            'watch', 'watches', 'watche', 'smartwatch', 'smartwatches',
            'samrtwatch', 'smartwach', 'smart watch', 'smart watches',
            'fitness watch', 'band', 'bands'
        }
    },
    6: {
        'name': 'Neckbands',
        'synonyms': {
            'neckband', 'neckbands', 'nekband', 'nekbands',
            'wireless neckband', 'neck band', 'neck bands'
        }
    },
    7: {
        'name': 'Headphones',
        'synonyms': {
            'headphone', 'headphones', 'head phone', 'head phones',
            'headfone', 'headfones', 'hedphone', 'hedphones',
            'head set', 'headset', 'head sets', 'headsets',
            'wireless headphones', 'wireless headphone', 'over ear', 'overear'
        }
    },
    8: {
        'name': 'Smart Eyewear',
        'synonyms': {
            'glasses', 'glases', 'eyewear', 'eyeware', 'smart glasses',
            'sunglasses', 'sunglases', 'smart eyewear', 'sun glasses'
        }
    },
    9: {
        'name': 'Power Bank',
        'synonyms': {
            'power bank', 'powerbank', 'power banks', 'powerbanks',
            'portable charger', 'battery pack', 'external battery'
        }
    }
}

# Master vocabulary for typo tolerance and spell fixing
ALL_VOCAB = set()
for cdata in CATEGORY_SYNONYMS.values():
    for syn in cdata['synonyms']:
        ALL_VOCAB.add(syn)
        ALL_VOCAB.add(syn.replace(' ', ''))
        for part in syn.split():
            ALL_VOCAB.add(part)

CATALOG_TERMS = {
    'colorfit', 'ultra', 'halo', 'icon', 'alpha', 'diva',
    'vs102', 'vs404', 'vs201', 'combat', 'master', 'pure',
    'charge', 'flair', 'two', 'glasses', 'noise', 'pro', 'anc'
}
ALL_VOCAB.update(CATALOG_TERMS)


def sanitize_text(text):
    """
    Convert input text to only alphanumeric text, stripping symbols/punctuation
    and normalizing whitespace.
    """
    if not text:
        return ''
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return ' '.join(cleaned.lower().split())


def correct_word(word):
    """
    Fix small spelling mistakes and phonetic typos using edit distance and fuzzy vocabulary matching.
    """
    w = word.lower().strip()
    if not w or len(w) < 3:
        return w
    if w in ALL_VOCAB:
        return w
    # Check phonetic fone -> phone
    if 'fone' in w:
        w_ph = w.replace('fone', 'phone')
        if w_ph in ALL_VOCAB:
            return w_ph
    matches = difflib.get_close_matches(w, list(ALL_VOCAB), n=1, cutoff=0.72)
    if matches:
        return matches[0]
    return w


def normalize_and_correct_query(query):
    """
    Preprocess search input:
    - Text-only sanitization
    - Collapsed whitespace form (e.g. 'head phones' -> 'headphones', 'vs 102' -> 'vs102')
    - Small spelling mistake correction (e.g. 'headfone' -> 'headphone', 'samrtwatch' -> 'smartwatch')
    """
    clean_q = sanitize_text(query)
    q_collapsed = clean_q.replace(' ', '')
    tokens = clean_q.split()
    corrected_tokens = [correct_word(t) for t in tokens]
    corrected_q = ' '.join(corrected_tokens)
    corrected_collapsed = ''.join(corrected_tokens)
    return clean_q, q_collapsed, corrected_q, corrected_collapsed


def detect_category_intent(query):
    """
    Intelligently map user search queries to category IDs, names, and remaining query.
    Supports:
    - Text-only sanitization (removes punctuation/symbols)
    - Spacing variations (e.g. 'head phones' vs 'headphones', 'smart watch' vs 'smartwatch')
    - Typo / spelling tolerance (e.g. 'headfone', 'hedphones', 'samrtwatch', 'nekband')
    - Multi-word compound queries (e.g. 'head phones bluetooth', 'combat ear buds')
    """
    if not query:
        return None, None, '', False

    clean_q, q_collapsed, corrected_q, corrected_collapsed = normalize_and_correct_query(query)

    # 1. Exact match with any synonym (with or without spaces)
    for cat_id, data in CATEGORY_SYNONYMS.items():
        for syn in data['synonyms']:
            syn_clean = sanitize_text(syn)
            syn_collapsed = syn_clean.replace(' ', '')
            if clean_q == syn_clean or q_collapsed == syn_collapsed:
                return cat_id, data['name'], '', True

    # 2. Typo-corrected match
    for cat_id, data in CATEGORY_SYNONYMS.items():
        for syn in data['synonyms']:
            syn_clean = sanitize_text(syn)
            syn_collapsed = syn_clean.replace(' ', '')
            if corrected_q == syn_clean or corrected_collapsed == syn_collapsed:
                return cat_id, data['name'], '', True

    # 3. Whole phrase/word match inside query (e.g. 'Combat earbuds' or 'head phones bluetooth')
    for cat_id, data in CATEGORY_SYNONYMS.items():
        sorted_syns = sorted(data['synonyms'], key=len, reverse=True)
        for s in sorted_syns:
            s_clean = sanitize_text(s)
            padded_q = f" {clean_q} "
            padded_s = f" {s_clean} "
            if padded_s in padded_q:
                rem = padded_q.replace(padded_s, " ").strip()
                return cat_id, data['name'], " ".join(rem.split()), False
            padded_cq = f" {corrected_q} "
            if padded_s in padded_cq:
                rem = padded_cq.replace(padded_s, " ").strip()
                return cat_id, data['name'], " ".join(rem.split()), False

    return None, None, query, False


CATEGORY_DISPLAY_ATTRS = {
    'Wireless Earbuds': ('Battery Life (hours)', 'Active Noise Cancelling'),
    'Smartwatches': ('Battery Life (hours)', None),
    'Neckbands': ('Battery Life (hours)', 'Active Noise Cancelling'),
    'Headphones': ('Battery Life (hours)', 'Active Noise Cancelling'),
    'Smart Eyewear': ('Battery Life (hours)', None),
    'Power Bank': ('battery size', 'MultiPorts'),
    'Studio Monitors': ('Acoustic Clarity (%)', None),
}


def get_badge_icon(name):
    """
    Enrich badge with an appropriate FontAwesome icon based on attribute name:
    - 'battery' or 'playtime' or 'life' or 'hours': 'fa-solid fa-battery-half text-slate-400'
    - 'port' or 'ports' or 'usb': 'fa-solid fa-plug text-slate-400'
    - 'metal' or 'body' or 'case': 'fa-solid fa-shield text-slate-400'
    - 'cancelling' or 'anc' or 'noise': 'fa-solid fa-shield-halved text-slate-400'
    - 'clarity' or 'sound' or 'acoustic': 'fa-solid fa-volume-high text-slate-400'
    - 'bluetooth' or 'wireless': 'fa-solid fa-bluetooth text-slate-400'
    - default: 'fa-solid fa-circle-check text-slate-400'
    """
    name_lower = (name or '').lower()
    if any(k in name_lower for k in ['battery', 'playtime', 'life', 'hours']):
        return 'fa-solid fa-battery-half text-slate-400'
    if any(k in name_lower for k in ['port', 'ports', 'usb']):
        return 'fa-solid fa-plug text-slate-400'
    if any(k in name_lower for k in ['metal', 'body', 'case']):
        return 'fa-solid fa-shield text-slate-400'
    if any(k in name_lower for k in ['cancelling', 'anc', 'noise']):
        return 'fa-solid fa-shield-halved text-slate-400'
    if any(k in name_lower for k in ['clarity', 'sound', 'acoustic']):
        return 'fa-solid fa-volume-high text-slate-400'
    if any(k in name_lower for k in ['bluetooth', 'wireless']):
        return 'fa-solid fa-bluetooth text-slate-400'
    return 'fa-solid fa-circle-check text-slate-400'


def format_badge_value(attr_name, val, data_type=None):
    """
    Format value:
    - If binary ('YES' / 'NO' / 1 / 0): show 'YES' or 'NO'
    - If numeric with hours: format as e.g. '40h'
    - If numeric with mah/battery size >= 1000: format as e.g. '10,000mAh' or '10000'
    - If integer-like: show integer (e.g. 2 instead of 2.0)
    """
    if val is None:
        return ''
    if isinstance(val, bool):
        return 'YES' if val else 'NO'

    attr_lower = (attr_name or '').lower()
    val_str = str(val).strip()
    val_upper = val_str.upper()

    # Direct binary representation strings
    if val_upper in ('YES', 'TRUE'):
        return 'YES'
    if val_upper in ('NO', 'FALSE'):
        return 'NO'

    # Binary check (data_type == 'binary' or known binary keywords in attribute name)
    is_binary = (data_type == 'binary') or any(k in attr_lower for k in ['cancelling', 'anc', 'metal'])
    if is_binary:
        try:
            num = float(val)
            return 'YES' if num > 0 else 'NO'
        except (ValueError, TypeError):
            pass

    # Numeric with hours (e.g. '40h')
    is_hours = any(k in attr_lower for k in ['hour', 'hours', 'playtime', 'battery life', 'life']) and 'size' not in attr_lower
    if is_hours:
        if val_str.lower().endswith('h'):
            return val_str
        try:
            num = float(val)
            return f"{int(num)}h" if num.is_integer() else f"{round(num, 1)}h"
        except (ValueError, TypeError):
            pass

    # Numeric with mah/battery size >= 1000 (e.g. '10,000mAh')
    is_mah = any(k in attr_lower for k in ['mah', 'battery size']) or ('battery' in attr_lower and 'size' in attr_lower)
    if is_mah:
        clean = val_str.replace(',', '').lower().replace('mah', '').strip()
        try:
            num = float(clean)
            if num >= 1000:
                return f"{int(num):,}mAh"
            return f"{int(num)}mAh" if num.is_integer() else f"{num}mAh"
        except (ValueError, TypeError):
            pass

    # Integer-like formatting (e.g. 2 instead of 2.0)
    try:
        num = float(val)
        return str(int(num)) if num.is_integer() else str(round(num, 2))
    except (ValueError, TypeError):
        pass

    return val_str


def build_display_badges_for_item(item):
    """
    Extract the 2 non-price, non-rating attributes from item.get('attributes', {})
    and generate display_badges.
    """
    attrs = item.get('attributes') or {}
    candidate_keys = [
        k for k in attrs.keys()
        if 'price' not in k.lower() and 'rating' not in k.lower()
    ]

    cat_name = item.get('category_name') or item.get('category') or ''
    if not cat_name and item.get('category_id') in CATEGORY_SYNONYMS:
        cat_name = CATEGORY_SYNONYMS[item['category_id']]['name']

    pref_1, pref_2 = CATEGORY_DISPLAY_ATTRS.get(cat_name, (None, None))

    selected_keys = []
    if pref_1 and pref_1 in attrs and 'price' not in pref_1.lower() and 'rating' not in pref_1.lower():
        selected_keys.append(pref_1)
    if pref_2 and pref_2 in attrs and 'price' not in pref_2.lower() and 'rating' not in pref_2.lower():
        selected_keys.append(pref_2)

    for k in candidate_keys:
        if len(selected_keys) >= 2:
            break
        if k not in selected_keys:
            selected_keys.append(k)

    badges = []
    for k in selected_keys[:2]:
        attr_obj = attrs[k]
        data_type = None
        if isinstance(attr_obj, dict):
            raw_val = attr_obj.get('display_value')
            if raw_val is None:
                raw_val = attr_obj.get('raw_value')
            data_type = attr_obj.get('data_type')
        else:
            raw_val = attr_obj
        formatted = format_badge_value(k, raw_val, data_type=data_type)
        icon = get_badge_icon(k)
        badges.append({
            'name': k,
            'value': formatted,
            'icon': icon
        })

    # Fallback to direct model/item fields if no attributes dict was present
    if not badges:
        b_life = item.get('battery_life')
        anc_val = item.get('anc')
        if b_life:
            badges.append({
                'name': 'Battery Life (hours)',
                'value': format_badge_value('Battery Life (hours)', b_life),
                'icon': get_badge_icon('Battery Life (hours)')
            })
        if anc_val is not None and cat_name not in ['Smartwatches', 'Smart Eyewear']:
            badges.append({
                'name': 'Active Noise Cancelling',
                'value': 'YES' if anc_val else 'NO',
                'icon': get_badge_icon('Active Noise Cancelling')
            })

    return badges


class RankingEngineClient:
    """
    Robust B2B client that connects the Noise E-Commerce site to the
    Weighted Ranking Engine microservice at http://localhost:5000.
    Includes automatic graceful fallback to local database search if engine is offline.
    """

    def __init__(self, base_url=None, company_id=None, timeout=3.0):
        self._custom_base_url = base_url
        self._custom_company_id = company_id
        self.timeout = timeout

    @property
    def base_url(self):
        if self._custom_base_url:
            return self._custom_base_url.rstrip('/')
        if has_app_context() and 'RANKING_ENGINE_URL' in current_app.config:
            return current_app.config['RANKING_ENGINE_URL'].rstrip('/')
        return 'http://localhost:5000'

    @property
    def company_id(self):
        if self._custom_company_id is not None:
            return self._custom_company_id
        if has_app_context() and 'RANKING_COMPANY_ID' in current_app.config:
            return current_app.config['RANKING_COMPANY_ID']
        return 1

    def health_check(self):
        """
        Check if the ranking engine microservice is reachable and measure latency.
        Returns dict with status ('online' / 'offline'), latency_ms, engine_url, company_id.
        """
        start = time.time()
        url = f"{self.base_url}/api/v1/categories"
        try:
            resp = requests.get(url, params={'company_id': self.company_id}, timeout=self.timeout)
            latency = (time.time() - start) * 1000.0
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'status': 'online',
                    'latency_ms': round(latency, 2),
                    'engine_url': self.base_url,
                    'company_id': self.company_id,
                    'company_name': data.get('company_name', 'Noise Official'),
                    'categories_count': len(data.get('categories', []))
                }
            return {
                'status': 'degraded',
                'latency_ms': round(latency, 2),
                'status_code': resp.status_code,
                'engine_url': self.base_url,
                'company_id': self.company_id
            }
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Health check failed: {e}")
            return {
                'status': 'offline',
                'latency_ms': None,
                'error': str(e),
                'engine_url': self.base_url,
                'company_id': self.company_id
            }

    def get_categories(self):
        """
        Fetch all categories and active attribute configurations for the tenant company.
        Falls back to local catalog categories if engine is unreachable.
        """
        url = f"{self.base_url}/api/v1/categories"
        try:
            resp = requests.get(url, params={'company_id': self.company_id}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                data['engine_status'] = 'online'
                return data
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Failed to fetch categories: {e}")

        # Fallback category configurations
        return {
            'status': 'success',
            'engine_status': 'offline',
            'company_id': self.company_id,
            'company_name': 'Noise Official (Offline Cache)',
            'categories': [
                {
                    'category_id': 4,
                    'name': 'Wireless Earbuds',
                    'display_attr_1': 'Battery Life (hours)',
                    'display_attr_2': 'Active Noise Cancelling',
                    'product_count': 7,
                    'attributes': [
                        {'attribute_id': 10, 'name': 'Battery Life (hours)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 0.0, 'max_value': 100.0, 'lower_is_better': False},
                        {'attribute_id': 11, 'name': 'Price (INR)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 500.0, 'max_value': 15000.0, 'lower_is_better': True},
                        {'attribute_id': 12, 'name': 'Rating', 'data_type': 'numeric', 'weight': 15.0, 'min_value': 0.0, 'max_value': 5.0, 'lower_is_better': False},
                        {'attribute_id': 13, 'name': 'Active Noise Cancelling', 'data_type': 'binary', 'weight': 15.0, 'min_value': 0.0, 'max_value': 1.0, 'lower_is_better': False}
                    ]
                },
                {
                    'category_id': 5,
                    'name': 'Smartwatches',
                    'display_attr_1': 'Battery Life (hours)',
                    'display_attr_2': 'Rating',
                    'product_count': 5,
                    'attributes': [
                        {'attribute_id': 14, 'name': 'Battery Life (hours)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 0.0, 'max_value': 300.0, 'lower_is_better': False},
                        {'attribute_id': 15, 'name': 'Price (INR)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 1000.0, 'max_value': 15000.0, 'lower_is_better': True},
                        {'attribute_id': 16, 'name': 'Rating', 'data_type': 'numeric', 'weight': 30.0, 'min_value': 0.0, 'max_value': 5.0, 'lower_is_better': False}
                    ]
                },
                {
                    'category_id': 6,
                    'name': 'Neckbands',
                    'display_attr_1': 'Battery Life (hours)',
                    'display_attr_2': 'Active Noise Cancelling',
                    'product_count': 2,
                    'attributes': [
                        {'attribute_id': 17, 'name': 'Battery Life (hours)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 0.0, 'max_value': 120.0, 'lower_is_better': False},
                        {'attribute_id': 18, 'name': 'Price (INR)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 500.0, 'max_value': 10000.0, 'lower_is_better': True},
                        {'attribute_id': 19, 'name': 'Rating', 'data_type': 'numeric', 'weight': 15.0, 'min_value': 0.0, 'max_value': 5.0, 'lower_is_better': False},
                        {'attribute_id': 20, 'name': 'Active Noise Cancelling', 'data_type': 'binary', 'weight': 15.0, 'min_value': 0.0, 'max_value': 1.0, 'lower_is_better': False}
                    ]
                },
                {
                    'category_id': 7,
                    'name': 'Headphones',
                    'display_attr_1': 'Battery Life (hours)',
                    'display_attr_2': 'Active Noise Cancelling',
                    'product_count': 1,
                    'attributes': [
                        {'attribute_id': 21, 'name': 'Battery Life (hours)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 0.0, 'max_value': 100.0, 'lower_is_better': False},
                        {'attribute_id': 22, 'name': 'Price (INR)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 500.0, 'max_value': 15000.0, 'lower_is_better': True},
                        {'attribute_id': 23, 'name': 'Rating', 'data_type': 'numeric', 'weight': 15.0, 'min_value': 0.0, 'max_value': 5.0, 'lower_is_better': False},
                        {'attribute_id': 24, 'name': 'Active Noise Cancelling', 'data_type': 'binary', 'weight': 15.0, 'min_value': 0.0, 'max_value': 1.0, 'lower_is_better': False}
                    ]
                },
                {
                    'category_id': 8,
                    'name': 'Smart Eyewear',
                    'display_attr_1': 'Battery Life (hours)',
                    'display_attr_2': 'Rating',
                    'product_count': 1,
                    'attributes': [
                        {'attribute_id': 25, 'name': 'Battery Life (hours)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 0.0, 'max_value': 24.0, 'lower_is_better': False},
                        {'attribute_id': 26, 'name': 'Price (INR)', 'data_type': 'numeric', 'weight': 35.0, 'min_value': 1000.0, 'max_value': 15000.0, 'lower_is_better': True},
                        {'attribute_id': 27, 'name': 'Rating', 'data_type': 'numeric', 'weight': 30.0, 'min_value': 0.0, 'max_value': 5.0, 'lower_is_better': False}
                    ]
                },
                {
                    'category_id': 9,
                    'name': 'Power Bank',
                    'display_attr_1': 'battery size',
                    'display_attr_2': 'MultiPorts',
                    'product_count': 3,
                    'attributes': [
                        {'attribute_id': 29, 'name': 'Rating', 'data_type': 'numeric', 'weight': 20.0, 'min_value': 1.0, 'max_value': 100.0, 'lower_is_better': False},
                        {'attribute_id': 30, 'name': 'MultiPorts', 'data_type': 'numeric', 'weight': 10.0, 'min_value': 1.0, 'max_value': 5.0, 'lower_is_better': False},
                        {'attribute_id': 31, 'name': 'bodytype[metal]', 'data_type': 'binary', 'weight': 5.0, 'min_value': 0.0, 'max_value': 1.0, 'lower_is_better': False},
                        {'attribute_id': 32, 'name': 'battery size', 'data_type': 'numeric', 'weight': 55.0, 'min_value': 0.0, 'max_value': 50000.0, 'lower_is_better': False},
                        {'attribute_id': 33, 'name': 'Price', 'data_type': 'numeric', 'weight': 10.0, 'min_value': 0.0, 'max_value': 10000.0, 'lower_is_better': True}
                    ]
                }
            ]
        }

    def get_category_map(self):
        """
        Calls get_categories() and returns dict mapping category names to IDs and IDs to names.
        """
        data = self.get_categories()
        categories = data.get('categories', [])
        cat_map = {}
        for cat in categories:
            cid = cat.get('category_id')
            cname = cat.get('name')
            if cid is not None and cname:
                cat_map[cname] = cid
                cat_map[cid] = cname
        return cat_map

    def get_product_breakdown(self, product_id):
        """
        Fetch ranking score breakdown for a specific product.
        Calls GET /api/v1/product/<product_id> on engine.
        If offline or not found in engine, synthesizes deterministic breakdown from local DB.
        """
        engine_product_id = product_id
        if has_app_context():
            from app.models import Product
            local_prod = db.session.get(Product, product_id)
            if local_prod:
                try:
                    s_resp = requests.get(
                        f"{self.base_url}/api/v1/search",
                        params={'company_id': self.company_id, 'q': local_prod.name},
                        timeout=self.timeout
                    )
                    if s_resp.status_code == 200:
                        s_data = s_resp.json()
                        for item in s_data.get('results', []):
                            if item.get('name', '').strip().lower() == local_prod.name.strip().lower():
                                engine_product_id = item.get('product_id', product_id)
                                break
                except (requests.exceptions.RequestException, ValueError) as e:
                    logger.warning(f"Failed to resolve engine product ID by name: {e}")

        url = f"{self.base_url}/api/v1/product/{engine_product_id}"
        try:
            resp = requests.get(url, params={'company_id': self.company_id}, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    data['engine_status'] = 'online'
                    if has_app_context():
                        from app.models import Product
                        local_p = db.session.get(Product, product_id)
                        if local_p and getattr(local_p, 'is_sponsored', False):
                            data['is_sponsored'] = True
                    return data
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Failed to fetch product breakdown: {e}")

        # Fallback to local DB product breakdown
        return self._fallback_product_breakdown(product_id)

    def search(self, query='', category_id=None, custom_weights=None, limit=20, offset=0, include_sponsors=True):
        """
        External search and ranking query.
        Calls GET/POST /api/v1/search with company_id, query, custom_weights.
        If connection fails or returns error, fallbacks gracefully to local database search
        and flags engine_status='offline'.
        """
        # Intelligent category detection for queries like "ear phones", "ear pods", "watches", "Combat earbuds"
        detected_cat_id, detected_cat_name, remaining, is_exact_synonym = detect_category_intent(query)
        effective_category_id = category_id or detected_cat_id

        url = f"{self.base_url}/api/v1/search"

        try:
            if custom_weights:
                payload = {
                    'company_id': self.company_id,
                    'q': query or '',
                    'category_id': effective_category_id or 4,
                    'custom_weights': custom_weights,
                    'limit': limit,
                    'offset': offset,
                    'include_sponsors': include_sponsors
                }
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 'success':
                        data['engine_status'] = 'online'
                        self._enrich_with_local_products(data.get('results', []))
                        return data
            else:
                # 1. If exact category synonym (e.g. 'ear phones', 'ear pods', 'earbuds', 'smartwatch'):
                # Query category_id on engine with EMPTY q so the engine scores and ranks all category items
                if is_exact_synonym and effective_category_id:
                    params = {
                        'company_id': self.company_id,
                        'category_id': effective_category_id,
                        'limit': limit,
                        'offset': offset,
                        'include_sponsors': 'true' if include_sponsors else 'false'
                    }
                    resp = requests.get(url, params=params, timeout=self.timeout)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('status') == 'success' and len(data.get('results', [])) > 0:
                            data['engine_status'] = 'online'
                            self._enrich_with_local_products(data.get('results', []))
                            return data

                # 2. Standard query or category filter
                params = {
                    'company_id': self.company_id,
                    'limit': limit,
                    'offset': offset,
                    'include_sponsors': 'true' if include_sponsors else 'false'
                }
                if query:
                    params['q'] = query
                if effective_category_id:
                    params['category_id'] = effective_category_id

                resp = requests.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 'success':
                        results = data.get('results', [])
                        if len(results) > 0:
                            data['engine_status'] = 'online'
                            self._enrich_with_local_products(results)
                            return data

                        # If 0 results found for query with category word (e.g. "Combat earbuds"),
                        # try searching with remaining keyword in that category
                        if detected_cat_id and remaining:
                            params2 = {
                                'company_id': self.company_id,
                                'category_id': detected_cat_id,
                                'q': remaining,
                                'limit': limit,
                                'offset': offset,
                                'include_sponsors': 'true' if include_sponsors else 'false'
                            }
                            resp2 = requests.get(url, params=params2, timeout=self.timeout)
                            if resp2.status_code == 200:
                                data2 = resp2.json()
                                if data2.get('status') == 'success' and len(data2.get('results', [])) > 0:
                                    data2['engine_status'] = 'online'
                                    self._enrich_with_local_products(data2.get('results', []))
                                    return data2

                        # If 0 results, try whitespace-collapsed or typo-corrected query (e.g. "vs 102" -> "vs102", "combatt" -> "combat")
                        clean_q, q_collapsed, corrected_q, _ = normalize_and_correct_query(query)
                        alt_candidates = []
                        if corrected_q and corrected_q != clean_q and corrected_q != query:
                            alt_candidates.append(corrected_q)
                        if q_collapsed and q_collapsed != clean_q and q_collapsed != query:
                            alt_candidates.append(q_collapsed)

                        for alt_q in alt_candidates:
                            alt_params = {
                                'company_id': self.company_id,
                                'q': alt_q,
                                'limit': limit,
                                'offset': offset,
                                'include_sponsors': 'true' if include_sponsors else 'false'
                            }
                            if effective_category_id:
                                alt_params['category_id'] = effective_category_id
                            resp_alt = requests.get(url, params=alt_params, timeout=self.timeout)
                            if resp_alt.status_code == 200:
                                data_alt = resp_alt.json()
                                if data_alt.get('status') == 'success' and len(data_alt.get('results', [])) > 0:
                                    data_alt['engine_status'] = 'online'
                                    self._enrich_with_local_products(data_alt.get('results', []))
                                    return data_alt

                        # If still 0 results and detected_cat_id exists, try category without q
                        if detected_cat_id:
                            params3 = {
                                'company_id': self.company_id,
                                'category_id': detected_cat_id,
                                'limit': limit,
                                'offset': offset,
                                'include_sponsors': 'true' if include_sponsors else 'false'
                            }
                            resp3 = requests.get(url, params=params3, timeout=self.timeout)
                            if resp3.status_code == 200:
                                data3 = resp3.json()
                                if data3.get('status') == 'success' and len(data3.get('results', [])) > 0:
                                    data3['engine_status'] = 'online'
                                    self._enrich_with_local_products(data3.get('results', []))
                                    return data3

                        data['engine_status'] = 'online'
                        self._enrich_with_local_products(results)
                        return data
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Ranking engine search error: {e}")

        # Graceful fallback to local DB search
        return self._fallback_local_search(query, effective_category_id, custom_weights, limit, offset)

    def _enrich_with_local_products(self, results):
        """Helper to attach local product images, description, slug, and display badges if available."""
        if not results:
            return

        prods_by_name = {}
        prods_by_id = {}
        if has_app_context():
            from app.models import Product

            names = [item.get('name', '').strip() for item in results if item.get('name')]
            product_ids = [item['product_id'] for item in results if 'product_id' in item]

            if names:
                matched_by_name = Product.query.filter(Product.name.in_(names)).all()
                for p in matched_by_name:
                    prods_by_name[p.name.strip().lower()] = p

            if product_ids:
                matched_by_id = Product.query.filter(Product.id.in_(product_ids)).all()
                for p in matched_by_id:
                    prods_by_id[p.id] = p

        def _extract_engine_price(attributes):
            if not attributes or not isinstance(attributes, dict):
                return None
            for key, val in attributes.items():
                if 'price' in key.lower():
                    if isinstance(val, dict) and 'raw_value' in val:
                        try:
                            return float(val['raw_value'])
                        except (ValueError, TypeError):
                            pass
                    elif isinstance(val, (int, float)):
                        return float(val)
            return None

        for item in results:
            p_name = item.get('name', '').strip()
            prod = prods_by_name.get(p_name.lower()) if p_name else None
            if not prod and 'product_id' in item:
                prod = prods_by_id.get(item['product_id'])

            engine_price = _extract_engine_price(item.get('attributes', {}))

            if prod:
                # If local product has erroneous price (<= 5.0) and engine has a valid price > 5.0, sync it
                if prod.price <= 5.0 and engine_price is not None and engine_price > 5.0:
                    prod.price = engine_price
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

                item['local_product_id'] = prod.id
                item['image_url'] = prod.image_url
                item['description'] = prod.description
                item['slug'] = prod.slug
                item['price'] = prod.price
                item['original_price'] = prod.original_price
                item['discount_pct'] = prod.discount_pct
                item['in_stock'] = prod.in_stock
                item['rating'] = prod.rating
                item['review_count'] = prod.review_count
                item['category_name'] = prod.category
                if getattr(prod, 'battery_life', None) and 'battery_life' not in item:
                    item['battery_life'] = prod.battery_life
                if getattr(prod, 'anc', None) is not None and 'anc' not in item:
                    item['anc'] = prod.anc
                if getattr(prod, 'is_sponsored', False):
                    item['is_sponsored'] = True
            else:
                if 'image_url' not in item or not item['image_url']:
                    item['image_url'] = 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600'
                item['price'] = engine_price if engine_price is not None else 2999.0
                item['rating'] = item.get('rating') or item.get('attributes', {}).get('Rating', {}).get('raw_value', 4.3)
                item['review_count'] = item.get('review_count', 145)

            # Ensure each product item in results has a list of display_badges
            if item.get('display_badges'):
                enriched_badges = []
                for badge in item['display_badges']:
                    if isinstance(badge, dict):
                        b_name = badge.get('name', '')
                        b_val = badge.get('value') if badge.get('value') is not None else badge.get('raw_value')
                        badge['name'] = b_name
                        badge['value'] = format_badge_value(b_name, b_val, badge.get('data_type'))
                        badge['icon'] = get_badge_icon(b_name)
                        enriched_badges.append(badge)
                item['display_badges'] = enriched_badges
            else:
                item['display_badges'] = build_display_badges_for_item(item)

        # Partition: sponsored items ALWAYS come FIRST at #1, organic items follow
        sponsored = [p for p in results if p.get('is_sponsored')]
        organic = [p for p in results if not p.get('is_sponsored')]
        results[:] = sponsored + organic
        for idx, item in enumerate(results, start=1):
            item['rank'] = idx
            item['display_rank'] = idx

    def sync_product_to_engine(self, product):
        """
        Sync product price, rating, and name to the Weighted Ranking Engine.
        Sends POST/PUT to f"{self.base_url}/api/v1/product/{product_id}?company_id={self.company_id}"
        with both 'price' and 'rating' as core default attributes.
        Handles network exceptions gracefully with logger.warning.
        """
        product_id = getattr(product, 'id', None) if not isinstance(product, dict) else product.get('id')
        price_val = getattr(product, 'price', None) if not isinstance(product, dict) else product.get('price')
        rating_val = getattr(product, 'rating', None) if not isinstance(product, dict) else product.get('rating')
        name_val = getattr(product, 'name', None) if not isinstance(product, dict) else product.get('name')

        if product_id is None:
            logger.warning("sync_product_to_engine called without product id")
            return None

        clean_price = float(price_val) if price_val is not None else 0.0
        clean_rating = float(rating_val) if rating_val is not None else 0.0
        clean_name = str(name_val).strip() if name_val else ''

        payload = {
            'price': clean_price,
            'rating': clean_rating,
            'name': clean_name,
            'attributes': {
                'Price (INR)': clean_price,
                'Price': clean_price,
                'Rating': clean_rating
            }
        }
        target_id = product_id
        url = f"{self.base_url}/api/v1/product/{target_id}?company_id={self.company_id}"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code in (404, 405):
                resp = requests.put(url, json=payload, timeout=self.timeout)

            # If 404, attempt resolution by product name on engine
            if resp.status_code == 404 and clean_name:
                try:
                    s_resp = requests.get(
                        f"{self.base_url}/api/v1/search",
                        params={'company_id': self.company_id, 'q': clean_name},
                        timeout=self.timeout
                    )
                    if s_resp.status_code == 200:
                        for item in s_resp.json().get('results', []):
                            if item.get('name', '').strip().lower() == clean_name.lower():
                                eng_id = item.get('product_id')
                                if eng_id and eng_id != target_id:
                                    alt_url = f"{self.base_url}/api/v1/product/{eng_id}?company_id={self.company_id}"
                                    resp = requests.post(alt_url, json=payload, timeout=self.timeout)
                                    if resp.status_code in (404, 405):
                                        resp = requests.put(alt_url, json=payload, timeout=self.timeout)
                                    break
                except Exception as inner_e:
                    logger.debug(f"Engine name resolution failed during sync: {inner_e}")

            return resp
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Failed to sync product #{product_id} to ranking engine: {e}")
            return None

    def _fallback_local_search(self, query='', category_id=None, custom_weights=None, limit=20, offset=0):
        """
        Execute deterministic weighted ranking search across local Noise products.
        Runs when the ranking engine is offline or for local store items.
        """
        if not has_app_context():
            return {
                'status': 'success',
                'engine_status': 'offline',
                'fallback': True,
                'total_results': 0,
                'results': []
            }

        from app.models import Product

        # Map weights
        # Default category weights for Earbuds/Audio & Electronics:
        # Both 'Rating' and 'Price (INR)' are permanent default core attributes
        weights = {
            'Battery Life (hours)': 35.0,
            'Price (INR)': 35.0,
            'Rating': 15.0,
            'Active Noise Cancelling': 15.0
        }
        if custom_weights and isinstance(custom_weights, dict):
            try:
                parsed = {k: float(v) for k, v in custom_weights.items()}
                # Support Price alias for Price (INR)
                if 'Price' in parsed and 'Price (INR)' not in parsed:
                    parsed['Price (INR)'] = parsed['Price']
                total = sum(parsed.values())
                if abs(total - 100.0) <= 1.0:
                    weights = parsed
            except (ValueError, TypeError):
                pass

        # Detect category intent and resolve synonyms
        detected_cat_id, detected_cat_name, remaining, is_exact = detect_category_intent(query)
        effective_cat_id = category_id or detected_cat_id

        q_filter = Product.query
        if category_id:
            cat_map = {
                4: ['Wireless Earbuds'],
                5: ['Smartwatches'],
                6: ['Neckbands'],
                7: ['Headphones'],
                8: ['Smart Eyewear'],
                9: ['Power Bank']
            }
            dyn_map = self.get_category_map()
            cname = dyn_map.get(category_id)
            if cname and category_id not in cat_map:
                cat_map[category_id] = [cname]
            allowed = cat_map.get(category_id)
            if allowed:
                q_filter = q_filter.filter(Product.category.in_(allowed))
        elif detected_cat_name:
            q_filter = q_filter.filter(Product.category == detected_cat_name)

        if query:
            clean_q, q_collapsed, corrected_q, corrected_tokens = normalize_and_correct_query(query)
            raw_tokens = clean_q.split()
            generic_audio = {
                'ear', 'phones', 'phone', 'pods', 'pod', 'earphones', 'earphone',
                'earbuds', 'earbud', 'tws', 'audio', 'sound', 'noise',
                'head', 'headphones', 'headphone', 'headset'
            }
            generic_watch = {'watch', 'watches', 'smartwatch', 'smartwatches', 'noise', 'smart'}
            generic_eyewear = {'glasses', 'eyewear', 'sunglasses', 'smart', 'noise', 'sun'}

            if effective_cat_id in [4, 6, 7]:
                informative = [t for t in raw_tokens if t not in generic_audio]
            elif effective_cat_id in [5, 8]:
                informative = [t for t in raw_tokens if t not in generic_watch and t not in generic_eyewear]
            else:
                informative = [t for t in raw_tokens if t != 'noise']

            from sqlalchemy import or_
            if informative:
                # User searched a specific model/feature, e.g. "vs102", "combat", "halo", "anc"
                search_terms = set(informative)
                for t in informative:
                    c = correct_word(t)
                    if c:
                        search_terms.add(c)
                if q_collapsed:
                    search_terms.add(q_collapsed)

                conditions = []
                for token in search_terms:
                    search_str = f"%{token}%"
                    conditions.append(Product.name.ilike(search_str))
                    conditions.append(Product.description.ilike(search_str))
                    conditions.append(Product.category.ilike(search_str))
                q_filter = q_filter.filter(or_(*conditions))
            elif not detected_cat_name:
                conditions = [
                    Product.name.ilike(f"%{clean_q}%"),
                    Product.category.ilike(f"%{clean_q}%"),
                    Product.description.ilike(f"%{clean_q}%")
                ]
                if q_collapsed != clean_q:
                    conditions.append(Product.name.ilike(f"%{q_collapsed}%"))
                if corrected_q != clean_q:
                    conditions.append(Product.name.ilike(f"%{corrected_q}%"))
                q_filter = q_filter.filter(or_(*conditions))

        matched_products = q_filter.all()

        scored_items = []
        for p in matched_products:
            score, attrs_data = self._calculate_local_score_and_attrs(p, weights)
            scored_items.append({
                'product': p,
                'composite_score': score,
                'score_pct': f"{score * 100:.2f}%",
                'attributes': attrs_data
            })

        # Deterministic tiebreak sort: sponsored items ALWAYS come FIRST at #1, then -score, -created_at, product_id
        scored_items.sort(
            key=lambda item: (
                0 if getattr(item['product'], 'is_sponsored', False) else 1,
                -item['composite_score'],
                -(item['product'].created_at.timestamp() if item['product'].created_at else 0.0),
                item['product'].id
            )
        )

        paginated = scored_items[offset:offset + limit]

        results = []
        for rank_idx, item in enumerate(paginated, start=offset + 1):
            p = item['product']
            res_item = {
                'rank': rank_idx,
                'display_rank': rank_idx,
                'product_id': p.id,
                'local_product_id': p.id,
                'name': p.name,
                'slug': p.slug,
                'category_name': p.category,
                'composite_score': item['composite_score'],
                'score_pct': item['score_pct'],
                'price': p.price,
                'original_price': p.original_price,
                'discount_pct': p.discount_pct,
                'image_url': p.image_url,
                'description': p.description,
                'in_stock': p.in_stock,
                'rating': p.rating,
                'review_count': p.review_count,
                'battery_life': p.battery_life,
                'anc': p.anc,
                'is_sponsored': bool(getattr(p, 'is_sponsored', False)),
                'attributes': item['attributes']
            }
            res_item['display_badges'] = build_display_badges_for_item(res_item)
            results.append(res_item)

        return {
            'status': 'success',
            'engine_status': 'offline',
            'fallback': True,
            'query': query,
            'category_id': category_id,
            'total_results': len(scored_items),
            'offset': offset,
            'limit': limit,
            'results': results
        }

    def _fallback_product_breakdown(self, product_id):
        """Generate score breakdown for local product when engine is offline."""
        if not has_app_context():
            return {'status': 'error', 'error': 'NO_APP_CONTEXT'}
        from app.models import Product

        prod = db.session.get(Product, product_id)
        if not prod:
            return {
                'status': 'error',
                'error': 'PRODUCT_NOT_FOUND',
                'message': f"Product {product_id} not found."
            }

        weights = {
            'Battery Life (hours)': 35.0,
            'Price (INR)': 35.0,
            'Rating': 15.0,
            'Active Noise Cancelling': 15.0
        }
        score, _ = self._calculate_local_score_and_attrs(prod, weights)

        # Attribute bounds
        if prod.category in ['Smartwatches', 'Smart Eyewear']:
            battery_min, battery_max = 24.0, 200.0
            price_min, price_max = 1000.0, 10000.0
        else:
            battery_min, battery_max = 0.0, 80.0
            price_min, price_max = 500.0, 15000.0
        rating_min, rating_max = 0.0, 5.0

        b_norm = min(max((prod.battery_life - battery_min) / (battery_max - battery_min), 0.0), 1.0)
        p_norm = min(max((price_max - prod.price) / (price_max - price_min), 0.0), 1.0) # lower is better
        r_val = prod.rating if prod.rating is not None else 0.0
        if r_val > 5.0 and r_val <= 100.0:
            r_val = r_val / 20.0
        r_norm = min(max((r_val - rating_min) / (rating_max - rating_min), 0.0), 1.0)
        anc_norm = 1.0 if prod.anc else 0.0

        w_battery = weights['Battery Life (hours)']
        w_price = weights['Price (INR)']
        w_rating = weights['Rating']
        w_anc = weights['Active Noise Cancelling']

        c_battery = round(b_norm * (w_battery / 100.0), 4)
        c_price = round(p_norm * (w_price / 100.0), 4)
        c_rating = round(r_norm * (w_rating / 100.0), 4)
        c_anc = round(anc_norm * (w_anc / 100.0), 4)

        breakdown = [
            {
                'attribute_name': 'Battery Life (hours)',
                'raw_value': prod.battery_life,
                'min_value': battery_min,
                'max_value': battery_max,
                'normalized_value': round(b_norm, 4),
                'normalized_pct': round(b_norm * 100, 1),
                'weight': w_battery,
                'contribution': c_battery,
                'contribution_pct': round((c_battery / score * 100) if score > 0 else 0, 1),
                'lower_is_better': False
            },
            {
                'attribute_name': 'Price (INR)',
                'raw_value': prod.price,
                'min_value': price_min,
                'max_value': price_max,
                'normalized_value': round(p_norm, 4),
                'normalized_pct': round(p_norm * 100, 1),
                'weight': w_price,
                'contribution': c_price,
                'contribution_pct': round((c_price / score * 100) if score > 0 else 0, 1),
                'lower_is_better': True
            },
            {
                'attribute_name': 'Rating',
                'raw_value': prod.rating,
                'min_value': rating_min,
                'max_value': rating_max,
                'normalized_value': round(r_norm, 4),
                'normalized_pct': round(r_norm * 100, 1),
                'weight': w_rating,
                'contribution': c_rating,
                'contribution_pct': round((c_rating / score * 100) if score > 0 else 0, 1),
                'lower_is_better': False
            },
            {
                'attribute_name': 'Active Noise Cancelling',
                'raw_value': 1.0 if prod.anc else 0.0,
                'min_value': 0.0,
                'max_value': 1.0,
                'normalized_value': round(anc_norm, 4),
                'normalized_pct': round(anc_norm * 100, 1),
                'weight': w_anc,
                'contribution': c_anc,
                'contribution_pct': round((c_anc / score * 100) if score > 0 else 0, 1),
                'lower_is_better': False
            }
        ]

        return {
            'status': 'success',
            'engine_status': 'offline',
            'product_id': prod.id,
            'name': prod.name,
            'category_name': prod.category,
            'composite_score': score,
            'score_pct': f"{score * 100:.2f}%",
            'is_sponsored': bool(getattr(prod, 'is_sponsored', False)),
            'score_breakdown': breakdown
        }

    def _calculate_local_score_and_attrs(self, product, weights):
        """Calculate composite score and normalized attribute dict for local product."""
        if product.category in ['Smartwatches', 'Smart Eyewear']:
            battery_min, battery_max = 24.0, 200.0
            price_min, price_max = 1000.0, 10000.0
        else:
            battery_min, battery_max = 0.0, 80.0
            price_min, price_max = 500.0, 15000.0
        rating_min, rating_max = 0.0, 5.0

        b_norm = min(max((product.battery_life - battery_min) / (battery_max - battery_min), 0.0), 1.0)
        p_norm = min(max((price_max - product.price) / (price_max - price_min), 0.0), 1.0)
        rating_val = product.rating if product.rating is not None else 0.0
        if rating_val > 5.0 and rating_val <= 100.0:
            rating_val = rating_val / 20.0
        r_norm = min(max((rating_val - rating_min) / (rating_max - rating_min), 0.0), 1.0)
        anc_norm = 1.0 if product.anc else 0.0

        w_battery = weights.get('Battery Life (hours)', 35.0)
        w_price = weights.get('Price (INR)', weights.get('Price', 35.0))
        w_rating = weights.get('Rating', weights.get('rating', 15.0))
        w_anc = weights.get('Active Noise Cancelling', 15.0)

        total_w = w_battery + w_price + w_rating + w_anc or 100.0
        raw_score = (
            b_norm * w_battery +
            p_norm * w_price +
            r_norm * w_rating +
            anc_norm * w_anc
        ) / total_w
        score = round(raw_score, 6)

        attrs = {
            'Battery Life (hours)': {
                'raw_value': product.battery_life,
                'normalized_value': round(b_norm, 4),
                'weight': w_battery,
                'lower_is_better': False,
                'display_value': product.battery_life
            },
            'Price (INR)': {
                'raw_value': product.price,
                'normalized_value': round(p_norm, 4),
                'weight': w_price,
                'lower_is_better': True,
                'display_value': product.price
            },
            'Rating': {
                'raw_value': product.rating,
                'normalized_value': round(r_norm, 4),
                'weight': w_rating,
                'lower_is_better': False,
                'display_value': product.rating
            },
            'Active Noise Cancelling': {
                'raw_value': 1.0 if product.anc else 0.0,
                'normalized_value': round(anc_norm, 4),
                'weight': w_anc,
                'lower_is_better': False,
                'display_value': 'YES' if product.anc else 'NO'
            }
        }
        return score, attrs


# Shared singleton instance
engine_client = RankingEngineClient()
