// alert.js - JavaScript para la página de detalles de alerta

// Variable para controlar si es navegación interna
let isInternalNavigation = false;

// Marcar navegación interna cuando se hace clic en enlaces internos
document.addEventListener('DOMContentLoaded', function() {
    // Obtener todos los enlaces internos
    const internalLinks = document.querySelectorAll('a[href^="/"], a[href^="{% url "]');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function() {
            isInternalNavigation = true;
            // Resetear después de un pequeño delay
            setTimeout(() => {
                isInternalNavigation = false;
            }, 100);
        });
    });

    // También marcar para el botón de volver específicamente
    const backButton = document.querySelector('.back-btn');
    if (backButton) {
        backButton.addEventListener('click', function() {
            isInternalNavigation = true;
        });
    }

    // Configurar zoom de imagen
    setupImageZoom();
});

// Auto-logout solo cuando realmente se cierra la pestaña/navegador
window.addEventListener('beforeunload', function(e) {
    // Solo hacer logout si NO es navegación interna
    if (!isInternalNavigation) {
        performLogout();
    }
});

// Evento alternativo más confiable para detectar cierre real
window.addEventListener('pagehide', function(e) {
    // Solo si la página se está descargando completamente (no navegación)
    if (e.persisted === false && !isInternalNavigation) {
        performLogout();
    }
});

// Detectar cuando realmente se cierra la pestaña vs navegación
window.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden' && !isInternalNavigation) {
        // Esperar un momento para ver si es navegación o cierre real
        setTimeout(() => {
            if (document.visibilityState === 'hidden' && !isInternalNavigation) {
                // Probablemente es cierre de pestaña, hacer logout
                performLogout();
            }
        }, 5000); // 5 segundos de gracia
    }
});

// Función centralizada para realizar logout
function performLogout() {
    // Nota: Esta URL debe ser configurada desde Django
    const logoutUrl = "/logout/"; // Cambiar por la URL correcta
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    
    if (navigator.sendBeacon && csrfToken) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        navigator.sendBeacon(logoutUrl, formData);
    }
}

// Función para descargar reporte
function downloadReport() {
    // Recopilar datos de la alerta desde el DOM
    const alertData = collectAlertData();

    // Crear contenido del reporte
    const reportContent = generateReportContent(alertData);

    // Crear y descargar archivo
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `weapon_detection_report_${alertData.alertId || 'alert'}_${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    // Mostrar mensaje de éxito
    showStatusMessage('Report downloaded successfully!', 'success');
}

// Función para recopilar datos de alerta desde el DOM
function collectAlertData() {
    const locationElement = document.querySelector('.location-value');
    const receiverElement = document.querySelector('.receiver-value');
    const timeElement = document.querySelector('.time-value');
    const statusElement = document.getElementById('alertStatus');
    
    return {
        location: locationElement ? locationElement.textContent.replace(/\s+/g, ' ').trim() : 'N/A',
        alertReceiver: receiverElement ? receiverElement.textContent.replace(/\s+/g, ' ').trim() : 'N/A',
        dateCreated: timeElement ? timeElement.textContent.replace(/\s+/g, ' ').trim() : 'N/A',
        status: statusElement ? statusElement.textContent : 'N/A',
        alertId: Math.random().toString(36).substr(2, 9), // Generar ID temporal
        reportGenerated: new Date().toLocaleString()
    };
}

// Función para generar el contenido del reporte
function generateReportContent(alertData) {
    return `
WEAPON DETECTION SYSTEM - SECURITY REPORT
==========================================

ALERT DETAILS:
--------------
Alert ID: ${alertData.alertId}
Detection Time: ${alertData.dateCreated}
Location: ${alertData.location}
Alert Sent To: ${alertData.alertReceiver}
Current Status: ${alertData.status}

INCIDENT SUMMARY:
-----------------
A potential weapon has been detected through the automated security system.
Immediate response and investigation are recommended.

SYSTEM INFORMATION:
-------------------
Report Generated: ${alertData.reportGenerated}
System: Weapon Detection System v2.0

RECOMMENDED ACTIONS:
--------------------
1. Verify the detection with security personnel
2. Investigate the reported location immediately
3. Contact relevant authorities if threat is confirmed
4. Review security protocols and response procedures

==========================================
This report is confidential and should only be shared with authorized personnel.
    `;
}

// Función para archivar alerta
function archiveAlert() {
    // Confirmar acción
    if (!confirm('Are you sure you want to archive this alert? This action cannot be undone.')) {
        return;
    }

    // Desactivar botón mientras procesa
    const archiveBtn = document.getElementById('archiveBtn');
    const originalText = archiveBtn.innerHTML;
    archiveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Archiving...';
    archiveBtn.disabled = true;

    // Simular llamada al servidor (reemplazar con tu lógica real)
    setTimeout(() => {
        // Aquí harías la llamada AJAX real a tu backend
        /*
        fetch('/archive-alert/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                alert_id: 'ALERT_ID_FROM_TEMPLATE'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateUIAfterArchive();
                showStatusMessage('Alert archived successfully!', 'success');
            } else {
                handleArchiveError(originalText);
            }
        })
        .catch(error => {
            handleArchiveError(originalText);
        });
        */

        // Por ahora, simular éxito
        updateUIAfterArchive();
        showStatusMessage('Alert archived successfully!', 'success');
    }, 2000); // Simular delay de red
}

// Función para actualizar UI después de archivar
function updateUIAfterArchive() {
    const statusElement = document.getElementById('alertStatus');
    const archiveBtn = document.getElementById('archiveBtn');
    
    if (statusElement) {
        statusElement.textContent = 'Archived';
        statusElement.style.color = '#64748b';
        
        const statusIcon = statusElement.previousElementSibling;
        if (statusIcon) {
            statusIcon.className = 'fas fa-archive';
            statusIcon.style.color = '#64748b';
        }
    }
    
    if (archiveBtn) {
        archiveBtn.innerHTML = '<i class="fas fa-check"></i> Archived';
        archiveBtn.style.background = '#64748b';
        archiveBtn.disabled = true;
    }
}

// Función para manejar errores de archivado
function handleArchiveError(originalText) {
    const archiveBtn = document.getElementById('archiveBtn');
    showStatusMessage('Error archiving alert. Please try again.', 'error');
    
    if (archiveBtn) {
        archiveBtn.innerHTML = originalText;
        archiveBtn.disabled = false;
    }
}

// Función para mostrar mensajes de estado
function showStatusMessage(message, type = 'success') {
    const statusMessage = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');
    
    if (!statusMessage || !statusText) return;
    
    statusText.textContent = message;
    statusMessage.className = 'status-message';
    
    if (type === 'error') {
        statusMessage.classList.add('error');
    } else if (type === 'warning') {
        statusMessage.classList.add('warning');
    }
    
    statusMessage.style.display = 'flex';
    
    // Ocultar después de 5 segundos
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}

// Función para configurar zoom de imagen
function setupImageZoom() {
    const image = document.querySelector('.detection-image-large');
    if (image) {
        image.addEventListener('click', function() {
            if (this.style.transform === 'scale(1.5)') {
                this.style.transform = 'scale(1)';
                this.style.cursor = 'zoom-in';
            } else {
                this.style.transform = 'scale(1.5)';
                this.style.cursor = 'zoom-out';
            }
        });
        image.style.cursor = 'zoom-in';
    }
}