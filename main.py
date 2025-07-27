from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent import generate_recommendations_from_input

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Smart Community Agent API is running."}

@app.post("/agent")
async def call_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input")

        if not user_input:
            return {"status": "error", "message": "Missing 'input'"}

        # ✅ Call the correct tool directly
        result = generate_recommendations_from_input(user_input)

        return {"status": "success", "response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
