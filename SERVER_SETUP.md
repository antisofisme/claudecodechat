# Setup Server API - Remote Control dari Claude Code

API server ini memungkinkan saya (Claude) untuk remote control server Anda dari chat!

## Quick Start

### 1. Install di Server/PC Anda

```bash
# Clone repo
git clone https://github.com/antisofisme/claudecodechat.git
cd claudecodechat

# Install dependencies
pip install -r requirements.txt

# Set secret key (PENTING!)
export API_SECRET="your-super-secret-key-here"

# Run server
python3 server-api.py
```

Server akan jalan di `http://localhost:5000`

### 2. Expose ke Internet (Pilih salah satu)

#### Opsi A: Ngrok (Tercepat untuk testing)
```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Run ngrok
ngrok http 5000
```

Copy URL yang muncul (contoh: `https://abc123.ngrok.io`)

#### Opsi B: Cloudflare Tunnel (Gratis & Permanen)
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Run tunnel
cloudflared tunnel --url http://localhost:5000
```

Copy URL yang muncul (contoh: `https://xyz.trycloudflare.com`)

#### Opsi C: Deploy ke Cloud (Production)
Deploy ke Railway/Render/Fly.io dengan auto-HTTPS

### 3. Kasih Info ke Claude

Setelah dapat URL publik, kasih ke saya:
```
URL: https://your-tunnel-url.com
Secret: your-super-secret-key-here
```

### 4. Test Connection

```bash
# Health check
curl https://your-url.com/health

# Test dengan auth
curl -X POST https://your-url.com/execute \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami"}'
```

## API Endpoints

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/health` | GET | Health check (no auth) |
| `/execute` | POST | Execute shell command |
| `/git/pull` | POST | Git pull di directory |
| `/service/restart` | POST | Restart service (systemd/pm2/docker) |
| `/service/status` | GET | Cek status service |
| `/logs` | GET | Read log files |
| `/deploy` | POST | Full deploy (pull + install + restart) |
| `/system/info` | GET | System metrics (CPU/RAM/Disk) |

## Contoh Usage dari Claude

Setelah setup, saya bisa:

```
Anda: "cek status backend server"
Claude: [calls /service/status] "Backend running, CPU 12%, uptime 3 days"

Anda: "deploy backend terbaru"
Claude: [calls /deploy] "Deployed! Git pulled 3 commits, dependencies installed, service restarted"

Anda: "lihat log error terakhir"
Claude: [calls /logs] "Last 5 errors: [shows logs]"

Anda: "restart nginx"
Claude: [calls /service/restart] "Nginx restarted successfully"
```

## Security

⚠️ **PENTING:**
1. Gunakan secret key yang kuat
2. Jangan expose tanpa auth
3. Kalau production, pakai HTTPS
4. Batasi IP access kalau perlu (firewall)
5. Jalankan sebagai user non-root kalau bisa

## Run as Service (Production)

### Systemd Service

Buat file `/etc/systemd/system/claude-api.service`:

```ini
[Unit]
Description=Claude Remote API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/claudecodechat
Environment="API_SECRET=your-secret-key"
Environment="PORT=5000"
ExecStart=/usr/bin/python3 /path/to/claudecodechat/server-api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable & start:
```bash
sudo systemctl enable claude-api
sudo systemctl start claude-api
sudo systemctl status claude-api
```

### PM2 (Alternatif)

```bash
pm2 start server-api.py --name claude-api --interpreter python3
pm2 save
pm2 startup
```

## Troubleshooting

**Permission denied saat execute command:**
- Tambahkan user ke sudoers
- Atau jalankan command tanpa sudo

**Tunnel disconnected:**
- Untuk production, deploy ke cloud platform
- Atau gunakan systemd untuk auto-restart tunnel

**Command timeout:**
- Edit timeout di code (default 5 menit)
- Atau jalankan long-running tasks di background

## Production Deployment

Untuk production yang reliable, deploy ke:

1. **VPS Anda** + Nginx reverse proxy + SSL
2. **Railway** (saya bisa auto-deploy via GitHub)
3. **Render** (auto-deploy, free tier)
4. **Fly.io** (global edge deployment)

Kasih tahu kalau mau saya setup production deployment!
