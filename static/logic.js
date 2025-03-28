let currentOperationId = null;
let channels = [];
let indicatorTypes = [];

// Load operations on page load
window.onload = () => {
  loadOperationList();

  // Fetch structured indicator types
  fetch('/indicator_types')
    .then(res => res.json())
    .then(data => {
      indicatorTypes = data;
      document.getElementById('ind_group').addEventListener('change', updateCategories);
      document.getElementById('ind_category').addEventListener('change', updateSubtypes);
      document.getElementById('ind_subtype').addEventListener('change', updateDefaults);
    });
};

// Load operation list into dropdown
function loadOperationList() {
  fetch('/operations')
    .then(res => res.json())
    .then(ops => {
      const sel = document.getElementById('op_select');
      sel.innerHTML = '<option value="">-- Select Operation --</option>';
      ops.forEach(op => {
        const opt = document.createElement('option');
        opt.value = op.id;
        opt.textContent = `${op.name} (${op.region})`;
        sel.appendChild(opt);
      });
    });
}

// Create new operation
function createOperation() {
  const data = {
    name: document.getElementById('op_name').value,
    description: document.getElementById('op_description').value,
    suspected_actor: document.getElementById('op_actor').value,
    region: document.getElementById('op_region').value,
    time_range: document.getElementById('op_range').value
  };
  fetch('/operations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(res => res.json())
    .then(res => {
      notify("Operation created.");
      loadOperationList();
      document.getElementById('op_select').value = res.id;
      loadOperation();
    });
}

// Load selected operation details
function loadOperation() {
  const opId = document.getElementById('op_select').value;
  if (!opId) return;

  currentOperationId = parseInt(opId);

  fetch(`/operations/${opId}`)
    .then(res => res.json())
    .then(data => {
      channels = data.channels;
      renderChannelList();
      renderChannelDropdowns();
    });

  fetch(`/links/${opId}`)
    .then(res => res.json())
    .then(links => {
      const view = document.getElementById('link_view');
      view.innerHTML = links.map(link =>
        `<p><strong>${getChannelName(link.from_channel_id)}</strong> ➜ <strong>${getChannelName(link.to_channel_id)}</strong> (${link.link_type})<br>${link.evidence}</p>`
      ).join('');
    });
}

// Helper to map channel ID to name
function getChannelName(id) {
  const ch = channels.find(c => c.id === id);
  return ch ? ch.name : `Channel ${id}`;
}

// Add new channel to operation
function addChannel() {
  const data = {
    operation_id: currentOperationId,
    name: document.getElementById('ch_name').value,
    platform: document.getElementById('ch_platform').value,
    url: document.getElementById('ch_url').value,
    notes: document.getElementById('ch_notes').value
  };
  fetch('/channels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(() => {
    notify("Channel added.");
    loadOperation();
  });
}

// Populate all channel-related dropdowns
function renderChannelDropdowns() {
  const dropdowns = ['ind_channel', 'link_from', 'link_to'];
  dropdowns.forEach(id => {
    const sel = document.getElementById(id);
    sel.innerHTML = '';
    channels.forEach(ch => {
      const opt = document.createElement('option');
      opt.value = ch.id;
      opt.textContent = ch.name;
      sel.appendChild(opt);
    });
  });
}

// Show list of channels
function renderChannelList() {
    const container = document.getElementById('channel_list');
    container.innerHTML = '<h3>Channels:</h3>' + channels.map(c => `
      <div class="channel-item" id="channel-${c.id}">
        <span class="delete-btn" onclick="deleteChannel(${c.id})">&times;</span>
        <strong>${c.name}</strong> (${c.platform})<br>
        ${c.url}<br>${c.notes}
      </div>
    `).join('');
  }
  
// Add structured indicator to channel
function addIndicator() {
  const subtypeId = parseInt(document.getElementById('ind_subtype').value);
  const subtype = indicatorTypes.find(i => i.id === subtypeId);
  if (!subtype) {
    notify("Please select a valid subtype.");
    return;
  }

  const data = {
    channel_id: parseInt(document.getElementById('ind_channel').value),
    type: subtype.group_type,
    name: subtype.subtype,
    weight: subtype.default_weight,
    confidence: subtype.default_confidence,
    evidence: document.getElementById('ind_evidence').value,
    source_type: document.getElementById('ind_source').value
  };

  fetch('/indicators', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(() => {
    notify("Indicator added.");
    loadChannelIndicators(data.channel_id);
  });
}

// Load indicators for selected channel
function loadChannelIndicators(channelId) {
  fetch(`/channels/${channelId}`)
    .then(res => res.json())
    .then(data => {
      const box = document.getElementById('indicators_view');
      box.innerHTML = `<h3>Indicators for ${data.channel.name}</h3>` + data.indicators.map(i =>
        `<p id="indicator-${i.id}">
          <span class="delete-btn" onclick="deleteIndicator(${i.id}, ${data.channel.id})">&times;</span>
          [${i.type}] <strong>${i.name}</strong> (Weight ${i.weight}, ${i.confidence})<br>${i.evidence}
        </p>`
      ).join(''); 
    });
}

// Add relationship between channels
function addLink() {
  const data = {
    operation_id: currentOperationId,
    from_channel_id: parseInt(document.getElementById('link_from').value),
    to_channel_id: parseInt(document.getElementById('link_to').value),
    link_type: document.getElementById('link_type').value,
    confidence: document.getElementById('link_conf').value,
    evidence: document.getElementById('link_evidence').value
  };
  fetch('/links', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(() => {
    notify("Link added.");
    loadOperation();
  });
}

// === STRUCTURED INDICATOR SELECTORS ===

function updateCategories() {
  const group = document.getElementById('ind_group').value;
  const categories = [...new Set(indicatorTypes
    .filter(i => i.group_type === group)
    .map(i => i.category))];

  const catSelect = document.getElementById('ind_category');
  catSelect.innerHTML = '<option value="">--</option>';
  categories.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    catSelect.appendChild(opt);
  });

  // Clear the subtype list
  document.getElementById('ind_subtype').innerHTML = '';
}

function updateSubtypes() {
  const group = document.getElementById('ind_group').value;
  const category = document.getElementById('ind_category').value;

  const subtypes = indicatorTypes
    .filter(i => i.group_type === group && i.category === category);

  const subSelect = document.getElementById('ind_subtype');
  subSelect.innerHTML = '<option value="">--</option>';
  subtypes.forEach(i => {
    const opt = document.createElement('option');
    opt.value = i.id;
    opt.textContent = i.subtype;
    opt.setAttribute('data-weight', i.default_weight);
    opt.setAttribute('data-confidence', i.default_confidence);
    subSelect.appendChild(opt);
  });
}

function updateDefaults() {
  const sel = document.getElementById('ind_subtype');
  const selected = sel.options[sel.selectedIndex];
  if (!selected) return;
  document.getElementById('ind_weight').value = selected.getAttribute('data-weight');
  document.getElementById('ind_conf').value = selected.getAttribute('data-confidence');
}

function runClassification() {
    if (!currentOperationId) {
      notify("Please select or create an operation first.");
      return;
    }
  
    fetch(`/classify/${currentOperationId}`)
      .then(res => res.json())
      .then(data => {
        const box = document.getElementById('classification_results');
        if (!data.length) {
          box.innerHTML = "<p>No channels or indicators to classify.</p>";
          return;
        }
  
        // === TEXT OUTPUT ===
        box.innerHTML = '<h3>Classification Results</h3>' + data.map(res => {
          return `
            <div class="result-card">
            <h4>${res.channel_name} <span class="delete-btn" onclick="deleteChannel(${res.channel_id})">&times;</span></h4>
              <p><strong>Classification:</strong> ${res.classification}</p>
              <p><strong>Score:</strong> ${res.score}</p>
              <p><strong>Confidence:</strong> High: ${res.confidence.High}, Medium: ${res.confidence.Medium}, Low: ${res.confidence.Low}</p>
              <details>
                <summary>Justification</summary>
                <ul>${res.justification.map(j => `<li>${j}</li>`).join('')}</ul>
              </details>
            </div>
          `;
        }).join('');
  
        // === VISUAL MATRIX OUTPUT ===
        const grouped = {
          "State Official Channel": [],
          "State-Controlled Outlet": [],
          "State-Linked Channel": [],
          "State-Aligned Channel": [],
          "Unclassified": []
        };
  
        data.forEach(item => {
          if (!grouped[item.classification]) {
            grouped["Unclassified"].push(item);
          } else {
            grouped[item.classification].push(item);
          }
        });
  
        const grid = document.getElementById('matrix_grid');
        grid.innerHTML = '';
  
        Object.entries(grouped).forEach(([category, items]) => {
          const box = document.createElement('div');
          box.className = 'matrix-box';
          box.innerHTML = `<h4>${category}</h4>` + items.map(ch => {
            let confClass = 'matrix-low';
            if (ch.confidence.High >= 2) confClass = 'matrix-high';
            else if (ch.confidence.Medium >= 2) confClass = 'matrix-medium';
  
            return `<div class="matrix-item ${confClass}">
              ${ch.channel_name} (Score: ${ch.score})
            </div>`;
          }).join('');
          grid.appendChild(box);
        });
      });
  }

  function notify(message, timeout = 2500) {
    const el = document.getElementById('notifier');
    el.textContent = message;
    el.style.display = 'block';
    setTimeout(() => {
      el.style.display = 'none';
    }, timeout);
  }
  
    
  function deleteChannel(id) {
    fetch(`/channels/${id}`, { method: 'DELETE' })
      .then(() => {
        document.getElementById(`channel-${id}`)?.remove();
        notify("Channel deleted.");
        loadOperation();
      });
  }
  
  function deleteIndicator(id, channelId) {
    fetch(`/indicators/${id}`, { method: 'DELETE' })
      .then(() => {
        document.getElementById(`indicator-${id}`)?.remove();
        notify("Indicator deleted.");
        loadChannelIndicators(channelId);
      });
  }
  
  function deleteOperation() {
    if (!currentOperationId) return;
    fetch(`/operations/${currentOperationId}`, { method: 'DELETE' })
      .then(() => {
        notify("Operation deleted.");
        currentOperationId = null;
        document.getElementById('op_select').value = '';
        document.getElementById('channel_list').innerHTML = '';
        document.getElementById('indicators_view').innerHTML = '';
        document.getElementById('classification_results').innerHTML = '';
        document.getElementById('matrix_grid').innerHTML = '';
        loadOperationList();
      });
  }

// Function to trigger report generation
function generateReport() {
  const notes = document.getElementById("analyst_notes").value;
  const opId = document.getElementById("op_select").value;

  fetch(`/generate_report/${opId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analyst_comments: notes })
  })
    .then(res => res.json())
    .then(data => {
      const rawMarkdown = data.report || "No output returned.";
      renderMarkdownOutput(rawMarkdown);
    });
}



function renderMarkdownOutput(raw) {
  const html = marked.parse(raw);
  document.getElementById("llm_rendered_output").innerHTML = html;
}
  
function exportReportAsPDF() {
  const element = document.getElementById("llm_rendered_output");
  const opt = {
    margin:       0.5,
    filename:     'FIMI_Report.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2 },
    jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
  };
  html2pdf().set(opt).from(element).save();
}


function downloadStix() {
  const opSelect = document.getElementById("op_select");
  const opId = opSelect.value;
  if (!opId) {
    alert("No operation selected.");
    return;
  }
  fetch(`/export_stix/${opId}`)
    .then(res => res.json())
    .then(data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fimi_operation_${opId}.stix.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
}
