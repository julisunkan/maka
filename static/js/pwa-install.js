
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  // Show install button/banner if you want
  showInstallPromotion();
});

function showInstallPromotion() {
  // You can create a custom install button here
  const installBtn = document.createElement('button');
  installBtn.className = 'btn btn-primary btn-sm position-fixed';
  installBtn.style.cssText = 'bottom: 80px; right: 20px; z-index: 1000;';
  installBtn.innerHTML = '<i class="bi bi-download"></i> Install App';
  installBtn.id = 'pwa-install-btn';
  
  installBtn.addEventListener('click', async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to the install prompt: ${outcome}`);
      deferredPrompt = null;
      installBtn.remove();
    }
  });
  
  // Only show if not already installed
  if (!window.matchMedia('(display-mode: standalone)').matches) {
    document.body.appendChild(installBtn);
  }
}

window.addEventListener('appinstalled', () => {
  console.log('PWA was installed');
  deferredPrompt = null;
  const installBtn = document.getElementById('pwa-install-btn');
  if (installBtn) {
    installBtn.remove();
  }
});

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(registration => {
        console.log('ServiceWorker registration successful:', registration.scope);
      })
      .catch(err => {
        console.log('ServiceWorker registration failed:', err);
      });
  });
}
