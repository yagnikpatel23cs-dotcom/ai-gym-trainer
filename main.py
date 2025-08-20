# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from supabase import create_client
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import json
from fastapi.responses import JSONResponse

# ---------------- Load .env ----------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BACKEND_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ---------------- Supabase client ----------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Gemini client ----------------
genai.configure(api_key=GOOGLE_API_KEY)

# ---------------- FastAPI setup ----------------
app = FastAPI(title="AI Gym Trainer Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------- Models ----------------
class SignupModel(BaseModel):
    email: str
    username: str
    password: str

class LoginModel(BaseModel):
    email: str
    password: str

class ProfileModel(BaseModel):
    user_id: int
    age: int
    height_cm: float
    weight_kg: float
    sex: str
    activity_level: str
    goal: str

class ChatModel(BaseModel):
    user_id: int
    message: str

class ProgressModel(BaseModel):
    user_id: int
    weight: float
    goal: str

# ---------------- Helper Functions ----------------
def calculate_macros(weight_kg: float):
    protein = round(weight_kg * 2.0, 1)
    carbs = round(weight_kg * 3.0, 1)
    fats = round(weight_kg * 1.0, 1)
    return {"protein": protein, "carbs": carbs, "fats": fats}

def today():
    return datetime.utcnow().isoformat()

def get_profile(user_id: int):
    res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]
    return None

# ---------------- Endpoints ----------------
@app.post("/signup")
def signup(user: SignupModel):
    try:
        res = supabase.table("users").insert({
            "email": user.email,
            "username": user.username,
            "password": user.password
        }).execute()
        
        # Check for errors in the response
        if hasattr(res, 'error') and res.error:
            raise HTTPException(status_code=400, detail=str(res.error))
            
        return {"message": "Signup successful!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

@app.post("/login")
def login(user: LoginModel):
    try:
        res = supabase.table("users").select("*").eq("email", user.email).eq("password", user.password).execute()
        
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return {"user_id": res.data[0]["id"], "access_token": "dummy-token", "message": "Login successful!"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.post("/profile/create")
def create_profile(profile: ProfileModel):
    try:
        res = supabase.table("profiles").upsert({
            "user_id": profile.user_id,
            "age": profile.age,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "sex": profile.sex,
            "activity_level": profile.activity_level,
            "goal": profile.goal
        }).execute()
        
        # Check for errors
        if hasattr(res, 'error') and res.error:
            raise HTTPException(status_code=400, detail=str(res.error))
            
        return {"message": "Profile saved!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Profile creation failed: {str(e)}")

@app.get("/profile/{user_id}")
def get_profile_endpoint(user_id: int):
    try:
        profile = get_profile(user_id)
        if not profile:
            return {}
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@app.get("/macros/{user_id}")
def get_macros_endpoint(user_id: int):
    try:
        profile = get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        macros = calculate_macros(profile.get("weight_kg", 70))
        return macros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating macros: {str(e)}")
@app.post("/chat")
def chat(chat: ChatModel):
    try:
        profile = get_profile(chat.user_id)
        if not profile:
            return {
                "response": "Please complete your profile first to receive personalized fitness advice.",
                "advice": "Your profile helps me understand your age, fitness level, goals, and body composition to provide customized plans.",
                "workout_plan": ["Complete profile setup to unlock personalized training program"],
                "nutrition_tips": "Profile information is essential for creating diet plans based on your metabolic needs",
                "macros": {"protein": 0, "carbs": 0, "fats": 0}
            }
        
        # Simplified but effective prompt
        prompt = f"""
You are an expert fitness trainer and nutritionist. Provide response in this exact JSON format:

{{
  "response": "Brief summary",
  "advice": "Detailed fitness advice",
  "workout_plan": ["exercise1", "exercise2", "exercise3"],
  "nutrition_tips": "Diet recommendations",
  "macros": {{
    "protein": 150,
    "carbs": 200,
    "fats": 50
  }}
}}

User Profile: {profile}
User Question: {chat.message}

Provide practical, science-based fitness advice. Respond with ONLY the JSON object.
"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            if response and hasattr(response, 'text') and response.text.strip():
                answer = response.text.strip()
                # Clean any Markdown formatting
                answer = answer.replace('```json', '').replace('```', '').strip()
                
                # Validate and parse JSON
                if answer and not answer.startswith('{'):
                    # If response doesn't start with JSON, create fallback
                    return create_fallback_response(profile, chat.message)
                
                try:
                    parsed_response = json.loads(answer)
                    # Validate required fields
                    required_fields = ["response", "advice", "workout_plan", "nutrition_tips", "macros"]
                    if all(field in parsed_response for field in required_fields):
                        return parsed_response
                    else:
                        return create_fallback_response(profile, chat.message)
                except json.JSONDecodeError:
                    return create_fallback_response(profile, chat.message)
            else:
                return create_fallback_response(profile, chat.message)
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return create_fallback_response(profile, chat.message)
            
    except Exception as e:
        print(f"System error: {e}")
        return create_fallback_response(None, chat.message)

def create_fallback_response(profile, user_message):
    """Create a reliable fallback response"""
    weight = profile.get('weight_kg', 70) if profile else 70
    goal = profile.get('goal', 'General Fitness') if profile else 'General Fitness'
    
    # Analyze user message for context
    user_lower = user_message.lower()
    
    if any(word in user_lower for word in ['workout', 'exercise', 'train', 'gym']):
        response = "Here's a balanced workout plan for your fitness goals"
        advice = "Focus on compound exercises with proper form. Progressive overload is key for continuous improvement."
        workout_plan = [
            "Monday: Upper Body - Bench Press 3x8-10, Rows 3x8-10, Shoulder Press 3x10-12",
            "Tuesday: Lower Body - Squats 3x8-10, Deadlifts 3x5-8, Lunges 3x12",
            "Wednesday: Rest or Active Recovery",
            "Thursday: Upper Body - Pull-ups 3xAMRAP, Dips 3x10-12, Bicep Curls 3x12",
            "Friday: Lower Body - Leg Press 4x12, Leg Curls 4x12, Calf Raises 4x15",
            "Weekend: Cardio and Mobility"
        ]
        nutrition_tips = f"Eat {round(weight*2)}g protein daily. Time carbs around workouts. Stay hydrated with 3-4L water."
        
    elif any(word in user_lower for word in ['diet', 'food', 'nutrition', 'eat']):
        response = "Nutrition advice for your fitness journey"
        advice = "Focus on whole foods, adequate protein, and proper meal timing around workouts."
        workout_plan = ["Combine proper nutrition with consistent training for best results"]
        nutrition_tips = f"""For {goal}:
- Protein: {round(weight*2)}g daily from chicken, fish, eggs, dairy
- Carbs: {round(weight*3)}g from rice, potatoes, oats, fruits
- Fats: {round(weight*1)}g from nuts, avocado, olive oil
- Meal frequency: 4-6 meals daily
- Hydration: 3-4 liters water minimum"""
        
    elif any(word in user_lower for word in ['weight loss', 'fat loss', 'lose weight']):
        response = "Weight loss strategy with sustainable approach"
        advice = "Create a moderate calorie deficit through diet and exercise. Focus on protein to preserve muscle."
        workout_plan = [
            "Monday: HIIT Cardio - 30min interval training",
            "Tuesday: Strength Training - Full body compound exercises",
            "Wednesday: Steady State Cardio - 45min moderate pace",
            "Thursday: Strength Training - Different exercises from Tuesday",
            "Friday: Active Recovery - Walking, stretching, mobility",
            "Weekend: Rest or light activity"
        ]
        nutrition_tips = f"Create 500-calorie deficit daily. Eat {round(weight*2)}g protein. Focus on fiber-rich foods for satiety."
        
    elif any(word in user_lower for word in ['muscle', 'gain', 'bulk', 'size']):
        response = "Muscle building program with progressive overload"
        advice = "Focus on compound lifts with progressive overload. Ensure calorie surplus with adequate protein."
        workout_plan = [
            "Monday: Chest & Triceps - Heavy pressing movements",
            "Tuesday: Back & Biceps - Pulling movements",
            "Wednesday: Legs & Core - Squats, deadlifts, accessories",
            "Thursday: Shoulders & Arms - Overhead press and isolation",
            "Friday: Weak Points - Address lagging muscle groups",
            "Weekend: Rest and recovery"
        ]
        nutrition_tips = f"Eat 300-500 calorie surplus. Protein: {round(weight*2.2)}g daily. Carbs around workouts for energy."
        
    else:
        response = "Comprehensive fitness guidance"
        advice = "Consistency in training and nutrition is the foundation of success. Focus on progressive improvement."
        workout_plan = [
            "Monday: Strength Training - Compound exercises 3-4 sets",
            "Tuesday: Cardiovascular Training - 30-45 minutes",
            "Wednesday: Active Recovery - Mobility and flexibility",
            "Thursday: Hypertrophy Training - 8-12 rep range",
            "Friday: Full Body Metabolic Conditioning",
            "Weekend: Rest or recreational activities"
        ]
        nutrition_tips = f"Balanced macronutrients: Protein {round(weight*2)}g, Carbs {round(weight*3)}g, Fats {round(weight*1)}g daily"
    
    return {
        "response": response,
        "advice": advice,
        "workout_plan": workout_plan,
        "nutrition_tips": nutrition_tips,
        "macros": calculate_macros(weight)
    }    
@app.post("/progress/add")
def add_progress(progress: ProgressModel):
    try:
        res = supabase.table("progress").insert({
            "user_id": progress.user_id,
            "weight": progress.weight,
            "goal": progress.goal,
            "date": today()
        }).execute()
        
        # Check for errors in the response
        if hasattr(res, 'error') and res.error:
            raise HTTPException(status_code=400, detail=str(res.error))
        
        # Return success response
        return {"message": "Progress added successfully!"}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Progress addition failed: {str(e)}")

@app.get("/progress/{user_id}")
def get_progress(user_id: int):
    try:
        res = supabase.table("progress").select("*").eq("user_id", user_id).order("date").execute()
        
        # Check for errors
        if hasattr(res, 'error') and res.error:
            raise HTTPException(status_code=400, detail=str(res.error))
        
        # Return data if available
        if hasattr(res, 'data'):
            return res.data
        else:
            return []
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching progress: {str(e)}")

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "OK", "message": "AI Gym Trainer Backend is running"}
