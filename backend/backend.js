import { createClient } from "@supabase/supabase-js";
import express from 'express';
import cors from 'cors';
import { supabase } from "../config/supabase";

const url= "https://vyxeojjzxwapzoevbrpb.supabase.co";
const key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ5eGVvamp6eHdhcHpvZXZicnBiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxNzY1OTYsImV4cCI6MjA3OTc1MjU5Nn0.zn1cG4IpjglAIpwVKNkHre2m3555qbJUwBMFZo-gB9M";
const supabase = createClient(url,key);
/*
Necessary Endpoints and Pathway essentially
All are POST
1. getting the image and uploading it to our supabase bucket - Task assigned to Koushik Karthik
2. Getting the most recent image from the bucket, running it through a CV model and returning the ingredients - Siddharth Nittur
3. Storing the ingredients as well as their respective expiry dates somewhere - Govind Nair
4. Taking the ingredients and running it through a API like spoontacular and returning the recipes and possibly their nutritional facts - Govind Nair
5. User login/Signup - Koushik Karthik 

Additional Tasks:
1. Deploy/Prod Pipeline (Cloudflare, Domain Management & Deploy, Api Deploy)  - Govind Nair
2. Integrating into Frontend (Taking the image and sending it off to the api, then displaying and asking the user to review ingredients)- Siddharth Nittur
3. Integrating into Frontend (Recipe recommendations & Progress tracking) - Govind Nair

*/