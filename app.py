# frontend/app.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime
import base64
from io import BytesIO

# ---------------- Load .env ----------------
load_dotenv()
BASE = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="AI Gym Trainer", 
    layout="wide",
    page_icon="💪",
    initial_sidebar_state="expanded"
)

# ---------------- Custom CSS for 3D Effects ----------------
st.markdown("""
<style>
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #4CAF50;
        --accent-color: #667eea;
        --text-color: #333;
        --bg-color: #ffffff;
        --card-bg: linear-gradient(145deg, #ffffff, #f0f0f0);
        --shadow: 5px 5px 15px rgba(0,0,0,0.2), -5px -5px 15px rgba(255,255,255,0.7);
    }
    
    [data-theme="dark"] {
        --primary-color: #64b5f6;
        --secondary-color: #81c784;
        --accent-color: #9575cd;
        --text-color: #ffffff;
        --bg-color: #1e1e1e;
        --card-bg: linear-gradient(145deg, #2d2d2d, #252525);
        --shadow: 5px 5px 15px rgba(0,0,0,0.4), -5px -5px 15px rgba(255,255,255,0.1);
    }
    
    body {
        background-color: var(--bg-color);
        color: var(--text-color);
        transition: all 0.3s ease;
    }
    
    .main-header {
        font-size: 3rem;
        color: var(--primary-color);
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
    }
    .card {
        background: var(--card-bg);
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: var(--shadow);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 8px 8px 20px rgba(0,0,0,0.25), 
                   -8px -8px 20px rgba(255,255,255,0.8);
    }
    .stButton>button {
        background: linear-gradient(145deg, var(--secondary-color), #45a049);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 25px;
        font-weight: bold;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 5px 5px 12px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: linear-gradient(135deg, var(--accent-color), #764ba2);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50, #34495e);
        color: white;
    }
    .progress-bar {
        height: 20px;
        background: linear-gradient(90deg, var(--secondary-color), #8BC34A);
        border-radius: 10px;
        margin: 10px 0;
    }
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #000;
        font-weight: bold;
        margin: 2px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .theme-toggle {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: var(--card-bg);
        border-radius: 50%;
        padding: 10px;
        box-shadow: var(--shadow);
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Theme Toggle ----------------
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Theme toggle button
st.markdown(f"""
<div class="theme-toggle" onclick="toggleTheme()">
    {'🌙' if st.session_state.dark_mode else '☀️'}
</div>
<script>
function toggleTheme() {{
    window.parent.document.querySelector('body').setAttribute('data-theme', 
        window.parent.document.querySelector('body').getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
    );
}}
</script>
""", unsafe_allow_html=True)

# Apply theme
if st.session_state.dark_mode:
    st.markdown("<script>document.body.setAttribute('data-theme', 'dark')</script>", unsafe_allow_html=True)
else:
    st.markdown("<script>document.body.setAttribute('data-theme', 'light')</script>", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown('<h1 class="main-header">🏋️‍♂️ AI Gym Trainer Pro</h1>', unsafe_allow_html=True)

# ---------------- Sidebar with Enhanced Styling ----------------
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h2 style='color: white;'>💪 Fitness Hub</h2>
        <p style='color: #bbb;'>Your AI Personal Trainer</p>
    </div>
    """, unsafe_allow_html=True)
    
    menu = ["🏠 Dashboard", "🔐 Login", "📝 Signup", "👤 Profile", "💬 Chat & Macros", "📊 Progress"]
    choice = st.selectbox("Navigation", menu, index=0)
    
    if "user" in st.session_state:
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px;'>
            <p style='color: white; margin: 0;'>Logged in as User ID: <strong>{st.session_state['user']}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state["user"]
            st.rerun()

# ---------------- Dashboard ----------
if choice == "🏠 Dashboard":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3>🎯 Your Goals</h3>
            <p>Track & Achieve</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3>💪 Workouts</h3>
            <p>AI-Powered Plans</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h3>🥗 Nutrition</h3>
            <p>Smart Macros</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Achievement Badges Section
    st.markdown("""
    <div class='card'>
        <h2>🏆 Your Achievements</h2>
        <div style='display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0;'>
            <span class='badge'>🔥 7-Day Streak</span>
            <span class='badge'>💪 5 Workouts</span>
            <span class='badge'>🥗 Healthy Eating</span>
            <span class='badge'>⚡ Energy Boost</span>
            <span class='badge'>🎯 Goal Crusher</span>
        </div>
        <p>Keep going! You're doing amazing! 🚀</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
        <h2>Welcome to AI Gym Trainer! 🎉</h2>
        <p>Get personalized workout plans, nutrition advice, and progress tracking powered by AI.</p>
        <p>👉 <strong>Get started by logging in or signing up!</strong></p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- Signup ----------
elif choice == "📝 Signup":
    st.markdown("""
    <div class='card'>
        <h2>Create Your Account 🚀</h2>
        <p>Join our fitness community and start your journey!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        s_email = st.text_input("📧 Email", placeholder="Enter your email")
        s_username = st.text_input("👤 Username", placeholder="Choose a username")
    
    with col2:
        s_password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
    
    if st.button("🎯 Create Account", use_container_width=True):
        if s_password != confirm_password:
            st.error("❌ Passwords don't match!")
        else:
            try:
                with st.spinner("Creating your account..."):
                    time.sleep(1)
                    r = requests.post(f"{BASE}/signup", json={"email": s_email,"username":s_username,"password":s_password})
                    if r.status_code == 200:
                        st.success("✅ " + r.json()["message"])
                        st.balloons()
                    else:
                        st.error("❌ " + r.json()["detail"])
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ---------------- Login ----------
elif choice == "🔐 Login":
    st.markdown("""
    <div class='card'>
        <h2>Welcome Back! 👋</h2>
        <p>Sign in to continue your fitness journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    l_email = st.text_input("📧 Email", placeholder="Your email address")
    l_password = st.text_input("🔒 Password", type="password", placeholder="Your password")
    
    if st.button("🚀 Login", use_container_width=True):
        try:
            with st.spinner("Signing you in..."):
                time.sleep(1)
                r = requests.post(f"{BASE}/login", json={"email": l_email,"password":l_password})
                if r.status_code == 200:
                    st.session_state["user"] = r.json()["user_id"]
                    st.success("✅ " + r.json().get("message","Login successful!"))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ " + r.json().get("detail","Invalid credentials"))
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------- Profile ----------
elif choice == "👤 Profile" and "user" in st.session_state:
    st.markdown("""
    <div class='card'>
        <h2>Your Fitness Profile 📊</h2>
        <p>Personalize your experience for better results</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.slider("🎂 Age", 18, 100, 25)
        height = st.slider("📏 Height (cm)", 100, 250, 175)
        weight = st.slider("⚖️ Weight (kg)", 30, 200, 70)
    
    with col2:
        sex = st.selectbox("👥 Sex", ["Male", "Female", "Other"])
        activity = st.selectbox("🏃 Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])
        goal = st.selectbox("🎯 Goal", ["Lose Weight", "Gain Muscle", "Maintain Weight", "Improve Fitness"])
    
    # Achievement Badges in Profile
    st.markdown("""
    <div class='card'>
        <h3>🏆 Your Achievement Badges</h3>
        <div style='display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;'>
            <span class='badge'>🔥 7-Day Streak</span>
            <span class='badge'>💪 Strength Master</span>
            <span class='badge'>🥗 Nutrition Pro</span>
            <span class='badge'>🏃 Cardio King</span>
            <span class='badge'>🎯 Goal Setter</span>
            <span class='badge'>⚡ Consistency</span>
        </div>
        <p>Earn more badges by staying consistent with your workouts! 💪</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("💾 Save Profile", use_container_width=True):
        try:
            data = {
                "user_id": st.session_state["user"],
                "age": age, "height_cm": height, "weight_kg": weight,
                "sex": sex, "activity_level": activity, "goal": goal
            }
            with st.spinner("Saving your profile..."):
                r = requests.post(f"{BASE}/profile/create", json=data)
                st.success("✅ " + r.json()["message"])
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------------- Chat & Macros ----------
elif choice == "💬 Chat & Macros" and "user" in st.session_state:
    st.markdown("""
    <div class='card'>
        <h2>AI Fitness Coach 💬</h2>
        <p>Get personalized advice from your AI trainer</p>
    </div>
    """, unsafe_allow_html=True)
    
    query = st.text_area("💭 Ask your fitness question...", height=100, 
                        placeholder="e.g., How can I build muscle? What's the best workout for beginners?")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🤖 Get AI Advice", use_container_width=True):
            try:
                with st.spinner("🧠 AI is thinking..."):
                    r = requests.post(f"{BASE}/chat", json={"user_id": st.session_state["user"], "message": query})
                    response_data = r.json()
                
                # Display response in a beautiful card
                st.markdown(f"""
                <div class='card' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;'>
                    <h3>💪 AI Fitness Advice</h3>
                    <p>{response_data.get('response', 'Welcome to your AI gym trainer!')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Detailed sections
                with st.expander("📋 Detailed Workout Plan", expanded=True):
                    st.write("**🎯 Advice:**")
                    st.info(response_data.get("advice", ""))
                    
                    st.write("**🏋️‍♂️ Workout Plan:**")
                    workout_plan = response_data.get("workout_plan", [])
                    if workout_plan:
                        for i, exercise in enumerate(workout_plan, 1):
                            st.write(f"**{i}.** {exercise}")
                    else:
                        st.write("No specific workout plan provided")
                
                with st.expander("🥗 Nutrition Guidance", expanded=True):
                    st.write("**🍎 Nutrition Tips:**")
                    st.success(response_data.get("nutrition_tips", ""))
                    
                    st.write("**📊 Recommended Daily Macros:**")
                    macros = response_data.get("macros", {})
                    if macros:
                        cols = st.columns(3)
                        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]
                        for i, (key, value) in enumerate(macros.items()):
                            with cols[i]:
                                st.markdown(f"""
                                <div style='background: {colors[i]}; color: white; padding: 15px; border-radius: 10px; text-align: center;'>
                                    <h4>{key.title()}</h4>
                                    <h2>{value}g</h2>
                                </div>
                                """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ Error fetching AI advice: {e}")
    
    with col2:
        if st.button("📈 Show My Macros", use_container_width=True):
            try:
                with st.spinner("Calculating macros..."):
                    r = requests.get(f"{BASE}/macros/{st.session_state['user']}")
                    macros = r.json()
                
                st.write("**🎯 Your Personalized Macros**")
                
                # Create a beautiful chart
                fig, ax = plt.subplots(figsize=(8, 6))
                nutrients = list(macros.keys())
                values = list(macros.values())
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
                
                bars = ax.bar(nutrients, values, color=colors, edgecolor='black', linewidth=2)
                ax.set_ylabel('Grams')
                ax.set_title('Daily Macronutrients')
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                           f'{value}g', ha='center', va='bottom', fontweight='bold')
                
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"❌ Error fetching macros: {e}")

# ---------------- Progress ----------
elif choice == "📊 Progress" and "user" in st.session_state:
    st.markdown("""
    <div class='card'>
        <h2>Progress Tracker 📈</h2>
        <p>Monitor your fitness journey and see your improvements</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Add New Progress")
        p_weight = st.slider("⚖️ Current Weight (kg)", 30, 200, 70)
        p_goal = st.selectbox("🎯 Current Goal", ["Lose Weight", "Gain Muscle", "Maintain Weight"])
        
        # Progress Photos Upload Feature
        st.subheader("📸 Progress Photos")
        uploaded_photo = st.file_uploader("Upload your progress photo", type=['png', 'jpg', 'jpeg'], key="progress_photo")
        
        if uploaded_photo:
            st.image(uploaded_photo, caption="Your progress photo", use_column_width=True)
            if st.button("💾 Save Photo", key="save_photo"):
                st.success("✅ Photo saved successfully!")
        
        if st.button("💾 Save Progress", use_container_width=True):
            try:
                with st.spinner("Saving your progress..."):
                    r = requests.post(f"{BASE}/progress/add", json={
                        "user_id": st.session_state["user"],
                        "weight": p_weight,
                        "goal": p_goal
                    })
                    st.success("✅ " + r.json()["message"])
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error adding progress: {e}")
    
    with col2:
        st.subheader("📊 Progress History")
        try:
            r = requests.get(f"{BASE}/progress/{st.session_state['user']}")
            history = r.json()
            
            if history:
                # Create DataFrame for better visualization
                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # Display progress chart
                st.line_chart(df.set_index('date')['weight'])
                
                # Show progress stats
                if len(df) > 1:
                    weight_change = df['weight'].iloc[-1] - df['weight'].iloc[0]
                    st.metric("Overall Weight Change", f"{weight_change:+.1f} kg")
                    
                # Achievement badges based on progress
                st.markdown("""
                <div class='card'>
                    <h3>🏆 Progress Achievements</h3>
                    <div style='display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;'>
                        <span class='badge'>📈 Track Master</span>
                        <span class='badge'>⚖️ Weight Warrior</span>
                        <span class='badge'>🎯 Consistency</span>
                    </div>
                    <p>Keep tracking to unlock more achievements! 🚀</p>
                </div>
                """, unsafe_allow_html=True)
                    
            else:
                st.info("📝 No progress data yet. Start tracking to see your journey!")
                
        except Exception as e:
            st.error(f"❌ Error fetching progress: {e}")

# ---------------- Not Logged In Message ----------
elif choice in ["👤 Profile", "💬 Chat & Macros", "📊 Progress"] and "user" not in st.session_state:
    st.warning("🔒 Please log in to access this section!")
    if st.button("👉 Go to Login"):
        choice = "🔐 Login"
        st.rerun()
