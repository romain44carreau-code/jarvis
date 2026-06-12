from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
import os

app = FastAPI(title="JARVIS Orchestrator")

# Autoriser les connexions depuis n'importe où (pour le dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des agents connectés
connected_agents = {}
logs = []

def add_log(message, agent_id="system"):
    """Ajoute un log avec timestamp"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_id,
        "message": message
    }
    logs.append(log_entry)
    print(f"[{log_entry['timestamp']}] [{agent_id}] {message}")

@app.get("/")
async def root():
    return {
        "name": "JARVIS",
        "status": "online",
        "agents_connected": len(connected_agents),
        "version": "1.0.0"
    }

@app.get("/status")
async def status():
    return {
        "agents": list(connected_agents.keys()),
        "logs": logs[-20:]  # Derniers 20 logs
    }

@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: str):
    """WebSocket pour les agents locaux"""
    await websocket.accept()
    connected_agents[agent_id] = websocket
    add_log(f"Agent connecté: {agent_id}", agent_id)
    
    try:
        # Envoyer un message de bienvenue
        await websocket.send_json({
            "type": "welcome",
            "message": f"Bienvenue {agent_id}, tu es connecté à JARVIS",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Recevoir les messages de l'agent
            data = await websocket.receive_text()
            message = json.loads(data)
            add_log(f"Reçu: {message}", agent_id)
            
            # Répondre avec un accusé de réception
            await websocket.send_json({
                "type": "ack",
                "received": message,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        connected_agents.pop(agent_id, None)
        add_log(f"Agent déconnecté: {agent_id}", agent_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🤖 JARVIS Orchestrator démarré sur port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)