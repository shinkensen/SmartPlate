import { createClient } from "@supabase/supabase-js";
import express from 'express';
import cors from 'cors';
import { supabase } from "../config/supabase";
import multer from 'multer'
const url= "https://vyxeojjzxwapzoevbrpb.supabase.co";
const key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ5eGVvamp6eHdhcHpvZXZicnBiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxNzY1OTYsImV4cCI6MjA3OTc1MjU5Nn0.zn1cG4IpjglAIpwVKNkHre2m3555qbJUwBMFZo-gB9M";
const supabase = createClient(url,key);
const upload = multer({ storage: multer.memoryStorage() });

/*
Necessary Endpoints and Pathway essentially
All are POST
1. getting the image and uploading it to our supabase bucket - Task assigned to Govind Nair - DONE
2. Getting the most recent image from the bucket, running it through a CV model and returning the ingredients - Siddharth Nittur done
3. Storing the ingredients as well as their respective expiry dates somewhere - Koushik done
4. Taking the ingredients and running it through a API like spoontacular and returning the recipes and possibly their nutritional facts - Koushik
5. User login/Signup - Koushik Karthik 

Additional Tasks:
1. Deploy/Prod Pipeline (Cloudflare, Domain Management & Deploy, Api Deploy)  - Govind Nair
2. Integrating into Frontend (Taking the image and sending it off to the api, then displaying and asking the user to review ingredients)- Siddharth Nittur
3. Integrating into Frontend (Recipe recommendations & Progress tracking) - Govind Nair
*/
const conn = express();
conn.use(cors({
    origin: '*', // Allow all origins (or specify your frontend URL)
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
}));
conn.use(express.json());
async function auth(req, res, next) {
    try {
        const authHeader = req.headers["authorization"];
        if (!authHeader) throw new Error("Missing Authorization header");

        const token = authHeader.split(" ")[1];
        const { data: { user }, error } = await supabase.auth.getUser(token);

        if (error || !user) throw new Error("Invalid or expired token");
        req.userId = user.id;
        next();
    } catch (err) {
        return res.status(401).json({ error: err.message });
    }
}
conn.post('uploadImage',auth,async(req,res)=>{
    try{
        const uuid= req.userId;
        const file = req.file;
        const date1 = new Date();
        const date = date1.toString();
        if (!file) {
            return res.status(400).json({ error: "No file uploaded" });
        }
        
        const filePath = `${uuid}/${date}`;
        const { data, error } = await supabase.storage
            .from("user-images")
            .upload(filePath, file.buffer, {
                contentType: file.mimetype,
                upsert: true,
            });
        
        if (error) {
            return res.status(500).json({ error: error.message });
        }
        res.json({filePath: data.path});
    }
    catch (e){
        res.status(500).json({error: e.message});
    }
    
});
conn.listen(3000,()=>{
    console.log("Successfully running on port 3000");
})

function checkUser(){
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    const userId = localStorage.getItem('userId');

    if (!isLoggedIn || !userId){
        window.location.href('signup-new.html');
        return false;
    }
    return true;
}

function logout(){
    if (confirm('U sure?')){
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('isLoggedIn');
        window.location.href('signin-new.html');
    }
}

function logoutBtn(){
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn){
        const navigate = document.getElementById('logoutBtn');
        if(navigate && !document.getElementById('logoutBtn')){

        }
    }
}