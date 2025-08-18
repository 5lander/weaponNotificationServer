// footer.js - JavaScript para el footer reutilizable

document.addEventListener('DOMContentLoaded', function() {
    // Actualizar año automáticamente
    updateFooterYear();
    
    // Agregar efectos interactivos al footer
    initFooterInteractions();
    
    // Configurar enlaces del footer
    setupFooterLinks();
});

// Función para actualizar el año actual en el footer
function updateFooterYear() {
    const currentYear = new Date().getFullYear();
    const copyrightElement = document.querySelector('.copyright span');
    
    if (copyrightElement) {
        // Reemplazar cualquier año de 4 dígitos con el año actual
        const text = copyrightElement.textContent;
        const updatedText = text.replace(/\b\d{4}\b/, currentYear);
        copyrightElement.textContent = updatedText;
    }
}

// Función para inicializar interacciones del footer
function initFooterInteractions() {
    // Efecto hover en las tech badges
    const techBadges = document.querySelectorAll('.tech-badge');
    techBadges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
        });
        
        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Efecto parallax sutil en el glow
    const footerGlow = document.querySelector('.footer-glow');
    if (footerGlow) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.2;
            footerGlow.style.transform = `translateX(-50%) translateY(${rate}px)`;
        });
    }
    
    // Animación de entrada cuando el footer es visible
    observeFooterVisibility();
}

// Función para configurar enlaces del footer
function setupFooterLinks() {
    const footerLinks = document.querySelectorAll('.footer-link');
    
    footerLinks.forEach(link => {
        // Agregar evento de click para enlaces vacíos
        if (link.getAttribute('href') === '#') {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                showComingSoonMessage(this.textContent.trim());
            });
        }
        
        // Marcar navegación interna para enlaces internos
        if (link.getAttribute('href') && link.getAttribute('href').startsWith('/')) {
            link.addEventListener('click', function() {
                // Marcar como navegación interna para evitar auto-logout
                if (window.isInternalNavigation !== undefined) {
                    window.isInternalNavigation = true;
                }
            });
        }
    });
    
    // Configurar enlaces del footer bottom
    const bottomLinks = document.querySelectorAll('.footer-links a');
    bottomLinks.forEach(link => {
        if (link.getAttribute('href') === '#') {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                showComingSoonMessage(this.textContent.trim());
            });
        }
    });
}

// Función para mostrar mensaje de "próximamente"
function showComingSoonMessage(linkName) {
    // Crear modal simple
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        max-width: 400px;
        margin: 1rem;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
        transform: scale(0.8);
        transition: transform 0.3s ease;
    `;
    
    modalContent.innerHTML = `
        <div style="color: #3b82f6; font-size: 3rem; margin-bottom: 1rem;">
            <i class="fas fa-clock"></i>
        </div>
        <h3 style="color: #1a1f36; margin-bottom: 1rem; font-size: 1.5rem;">Coming Soon</h3>
        <p style="color: #64748b; margin-bottom: 2rem; line-height: 1.6;">
            The <strong>${linkName}</strong> section is currently under development. 
            Stay tuned for updates!
        </p>
        <button onclick="this.closest('[style*=\"position: fixed\"]').remove()" 
                style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
                       color: white; border: none; padding: 0.75rem 2rem; 
                       border-radius: 12px; font-weight: 600; cursor: pointer; 
                       transition: all 0.3s ease;">
            Got it
        </button>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Animar entrada
    setTimeout(() => {
        modal.style.opacity = '1';
        modalContent.style.transform = 'scale(1)';
    }, 10);
    
    // Cerrar con ESC
    const closeHandler = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', closeHandler);
        }
    };
    document.addEventListener('keydown', closeHandler);
    
    // Cerrar haciendo click fuera del modal
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Función para observar visibilidad del footer
function observeFooterVisibility() {
    const footer = document.querySelector('.modern-footer');
    if (!footer) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Agregar clase de animación cuando sea visible
                footer.classList.add('footer-visible');
                
                // Animar elementos del footer con delay
                const sections = footer.querySelectorAll('.footer-section');
                sections.forEach((section, index) => {
                    setTimeout(() => {
                        section.style.opacity = '1';
                        section.style.transform = 'translateY(0)';
                    }, index * 200);
                });
            }
        });
    }, {
        threshold: 0.1
    });
    
    observer.observe(footer);
    
    // Preparar elementos para animación
    const sections = footer.querySelectorAll('.footer-section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'all 0.6s ease';
    });
}

// Función para scroll suave al top (opcional)
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Agregar funcionalidad de scroll to top si se desea
function addScrollToTop() {
    const footer = document.querySelector('.modern-footer');
    if (!footer) return;
    
    const scrollButton = document.createElement('button');
    scrollButton.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 1000;
    `;
    
    scrollButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollButton.title = 'Scroll to top';
    scrollButton.onclick = scrollToTop;
    
    document.body.appendChild(scrollButton);
    
    // Mostrar/ocultar botón basado en scroll
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollButton.style.opacity = '1';
            scrollButton.style.transform = 'translateY(0)';
        } else {
            scrollButton.style.opacity = '0';
            scrollButton.style.transform = 'translateY(20px)';
        }
    });
}

// Función para obtener información del sistema (opcional)
function getSystemInfo() {
    return {
        version: '2.0',
        lastUpdate: new Date().toLocaleDateString(),
        technologies: ['Django', 'Python', 'AI/ML', 'Computer Vision'],
        university: 'Universidad Internacional del Ecuador (UIDE)'
    };
}

// Exportar funciones para uso externo si es necesario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        updateFooterYear,
        showComingSoonMessage,
        scrollToTop,
        getSystemInfo
    };
}