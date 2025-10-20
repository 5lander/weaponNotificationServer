"""
Configuración de Gunicorn optimizada para Django + Gmail SMTP asíncrono
Evita timeouts y optimiza el rendimiento
"""
import multiprocessing
import os

# ============================================
# CONFIGURACIÓN DE RED
# ============================================

# Puerto configurado por Render o 10000 por defecto
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Backlog de conexiones
backlog = 2048

# ============================================
# WORKERS
# ============================================

# Número de workers basado en CPU
# Fórmula: (2 x $num_cores) + 1
# Para Render free tier (0.5 CPU) → 2 workers
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
workers = min(workers, 4)  # Máximo 4 workers en free tier

# Tipo de worker
worker_class = 'sync'  # Sync es mejor para Django con threads internos

# Conexiones por worker
worker_connections = 1000

# Threads por worker (importante para emails asíncronos)
threads = 2  # Permite 2 threads por worker

# ============================================
# TIMEOUTS
# ============================================

# Timeout general de requests (aumentado para evitar SIGKILL)
timeout = 60  # 60 segundos - suficiente para cualquier operación

# Graceful timeout (tiempo para terminar requests actuales antes de matar el worker)
graceful_timeout = 30

# Keepalive
keepalive = 5

# ============================================
# GESTIÓN DE WORKERS
# ============================================

# Reiniciar workers después de N requests (previene memory leaks)
max_requests = 1000
max_requests_jitter = 50  # Variación aleatoria para evitar reinicios simultáneos

# Preload de la aplicación (carga el código antes de fork workers)
preload_app = True  # Mejora el tiempo de inicio

# ============================================
# LOGGING
# ============================================

# Access log (requests)
accesslog = '-'  # stdout

# Error log
errorlog = '-'  # stderr

# Log level
loglevel = 'info'  # 'debug', 'info', 'warning', 'error', 'critical'

# Formato de access log
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'
# %(D)s = Tiempo de respuesta en microsegundos

# ============================================
# PROCESS NAMING
# ============================================

proc_name = 'weapon_detection_system'

# ============================================
# SERVER MECHANICS
# ============================================

daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Limit request line size
limit_request_line = 4094

# Limit request header size
limit_request_fields = 100
limit_request_field_size = 8190

# ============================================
# DEBUGGING & RELOADING
# ============================================

# Reload cuando cambian archivos (SOLO DESARROLLO)
reload = os.environ.get('DEBUG', 'False').lower() == 'true'

# ============================================
# HOOKS (eventos del ciclo de vida)
# ============================================

def on_starting(server):
    """Se ejecuta cuando el master process arranca"""
    print("\n" + "="*60)
    print("🚀 WEAPON DETECTION SYSTEM - Iniciando Gunicorn")
    print("="*60)
    print(f"   Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"   Workers: {workers}")
    print(f"   Threads per worker: {threads}")
    print(f"   Timeout: {timeout}s")
    print(f"   Bind: {bind}")
    print(f"   Preload: {preload_app}")
    print(f"   Max requests: {max_requests}")
    print("="*60 + "\n")


def on_reload(server):
    """Se ejecuta cuando se recarga la aplicación"""
    print("🔄 Recargando aplicación...")


def when_ready(server):
    """Se ejecuta cuando el servidor está listo"""
    print("✅ Gunicorn listo - Aceptando conexiones")
    print(f"   PID: {os.getpid()}")
    print(f"   Workers activos: {len(server.WORKERS)}\n")


def worker_int(worker):
    """Se ejecuta cuando un worker recibe SIGINT o SIGQUIT"""
    print(f"⚠️ Worker {worker.pid} interrumpido")


def worker_abort(worker):
    """Se ejecuta cuando un worker es abortado (SIGABRT)"""
    print(f"❌ Worker {worker.pid} abortado (SIGABRT)")


def pre_fork(server, worker):
    """Se ejecuta antes de fork un nuevo worker"""
    pass


def post_fork(server, worker):
    """Se ejecuta después de fork un nuevo worker"""
    print(f"👶 Worker {worker.pid} iniciado")


def pre_exec(server):
    """Se ejecuta antes de re-exec del master"""
    print("🔄 Re-ejecutando master process...")


def post_worker_init(worker):
    """Se ejecuta después de inicializar un worker"""
    print(f"✅ Worker {worker.pid} inicializado y listo")


def worker_exit(server, worker):
    """Se ejecuta cuando un worker está saliendo"""
    print(f"👋 Worker {worker.pid} terminando...")


def nworkers_changed(server, new_value, old_value):
    """Se ejecuta cuando cambia el número de workers"""
    print(f"📊 Workers: {old_value} → {new_value}")


def on_exit(server):
    """Se ejecuta cuando el master está saliendo"""
    print("\n" + "="*60)
    print("👋 Gunicorn detenido - Hasta luego")
    print("="*60 + "\n")


# ============================================
# CONFIGURACIÓN SSL (si es necesario)
# ============================================

# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'
# ssl_version = 2  # TLS 1.2
# cert_reqs = 0  # No requiere certificado del cliente