# PriceIQ — The Smart Pricing Dashboard

Welcome to **PriceIQ**! This is an intelligent, AI-powered web application designed to help e-commerce store owners and analysts automatically determine the perfect price for their products. 

Instead of guessing or spending hours researching competitors, PriceIQ uses artificial intelligence to do the heavy lifting for you, while keeping you in total control.

---

## 🌟 What Does It Do?

Imagine you are selling a "Garmin Watch". PriceIQ works as your personal team of analysts:
1. **It spies on competitors:** It looks at what prices your competitors are currently charging.
2. **It checks your stock:** It checks how many watches you have left in your warehouse and what your profit margins are.
3. **It predicts demand:** It figures out if this product is currently trending or in high demand.
4. **It gives you a recommendation:** It puts all this information together and recommends the perfect new price for your watch.
5. **You make the final call:** It shows you the recommendation. If you approve it, it automatically updates the price on your store. If you don't like it, you can reject or modify it!

---

## 🤖 How the AI "Brain" Works

PriceIQ doesn't just use one AI; it uses a "Multi-Agent System". Think of it as a boardroom meeting with 5 different experts:

* 🕵️ **The Market Expert:** Figures out what Amazon, Walmart, and other competitors are doing.
* 📦 **The Inventory Expert:** Ensures you never sell a product for less than it costs you to buy it.
* 📈 **The Demand Expert:** Looks at seasonal trends and shopping behaviors.
* 🧠 **The Strategy Expert:** The "boss" who listens to the other three and makes the final pricing decision.
* 🛡️ **The Compliance Expert:** Makes sure the final decision is executed safely and logs everything in the Audit Trail.

---

## 🐳 The Easiest Way: Run with Docker

If you have Docker Desktop installed, you can skip the manual setup and launch the entire app with a single command!

1. Open your terminal in the root folder (`PriceIQ`).
2. Type this command:
   ```bash
   docker-compose up --build -d
   ```
3. Wait 1-2 minutes for it to build. Once finished, go to 👉 **http://localhost:3000**

*(Note: Don't forget to put your `GROQ_API_KEY` inside `backend/.env` before you build it!)*

---

## 🚀 The Manual Way: Run on Your Computer

If you don't have Docker, you can run the application manually by following these step-by-step instructions.

### Prerequisites
Before you start, make sure you have installed:
* **Python** (for the backend server)
* **Node.js** (for the frontend website)

### Step 1: Start the Backend (The Brain)
Open your computer's terminal (Command Prompt or PowerShell), and type these commands one by one:

```bash
# 1. Go into the backend folder
cd backend

# 2. Create a virtual environment (a safe space for python)
python -m venv venv

# 3. Activate the environment (Windows)
.\venv\Scripts\Activate.ps1

# 4. Install the required files
pip install -r requirements.txt

# 5. Set up your secret keys
cp .env.example .env
```
*(Note: Open the newly created `.env` file in the backend folder and add your `GROQ_API_KEY` to enable the AI).*

```bash
# 6. Set up the database and load demo data
alembic upgrade head
python scripts/seed.py

# 7. Turn on the server!
uvicorn app.main:app --reload
```

### Step 2: Start the Frontend (The Website)
Open a **new, second terminal window**, and type these commands:

```bash
# 1. Go into the frontend folder
cd frontend

# 2. Install the required website files
npm install

# 3. Set up the website settings
cp .env.example .env.local

# 4. Turn on the website!
npm run dev
```

---

## 🎮 How to Test the App

Once both the backend and frontend are running, open your web browser and go to:
👉 **http://localhost:3000**

### Demo Login Accounts
You can log in using these demo credentials:
* **Admin Account:** `admin@klypup.com` | Password: `Admin@123`
* **Analyst Account:** `analyst@klypup.com` | Password: `Analyst@123`

### Step-by-Step Test Drive
1. **Login:** Log in with the Admin account.
2. **View Catalog:** Click on **Catalog** to see all your products.
3. **Run AI:** Click the **Run AI Analysis** button in the top right. 
4. **Review:** Go to the **Recommendations** tab to see what the AI suggested!
5. **Approve:** Click "Approve" on a recommendation, and then go to the **Audit Trail** tab to see the official record of your price change. 

---

## 📸 Screenshots (Admin View)

Here is a glimpse of the PriceIQ dashboard running under the Admin account:

### 1. Terminal Setup
![Terminal Setup](docs/terminal-setup.png)

### 2. Admin Dashboard Overview
![Admin Overview](docs/admin-overview.png)

### 3. Product Catalog
![Product Catalog](docs/product-catalog.png)

### 4. Running AI Analysis
![Running AI Analysis](docs/analyzing-catalog.png)

### 5. AI Recommendations
![AI Recommendations](docs/ai-recommendations.png)

*(Note: Please ensure the images you uploaded are saved inside the `docs/` folder with the filenames matching the links above, or update the links to point to your image locations.)*

---

## 📸 Screenshots (Analyst View)

Here is a glimpse of the PriceIQ dashboard running under the Analyst account:

### 1. Analyst Dashboard Overview
![Analyst Overview](docs/analyst-overview.png)

### 2. Recommendations
![Analyst Recommendations](docs/analyst-recommendations.png)

### 3. Audit Trail
![Analyst Audit Trail](docs/analyst-audit-trail.png)

---

## 📚 Technical Documentation
For evaluators and engineers, please see the `docs` folder for architectural and product decisions:
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Technical Decisions](docs/DECISIONS.md)

---

*Built with FastAPI, Next.js, and Groq LLM infrastructure.*
