from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
load_dotenv()

import io
from PIL import Image
import torch
import torchvision.transforms as T
from supabase import create_client, Client
import json
from datetime import datetime, timezone
import aiohttp
import asyncio
import openfoodfacts

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="SmartPlate CV Service")

class DetectRequest(BaseModel):
    user_id: str
    bucket: Optional[str] = "fridge-images"

# COCO class names (index 0 is __background__)
COCO_INSTANCE_CATEGORY_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter',
    'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
    'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle',
    'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
    'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave',
    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

# Select COCO classes that correspond to common ingredients/food items
FOOD_CLASSES = set([
    'banana', 'apple', 'orange', 'broccoli', 'carrot', 'pizza', 'donut', 'sandwich', 'hot dog',
    'bottle', 'wine glass', 'cup', 'bowl', 'cake'
])

# Open Food Facts product mapping
FOOD_TO_PRODUCT_CATEGORIES = {
    'banana': 'bananas',
    'apple': 'apples',
    'orange': 'oranges',
    'broccoli': 'broccoli',
    'carrot': 'carrots',
    'pizza': 'pizzas',
    'donut': 'donuts',
    'sandwich': 'sandwiches',
    'hot dog': 'hot-dogs',
    'bottle': 'waters',
    'wine glass': 'wines',
    'cup': 'milks',
    'bowl': 'soups',
    'cake': 'cakes'
}

# Average shelf life in days (fallback if Open Food Facts doesn't have data)
DEFAULT_SHELF_LIFE = {
    'banana': 7,
    'apple': 30,
    'orange': 14,
    'broccoli': 7,
    'carrot': 21,
    'pizza': 3,
    'donut': 2,
    'sandwich': 2,
    'hot dog': 7,
    'bottle': 365,
    'wine glass': 1095,
    'cup': 7,
    'bowl': 3,
    'cake': 5
}

async def get_food_facts_info(food_item: str):
    """Get product information from Open Food Facts API"""
    try:
        category = FOOD_TO_PRODUCT_CATEGORIES.get(food_item, food_item)
        api = openfoodfacts.API(user_agent="SmartPlate/1.0")
        
        search_results = api.product.text_search(category, page_size=5)
        
        if search_results.get('products'):
            for product in search_results['products']:
                expiration_info = extract_expiration_info(product)
                if expiration_info:
                    return {
                        'food_item': food_item,
                        'product_name': product.get('product_name', 'Unknown'),
                        'brand': product.get('brands', 'Unknown'),
                        'expiration_info': expiration_info,
                        'status': 'success',
                        'source': 'openfoodfacts'
                    }
        
        # Fallback to default shelf life
        return {
            'food_item': food_item,
            'product_name': food_item.title(),
            'expiration_info': {
                'shelf_life_days': DEFAULT_SHELF_LIFE.get(food_item, 7),
                'storage_advice': 'Store in cool, dry place',
                'is_estimated': True
            },
            'status': 'estimated',
            'source': 'default'
        }
        
    except Exception as e:
        return {
            'food_item': food_item,
            'product_name': food_item.title(),
            'expiration_info': {
                'shelf_life_days': DEFAULT_SHELF_LIFE.get(food_item, 7),
                'storage_advice': 'Store in cool, dry place',
                'is_estimated': True,
                'error': str(e)
            },
            'status': 'fallback',
            'source': 'default'
        }

def extract_expiration_info(product: dict) -> dict:
    """Extract expiration information from product data"""
    expiration_info = {}
    
    if product.get('expiration_date'):
        expiration_info['expiration_date'] = product['expiration_date']
    
    if product.get('best_before_date'):
        expiration_info['best_before_date'] = product['best_before_date']
    
    expiration_info['shelf_life_days'] = estimate_shelf_life(product)
    expiration_info['storage_advice'] = get_storage_advice(product)
    expiration_info['is_estimated'] = True
    
    return expiration_info

def estimate_shelf_life(product: dict) -> int:
    """Estimate shelf life based on product characteristics"""
    product_name = product.get('product_name', '').lower()
    categories = product.get('categories', '').lower()
    
    if any(word in categories for word in ['dairy', 'milk', 'yogurt', 'cheese']):
        return 7
    elif any(word in categories for word in ['meat', 'poultry', 'fish', 'seafood']):
        return 3
    elif any(word in categories for word in ['bread', 'bakery', 'pastry']):
        return 5
    elif any(word in categories for word in ['fruit', 'vegetable', 'produce']):
        return 14
    elif any(word in categories for word in ['canned', 'preserved', 'jar']):
        return 365
    else:
        return 30

def get_storage_advice(product: dict) -> str:
    """Get appropriate storage advice based on product type"""
    categories = product.get('categories', '').lower()
    
    if any(word in categories for word in ['dairy', 'milk', 'yogurt']):
        return 'Refrigerate at 4°C or below'
    elif any(word in categories for word in ['meat', 'poultry', 'fish']):
        return 'Refrigerate at 4°C or below, use within 3 days'
    elif any(word in categories for word in ['fruit', 'vegetable']):
        return 'Store in refrigerator crisper drawer'
    elif any(word in categories for word in ['bread', 'bakery']):
        return 'Store in cool, dry place or freeze to extend freshness'
    else:
        return 'Store in cool, dry place away from direct sunlight'

def calculate_expiration_date(shelf_life_days: int) -> dict:
    """Calculate expiration date based on shelf life"""
    from datetime import timedelta
    
    current_date = datetime.now(timezone.utc)
    expiration_date = current_date + timedelta(days=shelf_life_days)
    
    return {
        'shelf_life_days': shelf_life_days,
        'purchase_date': current_date.isoformat(),
        'expiration_date': expiration_date.isoformat(),
        'days_until_expiry': shelf_life_days
    }

def save_ingredients_to_supabase(user_id: str, ingredients: list, file_name: str, expiration_data: dict = None):
    """Save detected ingredients to Supabase detected_ingredients table"""
    try:
        ingredients_count = len(ingredients)
        detection_confidence = max([ingredient.get('score', 0) for ingredient in ingredients]) if ingredients else 0
        
        data = {
            'user_id': user_id,
            'ingredients': json.dumps(ingredients),
            'image_file': file_name,
            'expiration_data': json.dumps(expiration_data) if expiration_data else None,
            'detection_confidence': float(detection_confidence),
            'ingredients_count': ingredients_count,
            'detected_at': datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table('detected_ingredients').insert(data).execute()
        
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
        return True
    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return False

def list_user_files(bucket: str, user_id: str):
    """List files under a user's top-level folder. Returns list of file metadata dicts."""
    try:
        res = supabase.storage.from_(bucket).list(path=user_id)
    except Exception:
        res = supabase.storage.from_(bucket).list()
        if isinstance(res, list):
            res = [f for f in res if f.get('name','').startswith(f"{user_id}/")]

    if not res:
        return []

    try:
        files = sorted(res, key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception:
        files = res
    return files

def download_file_bytes(bucket: str, file_name: str) -> bytes:
    """Download file bytes from Supabase storage. Returns bytes."""
    data = supabase.storage.from_(bucket).download(file_name)
    if hasattr(data, 'read'):
        return data.read()
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, dict) and 'content' in data:
        return data['content']
    raise RuntimeError('Unsupported download response type from Supabase')

@app.post('/detect')
async def detect(req: DetectRequest):
    bucket = req.bucket
    user_id = req.user_id

    files = list_user_files(bucket, user_id)
    if not files:
        raise HTTPException(status_code=404, detail=f'No files found for user {user_id} in bucket {bucket}')

    latest = files[0]
    file_name = latest.get('name')
    if not file_name:
        raise HTTPException(status_code=500, detail='Latest file metadata missing name')

    try:
        file_bytes = download_file_bytes(bucket, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to download file: {e}')

    try:
        image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to open image: {e}')

    # Prepare image tensor
    transform = T.Compose([T.ToTensor()])
    img_t = transform(image)

    # Load model (cache globally to avoid reloading on each request)
    if not hasattr(app.state, 'model'):
        import torchvision
        model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        model.eval()
        app.state.model = model
    model = app.state.model

    with torch.no_grad():
        outputs = model([img_t])[0]

    labels = outputs.get('labels').cpu().numpy()
    scores = outputs.get('scores').cpu().numpy()

    detected = []
    for label, score in zip(labels, scores):
        if score < 0.35:
            continue
        name = COCO_INSTANCE_CATEGORY_NAMES[label]
        lname = name.lower()
        if lname in FOOD_CLASSES:
            detected.append({'name': lname, 'score': float(score)})

    # Deduplicate by name keeping highest score
    result_map = {}
    for d in detected:
        n = d['name']
        s = d['score']
        if n not in result_map or s > result_map[n]:
            result_map[n] = s

    ingredients = [{'name': k, 'score': v} for k, v in sorted(result_map.items(), key=lambda x: -x[1])]

    # Get expiration information for detected ingredients
    expiration_results = {}
    if ingredients:
        tasks = [get_food_facts_info(ingredient['name']) for ingredient in ingredients]
        expiration_responses = await asyncio.gather(*tasks)
        
        for response in expiration_responses:
            expiration_results[response['food_item']] = response

    # Enhance ingredients with expiration data
    enhanced_ingredients = []
    for ingredient in ingredients:
        enhanced_ingredient = ingredient.copy()
        expiration_info = expiration_results.get(ingredient['name'], {})
        
        if expiration_info.get('expiration_info', {}).get('shelf_life_days'):
            shelf_life = expiration_info['expiration_info']['shelf_life_days']
            expiration_dates = calculate_expiration_date(shelf_life)
            expiration_info['expiration_info']['dates'] = expiration_dates
        
        enhanced_ingredient['expiration_info'] = expiration_info
        enhanced_ingredients.append(enhanced_ingredient)

    # Save to Supabase
    save_success = save_ingredients_to_supabase(user_id, enhanced_ingredients, file_name, expiration_results)
    
    return {
        'file': file_name,
        'ingredients': enhanced_ingredients,
        'saved_to_supabase': save_success
    }

@app.get('/expiration-info/{food_item}')
async def get_expiration_info(food_item: str):
    """Get expiration information for a specific food item"""
    try:
        expiration_info = await get_food_facts_info(food_item)
        return expiration_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch expiration info: {e}')

@app.get('/user-ingredients/{user_id}')
async def get_user_ingredients(user_id: str):
    """Get all detected ingredients for a specific user from Supabase"""
    try:
        response = supabase.table('detected_ingredients')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('detected_at', desc=True)\
            .execute()
        
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
            
        results = response.data if hasattr(response, 'data') else []
        
        for result in results:
            if 'ingredients' in result and isinstance(result['ingredients'], str):
                result['ingredients'] = json.loads(result['ingredients'])
            if 'expiration_data' in result and isinstance(result['expiration_data'], str):
                result['expiration_data'] = json.loads(result['expiration_data'])
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch user ingredients: {e}')

@app.get('/all-ingredients')
async def get_all_ingredients():
    """Get all detected ingredients from all users from Supabase"""
    try:
        response = supabase.table('detected_ingredients')\
            .select('*')\
            .order('detected_at', desc=True)\
            .execute()
        
        if hasattr(response, 'error') and response.error:
            raise Exception(response.error)
            
        results = response.data if hasattr(response, 'data') else []
        
        for result in results:
            if 'ingredients' in result and isinstance(result['ingredients'], str):
                result['ingredients'] = json.loads(result['ingredients'])
            if 'expiration_data' in result and isinstance(result['expiration_data'], str):
                result['expiration_data'] = json.loads(result['expiration_data'])
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch all ingredients: {e}')

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'SmartPlate CV Service'
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('cv:app', host='0.0.0.0', port=8001, reload=True)