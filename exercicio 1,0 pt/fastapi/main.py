from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from typing import List
from datetime import datetime

app = FastAPI()

# Monta o diretório 'static' para servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Conteúdo HTML da página do chat
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="chat-container">
        <div id="chat" class="chat-box"></div>
        <input type="text" id="messageText" class="chat-input" placeholder="Type a message..." />
    </div>
    <script>
        let ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = function(event) {
            let messages = document.getElementById('chat');
            let message = document.createElement('div');
            message.className = 'chat-message';
            message.textContent = event.data;
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        };
        document.getElementById('messageText').addEventListener('keyup', function(event) {
            if (event.keyCode === 13) {
                let input = document.getElementById('messageText');
                ws.send(input.value);
                input.value = '';
            }
        });
    </script>
</body>
</html>
"""

# Classe para gerenciar as conexões WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_message(self, message: str):
        now = datetime.now().strftime("%H:%M")
        for connection in self.active_connections:
            await connection.send_text(f"{now} - {message}")

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_message(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)
