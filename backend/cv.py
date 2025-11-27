import torch
import torchvision
from PIL import Image
import io
import requests
import numpy as np
import json
import supabase
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

bucketName = ""

def getImages(name):
    try:
        res = supabase.storage.from_(name).list()
        if not res:
            print("No files found in the storage bucket.")
            return None
        files = sorted(res, key=lambda x: x.get('created_at', ''), reverse=True)
        latest = files[0]
        print("Latest file: ", latest['name'])

        file = supabase.storage.from_(name).download(latest['name'])
        return file
    except Exception as e:
        print(e)
        return None
    
latest = getImages(bucketName)
if latest:
    image = Image.open(io.BytesIO(latest))
    image.show()