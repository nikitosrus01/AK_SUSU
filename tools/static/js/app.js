let telemetryData = [];
let analysisResults = null;
let currentIndex = 0;
let isPlaying = false;
let playbackInterval = null;
let playbackSpeed = 1;
const Hz = 50; 

let charts = {};
let map, mapMarker, mapTrack;
let scene, camera, renderer, spaceCapsule;

document.addEventListener("DOMContentLoaded", () => {
    // Инициализация интерфейса
    initMap();
    init3D();
    initCharts();

    // Привязка событий управления
    const btnTriggerUpload = document.getElementById('btn-trigger-upload');
    const fileInput = document.getElementById('csv-file');
    if (btnTriggerUpload && fileInput) {
        btnTriggerUpload.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileSelect);
    }

    const btnPlay = document.getElementById('btn-play');
    if (btnPlay) btnPlay.addEventListener('click', () => togglePlay());

    const btnPause = document.getElementById('btn-pause');
    if (btnPause) btnPause.addEventListener('click', () => togglePlay(false));

    const timelineSlider = document.getElementById('timeline-slider');
    if (timelineSlider) {
        timelineSlider.addEventListener('input', (e) => onSliderMove(e.target.value));
    }

    const speedSelector = document.getElementById('speed-selector');
    if (speedSelector) {
        speedSelector.addEventListener('change', (e) => changeSpeed(e.target.value));
    }

    const btnModalOpen = document.getElementById('btn-modal-open');
    if (btnModalOpen) btnModalOpen.addEventListener('click', openAnalysisModal);

    const btnModalClose = document.getElementById('btn-modal-close');
    if (btnModalClose) btnModalClose.addEventListener('click', closeAnalysisModal);

    const btnExport = document.getElementById('btn-export');
    if (btnExport) btnExport.addEventListener('click', exportData);
});

function initMap() {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;

    map = L.map('map').setView([55.7558, 37.6173], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    mapMarker = L.circleMarker([0, 0], {color: '#2ecc71', radius: 8}).addTo(map);
    mapTrack = L.polyline([], {color: '#3498db', weight: 3}).addTo(map);
}

// === ОБНОВЛЕННАЯ 3D-МОДЕЛЬ ПО РЕФЕРЕНСУ ===
function init3D() {
    const container = document.getElementById('canvas-3d-container');
    if (!container) return;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d1222);

    camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 1.5, 4);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    // Добавляем освещение (чтобы модель была объемной, а не просто сеткой)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    // Главная группа аппарата
    spaceCapsule = new THREE.Group();

    // Материал корпуса (серый металлик, как на картинке SolidWorks)
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x707a8a, roughness: 0.4, metalness: 0.6 });
    const boardMat = new THREE.MeshStandardMaterial({ color: 0x2c3e50, roughness: 0.5 }); // Боковой отсек

    // 1. Коническая часть корпуса (верхний конус)
    const coneGeo = new THREE.CylinderGeometry(0.5, 0.9, 1.2, 32);
    const coneMesh = new THREE.Mesh(coneGeo, bodyMat);
    coneMesh.position.y = 0.2;
    spaceCapsule.add(coneMesh);

    // 2. Скругленное дно (полусфера снизу)
    const bottomGeo = new THREE.SphereGeometry(0.9, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
    const bottomMesh = new THREE.Mesh(bottomGeo, bodyMat);
    bottomMesh.position.y = -0.4;
    bottomMesh.rotation.x = Math.PI; // Переворачиваем полусферу вниз лобовым экраном
    spaceCapsule.add(bottomMesh);

    // 3. Верхнее ушко (рым-болт для парашюта)
    const torusGeo = new THREE.TorusGeometry(0.08, 0.02, 8, 24);
    const torusMesh = new THREE.Mesh(torusGeo, bodyMat);
    torusMesh.position.y = 0.85;
    torusMesh.rotation.x = Math.PI / 2;
    spaceCapsule.add(torusMesh);

    // 4. Выступающая боковая монтажная панель с аппаратурой
    const plateGeo = new THREE.BoxGeometry(0.15, 0.8, 0.4);
    const plateMesh = new THREE.Mesh(plateGeo, boardMat);
    plateMesh.position.set(-0.75, 0.1, 0); // Смещаем на бок конуса
    spaceCapsule.add(plateMesh);

    scene.add(spaceCapsule);

    // Трос парашюта
    const lineMat = new THREE.LineBasicMaterial({ color: 0xaaaaaa });
    const points = [new THREE.Vector3(0, 0.85, 0), new THREE.Vector3(0, 2.5, 0)];
    const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
    const parachuteLine = new THREE.Line(lineGeo, lineMat);
    spaceCapsule.add(parachuteLine);

    window.addEventListener('resize', () => {
        const updateContainer = document.getElementById('canvas-3d-container');
        if (updateContainer && camera && renderer) {
            camera.aspect = updateContainer.clientWidth / updateContainer.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(updateContainer.clientWidth, updateContainer.clientHeight);
        }
    });

    function animate() {
        requestAnimationFrame(animate);
        if (isPlaying && spaceCapsule) {
            spaceCapsule.rotation.y += 0.005; // Медленное вращение вокруг оси в полете
        }
        if (renderer && scene && camera) {
            renderer.render(scene, camera);
        }
    }
    animate();
}

// === НАСТРОЙКА ГРАФИКОВ С ПОДПИСЯМИ ОСЕЙ ===
function initCharts() {
    const configFactory = (label, yTitle, color) => ({
        type: 'line',
        data: { labels: [], datasets: [{ label: label, data: [], borderColor: color, borderWidth: 1.5, pointRadius: 0, fill: false }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: true, labels: { color: '#64748b', font: { size: 10 } } } 
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Время (с)', color: '#64748b', font: { size: 10 } },
                    grid: { color: '#1e2942' },
                    ticks: { color: '#64748b', font: { size: 9 } }
                },
                y: { 
                    title: { display: true, text: yTitle, color: '#64748b', font: { size: 10 } },
                    grid: { color: '#1e2942' }, 
                    ticks: { color: '#64748b', font: { size: 9 } } 
                }
            }
        }
    });

    const cAlt = document.getElementById('chart-alt');
    const cSpeed = document.getElementById('chart-speed');
    const cAccel = document.getElementById('chart-accel');
    const cPress = document.getElementById('chart-press');

    if (cAlt) charts.alt = new Chart(cAlt.getContext('2d'), configFactory('Высота', 'Высота (м)', '#2ecc71'));
    if (cSpeed) charts.speed = new Chart(cSpeed.getContext('2d'), configFactory('Скорость', 'Скорость (м/с)', '#3498db'));
    if (cAccel) charts.accel = new Chart(cAccel.getContext('2d'), configFactory('Ускорение', 'Ускорение (м/с²)', '#e74c3c'));
    if (cPress) charts.press = new Chart(cPress.getContext('2d'), configFactory('Давление', 'Давление (Па)', '#f1c40f'));
}

async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/process-telemetry', { method: 'POST', body: formData });
        if (!response.ok) throw new Error('Ошибка обработки файла сервером');
        
        const res = await response.json();
        telemetryData = res.telemetry;
        analysisResults = res.analysis;

        initPlayback();
        fillTable();
        updateChartsData();
        renderAnalysis();
    } catch (err) {
        alert(err.message);
    }
}

function initPlayback() {
    currentIndex = 0;
    isPlaying = false;
    clearInterval(playbackInterval);
    
    const slider = document.getElementById('timeline-slider');
    if (slider) {
        slider.max = telemetryData.length - 1;
        slider.value = 0;
    }
    
    const totalTime = telemetryData[telemetryData.length - 1].Time;
    const totalTimeStr = document.getElementById('total-time-string');
    if (totalTimeStr) totalTimeStr.innerText = formatTime(totalTime);
    
    if (mapTrack) {
        const latLngs = telemetryData.map(d => [d.Lat, d.Lon]);
        mapTrack.setLatLngs(latLngs);
        if (latLngs.length > 0 && map) map.fitBounds(mapTrack.getBounds());
    }
    
    updateUI(telemetryData[0]);
}

function fillTable() {
    const tbody = document.querySelector("#telemetry-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    telemetryData.forEach((row, index) => {
        if (index % 10 === 0 || index === telemetryData.length - 1) { 
            const tr = document.createElement('tr');
            tr.id = `t-row-${index}`;
            tr.innerHTML = `
                <td>${row.Time.toFixed(2)}</td>
                <td>${row.Altitude.toFixed(1)}</td>
                <td>${row.Speed.toFixed(1)}</td>
                <td>${row.Acceleration.toFixed(1)}</td>
                <td>${row.Pressure.toFixed(0)}</td>
                <td>${row.State}</td>
            `;
            tbody.appendChild(tr);
        }
    });
}

function updateChartsData() {
    const labels = telemetryData.map(d => d.Time.toFixed(1));
    
    if (charts.alt) {
        charts.alt.data.labels = labels;
        charts.alt.data.datasets[0].data = telemetryData.map(d => d.Altitude);
        charts.alt.update();
    }
    if (charts.speed) {
        charts.speed.data.labels = labels;
        charts.speed.data.datasets[0].data = telemetryData.map(d => d.Speed);
        charts.speed.update();
    }
    if (charts.accel) {
        charts.accel.data.labels = labels;
        charts.accel.data.datasets[0].data = telemetryData.map(d => d.Acceleration);
        charts.accel.update();
    }
    if (charts.press) {
        charts.press.data.labels = labels;
        charts.press.data.datasets[0].data = telemetryData.map(d => d.Pressure);
        charts.press.update();
    }
}

function togglePlay(status = null) {
    isPlaying = (status !== null) ? status : !isPlaying;
    const btnPlay = document.getElementById('btn-play');
    if (btnPlay) btnPlay.style.borderColor = isPlaying ? '#2ecc71' : '#334155';
    
    if (isPlaying) {
        playbackInterval = setInterval(() => {
            if (currentIndex >= telemetryData.length - 1) {
                togglePlay(false);
                return;
            }
            currentIndex++;
            const slider = document.getElementById('timeline-slider');
            if (slider) slider.value = currentIndex;
            updateUI(telemetryData[currentIndex]);
        }, 1000 / (Hz * playbackSpeed));
    } else {
        clearInterval(playbackInterval);
    }
}

function changeSpeed(val) {
    playbackSpeed = parseFloat(val);
    if (isPlaying) { togglePlay(false); togglePlay(true); }
}

function onSliderMove(val) {
    currentIndex = parseInt(val);
    updateUI(telemetryData[currentIndex]);
}

function updateUI(data) {
    if (!data) return;

    const elTime = document.getElementById('exp-time');
    const elAlt = document.getElementById('exp-alt');
    const elSpeed = document.getElementById('exp-speed');
    const elState = document.getElementById('exp-state');
    const elCurTime = document.getElementById('current-time-string');

    if (elTime) elTime.innerText = formatTime(data.Time);
    if (elAlt) elAlt.innerText = data.Altitude.toFixed(2);
    if (elSpeed) elSpeed.innerText = data.Speed.toFixed(2);
    if (elState) elState.innerText = data.State;
    if (elCurTime) elCurTime.innerText = formatTime(data.Time);

    if (mapMarker) mapMarker.setLatLng([data.Lat, data.Lon]);

    // Движение модельки вверх/вниз в зависимости от текущей высоты
    if (spaceCapsule) {
        spaceCapsule.position.y = (data.Altitude / 50) * 2 - 0.5; 
    }

    document.querySelectorAll('.state-list li').forEach(el => el.classList.remove('active'));
    const stateClean = data.State.toUpperCase();
    
    const stStart = document.getElementById('st-start');
    const stFlight = document.getElementById('st-flight');
    const stDrogue = document.getElementById('st-drogue');
    const stMain = document.getElementById('st-main');
    const stLanding = document.getElementById('st-landing');

    if (stateClean.includes("СТАРТ") && stStart) stStart.classList.add('active');
    else if (stateClean.includes("ПОЛЁТ") && stFlight) stFlight.classList.add('active');
    else if (stateClean.includes("ДРОГ") && stDrogue) stDrogue.classList.add('active');
    else if (stateClean.includes("ОСН") && stMain) stMain.classList.add('active');
    else if (stateClean.includes("ПОСАДКА") && stLanding) stLanding.classList.add('active');
    
    const hwDrogue = document.getElementById('hw-drogue');
    const hwMain = document.getElementById('hw-main');
    if (stateClean.includes("ДРОГ") && hwDrogue) { hwDrogue.className = "badge green"; hwDrogue.innerText = "РАСКРЫТ"; }
    if (stateClean.includes("ОСН") && hwMain) { hwMain.className = "badge green"; hwMain.innerText = "РАСКРЫТ"; }

    const batteryPercent = Math.max(0, 100 - Math.floor(data.Time * 0.1));
    const batEl = document.getElementById('hw-battery');
    if (batEl) {
        batEl.style.width = `${batteryPercent}%`;
        batEl.innerText = `${batteryPercent}%`;
    }

    document.querySelectorAll('#telemetry-table tr').forEach(r => r.classList.remove('active-row'));
    const tableRowIndex = Math.floor(currentIndex / 10) * 10; 
    const activeRow = document.getElementById(`t-row-${tableRowIndex}`);
    if (activeRow) {
        activeRow.classList.add('active-row');
        activeRow.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
}

function formatTime(seconds) {
    let date = new Date(null);
    date.setSeconds(seconds);
    let ms = Math.floor((seconds % 1) * 100);
    let timeString = date.toISOString().substr(11, 8);
    return `${timeString}.${ms < 10 ? '0' : ''}${ms}`;
}

function renderAnalysis() {
    if (!analysisResults) return;
    const container = document.getElementById('analysis-results');
    if (!container) return;
    
    const renderRow = (item) => `
        <div style="margin: 15px 0; font-size:0.9rem;">
            <span>${item.msg}</span>
            <span class="status-badge ${item.status ? 'passed' : 'failed'}">
                ${item.status ? '✔ ПРОЙДЕНО' : '❌ СБОЙ'}
            </span>
        </div>
    `;

    container.innerHTML = `
        <div style="border: 1px solid var(--border-color); padding: 15px; margin-bottom: 20px;">
            <h3>ИТОГОВЫЙ ВЕРДИКТ: 
                <span class="${analysisResults.verdict ? 'passed' : 'failed'}">
                    ${analysisResults.verdict ? 'СООТВЕТСТВУЕТ ТЗ' : 'НЕ СООТВЕТСТВУЕТ ТЗ'}
                </span>
            </h3>
        </div>
        ${renderRow(analysisResults.max_altitude)}
        ${renderRow(analysisResults.legs_deployment)}
        ${renderRow(analysisResults.landing_speed)}
    `;
}

function openAnalysisModal() { 
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.style.display = 'flex'; 
}
function closeAnalysisModal() { 
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.style.display = 'none'; 
}
function exportData() { alert("Экспорт аналитического отчета в PDF/XLSX запущен!"); }