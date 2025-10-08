const backend = 'http://127.0.0.1:5000';
let rid = null;

async function fetchJson(url, opts = {}) {
  const res = await fetch(url, opts);
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    const text = await res.text(); 
    throw new Error(text);
  }
  const json = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(json));
  return json;
}

function showMessage(elementId, message, isError = false) {
  const el = document.getElementById(elementId);
  el.textContent = message;
  el.className = isError ? 'error' : 'ok';
  setTimeout(() => { el.textContent = ''; el.className = 'muted'; }, 5000);
}

// Section 1: Récupération des données depuis localStorage
let agentId = null;

// Section 2: Nettoiement
const saveNettoiementBtn = document.getElementById('saveNettoiementBtn');
if (saveNettoiementBtn) {
  saveNettoiementBtn.addEventListener('click', async () => {
  if (!rid) {
    showMessage('nettoiementMsg', 'Créez d\'abord le rapport', true);
    return;
  }
  
  const payload = {
    circuits_planifies: document.getElementById('netPlan').value || null,
    circuits_balayes: document.getElementById('netBal').value || null,
    kilometrage_planifie: Number(document.getElementById('netKmPlan').value || 0),
    kilometrage_balaye: Number(document.getElementById('netKmBal').value || 0),
    kilometrage_desensable: Number(document.getElementById('netKmDes').value || 0)
  };
  
  try {
    await fetch(`${backend}/rapport_journalier/${rid}/nettoiement`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload)
    });
    showMessage('nettoiementMsg', 'Nettoiement enregistré');
  } catch(e) { 
    showMessage('nettoiementMsg', 'Erreur: ' + e.message, true);
  }
  });
}

// Section 3: Mobilier Urbain
const saveMobilierBtn = document.getElementById('saveMobilierBtn');
if (saveMobilierBtn) {
  saveMobilierBtn.addEventListener('click', async () => {
  if (!rid) {
    showMessage('mobilierMsg', 'Créez d\'abord le rapport', true);
    return;
  }
  
  const payload = {
    prn: {
      sites: Number(document.getElementById('prnSites').value || 0),
      bacs: Number(document.getElementById('prnBacs').value || 0),
      bacs_leves: Number(document.getElementById('prnLeves').value || 0),
      observations: document.getElementById('prnObs').value || null
    },
    pp: {
      sites: Number(document.getElementById('ppSites').value || 0),
      bacs: Number(document.getElementById('ppBacs').value || 0),
      bacs_leves: Number(document.getElementById('ppLeves').value || 0),
      observations: document.getElementById('ppObs').value || null
    },
    bacs_rue: {
      sites: Number(document.getElementById('bacSites').value || 0),
      bacs: Number(document.getElementById('bacBacs').value || 0),
      bacs_leves: Number(document.getElementById('bacLeves').value || 0),
      observations: document.getElementById('bacObs').value || null
    }
  };
  
  try {
    await fetch(`${backend}/rapport_journalier/${rid}/mobilier_urbain`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload)
    });
    showMessage('mobilierMsg', 'Mobilier urbain enregistré');
  } catch(e) { 
    showMessage('mobilierMsg', 'Erreur: ' + e.message, true);
  }
  });
}

// Section 4: Interventions Ponctuelles
document.getElementById('saveInterventionsBtn').addEventListener('click', async () => {
  if (!rid) {
    showMessage('interventionsMsg', 'Créez d\'abord le rapport', true);
    return;
  }
  
  const payload = {
    agents_mobilises: Number(document.getElementById('intAgents').value || 0),
    pelles_mecaniques: Number(document.getElementById('intPelles').value || 0),
    tasseuses: Number(document.getElementById('intTasseuses').value || 0),
    camions_ciel_ouvert: Number(document.getElementById('intCamions').value || 0),
    sites_intervention: document.getElementById('intSites').value || null
  };
  
  try {
    await fetch(`${backend}/rapport_journalier/${rid}/interventions_ponctuelles`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload)
    });
    showMessage('interventionsMsg', 'Interventions enregistrées');
  } catch(e) { 
    showMessage('interventionsMsg', 'Erreur: ' + e.message, true);
  }
});

// Section 5: Récapitulatif
document.getElementById('refreshRecap').addEventListener('click', async () => {
  const box = document.getElementById('recapBox');
  if (!rid) {
    showMessage('recapMsg', 'Créez d\'abord le rapport', true);
    return;
  }
  
  try {
    const data = await fetchJson(`${backend}/rapport_journalier/${rid}`);
    box.textContent = JSON.stringify(data, null, 2);
    showMessage('recapMsg', 'Récapitulatif mis à jour');
  } catch(e) { 
    box.textContent = 'Erreur: ' + e.message; 
    showMessage('recapMsg', 'Erreur lors du chargement', true);
  }
});

// Export PDF (placeholder)
const exportBtn = document.getElementById('exportBtn');
if (exportBtn) {
  exportBtn.addEventListener('click', () => {
    if (!rid) {
      showMessage('recapMsg', 'Créez d\'abord le rapport', true);
      return;
    }
    alert('Fonctionnalité d\'export PDF à implémenter côté backend');
  });
}

// Section Photos
const addPhotoBtn = document.getElementById('addPhotoBtn');
if (addPhotoBtn) {
  addPhotoBtn.addEventListener('click', async () => {
    if (!rid) {
      showMessage('photoMsg', 'Créez d\'abord le rapport', true);
      return;
    }
    
    const photoUrl = document.getElementById('photoUrl').value.trim();
    if (!photoUrl) {
      showMessage('photoMsg', 'Veuillez saisir une URL de photo', true);
      return;
    }
    
    try {
      const response = await fetch(`${backend}/rapport_journalier/${rid}/photos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photo_url: photoUrl })
      });
      
      if (response.ok) {
        showMessage('photoMsg', 'Photo ajoutée avec succès');
        document.getElementById('photoUrl').value = '';
        loadPhotos();
      } else {
        throw new Error(await response.text());
      }
    } catch(e) {
      showMessage('photoMsg', 'Erreur: ' + e.message, true);
    }
  });
}

const uploadPhotoBtn = document.getElementById('uploadPhotoBtn');
if (uploadPhotoBtn) {
  uploadPhotoBtn.addEventListener('click', async () => {
    if (!rid) {
      showMessage('photoMsg', 'Créez d\'abord le rapport', true);
      return;
    }
    
    const fileInput = document.getElementById('photoFile');
    const file = fileInput.files[0];
    if (!file) {
      showMessage('photoMsg', 'Veuillez sélectionner un fichier', true);
      return;
    }
    
    // Pour l'instant, on simule l'upload en créant une URL locale
    // Dans un vrai système, il faudrait uploader vers un serveur de fichiers
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const response = await fetch(`${backend}/rapport_journalier/${rid}/photos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ photo_url: e.target.result })
        });
        
        if (response.ok) {
          showMessage('photoMsg', 'Photo uploadée avec succès');
          fileInput.value = '';
          loadPhotos();
        } else {
          throw new Error(await response.text());
        }
      } catch(error) {
        showMessage('photoMsg', 'Erreur: ' + error.message, true);
      }
    };
    reader.readAsDataURL(file);
  });
}

// Fonction pour charger et afficher les photos
async function loadPhotos() {
  if (!rid) return;
  
  try {
    const response = await fetch(`${backend}/rapport_journalier/${rid}`);
    if (response.ok) {
      const data = await response.json();
      const photoList = document.getElementById('photoList');
      if (photoList) {
        photoList.innerHTML = '';
        
        if (data.photos && data.photos.length > 0) {
          data.photos.forEach((photo, index) => {
            const photoItem = document.createElement('div');
            photoItem.className = 'photo-item';
            photoItem.innerHTML = `
              <img src="${photo}" alt="Photo ${index + 1}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjYwIiBoZWlnaHQ9IjYwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMCAyMEg0MFY0MEgyMFYyMFoiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+'" />
              <div class="photo-info">
                <div class="photo-url">${photo}</div>
              </div>
              <div class="photo-actions">
                <button onclick="deletePhoto(${index})">Supprimer</button>
              </div>
            `;
            photoList.appendChild(photoItem);
          });
        } else {
          photoList.innerHTML = '<div class="muted">Aucune photo ajoutée</div>';
        }
      }
    }
  } catch(e) {
    console.error('Erreur lors du chargement des photos:', e);
  }
}

// Fonction pour supprimer une photo
async function deletePhoto(index) {
  if (!rid) return;
  
  try {
    const response = await fetch(`${backend}/rapport_journalier/${rid}/photos/${index}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showMessage('photoMsg', 'Photo supprimée');
      loadPhotos();
    } else {
      throw new Error(await response.text());
    }
  } catch(e) {
    showMessage('photoMsg', 'Erreur lors de la suppression: ' + e.message, true);
  }
}

// Rendre les fonctions globales pour les boutons
window.deletePhoto = deletePhoto;

// Prefill from localStorage
(function initFromStorage(){
  const sRid = localStorage.getItem('dailyReportId');
  if (sRid){ 
    rid = Number(sRid); 
    const ridBox = document.getElementById('ridBox');
    if (ridBox) ridBox.value = rid;
  }

  const sAgentName = localStorage.getItem('agentName');
  if (sAgentName){
    const an = document.getElementById('agentName');
    if (an) an.value = sAgentName;
  }

  const sAgentId = localStorage.getItem('agentId');
  if (sAgentId){
    agentId = Number(sAgentId);
  }

  // Afficher les informations récupérées
  console.log('dailyNet - Récupéré depuis localStorage:', {
    rid: rid,
    agentName: sAgentName,
    agentId: sAgentId
  });
  
  // Charger les photos si un rapport existe
  if (rid) {
    loadPhotos();
  }
})();

// Finalisation depuis la page Nettoiement
const finalizeBtnNet = document.getElementById('finalizeBtnNet');
if (finalizeBtnNet){
  finalizeBtnNet.addEventListener('click', async ()=>{
    const msg = document.getElementById('recapMsg');
    if (!rid){ showMessage('recapMsg', 'Créez d\'abord le rapport', true); return; }
    try{
      const resp = await fetch(`${backend}/rapport_journalier/${rid}/completion`);
      const comp = resp.ok ? await resp.json() : { sections:{} };
      const sections = comp.sections || {};
      const missing = Object.entries(sections).filter(([k,v])=> Number(v||0)===0).map(([k])=>k);
      const ok = confirm(missing.length? `Sections manquantes: ${missing.join(', ')}. Finaliser quand même ?` : 'Finaliser ce rapport ?');
      if (!ok) return;
      const res = await fetch(`${backend}/rapport_journalier/${rid}/finaliser`, { method:'POST' });
      if (!res.ok) throw new Error(await res.text());
      showMessage('recapMsg', 'Rapport finalisé');
      // Reset session/localStorage et UI
      try{
        localStorage.removeItem('dailyReportId');
        localStorage.removeItem('agentId');
        localStorage.removeItem('agentName');
      }catch(_e){}
      rid = null;
      const ridBox = document.getElementById('ridBox');
      if (ridBox) ridBox.value = '';
      const agentNameEl = document.getElementById('agentName');
      if (agentNameEl) agentNameEl.value = '';
    }catch(e){ showMessage('recapMsg', 'Erreur: '+e.message, true); }
  });
}
