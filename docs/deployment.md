# Deployment instrukcijas

## MVP Development Setup

### Priekšnosacījumi

#### Windows sistēmai:
1. **Python 3.9+**
   ```powershell
   python --version
   # Ja nav instalēts: https://python.org/downloads
   ```

2. **Node.js 18+**
   ```powershell
   node --version
   npm --version
   # Ja nav instalēts: https://nodejs.org
   ```

3. **Tesseract OCR**
   ```powershell
   # Lejupielādēt no: https://github.com/UB-Mannheim/tesseract/wiki
   # Instalēt ar latviešu valodas paketi
   # Pievienot PATH mainīgajam
   tesseract --version
   ```

#### Linux sistēmai:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm tesseract-ocr tesseract-ocr-lav

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm tesseract tesseract-langpack-lav
```

### Backend Setup

1. **Pāriet uz backend direktoriju**
   ```bash
   cd backend
   ```

2. **Izveidot virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalēt dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurēt vides mainīgos** (izveidot `.env` failu)
   ```env
   DATABASE_URL=sqlite:///./data/invoices.db
   UPLOAD_DIR=../uploads
   MAX_FILE_SIZE=10485760
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   DEBUG=True
   ```

5. **Inicializēt datubāzi**
   ```bash
   # TODO: Izveidot migration skriptu
   python -c "from app.database import create_tables; create_tables()"
   ```

6. **Palaist development serveri**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend būs pieejams: http://localhost:8000

### Frontend Setup

1. **Pāriet uz frontend direktoriju**
   ```bash
   cd frontend
   ```

2. **Instalēt dependencies**
   ```bash
   npm install
   ```

3. **Izveidot .env failu**
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_APP_TITLE=Invoice Processing MVP
   ```

4. **Palaist development serveri**
   ```bash
   npm run dev
   ```

   Frontend būs pieejams: http://localhost:5173

## Production Deployment (Linux Server)

### 1. Servera sagatavošana

```bash
# Atjaunināt sistēmu
sudo apt update && sudo apt upgrade -y

# Instalēt nepieciešamos paketes
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx postgresql-client git

# Instalēt Tesseract ar latviešu valodu
sudo apt install -y tesseract-ocr tesseract-ocr-lav

# Instalēt Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Projekta izvietošana

```bash
# Klonēt repozitoriju
git clone <repository-url> /opt/invoice-processing
cd /opt/invoice-processing

# Izveidot lietotāju aplikācijai
sudo useradd -r -s /bin/false invoice-app
sudo chown -R invoice-app:invoice-app /opt/invoice-processing
```

### 3. Backend Production Setup

```bash
# Izveidot production virtual environment
sudo -u invoice-app python3 -m venv /opt/invoice-processing/venv
sudo -u invoice-app /opt/invoice-processing/venv/bin/pip install -r /opt/invoice-processing/backend/requirements.txt

# Pievienot production dependencies
sudo -u invoice-app /opt/invoice-processing/venv/bin/pip install gunicorn

# Izveidot production konfigurāciju
sudo tee /opt/invoice-processing/backend/.env.production << EOF
DATABASE_URL=postgresql://invoice_user:password@localhost/invoice_db
UPLOAD_DIR=/opt/invoice-processing/uploads
MAX_FILE_SIZE=50485760
TESSERACT_PATH=/usr/bin/tesseract
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### 4. PostgreSQL Setup (Production)

```bash
# Instalēt PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Izveidot datubāzi un lietotāju
sudo -u postgres psql << EOF
CREATE DATABASE invoice_db;
CREATE USER invoice_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;
\q
EOF

# Migrēt uz PostgreSQL
# TODO: Izveidot migration skriptu no SQLite uz PostgreSQL
```

### 5. Systemd serviss

```bash
# Izveidot systemd service failu
sudo tee /etc/systemd/system/invoice-api.service << EOF
[Unit]
Description=Invoice Processing API
After=network.target

[Service]
Type=exec
User=invoice-app
Group=invoice-app
WorkingDirectory=/opt/invoice-processing/backend
Environment=PATH=/opt/invoice-processing/venv/bin
ExecStart=/opt/invoice-processing/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Aktivizēt un palaist servisu
sudo systemctl daemon-reload
sudo systemctl enable invoice-api
sudo systemctl start invoice-api
```

### 6. Frontend Production Build

```bash
# Build frontend
cd /opt/invoice-processing/frontend
npm ci --production
npm run build

# Nokopēt build failus uz nginx direktoriju
sudo cp -r dist/* /var/www/html/invoice-processing/
```

### 7. Nginx konfigurācija

```bash
# Izveidot nginx konfigurāciju
sudo tee /etc/nginx/sites-available/invoice-processing << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /var/www/html/invoice-processing;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # File uploads
    client_max_body_size 50M;
}
EOF

# Aktivizēt konfigurāciju
sudo ln -s /etc/nginx/sites-available/invoice-processing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. SSL sertifikāts (Let's Encrypt)

```bash
# Instalēt Certbot
sudo apt install -y certbot python3-certbot-nginx

# Iegūt SSL sertifikātu
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Pievienot rindu:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Docker Deployment (Alternatīva)

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: invoice_db
      POSTGRES_USER: invoice_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://invoice_user:secure_password@postgres/invoice_db
      REDIS_URL: redis://redis:6379
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Palaišana ar Docker
```bash
# Build un palaist
docker-compose up -d

# Skalēt backend
docker-compose up -d --scale backend=3
```

## Monitoring un Logging

### 1. Logging konfigurācija
```python
# backend/logging.conf
[loggers]
keys=root,uvicorn,app

[handlers]
keys=console,file

[formatters]
keys=standard

[logger_root]
level=INFO
handlers=console,file

[logger_app]
level=DEBUG
handlers=file
qualname=app
propagate=0

[handler_file]
class=FileHandler
level=DEBUG
formatter=standard
args=('/var/log/invoice-processing/app.log', 'a')

[formatter_standard]
format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

### 2. Monitoring ar Prometheus
```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

## Backup automatizācija

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/invoice-processing"

# Datubāzes backup
pg_dump -U invoice_user invoice_db | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Failu backup
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /opt/invoice-processing/uploads/

# Dzēst vecus backups (>30 dienas)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Cron job (katru dienu 2:00)
# 0 2 * * * /opt/scripts/backup.sh
```

## Problēmu risināšana

### Biežākās problēmas:

1. **Tesseract nav atrasts**
   ```bash
   which tesseract
   sudo apt install tesseract-ocr tesseract-ocr-lav
   ```

2. **Permission denied upload direktorijā**
   ```bash
   sudo chown -R invoice-app:invoice-app /opt/invoice-processing/uploads
   sudo chmod 755 /opt/invoice-processing/uploads
   ```

3. **Datubāzes savienojuma kļūda**
   ```bash
   # Pārbaudīt PostgreSQL statusu
   sudo systemctl status postgresql
   # Pārbaudīt konfigurāciju
   sudo -u postgres psql -c "\l"
   ```

4. **Memory problēmas ar lieliem failiem**
   ```bash
   # Uzstādīt memory limits nginx
   client_max_body_size 50M;
   # Uzstādīt memory limits systemd
   MemoryMax=2G
   ```
