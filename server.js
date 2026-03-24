const WebSocket = require('ws');
const net = require('net');

const VPS_IP = process.env.VPS_IP;
const PORT_TUNNEL = parseInt(process.env.PORT_TUNNEL || "22");
const PORT = process.env.PORT || 8080;

if (!VPS_IP) {
  console.error("Missing VPS_IP env");
  process.exit(1);
}

const wss = new WebSocket.Server({ port: PORT });

console.log(`WS relay listening on ${PORT}`);
console.log(`Forwarding to ${VPS_IP}:${PORT_TUNNEL}`);

wss.on('connection', function connection(ws, req) {
  console.log("New client:", req.socket.remoteAddress);

  const tcp = net.connect(PORT_TUNNEL, VPS_IP, () => {
    console.log("Connected to VPS");
  });
  ws.on('message', (msg) => {
    if (tcp.writable) {
      tcp.write(msg);
    }
  });

  tcp.on('data', (data) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(data);
    }
  });
  
  ws.on('close', () => {
    tcp.destroy();
  });

  tcp.on('close', () => {
    ws.close();
  });

  ws.on('error', () => tcp.destroy());
  tcp.on('error', () => ws.close());
});
