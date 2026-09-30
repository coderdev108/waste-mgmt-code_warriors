// Smart Waste Management System - Main JavaScript & Real-time Polling
window._maps = window._maps || {};

// High Quality, 100% Free Tile Layer (NO API Key Needed, No Rate Limits)
// Uses Esri ArcGIS World Street Map with worldwide road & street detail
const TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}';
const TILE_ATTR = 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012';

// ============================
// Auto-dismiss messages
// ============================
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert.auto-dismiss');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            alert.style.transition = 'all 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 4500);
    });
});

// ============================
// Leaflet Map for Citizen Reporting
// ============================
function initReportMap(defaultLat, defaultLng) {
    const mapEl = document.getElementById('report-map');
    if (!mapEl || typeof L === 'undefined') return;

    if (window._maps['report-map']) {
        try { window._maps['report-map'].remove(); } catch(e) {}
    }
    if (mapEl._leaflet_id) {
        mapEl._leaflet_id = null;
    }

    const startLat = defaultLat || 28.6139;
    const startLng = defaultLng || 77.2090;

    const map = L.map('report-map', {
        center: [startLat, startLng],
        zoom: 13,
        scrollWheelZoom: true
    });
    window._maps['report-map'] = map;

    L.tileLayer(TILE_URL, {
        attribution: TILE_ATTR,
        maxZoom: 19
    }).addTo(map);

    let marker = null;

    const greenIcon = L.divIcon({
        html: '<div style="background:#2ecc71;width:28px;height:28px;border-radius:50%;border:3px solid white;box-shadow:0 3px 12px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;color:white;font-size:14px">📍</div>',
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        className: 'custom-pin-marker'
    });

    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(6);
        const lng = e.latlng.lng.toFixed(6);

        if (marker) map.removeLayer(marker);
        marker = L.marker([lat, lng], { icon: greenIcon }).addTo(map);
        marker.bindPopup(`<strong>📍 Selected Location</strong><br><small class="text-muted">${lat}, ${lng}</small>`).openPopup();

        const latInput = document.getElementById('latitude') || document.getElementById('pickup_lat');
        const lngInput = document.getElementById('longitude') || document.getElementById('pickup_lng');
        if (latInput) latInput.value = lat;
        if (lngInput) lngInput.value = lng;

        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
            .then(r => r.json())
            .then(data => {
                const addrField = document.getElementById('location_address') || document.getElementById('pickup_address');
                if (addrField && data.display_name) {
                    addrField.value = data.display_name.substring(0, 250);
                }
            }).catch(() => {});
    });

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos) {
            try {
                map.setView([pos.coords.latitude, pos.coords.longitude], 15);
            } catch(e) {}
        }, function() {}, { timeout: 5000 });
    }

    setTimeout(() => { map.invalidateSize(); }, 300);
}

// ============================
// Leaflet Map for Admin Hotspots & Dashboard
// ============================
function initHotspotMap(rawMapData) {
    if (typeof L === 'undefined') return;

    let mapId = null;
    if (document.getElementById('hotspot-map')) mapId = 'hotspot-map';
    else if (document.getElementById('map')) mapId = 'map';
    if (!mapId) return;

    const mapEl = document.getElementById(mapId);
    if (!mapEl) return;

    if (window._maps[mapId]) {
        try { window._maps[mapId].remove(); } catch(e) {}
    }
    if (mapEl._leaflet_id) {
        mapEl._leaflet_id = null;
    }

    let mapData = [];
    try {
        if (typeof rawMapData === 'string') {
            mapData = JSON.parse(rawMapData);
        } else if (Array.isArray(rawMapData)) {
            mapData = rawMapData;
        }
    } catch(e) {
        console.warn('Map data parse error:', e);
        mapData = [];
    }

    const map = L.map(mapId, {
        center: [28.6139, 77.2090],
        zoom: 11,
        scrollWheelZoom: true
    });
    window._maps[mapId] = map;

    L.tileLayer(TILE_URL, {
        attribution: TILE_ATTR,
        maxZoom: 19
    }).addTo(map);

    const statusColors = {
        'pending': '#f39c12',
        'in_progress': '#3498db',
        'resolved': '#2ecc71',
        'rejected': '#e74c3c'
    };

    const bounds = [];
    if (mapData && mapData.length > 0) {
        mapData.forEach(function(complaint) {
            const lat = parseFloat(complaint.latitude);
            const lng = parseFloat(complaint.longitude);
            if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
                const color = statusColors[complaint.status] || '#95a5a6';
                const icon = L.divIcon({
                    html: `<div style="background:${color};width:22px;height:22px;border-radius:50%;border:2px solid white;box-shadow:0 2px 10px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:700">●</div>`,
                    iconSize: [22, 22],
                    iconAnchor: [11, 11],
                    className: ''
                });
                const marker = L.marker([lat, lng], { icon }).addTo(map);
                const title = complaint.title || 'Waste Complaint';
                const status = (complaint.status || 'pending').toUpperCase();
                const address = complaint.location_address || 'No address provided';
                
                marker.bindPopup(`
                    <div style="font-family:inherit;min-width:190px">
                        <div style="font-weight:700;font-size:13px;margin-bottom:4px;color:#1e293b">${title}</div>
                        <span style="display:inline-block;padding:2px 8px;border-radius:12px;background:${color};color:white;font-size:10px;font-weight:700;margin-bottom:6px">${status}</span>
                        <div style="font-size:11px;color:#64748b;line-height:1.3"><i class="bi bi-geo-alt"></i> ${address}</div>
                        ${complaint.id ? `<div class="mt-2"><a href="/admin-panel/complaints/${complaint.id}/assign/" style="font-size:11px;font-weight:600;color:#2ecc71;text-decoration:none">Assign / Manage &rarr;</a></div>` : ''}
                    </div>
                `);
                bounds.push([lat, lng]);
            }
        });
        if (bounds.length > 0) {
            try {
                map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
            } catch(e) {}
        }
    }

    setTimeout(() => { map.invalidateSize(); }, 300);
}

// ============================
// Leaflet Map for Single Task / Complaint View
// ============================
function initSingleLocationMap(containerId, lat, lng, title, address) {
    const mapEl = document.getElementById(containerId);
    if (!mapEl || typeof L === 'undefined') return;

    const pLat = parseFloat(lat);
    const pLng = parseFloat(lng);
    if (isNaN(pLat) || isNaN(pLng) || pLat === 0) return;

    if (window._maps[containerId]) {
        try { window._maps[containerId].remove(); } catch(e) {}
    }
    if (mapEl._leaflet_id) {
        mapEl._leaflet_id = null;
    }

    const map = L.map(containerId, {
        center: [pLat, pLng],
        zoom: 15,
        scrollWheelZoom: false
    });
    window._maps[containerId] = map;

    L.tileLayer(TILE_URL, {
        attribution: TILE_ATTR,
        maxZoom: 19
    }).addTo(map);

    const icon = L.divIcon({
        html: '<div style="background:#2ecc71;width:26px;height:26px;border-radius:50%;border:3px solid white;box-shadow:0 3px 10px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;color:white;font-size:13px">📍</div>',
        iconSize: [26, 26],
        iconAnchor: [13, 13]
    });

    const marker = L.marker([pLat, pLng], { icon }).addTo(map);
    marker.bindPopup(`<strong>${title || 'Location'}</strong><br><small class="text-muted">${address || ''}</small>`).openPopup();

    setTimeout(() => { map.invalidateSize(); }, 300);
}

// ============================
// Real-Time Collector Tasks Live Polling
// ============================
function initCollectorRealtimeSync(apiUrl) {
    if (!apiUrl) return;

    let previousTotal = null;

    function checkUpdates() {
        fetch(apiUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network error');
            return response.json();
        })
        .then(data => {
            const currentTotal = data.total;
            if (previousTotal !== null && currentTotal > previousTotal) {
                showLiveToast(`🔔 New Task Assigned! You have ${currentTotal} active task(s).`, 'success');
                setTimeout(() => { window.location.reload(); }, 1500);
            } else if (previousTotal !== null && currentTotal < previousTotal) {
                previousTotal = currentTotal;
            } else {
                previousTotal = currentTotal;
            }

            const badge = document.getElementById('collectorLiveBadge');
            if (badge) {
                badge.innerText = `${currentTotal} Active`;
            }
        })
        .catch(err => {});
    }

    setInterval(checkUpdates, 8000);
    checkUpdates();
}

function showLiveToast(message, type = 'success') {
    let container = document.getElementById('liveToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'liveToastContainer';
        container.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;max-width:350px';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg d-flex align-items-center gap-2 fade show`;
    toast.style.cssText = 'border-radius:12px;font-weight:600;font-size:14px;border:none;background:linear-gradient(135deg,#2ecc71,#27ae60);color:white;box-shadow:0 8px 25px rgba(46,204,113,0.4);animation:slideInRight 0.4s ease';
    toast.innerHTML = `<div>${message}</div>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

// ============================
// Photo Preview Helper
// ============================
document.addEventListener('DOMContentLoaded', function() {
    const photoInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    photoInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(ev) {
                let preview = document.getElementById('photo-preview');
                if (!preview) {
                    preview = document.createElement('img');
                    preview.id = 'photo-preview';
                    preview.style.cssText = 'max-width:100%;max-height:220px;border-radius:10px;margin-top:10px;box-shadow:0 4px 15px rgba(0,0,0,0.12);display:block;object-fit:cover';
                    input.parentNode.appendChild(preview);
                }
                preview.src = ev.target.result;
            };
            reader.readAsDataURL(file);
        });
    });
});

// ============================
// Delete Confirmations
// ============================
document.addEventListener('DOMContentLoaded', function() {
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to proceed? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});

// ============================
// Auto submit select filters
// ============================
document.addEventListener('DOMContentLoaded', function() {
    const autoFilters = document.querySelectorAll('.auto-filter');
    autoFilters.forEach(function(select) {
        select.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });
});
