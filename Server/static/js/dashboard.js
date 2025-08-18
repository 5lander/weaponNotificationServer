// dashboard.js - JavaScript para la página del dashboard

// Inicializar datepicker cuando el documento esté listo
jQuery(document).ready(function($){
  var date_input = $('.date-picker');
  var container = $('.search-card').length > 0 ? $('.search-card') : "body";
  var options = {
    format: 'yyyy-mm-dd',
    container: container,
    todayHighlight: true,
    autoclose: true,
  };
  date_input.datepicker(options);
});

// Función para cambiar el tamaño de página
function changePageSize(newSize) {
  const url = new URL(window.location.href);
  url.searchParams.set('per_page', newSize);
  url.searchParams.set('page', '1'); // Reset to first page
  
  // Marcar como navegación interna
  window.isInternalNavigation = true;
  window.location.href = url.toString();
}

// Configuración principal cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
  // Configurar animaciones de paginación
  setupPaginationAnimations();
  
  // Configurar navegación interna
  setupInternalNavigation();
  
  // Configurar auto-logout
  setupAutoLogout();
});

// Función para configurar animaciones de paginación
function setupPaginationAnimations() {
  const paginationLinks = document.querySelectorAll('.pagination-btn:not(.pagination-btn-disabled)');
  
  paginationLinks.forEach(link => {
    if (link.href) {
      link.addEventListener('click', function(e) {
        // Marcar como navegación interna
        window.isInternalNavigation = true;
        
        // Agregar estado de carga
        this.style.opacity = '0.7';
        this.style.pointerEvents = 'none';
        
        // Agregar spinner de carga
        const originalContent = this.innerHTML;
        if (!this.classList.contains('pagination-btn-number')) {
          this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
        
        // Permitir que la navegación proceda
        setTimeout(() => {
          this.innerHTML = originalContent;
          this.style.opacity = '1';
          this.style.pointerEvents = 'auto';
        }, 100);
      });
    }
  });
}

// Función para configurar la navegación interna
function setupInternalNavigation() {
  // Variable para controlar navegación interna
  let isInternalNavigation = false;
  window.isInternalNavigation = false;

  // Detectar navegación interna
  const internalLinks = document.querySelectorAll('a[href^="/"], a[href*="alert/"], .view-btn, .pagination-btn');
  internalLinks.forEach(link => {
    link.addEventListener('click', function() {
      isInternalNavigation = true;
      window.isInternalNavigation = true;
      
      // Resetear después de un pequeño delay
      setTimeout(() => {
        isInternalNavigation = false;
        window.isInternalNavigation = false;
      }, 100);
    });
  });

  // También detectar navegación de formularios
  const searchForm = document.querySelector('form[method="get"]');
  if (searchForm) {
    searchForm.addEventListener('submit', function() {
      window.isInternalNavigation = true;
    });
  }
}

// Función para configurar auto-logout
function setupAutoLogout() {
  // Auto-logout inteligente
  window.addEventListener('beforeunload', function(e) {
    if (!window.isInternalNavigation) {
      performLogout();
    }
  });

  // Evento alternativo más confiable
  window.addEventListener('pagehide', function(e) {
    if (e.persisted === false && !window.isInternalNavigation) {
      performLogout();
    }
  });

  // Detectar cierre de pestaña vs navegación
  window.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden' && !window.isInternalNavigation) {
      // Esperar un momento para ver si es navegación o cierre real
      setTimeout(() => {
        if (document.visibilityState === 'hidden' && !window.isInternalNavigation) {
          performLogout();
        }
      }, 5000); // 5 segundos de gracia
    }
  });
}

// Función para realizar logout
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

// Función para mejorar la experiencia del usuario con feedback visual
function addLoadingState(element, originalText, loadingText = 'Loading...') {
  element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`;
  element.disabled = true;
  element.style.opacity = '0.7';
  
  return function restore() {
    element.innerHTML = originalText;
    element.disabled = false;
    element.style.opacity = '1';
  };
}

// Función para mostrar notificaciones toast (opcional)
function showToast(message, type = 'info', duration = 3000) {
  // Crear elemento toast
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${getToastBackground(type)};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
  `;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  // Animar entrada
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
  }, 100);
  
  // Remover después del tiempo especificado
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, duration);
}

// Función auxiliar para obtener color de fondo del toast
function getToastBackground(type) {
  const colors = {
    'success': '#10b981',
    'error': '#ef4444',
    'warning': '#f59e0b',
    'info': '#3b82f6'
  };
  return colors[type] || colors.info;
}

// Función para validar formularios (opcional)
function validateSearchForm() {
  const form = document.querySelector('form[method="get"]');
  if (!form) return true;
  
  const inputs = form.querySelectorAll('.form-input');
  let hasValue = false;
  
  inputs.forEach(input => {
    if (input.value.trim() !== '') {
      hasValue = true;
    }
  });
  
  if (!hasValue) {
    showToast('Please enter at least one search criteria', 'warning');
    return false;
  }
  
  return true;
}

// Mejorar accesibilidad con navegación por teclado
document.addEventListener('keydown', function(e) {
  // Esc para cerrar modals o resetear formularios
  if (e.key === 'Escape') {
    const searchForm = document.querySelector('form[method="get"]');
    if (searchForm && confirm('Clear search form?')) {
      searchForm.reset();
      window.location.href = window.location.pathname;
    }
  }
  
  // Ctrl+F para enfocar primer campo de búsqueda
  if (e.ctrlKey && e.key === 'f') {
    e.preventDefault();
    const firstInput = document.querySelector('.form-input');
    if (firstInput) {
      firstInput.focus();
      firstInput.select();
    }
  }
});

// Función para exportar datos (opcional - para futuras funcionalidades)
function exportData(format = 'csv') {
  // Esta función se puede implementar más tarde para exportar los datos de la tabla
  showToast(`Export feature coming soon (${format.toUpperCase()})`, 'info');
}