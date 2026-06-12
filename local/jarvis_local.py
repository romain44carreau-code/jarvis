import asyncio
import websockets
import json
import psutil
from datetime import datetime
import os

class JarvisLocalAgent:
    def __init__(self):
        self.agent_id = f"windows-pc-{os.getenv('USERNAME', 'user')}"
        self.orchestrator_url = None  # À définir plus tard
        self.websocket = None
        self.running = False
    
    def get_system_info(self):
        """Récupère les infos système du PC"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('C:').percent,
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_message(self, message_type, data):
        """Envoie un message à l'orchestrateur"""
        if self.websocket:
            message = {
                "type": message_type,
                "agent_id": self.agent_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(message))
            print(f"📤 Envoyé: {message_type} -> {data}")
    
    async def handle_message(self, message):
        """Traite les messages reçus de l'orchestrateur"""
        print(f"📨 Reçu: {message}")
        
        if message["type"] == "welcome":
            # Répondre avec les infos système
            system_info = self.get_system_info()
            await self.send_message("system_info", system_info)
            
        elif message["type"] == "ack":
            print("✅ Message acquitté par l'orchestrateur")
    
    async def connect_to_orchestrator(self, url):
        """Se connecte à l'orchestrateur JARVIS"""
        self.orchestrator_url = url
        websocket_url = f"{url}/ws/agent/{self.agent_id}"
        
        try:
            print(f"🔗 Connexion à JARVIS: {websocket_url}")
            async with websockets.connect(websocket_url) as websocket:
                self.websocket = websocket
                self.running = True
                print("✅ Connecté à JARVIS!")
                
                # Écouter les messages
                while self.running:
                    try:
                        message_raw = await websocket.recv()
                        message = json.loads(message_raw)
                        await self.handle_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        print("❌ Connexion fermée")
                        break
                        
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
    
    def stop(self):
        """Arrête l'agent"""
        self.running = False

async def main():
    """Test local de l'agent"""
    agent = JarvisLocalAgent()
    
    # Pour les tests, on se connecte en local
    print("🤖 Agent JARVIS Local démarré")
    print(f"💻 Agent ID: {agent.agent_id}")
    
    # Test avec un orchestrateur local (Phase 1)
    # Connexion à JARVIS dans le cloud
    cloud_url = "wss://jarvis-e4xu.onrender.com"
    await agent.connect_to_orchestrator(cloud_url)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Agent JARVIS Local arrêté")