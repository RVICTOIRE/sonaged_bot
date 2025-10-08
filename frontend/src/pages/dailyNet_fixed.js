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
const saveInterventionsBtn = document.getElementById('saveInterventionsBtn');
if (saveInterventionsBtn) {
  saveInterventionsBtn.addEventListener('click', async () => {
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
}

// Section 5: Récapitulatif
const refreshRecap = document.getElementById('refreshRecap');
if (refreshRecap) {
  refreshRecap.addEventListener('click', async () => {
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
}

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
})();
