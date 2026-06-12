import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(title="JARVIS Orchestrator")

# Autoriser les connexions depuis n'importe où
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des connexions
connected_agents = {}
connected_interfaces = {}
logs = []
system_metrics = {}

def add_log(message, agent_id="system"):
    """Ajoute un log avec timestamp"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_id,
        "message": message
    }
    logs.append(log_entry)
    
    # Garder seulement les 100 derniers logs
    if len(logs) > 100:
        logs.pop(0)
    
    print(f"[{log_entry['timestamp']}] [{agent_id}] {message}")
    
    # Diffuser le log aux interfaces connectées
    broadcast_to_interfaces("log", {"message": message, "agent": agent_id})

def broadcast_to_interfaces(message_type, data):
    """Diffuse un message à toutes les interfaces connectées"""
    for interface_id, websocket in connected_interfaces.items():
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            asyncio.create_task(websocket.send_text(json.dumps(message)))
        except:
            pass  # Ignorer les connexions fermées

async def send_to_interface(interface_id, message_type, data):
    """Envoie un message à une interface spécifique"""
    if interface_id in connected_interfaces:
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await connected_interfaces[interface_id].send_text(json.dumps(message))
        except:
            pass

# Routes pour servir l'interface web
frontend_path = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def serve_interface():
    """Sert l'interface web directement"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return HTMLResponse("""
        <h1>🤖 JARVIS Orchestrator</h1>
        <p>Interface web non trouvée. Développement en cours...</p>
        <p><a href="/status">Voir le statut</a></p>
        """)

@app.get("/style.css")
async def serve_css():
    css_path = frontend_path / "style.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse("/* CSS non trouvé */", media_type="text/css")

@app.get("/script.js")
async def serve_js():
    js_path = frontend_path / "script.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse("/* JavaScript non trouvé */", media_type="application/javascript")

@app.get("/api/status")
async def api_status():
    """API REST pour le statut"""
    return {
        "name": "JARVIS",
        "status": "online",
        "agents_connected": len(connected_agents),
        "interfaces_connected": len(connected_interfaces),
        "version": "1.0.0",
        "agents": list(connected_agents.keys()),
        "logs": logs[-20:],
        "system_metrics": system_metrics
    }

# Compatibility route
@app.get("/status")
async def status():
    return await api_status()

@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: str):
    """WebSocket pour les agents locaux"""
    await websocket.accept()
    connected_agents[agent_id] = websocket
    add_log(f"Agent connecté: {agent_id}", agent_id)
    
    try:
        # Message de bienvenue
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": f"Bienvenue {agent_id}, tu es connecté à JARVIS",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Recevoir les messages de l'agent
            data = await websocket.receive_text()
            message = json.loads(data)
            add_log(f"Reçu de {agent_id}: {message.get('type', 'unknown')}", agent_id)
            
            # Traiter les messages spéciaux
            if message.get("type") == "system_info":
                system_metrics[agent_id] = message.get("data", {})
                broadcast_to_interfaces("system_info", message.get("data", {}))
            
            # Accusé de réception
            await websocket.send_text(json.dumps({
                "type": "ack",
                "received": message,
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        connected_agents.pop(agent_id, None)
        system_metrics.pop(agent_id, None)
        add_log(f"Agent déconnecté: {agent_id}", agent_id)

@app.websocket("/ws/interface/{interface_id}")
async def websocket_interface(websocket: WebSocket, interface_id: str):
    """WebSocket pour les interfaces web"""
    await websocket.accept()
    connected_interfaces[interface_id] = websocket
    add_log(f"Interface connectée: {interface_id}", "interface")
    
    try:
        # Message de bienvenue
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": f"Interface {interface_id} connectée à JARVIS",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Envoyer le statut initial
        await send_to_interface(interface_id, "status_response", {
            "agents": list(connected_agents.keys()),
            "system_metrics": system_metrics
        })
        
        while True:
            # Recevoir les messages de l'interface
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            message_data = message.get("data", {})
            
            add_log(f"Reçu de {interface_id}: {message_type}", "interface")
            
            if message_type == "get_status":
                await send_to_interface(interface_id, "status_response", {
                    "agents": list(connected_agents.keys()),
                    "system_metrics": system_metrics
                })
                
            elif message_type == "chat":
                # Pour l'instant, réponse simple
                user_message = message_data.get("message", "")
                response = f"JARVIS a reçu: '{user_message}'. Traitement en cours..."
                
                await send_to_interface(interface_id, "chat_response", {
                    "response": response,
                    "original_message": user_message
                })
                
            elif message_type == "command":
                # Transmettre la commande aux agents appropriés
                command = message_data.get("command", "")
                target_agent = message_data.get("target", None)
                
                if target_agent and target_agent in connected_agents:
                    try:
                        await connected_agents[target_agent].send_text(json.dumps({
                            "type": "command",
                            "command": command,
                            "from_interface": interface_id,
                            "timestamp": datetime.now().isoformat()
                        }))
                        add_log(f"Commande transmise à {target_agent}: {command}", "orchestrator")
                    except:
                        await send_to_interface(interface_id, "error", {
                            "message": f"Impossible d'envoyer la commande à {target_agent}"
                        })
                else:
                    await send_to_interface(interface_id, "error", {
                        "message": "Agent cible non trouvé ou non connecté"
                    })
            
    except WebSocketDisconnect:
        connected_interfaces.pop(interface_id, None)
        add_log(f"Interface déconnectée: {interface_id}", "interface")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🤖 JARVIS Orchestrator démarré sur port {port}")
    print(f"📱 Interface web disponible sur http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)