const state = {
  menu: [],
  activeSectionId: null,
  activeActionId: null,
  mode: "realtime",
  currentJobId: null,
  timerStartedAt: Date.now(),
  settings: {},
  apiToken: localStorage.getItem("secids_api_token") || "",
  timeoutSeconds: 1800,
  auth: { username: "anonymous", role: "viewer", authenticated: false, auth_method: "anonymous" },
  users: [],
  models: [],
  system: { scheduler: "unknown", queue: { paused: false, pending: 0, running: 0, max_concurrent: 1 } },
  realtimeDevices: [],
  activeInterface: "eth0",
  topologyPan: { x: 0, y: 0 },
  topologyDrag: { active: false, lastX: 0, lastY: 0 },
  detectedNodes: new Set(),
  seenWorkflowEvents: new Set(),
  lastJobStatus: null,
  liveModelChooserVisible: false,
  activePacketLogTab: "action",
  packetCapture: { running: false, paused: false, interface: "-", source: "-", rows: 0, last_error: "" },
  controlSurfaceRealtime: {
    observed_at: "",
    interval_ms: 1000,
    active_interface: "eth0",
    devices: { total: 0, unknown_total: 0, items: [] },
    apps: [],
    connections: [],
    access_paths: [],
    vectors: [],
    threat: { severity: "low", signals: [], suspected_vectors: [], recommended_response: "monitor" },
  },
  deviceProfile: "desktop",
  pageZoom: 1,
  autoAdjustWindow: false,
  refreshInFlight: false,
  refreshQueued: false,
  popupMode: "onboarding",
  identification: {
    previousSectionId: null,
    filter: "all",
    selectedIp: "",
    items: [],
    counts: { total: 0 },
    editorMode: "",
    deepIdentify: false,
    status: { tone: "neutral", text: "Ready" },
  },
};

const appShell = document.querySelector(".app-shell");
const menuList = document.getElementById("menu-list");
const actionTitle = document.getElementById("action-title");
const actionDescription = document.getElementById("action-description");
const paramsForm = document.getElementById("params-form");
const runBtn = document.getElementById("run-action");
const logsOutput = document.getElementById("logs-output");
const jobStatus = document.getElementById("job-status");
const uptime = document.getElementById("uptime");
const schedulerPill = document.getElementById("scheduler-pill");
const queuePill = document.getElementById("queue-pill");
const rolePill = document.getElementById("role-pill");
const userPill = document.getElementById("user-pill");
const systemTime = document.getElementById("system-time");
const zoomOutBtn = document.getElementById("zoom-out");
const zoomInBtn = document.getElementById("zoom-in");
const zoomAutoBtn = document.getElementById("zoom-auto");
const zoomLabel = document.getElementById("zoom-label");
const realtimeBtn = document.getElementById("mode-realtime");
const simulationBtn = document.getElementById("mode-simulation");
const settingsForm = document.getElementById("settings-form");
const settingsSaveBtn = document.getElementById("settings-save");
const historyBody = document.getElementById("history-body");
const historyRefreshBtn = document.getElementById("history-refresh");
const schedulerStartBtn = document.getElementById("scheduler-start");
const schedulerStopBtn = document.getElementById("scheduler-stop");
const queuePauseBtn = document.getElementById("queue-pause");
const queueResumeBtn = document.getElementById("queue-resume");
const queueClearBtn = document.getElementById("queue-clear");
const jobPauseBtn = document.getElementById("job-pause");
const jobResumeBtn = document.getElementById("job-resume");
const jobCancelBtn = document.getElementById("job-cancel");
const jobRetryBtn = document.getElementById("job-retry");
const sudoPasswordInput = document.getElementById("sudo-password");
const saveSudoPasswordBtn = document.getElementById("save-sudo-password");
const sudoForm = document.getElementById("sudo-form");
const sudoRemember = document.getElementById("sudo-remember");
const apiTokenInput = document.getElementById("api-token");
const saveTokenBtn = document.getElementById("save-token");
const auditBody = document.getElementById("audit-body");
const auditRefreshBtn = document.getElementById("audit-refresh");
const auditExportBtn = document.getElementById("audit-export");
const auditRoleFilter = document.getElementById("audit-role-filter");
const auditStatusFilter = document.getElementById("audit-status-filter");
const auditEventFilter = document.getElementById("audit-event-filter");
const auditSearchInput = document.getElementById("audit-search");
const auditApplyBtn = document.getElementById("audit-apply");
const authUserInput = document.getElementById("auth-user");
const authPassInput = document.getElementById("auth-pass");
const authNewPassInput = document.getElementById("auth-new-pass");
const authLoginBtn = document.getElementById("auth-login");
const authChangePassBtn = document.getElementById("auth-change-pass");
const authLogoutBtn = document.getElementById("auth-logout");
const usersBody = document.getElementById("users-body");
const usersRefreshBtn = document.getElementById("users-refresh");
const userCreateNameInput = document.getElementById("user-create-name");
const userCreateRoleInput = document.getElementById("user-create-role");
const userCreatePassInput = document.getElementById("user-create-pass");
const userCreateBtn = document.getElementById("user-create-btn");
const adminOnlyPanels = document.querySelectorAll("[data-access='admin']");
const modelsBody = document.getElementById("models-body");
const modelsRefreshBtn = document.getElementById("models-refresh");
const modelsSyncBtn = document.getElementById("models-sync");
const modelRegisterPathInput = document.getElementById("model-register-path");
const modelRegisterBtn = document.getElementById("model-register-btn");
const modelsDbPill = document.getElementById("models-db-pill");
const actionlogBody = document.getElementById("actionlog-body");
const packetflowBody = document.getElementById("packetflow-body");
const packetlogsRefreshBtn = document.getElementById("packetlogs-refresh");
const packetCaptureStartBtn = document.getElementById("packet-capture-start");
const packetCapturePauseBtn = document.getElementById("packet-capture-pause");
const packetCaptureStopBtn = document.getElementById("packet-capture-stop");
const packetCaptureStatusPill = document.getElementById("packet-capture-status");
const showActionLogBtn = document.getElementById("show-action-log");
const showPacketLogBtn = document.getElementById("show-packet-log");
const actionlogsWrap = document.getElementById("actionlogs-wrap");
const packetflowWrap = document.getElementById("packetflow-wrap");
const actionlogsTable = document.getElementById("actionlogs-table");
const packetflowTable = document.getElementById("packetflow-table");
const liveModelCurrent = document.getElementById("live-model-current");
const liveModelModeAutoBtn = document.getElementById("live-model-mode-auto");
const liveModelModeManualBtn = document.getElementById("live-model-mode-manual");
const liveModelSelect = document.getElementById("live-model-select");
const liveModelSaveBtn = document.getElementById("live-model-save");
const modelChooserPanel = document.getElementById("model-chooser-panel");
const operationProgressFill = document.getElementById("operation-progress-fill");
const operationProgressLabel = document.getElementById("operation-progress-label");
const topologyLayer = document.getElementById("topology-layer");
const topologyLinks = document.getElementById("topology-links");
const topologyNodes = document.getElementById("topology-nodes");
const topologyTooltip = document.getElementById("topology-tooltip");
const toastStack = document.getElementById("toast-stack");
const simulationPanel = document.getElementById("simulation-panel");
const launchSimulationBtn = document.getElementById("launch-simulation");
const simArchitectureType = document.getElementById("sim-architecture-type");
const simArchitectureSummary = document.getElementById("simulation-architecture-summary");
const simAttackerProfile = document.getElementById("sim-attacker-profile");
const simDefenderProfile = document.getElementById("sim-defender-profile");
const simCountermeasureMode = document.getElementById("sim-countermeasure-mode");
const simIntensity = document.getElementById("sim-intensity");
const simAttackers = document.getElementById("sim-attackers");
const simDuration = document.getElementById("sim-duration");
const simSeed = document.getElementById("sim-seed");
const simRetrain = document.getElementById("sim-retrain");
const popupModeToggleBtn = document.getElementById("popup-mode-toggle");
const popupModePill = document.getElementById("popup-mode-pill");
const contextPopupPanel = document.getElementById("context-popup-panel");
const contextPopupTitle = document.getElementById("context-popup-title");
const contextPopupBody = document.getElementById("context-popup-body");
const controlSurfaceStatus = document.getElementById("control-surface-status");
const identificationListPanel = document.getElementById("identification-list-panel");
const identificationListSummary = document.getElementById("identification-list-summary");
const identificationListBody = document.getElementById("identification-list-body");
const identificationDeepIdentify = document.getElementById("identification-deep-identify");
const identificationStatusChip = document.getElementById("identification-status-chip");
const identificationEditor = document.getElementById("identification-editor");
const identificationEditorTitle = document.getElementById("identification-editor-title");
const identificationEditorIp = document.getElementById("identification-editor-ip");
const identificationEditorTag = document.getElementById("identification-editor-tag");
const identificationEditorNotes = document.getElementById("identification-editor-notes");
const identificationEditorSave = document.getElementById("identification-editor-save");
const identificationEditorCancel = document.getElementById("identification-editor-cancel");

const IDENTIFICATION_SECTION_ID = "identification-listing";
const IDENTIFICATION_TAGS = ["whitelist", "blacklist", "greylist", "intruder", "unidentified"];
const IDENTIFICATION_FILTER_BY_ACTION = {
  "id-list-whitelist": "whitelist",
  "id-list-blacklist": "blacklist",
  "id-list-greylist": "greylist",
  "id-list-intruder": "intruder",
  "id-list-unidentified": "unidentified",
};
const IDENTIFICATION_REDIRECT_ACTIONS = new Set(["view-whitelist", "view-blacklist", "update-lists"]);

const TOPOLOGY_NODE_DATA = [
  { id: "iot", label: "IoT", icon: "📟", x: 8, y: 52 },
  { id: "endpoint", label: "Device", icon: "💻", x: 20, y: 52 },
  { id: "fileserver", label: "File Server", icon: "🗄️", x: 34, y: 52 },
  { id: "router", label: "Router", icon: "📶", x: 48, y: 52 },
  { id: "switch", label: "Switch", icon: "🔀", x: 62, y: 52 },
  { id: "capture", label: "Capture", icon: "📡", x: 74, y: 38 },
  { id: "deepScan", label: "Deep Scan", icon: "🧪", x: 86, y: 38 },
  { id: "cnn", label: "CNN Model", icon: "🧠", x: 74, y: 66 },
  { id: "countermeasure", label: "Countermeasure", icon: "🛡️", x: 86, y: 66 },
  { id: "reports", label: "Reports", icon: "📊", x: 94, y: 52 },
];

const TOPOLOGY_CONNECTIONS = [
  ["iot", "endpoint"],
  ["endpoint", "fileserver"],
  ["fileserver", "router"],
  ["router", "switch"],
  ["switch", "capture"],
  ["capture", "deepScan"],
  ["switch", "cnn"],
  ["cnn", "countermeasure"],
  ["deepScan", "reports"],
  ["countermeasure", "reports"],
  ["cnn", "reports"],
];

const ACTION_NODE_HINTS = {
  "live-detect-fast": ["endpoint", "router", "switch", "cnn", "reports"],
  "live-detect-standard": ["endpoint", "router", "switch", "cnn", "reports"],
  "live-detect-slow": ["endpoint", "router", "switch", "cnn", "reports"],
  "deep-scan-live": ["capture", "deepScan", "reports"],
  "deep-scan-file": ["fileserver", "deepScan", "reports"],
  "integrated-adaptive-workflow": ["iot", "endpoint", "router", "switch", "capture", "cnn", "countermeasure", "reports"],
  "integrated-adaptive-workflow-continuous": ["iot", "endpoint", "router", "switch", "capture", "cnn", "countermeasure", "reports"],
  "integrated-adaptive-workflow-stop": ["router", "switch", "capture", "cnn", "countermeasure", "reports"],
  "simulate-ddos-training-loop": ["iot", "endpoint", "router", "switch", "cnn", "countermeasure", "reports"],
  "detect-file-default": ["fileserver", "cnn", "reports"],
  "capture-quick": ["iot", "endpoint", "router", "switch", "capture"],
  "capture-custom": ["iot", "endpoint", "router", "switch", "capture"],
  "capture-continuous": ["iot", "endpoint", "router", "switch", "capture"],
  "pipeline-capture": ["iot", "endpoint", "router", "switch", "capture", "cnn", "reports"],
  "analyze-csv": ["fileserver", "cnn", "reports"],
  "analyze-pcap": ["capture", "fileserver", "cnn", "reports"],
  "batch-analysis": ["fileserver", "cnn", "reports"],
  "pcap-to-csv": ["capture", "fileserver"],
  "refine-dataset": ["fileserver"],
  "history-rerun": ["router", "switch", "capture", "deepScan", "cnn", "reports"],
};

const SIMULATION_ARCHITECTURE_PRESETS = {
  school: {
    label: "School (Simple)",
    hardware: ["1 edge router", "1 managed switch", "1 file/NAS server", "20 student devices", "1 AP"],
    software: ["DHCP + DNS", "content filter", "endpoint AV", "basic SIEM logging", "SecIDS-CNN node"],
    quality: "Balanced training quality across classroom traffic and burst traffic.",
  },
  library: {
    label: "Library (Simple)",
    hardware: ["1 edge router", "1 switch", "1 circulation server", "12 public terminals", "1 AP"],
    software: ["public session manager", "DNS filtering", "endpoint AV", "log aggregator", "SecIDS-CNN node"],
    quality: "High consistency for low-variance browsing traffic simulations.",
  },
  restaurant: {
    label: "Restaurant (Simple)",
    hardware: ["1 edge router", "1 PoS gateway", "1 switch", "6 PoS/tablet devices", "2 APs"],
    software: ["PoS stack", "guest Wi-Fi portal", "payment endpoint controls", "log collector", "SecIDS-CNN node"],
    quality: "Good quality for mixed payment, guest Wi-Fi, and IoT-like traffic bursts.",
  },
};

if (apiTokenInput) {
  apiTokenInput.value = state.apiToken;
}

function notify(title, message, tone = "success", timeoutMs = 4200) {
  if (!toastStack) {
    return;
  }

  const toast = document.createElement("div");
  toast.className = `toast ${tone}`;
  toast.innerHTML = `<div class="toast-title">${title}</div><div class="toast-message">${message}</div>`;
  toastStack.prepend(toast);

  requestAnimationFrame(() => {
    toast.classList.add("visible");
  });

  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 220);
  }, timeoutMs);
}

function applyPageZoom() {
  if (state.deviceProfile === "mobile") {
    document.body.style.zoom = "100%";
    if (zoomLabel) {
      zoomLabel.textContent = "100%";
    }
    if (zoomAutoBtn) {
      zoomAutoBtn.classList.remove("active-switch");
    }
    return;
  }

  const clamped = Math.max(0.7, Math.min(1.4, state.pageZoom || 1));
  state.pageZoom = clamped;
  document.body.style.zoom = `${Math.round(clamped * 100)}%`;
  if (zoomLabel) {
    zoomLabel.textContent = `${Math.round(clamped * 100)}%`;
  }
  if (zoomAutoBtn) {
    zoomAutoBtn.classList.toggle("active-switch", Boolean(state.autoAdjustWindow));
  }
}

function getDeviceProfile() {
  const width = window.innerWidth || document.documentElement.clientWidth || 1280;
  if (width <= 768) {
    return "mobile";
  }
  if (width <= 1100) {
    return "tablet";
  }
  return "desktop";
}

function applyDeviceProfile() {
  const profile = getDeviceProfile();
  state.deviceProfile = profile;
  document.body.setAttribute("data-device-profile", profile);

  if (profile === "mobile") {
    state.autoAdjustWindow = false;
    state.pageZoom = 1;
    if (zoomAutoBtn) {
      zoomAutoBtn.disabled = true;
    }
  } else if (profile === "tablet") {
    if (zoomAutoBtn) {
      zoomAutoBtn.disabled = false;
    }
    if (!state.autoAdjustWindow) {
      state.pageZoom = Math.max(0.9, Math.min(1.1, state.pageZoom || 1));
    }
  } else {
    if (zoomAutoBtn) {
      zoomAutoBtn.disabled = false;
    }
  }

  applyPageZoom();
}

function renderSimulationArchitectureSummary() {
  if (!simArchitectureSummary) {
    return;
  }

  const selected = (simArchitectureType?.value || "school").trim().toLowerCase();
  const preset = SIMULATION_ARCHITECTURE_PRESETS[selected] || SIMULATION_ARCHITECTURE_PRESETS.school;
  const hardware = preset.hardware.map((item) => `<span class="sim-chip">${item}</span>`).join("");
  const software = preset.software.map((item) => `<span class="sim-chip">${item}</span>`).join("");

  simArchitectureSummary.innerHTML = `
    <div class="sim-arch-title">${preset.label}</div>
    <div class="sim-arch-group"><strong>Hardware:</strong> ${hardware}</div>
    <div class="sim-arch-group"><strong>Software:</strong> ${software}</div>
    <div class="sim-arch-quality"><strong>Simulation Quality:</strong> ${preset.quality}</div>
  `;
}

function autoAdjustToWindow() {
  if (!appShell) {
    return;
  }

  if (state.deviceProfile === "mobile") {
    state.pageZoom = 1;
    applyPageZoom();
    return;
  }

  const targetWidth = state.deviceProfile === "tablet" ? 1180 : 1600;
  const targetHeight = state.deviceProfile === "tablet" ? 900 : 980;
  const ratio = Math.min(window.innerWidth / targetWidth, window.innerHeight / targetHeight);
  state.pageZoom = Math.max(0.75, Math.min(1.25, ratio));
  applyPageZoom();
}

function zoomBy(delta) {
  if (state.deviceProfile === "mobile") {
    return;
  }
  state.autoAdjustWindow = false;
  state.pageZoom = (state.pageZoom || 1) + delta;
  applyPageZoom();
}

function setGlobalProgress(status = "idle", logs = []) {
  if (!operationProgressFill || !operationProgressLabel) {
    return;
  }

  const statusMap = {
    idle: 0,
    queued: 12,
    running: 55,
    paused: 55,
    stopping: 85,
    completed: 100,
    failed: 100,
    timeout: 100,
    cancelled: 100,
  };

  let percentage = Object.prototype.hasOwnProperty.call(statusMap, status) ? statusMap[status] : 25;
  if (status === "running") {
    percentage = 55 + (Math.floor(Date.now() / 1000) % 35);
  }
  let latestStage = "";
  (logs || []).forEach((line) => {
    const text = String(line || "");
    const match = text.match(/STAGE\s+([A-D])\s*:/i);
    if (match) {
      latestStage = String(match[1] || "").toUpperCase();
    }
  });
  if (latestStage) {
    const stagePctMap = { A: 25, B: 45, C: 70, D: 90 };
    percentage = Math.max(percentage, stagePctMap[latestStage] || percentage);
  }

  operationProgressFill.style.width = `${Math.max(0, Math.min(percentage, 100))}%`;
  operationProgressLabel.textContent = `${status || "idle"} • ${Math.round(percentage)}%`;
}

function parseWorkflowStageEvents(logs = []) {
  const events = [];
  const stageRegex = /STAGE\s+([A-D])\s*:\s*([^\[]+?)\s*\[([^\]]+)\]/i;

  logs.forEach((line) => {
    const text = String(line || "");
    const match = text.match(stageRegex);
    if (!match) {
      return;
    }

    const stageCode = (match[1] || "").toUpperCase();
    const stageName = (match[2] || "").trim();
    const status = (match[3] || "").trim().toUpperCase();
    const key = `${stageCode}:${stageName}:${status}`;

    if (state.seenWorkflowEvents.has(key)) {
      return;
    }

    state.seenWorkflowEvents.add(key);
    if (state.seenWorkflowEvents.size > 400) {
      const [first] = state.seenWorkflowEvents;
      state.seenWorkflowEvents.delete(first);
    }

    events.push({ stageCode, stageName, status });
  });

  return events;
}

async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.apiToken) {
    headers["X-SECIDS-Token"] = state.apiToken;
  }

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    let timeoutTriggered = false;
    try {
      const data = await response.clone().json();
      timeoutTriggered = data.code === "SESSION_TIMEOUT";
    } catch {
      timeoutTriggered = false;
    }

    logsOutput.textContent = timeoutTriggered
      ? "Session timed out due to inactivity. Redirecting to login..."
      : "Unauthorized: login or set API token in toolbar.";
    jobStatus.textContent = "auth";

    if (timeoutTriggered) {
      const nextLoginPath = state.system?.login_path || "/login";
      setTimeout(() => {
        window.location.href = nextLoginPath;
      }, 500);
    }
  }
  if (response.status === 403) {
    try {
      const data = await response.clone().json();
      if (data.code === "PASSWORD_CHANGE_REQUIRED") {
        logsOutput.textContent = "Password change required before protected operations.";
        jobStatus.textContent = "auth";
      }
    } catch {
      // ignore non-json
    }
  }
  return response;
}

function getActiveSection() {
  return state.menu.find((section) => section.id === state.activeSectionId) || null;
}

function getActiveAction() {
  const section = getActiveSection();
  if (!section) {
    return null;
  }
  return section.actions.find((action) => action.id === state.activeActionId) || null;
}

function renderDeviceStrip(payload = null) {
  const strip = document.getElementById("device-strip");
  if (!strip) {
    return;
  }

  if (state.activeSectionId === IDENTIFICATION_SECTION_ID) {
    strip.innerHTML = [
      `<button class="device-item btn" data-device-action="ident-add" title="Add IP to list">Add to List</button>`,
      `<button class="device-item btn" data-device-action="ident-remove" title="Remove selected IP">Remove from List</button>`,
      `<button class="device-item btn" data-device-action="ident-change-tag" title="Move selected IP to another tag">Change Tag</button>`,
      `<button class="device-item btn" data-device-action="ident-return" title="Return to main control surface">Return</button>`,
    ].join("");
    if (controlSurfaceStatus) {
      controlSurfaceStatus.innerHTML = [
        `filter:${state.identification.filter || "all"}`,
        `selected:${state.identification.selectedIp || "none"}`,
        `total:${state.identification.counts?.total || 0}`,
      ]
        .map((item) => `<span class="control-surface-status-item">${item}</span>`)
        .join("");
    }
    return;
  }

  const interfaces = payload?.interfaces || [];
  const counts = payload?.counts || {};
  const connectedCount = Array.isArray(payload?.connected_devices) ? payload.connected_devices.length : state.realtimeDevices.length;
  const countermeasureMode = String(
    state.settings?.countermeasure_mode || payload?.selected_countermeasure_mode || "active",
  ).toLowerCase() === "passive"
    ? "passive"
    : "active";
  const actionButtons = [
    `<button class="device-item btn" data-device-action="choose-model" title="Select live detection model">Models</button>`,
    `<button class="device-item btn" data-device-action="toggle-countermeasure-mode" data-countermeasure-mode="${countermeasureMode}" title="Toggle countermeasure mode">${countermeasureMode === "passive" ? "Passive" : "Active"}</button>`,
    `<button class="device-item btn" data-device-action="reset-view" title="Reset control surface position">Reset View</button>`,
  ];

  if (state.auth.role === "admin") {
    actionButtons.push(
      `<button class="device-item btn" data-device-action="open-server-db" title="Open server database">Server</button>`,
    );
  }

  strip.innerHTML = actionButtons.join("");

  if (controlSurfaceStatus) {
    const activeInterface = state.activeInterface || state.settings?.last_interface || interfaces[0] || "eth0";
    const queue = state.system?.queue || {};
    const statusItems = [
      `interface:${activeInterface}`,
      `models:${counts.models ?? 0}`,
      `connected:${connectedCount}`,
      `apps:${(state.controlSurfaceRealtime?.apps || []).length}`,
      `paths:${(state.controlSurfaceRealtime?.access_paths || []).length}`,
      `threat:${String(state.controlSurfaceRealtime?.threat?.severity || "low")}`,
      `scheduler:${payload?.scheduler || state.system?.scheduler || "unknown"}`,
      `queue:${queue.running || 0}R/${queue.pending || 0}P`,
    ];

    controlSurfaceStatus.innerHTML = statusItems
      .map((item) => `<span class="control-surface-status-item">${item}</span>`)
      .join("");
  }
}

function getListStatus(device = {}) {
  const raw = String(device.list_status || device.status || "").toLowerCase();
  if (raw === "whitelist") {
    return "whitelist";
  }
  // blacklist = manually/explicitly blocked by admin → dark-red static
  if (raw === "blacklist") {
    return "blacklist";
  }
  // intruder/attacker = CNN-detected active threat → pulsing red
  if (raw === "attacker" || raw === "attackers" || raw === "intruder" || raw === "intrusion") {
    return "intruder";
  }
  if (raw === "greylist" || raw === "graylist") {
    return "greylist";
  }
  return "unknown";
}

function getDeviceColorClass(device = {}) {
  const status = getListStatus(device);
  if (status === "whitelist") return "whitelist";
  if (status === "blacklist") return "blacklist";
  if (status === "intruder")  return "intruder";
  if (status === "greylist")  return "greylist";
  return "unknown";
}

function isIdentificationMode() {
  return state.activeSectionId === IDENTIFICATION_SECTION_ID;
}

function formatIdentificationTag(tag) {
  const normalized = String(tag || "unidentified").trim().toLowerCase();
  if (normalized === "greylist") return "Greylist";
  if (normalized === "blacklist") return "Blacklist";
  if (normalized === "whitelist") return "Whitelist";
  if (normalized === "intruder") return "Intruder";
  return "Unidentified";
}

function getFilteredIdentificationItems() {
  const allItems = Array.isArray(state.identification.items) ? state.identification.items : [];
  const filter = String(state.identification.filter || "all").toLowerCase();
  if (filter === "all") {
    return allItems;
  }
  return allItems.filter((item) => String(item.tag || "").toLowerCase() === filter);
}

function renderIdentificationListPanel() {
  if (!identificationListPanel || !identificationListBody || !identificationListSummary) {
    return;
  }

  if (identificationDeepIdentify) {
    identificationDeepIdentify.checked = Boolean(state.identification.deepIdentify);
  }
  renderIdentificationStatusChip();

  const enabled = isIdentificationMode();
  identificationListPanel.classList.toggle("hidden", !enabled);
  if (!enabled) {
    return;
  }

  const filteredItems = getFilteredIdentificationItems();
  const counts = state.identification.counts || {};
  const countText = state.identification.filter === "all"
    ? `total: ${counts.total || filteredItems.length}`
    : `${state.identification.filter}: ${filteredItems.length}`;
  identificationListSummary.textContent = countText;

  if (!filteredItems.length) {
    identificationListBody.innerHTML = `<div class="identification-row unidentified"><span class="identification-tag-pill">Empty</span><span>No entries for current filter.</span><span>--</span></div>`;
    return;
  }

  identificationListBody.innerHTML = filteredItems
    .map((item) => {
      const ip = String(item.ip || "").trim();
      const tag = String(item.tag || "unidentified").toLowerCase();
      const source = String(item.source || "runtime");
      const selected = ip && state.identification.selectedIp === ip ? "selected" : "";
      return `
        <button class="identification-row ${tag} ${selected}" data-identification-ip="${ip}" data-identification-tag="${tag}">
          <span class="identification-tag-pill">${formatIdentificationTag(tag)}</span>
          <span>${ip || "unknown"}</span>
          <span>${source}</span>
        </button>
      `;
    })
    .join("");
}

function setIdentificationStatus(text, tone = "neutral") {
  state.identification.status = {
    text: String(text || "Ready"),
    tone: ["neutral", "success", "error"].includes(String(tone)) ? String(tone) : "neutral",
  };
  renderIdentificationStatusChip();
}

function renderIdentificationStatusChip() {
  if (!identificationStatusChip) {
    return;
  }
  const status = state.identification.status || { text: "Ready", tone: "neutral" };
  identificationStatusChip.textContent = status.text || "Ready";
  identificationStatusChip.classList.remove("neutral", "success", "error");
  identificationStatusChip.classList.add(status.tone || "neutral");
}

async function loadIdentificationListing() {
  const response = await apiFetch("/api/identification-list");
  if (!response.ok) {
    return;
  }

  const data = await response.json();
  state.identification.items = Array.isArray(data.items) ? data.items : [];
  state.identification.counts = data.counts || { total: state.identification.items.length };
  renderIdentificationListPanel();
  if (isIdentificationMode()) {
    renderDeviceStrip();
  }
}

function normalizePromptTag(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "graylist") {
    return "greylist";
  }
  if (["attacker", "attackers", "intrusion"].includes(normalized)) {
    return "intruder";
  }
  return IDENTIFICATION_TAGS.includes(normalized) ? normalized : "";
}

function openIdentificationEditor(mode) {
  if (!identificationEditor || !identificationEditorIp || !identificationEditorTag || !identificationEditorTitle) {
    return;
  }

  state.identification.editorMode = mode;
  identificationEditor.classList.remove("hidden");

  const selected = (state.identification.items || []).find(
    (item) => String(item.ip || "").trim() === String(state.identification.selectedIp || "").trim(),
  );

  const selectedIp = selected?.ip || state.identification.selectedIp || "";
  const selectedTag = normalizePromptTag(selected?.tag || state.identification.filter || "") || "unidentified";

  if (mode === "add") {
    identificationEditorTitle.textContent = "Add to Identification List";
    identificationEditorIp.value = selectedIp;
    identificationEditorTag.value = selectedTag;
    identificationEditorTag.disabled = false;
  } else if (mode === "change-tag") {
    identificationEditorTitle.textContent = "Change Identification Tag";
    identificationEditorIp.value = selectedIp;
    identificationEditorTag.value = selectedTag;
    identificationEditorTag.disabled = false;
  } else {
    identificationEditorTitle.textContent = "Remove from Identification List";
    identificationEditorIp.value = selectedIp;
    identificationEditorTag.value = selectedTag;
    identificationEditorTag.disabled = true;
  }

  if (identificationEditorNotes) {
    identificationEditorNotes.value = "";
  }
  identificationEditorIp.focus();
}

function closeIdentificationEditor() {
  state.identification.editorMode = "";
  if (!identificationEditor) {
    return;
  }
  identificationEditor.classList.add("hidden");
}

async function identificationApiWrite(path, payload, successTitle) {
  const response = await apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    setIdentificationStatus(data.error || "Action failed", "error");
    notify("Identification Listing", data.error || "Operation failed", "error", 2200);
    return null;
  }

  state.identification.items = Array.isArray(data.items) ? data.items : state.identification.items;
  state.identification.counts = data.counts || state.identification.counts;
  renderIdentificationListPanel();
  renderDeviceStrip();
  setIdentificationStatus(successTitle, "success");
  notify("Identification Listing", successTitle, "success", 1600);
  return data;
}

async function addToIdentificationList() {
  openIdentificationEditor("add");
}

async function removeFromIdentificationList() {
  openIdentificationEditor("remove");
}

async function changeIdentificationTag() {
  openIdentificationEditor("change-tag");
}

async function runIdentifyUnknownItems() {
  const response = await apiFetch("/api/identification-list/identify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ deep_test: Boolean(state.identification.deepIdentify) }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    setIdentificationStatus(data.error || "Identify scan failed", "error");
    notify("Identify", data.error || "Identify scan failed", "error", 2200);
    return;
  }

  state.identification.items = Array.isArray(data.items) ? data.items : state.identification.items;
  state.identification.counts = data.counts || state.identification.counts;
  renderIdentificationListPanel();
  renderDeviceStrip();
  const movedCount = Array.isArray(data.moved) ? data.moved.length : 0;
  const deepLabel = data.deep_test?.enabled ? " (deep)" : "";
  setIdentificationStatus(`Identify complete: ${movedCount}${deepLabel}`, "success");
  notify("Identify", `Classified ${movedCount} unidentified item(s)${deepLabel}.`, "success", 2200);
}

async function submitIdentificationEditor() {
  const mode = String(state.identification.editorMode || "").trim();
  if (!mode || !identificationEditorIp) {
    return;
  }

  const ip = String(identificationEditorIp.value || "").trim();
  const tag = normalizePromptTag(identificationEditorTag?.value || "");
  const notes = String(identificationEditorNotes?.value || "").trim();

  if (!ip) {
    setIdentificationStatus("IP required", "error");
    notify("Identification Listing", "IP is required", "error", 1800);
    identificationEditorIp.focus();
    return;
  }

  let result = null;
  if (mode === "add") {
    if (!tag) {
      setIdentificationStatus("Tag required", "error");
      notify("Identification Listing", "Tag is required", "error", 1800);
      return;
    }
    result = await identificationApiWrite(
      "/api/identification-list/add",
      { ip, tag, notes, source: "manual" },
      `Added ${ip} to ${tag}`,
    );
  } else if (mode === "change-tag") {
    if (!tag) {
      setIdentificationStatus("Tag required", "error");
      notify("Identification Listing", "Tag is required", "error", 1800);
      return;
    }
    result = await identificationApiWrite(
      "/api/identification-list/change-tag",
      { ip, tag, notes, source: "manual" },
      `Moved ${ip} to ${tag}`,
    );
  } else if (mode === "remove") {
    result = await identificationApiWrite("/api/identification-list/remove", { ip }, `Removed ${ip}`);
  }

  if (result) {
    state.identification.selectedIp = ip;
    closeIdentificationEditor();
    renderIdentificationListPanel();
  }
}

function enterIdentificationSection() {
  if (!state.identification.previousSectionId || state.identification.previousSectionId === IDENTIFICATION_SECTION_ID) {
    const fallback = (state.menu || []).find((section) => section.id !== IDENTIFICATION_SECTION_ID);
    state.identification.previousSectionId = fallback?.id || "detection";
  }
  if (!state.identification.filter) {
    state.identification.filter = "all";
  }
  if (!state.identification.status?.text) {
    setIdentificationStatus("Ready", "neutral");
  }
  renderIdentificationListPanel();
  renderDeviceStrip();
}

function leaveIdentificationSection() {
  state.identification.filter = "all";
  state.identification.selectedIp = "";
  setIdentificationStatus("Ready", "neutral");
  closeIdentificationEditor();
  renderIdentificationListPanel();
}

function handleIdentificationActionSelection(actionId) {
  if (actionId === "id-list-identify") {
    runIdentifyUnknownItems();
    return;
  }
  const nextFilter = IDENTIFICATION_FILTER_BY_ACTION[actionId] || "all";
  state.identification.filter = nextFilter;
  renderIdentificationListPanel();
  renderDeviceStrip();
}

async function loadOverview() {
  const response = await apiFetch("/api/overview");
  if (!response.ok) {
    renderDeviceStrip();
    return;
  }

  const data = await response.json();
  const previousDeviceKeys = new Set(
    (state.realtimeDevices || [])
      .map((device) => String(device.ip || "").trim())
      .filter((value) => value.length > 0),
  );

  state.settings.live_model_path = data.selected_live_model || state.settings.live_model_path || "";
  state.settings.live_backend = data.selected_live_backend || state.settings.live_backend || "";
  state.settings.countermeasure_mode = data.selected_countermeasure_mode || state.settings.countermeasure_mode || "active";
  state.realtimeDevices = Array.isArray(data.connected_devices) ? data.connected_devices : [];
  state.activeInterface = data.active_interface || state.settings?.last_interface || "eth0";

  const newDevices = state.realtimeDevices.filter((device) => {
    const key = String(device.ip || "").trim();
    return key && !previousDeviceKeys.has(key);
  });

  syncCountermeasureModeUI();
  renderLiveModelSelection();
  renderDeviceStrip(data);
  renderTopology();

  if (newDevices.length) {
    const latest = newDevices[0];
    notify(
      "New Device Detected",
      `${latest.ip || "unknown"} (${String(latest.interface || state.activeInterface || "iface")})`,
      "warn",
      2200,
    );
    setTimeout(() => {
      refreshSystemInfo();
    }, 120);
  }
}

async function loadControlSurfaceRealtime() {
  const response = await apiFetch("/api/control-surface/realtime");
  if (!response.ok) {
    return;
  }

  const data = await response.json();
  state.controlSurfaceRealtime = data || state.controlSurfaceRealtime;

  const items = Array.isArray(data?.devices?.items) ? data.devices.items : [];
  if (items.length) {
    state.realtimeDevices = items;
  }

  if (String(data?.active_interface || "").trim()) {
    state.activeInterface = data.active_interface;
  }

  renderDeviceStrip();
  renderTopology();
}

function renderActionLogs(rows = []) {
  if (!actionlogBody) {
    return;
  }

  if (!rows.length) {
    actionlogBody.innerHTML = `<tr><td colspan="7">No action logs yet.</td></tr>`;
    return;
  }

  actionlogBody.innerHTML = rows
    .map(
      (row) => `
      <tr>
        <td>${row.timestamp || "-"}</td>
        <td>${row.action_id || "-"}</td>
        <td>${row.status || "-"}</td>
        <td>${row.operator || "-"}</td>
        <td>${row.mode || "-"}</td>
        <td>${row.activity || "-"}</td>
        <td>${row.message || "-"}<br><span class="packetlog-details">${row.details || "-"}</span></td>
      </tr>
    `,
    )
    .join("");
}

function renderPacketFlow(rows = []) {
  if (!packetflowBody) {
    return;
  }

  if (!rows.length) {
    packetflowBody.innerHTML = `<tr><td colspan="9">No packet flow data yet.</td></tr>`;
    return;
  }

  packetflowBody.innerHTML = rows
    .map(
      (row) => `
      <tr class="packet-row ${getPacketTrafficClass(row)} ${getPacketModelClass(row)}">
        <td>${row.timestamp || "-"}</td>
        <td>${row.number || "-"}</td>
        <td>${row.source || "-"}</td>
        <td>${row.destination || "-"}</td>
        <td>${row.protocol || "-"}</td>
        <td>${row.length || "-"}</td>
        <td>${row.flags || "-"}</td>
        <td>${row.model_flags || "-"}</td>
        <td>${row.info || "-"}</td>
      </tr>
    `,
    )
    .join("");
}

function parsePacketLength(lengthValue) {
  const parsed = Number.parseInt(String(lengthValue || "").trim(), 10);
  return Number.isFinite(parsed) ? parsed : 0;
}

function getPacketModelClass(row = {}) {
  const modelFlags = String(row.model_flags || "").toLowerCase();
  const info = String(row.info || "").toLowerCase();
  const source = String(row.source || "").trim();
  const destination = String(row.destination || "").trim();

  if (modelFlags.includes("blacklist") || info.includes("blacklist")) {
    return "model-blacklist";
  }
  if (modelFlags.includes("greylist") || modelFlags.includes("graylist") || info.includes("greylist") || info.includes("graylist")) {
    return "model-greylist";
  }
  if (modelFlags.includes("whitelist") || info.includes("whitelist")) {
    return "model-whitelist";
  }

  const byIpStatus = (ip) => {
    if (!ip) {
      return "unknown";
    }
    const peer = (state.realtimeDevices || []).find((device) => String(device.ip || "").trim() === ip);
    return peer ? getListStatus(peer) : "unknown";
  };

  const sourceStatus = byIpStatus(source);
  if (sourceStatus === "blacklist") {
    return "model-blacklist";
  }
  if (sourceStatus === "greylist") {
    return "model-greylist";
  }
  if (sourceStatus === "whitelist") {
    return "model-whitelist";
  }

  const destinationStatus = byIpStatus(destination);
  if (destinationStatus === "blacklist") {
    return "model-blacklist";
  }
  if (destinationStatus === "greylist") {
    return "model-greylist";
  }
  if (destinationStatus === "whitelist") {
    return "model-whitelist";
  }

  return "model-unknown";
}

function getPacketTrafficClass(row = {}) {
  const protocol = String(row.protocol || "").toUpperCase();
  const info = String(row.info || "").toLowerCase();
  const length = parsePacketLength(row.length);

  if (protocol.includes("ARP")) {
    return "ws-arp";
  }
  if (protocol.includes("ICMP")) {
    return "ws-icmp";
  }
  if (protocol.includes("DNS")) {
    return "ws-dns";
  }
  if (protocol.includes("TLS") || protocol.includes("SSL") || protocol.includes("HTTPS")) {
    return "ws-tls";
  }
  if (protocol.includes("HTTP")) {
    return "ws-http";
  }
  if (protocol.includes("UDP")) {
    return "ws-udp";
  }

  const tcpAnomalyHints = [
    "retransmission",
    "dup ack",
    "out-of-order",
    "previous segment not captured",
    "checksum error",
    "bad checksum",
    "malformed",
    "reset",
  ];
  if (protocol.includes("TCP") && tcpAnomalyHints.some((hint) => info.includes(hint))) {
    return "ws-tcp-anomaly";
  }
  if (protocol.includes("TCP")) {
    return "ws-tcp";
  }

  if (length >= 1200) {
    return "ws-large";
  }
  return "ws-default";
}

async function loadActionLogs() {
  if (!actionlogBody) {
    return;
  }

  const response = await apiFetch("/api/packet-logs?limit=180");
  const data = await response.json();
  if (!response.ok) {
    renderActionLogs([]);
    return;
  }

  renderActionLogs(data.rows || []);
}

async function loadPacketFlow() {
  if (!packetflowBody) {
    return;
  }

  const response = await apiFetch("/api/packet-flow?limit=220");
  const data = await response.json();
  if (!response.ok) {
    renderPacketFlow([]);
    return;
  }

  renderPacketFlow(data.rows || []);
}

function renderPacketCaptureStatus() {
  if (!packetCaptureStatusPill) {
    return;
  }

  const capture = state.packetCapture || {};
  const mode = String(state.settings?.countermeasure_mode || "active").toLowerCase() === "passive" ? "passive" : "active";
  const managedMode = String(capture.managed_mode || "manual").toLowerCase() === "auto" ? "auto" : "manual";
  let statusText = "stopped";
  if (capture.running && capture.paused) {
    statusText = "paused";
  } else if (capture.running) {
    statusText = "running";
  }

  packetCaptureStatusPill.textContent = `capture: ${statusText} • ${capture.interface || "-"} • mode=${mode} • control=${managedMode}`;
  if (packetCaptureStartBtn) {
    packetCaptureStartBtn.textContent = capture.paused ? "Start" : "Start";
  }
  if (packetCapturePauseBtn) {
    packetCapturePauseBtn.disabled = !capture.running || capture.paused;
  }
  if (packetCaptureStopBtn) {
    packetCaptureStopBtn.disabled = !capture.running && !capture.paused;
  }
}

async function loadPacketCaptureStatus() {
  const response = await apiFetch("/api/packet-capture/status");
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  state.packetCapture = data.capture || state.packetCapture;
  renderPacketCaptureStatus();
}

async function controlPacketCapture(action, payload = {}, options = {}) {
  const response = await apiFetch(`/api/packet-capture/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  const data = await response.json();

  if (!response.ok || !data.ok) {
    state.packetCapture = data.capture || state.packetCapture;
    renderPacketCaptureStatus();
    if (!options.silent) {
      logsOutput.textContent = data.error || data.message || `Packet capture ${action} failed.`;
      jobStatus.textContent = "packet-capture";
      notify("Packet Capture", data.message || `Failed to ${action} capture`, "error", 2400);
    }
    return false;
  }

  state.packetCapture = data.capture || state.packetCapture;
  renderPacketCaptureStatus();
  if (!options.silent) {
    logsOutput.textContent = data.message || `Packet capture ${action} ok.`;
    jobStatus.textContent = "packet-capture";
    notify("Packet Capture", data.message || `Capture ${action} ok`, "success", 1800);
  }
  if (action === "start" || action === "stop") {
    await loadPacketFlow();
  }
  return true;
}

async function enforcePacketCapturePolicy() {
  const mode = String(state.settings?.countermeasure_mode || "active").toLowerCase() === "passive" ? "passive" : "active";
  if (mode !== "passive") {
    return;
  }

  await controlPacketCapture(
    "start",
    {
      interface: state.settings?.last_interface || state.activeInterface || "eth0",
      auto: true,
    },
    { silent: true },
  );
}

function getTrafficState() {
  if (state.system?.queue?.paused) {
    return "paused";
  }
  if (state.mode === "realtime" && (state.system?.queue?.running || 0) > 0) {
    return "live";
  }
  return "stopped";
}

function getNodeInfo(nodeId) {
  const queue = state.system?.queue || { pending: 0, running: 0, paused: false, max_concurrent: 1 };
  const status = getTrafficState();
  const interfaceName = state.settings?.last_interface || "eth0";
  const surface = state.controlSurfaceRealtime || {};
  const threat = surface.threat || {};
  const threatSeverity = String(threat.severity || "low");

  const generic = [
    `Traffic: ${status}`,
    `Interface: ${interfaceName}`,
    `Running jobs: ${queue.running}`,
    `Pending jobs: ${queue.pending}`,
    `Queue paused: ${queue.paused ? "yes" : "no"}`,
    `Scheduler: ${state.system?.scheduler || "unknown"}`,
    `Threat severity: ${threatSeverity}`,
    `Active paths: ${(surface.access_paths || []).length}`,
    `Response: ${threat.recommended_response || "monitor"}`,
  ];

  const byNode = {
    iot: ["Source: IoT telemetry traffic", "Observed via live capture and packet pipeline"],
    endpoint: ["Source: endpoint/host events", "Used for threat behavior inference"],
    fileserver: ["Source: file/CSV analysis path", "Feeds file-based detection workflows"],
    router: ["Network junction for routed packets", "Forwarding toward switch/capture path"],
    switch: ["Local distribution point", "Mirrors traffic toward capture + model branches"],
    capture: ["Tool: live and continuous capture", "Supports quick/custom and continuous capture jobs"],
    deepScan: ["Tool: deep scan engine", "Performs multi-pass live/file inspection"],
    cnn: ["Engine: SecIDS-CNN model", "Runs realtime or file-based threat classification"],
    countermeasure: ["Action: mitigation stage", "Deploys defensive responses when enabled"],
    reports: ["Output: reports and result artifacts", "Includes audit/history and threat reports"],
  };

  if (String(nodeId).startsWith("peer-")) {
    const index = Number(String(nodeId).split("peer-")[1]);
    const peer = Number.isNaN(index) ? null : state.realtimeDevices[index];
    if (peer) {
      const listStatus = getListStatus(peer);
      return [
        `Peer IP: ${peer.ip || "unknown"}`,
        `MAC: ${peer.mac || "unknown"}`,
        `State: ${peer.state || "unknown"}`,
        `List Status: ${listStatus}`,
        `Interface: ${peer.interface || state.activeInterface}`,
        ...generic,
      ];
    }
  }

  if (String(nodeId).startsWith("app-")) {
    const appKey = String(nodeId).replace("app-", "");
    const app = (surface.apps || []).find((item) => String(item.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-") === appKey);
    if (app) {
      return [
        `Category: ${app.category || "unknown"}`,
        `Instances: ${app.count || 0}`,
        `PIDs: ${(app.pids || []).join(", ") || "-"}`,
        `Command: ${app.command || "-"}`,
        ...generic,
      ];
    }
  }

  if (String(nodeId).startsWith("vector-")) {
    const vector = String(nodeId).replace("vector-", "");
    const related = (surface.access_paths || []).filter((item) => String(item.vector || "") === vector);
    return [
      `Vector: ${vector}`,
      `Active paths: ${related.length}`,
      `Example: ${related[0]?.path || "none"}`,
      ...generic,
    ];
  }

  if (String(nodeId) === "threat") {
    const signals = (threat.signals || []).slice(0, 4);
    return [
      `Severity: ${threatSeverity}`,
      `Recommended response: ${threat.recommended_response || "monitor"}`,
      ...(signals.length ? signals : ["No active threat signals"]),
      ...generic,
    ];
  }

  return [...(byNode[nodeId] || []), ...generic];
}

function renderContextPopup(title, text) {
  if (!contextPopupTitle || !contextPopupBody || !contextPopupPanel) {
    return;
  }

  contextPopupTitle.textContent = title;
  contextPopupBody.textContent = text;
  contextPopupPanel.classList.toggle("technical", state.popupMode === "technical");
}

function getPopupTopic(target) {
  if (!target) {
    return "overview";
  }

  if (target.closest("#topology-layer") || target.closest(".topology-node")) {
    return "topology";
  }
  if (target.closest(".mode-switch") || target.id === "mode-realtime" || target.id === "mode-simulation") {
    return "mode-switch";
  }
  if (target.closest("#simulation-panel") || target.id === "launch-simulation") {
    return "simulation";
  }
  if (target.closest("#device-strip") || target.closest("#model-chooser-panel")) {
    return "surface-controls";
  }
  if (target.closest("#menu-list") || target.closest(".action-box")) {
    return "actions";
  }
  if (target.closest("#logs-output") || target.closest(".operation-progress") || target.id === "job-status") {
    return "logs";
  }
  if (target.closest("#settings-form") || target.id === "settings-save") {
    return "settings";
  }
  if (target.closest(".packetlogs-panel") || target.id === "packet-capture-start" || target.id === "packet-capture-stop") {
    return "packet-log";
  }
  if (target.closest(".toolbar")) {
    return "toolbar";
  }
  if (target.closest(".history-table-wrap") || target.closest("#audit-body") || target.closest("#history-body")) {
    return "history-audit";
  }
  if (target.closest("#users-body") || target.closest("[data-access='admin']")) {
    return "users";
  }
  if (target.closest("#models-body") || target.closest("#model-register-btn") || target.closest("#models-sync")) {
    return "models";
  }
  return "overview";
}

function getPopupText(topic) {
  const onboarding = {
    overview: [
      "Guided Popup: New User",
      "This panel explains every area you hover over. It tells you what the control is, how it works, and why the platform uses it during detection and response.",
    ],
    topology: [
      "Control Surface Overview",
      "This is a live map of your defense pipeline. Packet traces move along cables so you can visually follow where traffic starts, where it is analyzed, and where responses are applied.",
    ],
    "mode-switch": [
      "Realtime vs Simulation",
      "Realtime watches actual interface traffic. Simulation creates safe synthetic attack traffic so you can train and verify workflows without touching production traffic.",
    ],
    simulation: [
      "Simulation Lab",
      "Set the architecture, attack profile, and duration here. The system runs a safe scenario to show behavior, test response logic, and optionally build a new model.",
    ],
    "surface-controls": [
      "Quick Surface Controls",
      "These buttons give fast access to model selection, countermeasure mode, and view reset. They are designed for rapid adjustments while monitoring packets.",
    ],
    actions: [
      "Command Actions",
      "Choose a command category, then pick an action card and run it with parameters. Each action becomes a tracked job with logs and status updates.",
    ],
    logs: [
      "Execution Logs",
      "This area shows what the system is doing right now and whether tasks pass or fail. It helps you confirm behavior and quickly troubleshoot.",
    ],
    settings: [
      "Settings Panel",
      "Use settings to save your preferred interface, capture behavior, and UI layout. Saved settings are reused so your daily workflow is faster.",
    ],
    "packet-log": [
      "Packet Log Workspace",
      "Action Log shows workflow events, and Packet Log shows traffic rows. Start/Pause/Stop lets you control packet collection while keeping visibility of threats.",
    ],
    toolbar: [
      "Top Toolbar",
      "This bar shows time, role, scheduler, queue, and session controls. It is the fastest way to manage runtime operations and authentication context.",
    ],
    "history-audit": [
      "History and Audit",
      "History helps rerun prior commands. Audit tracks who did what and whether actions were allowed or blocked for accountability.",
    ],
    users: [
      "User Administration",
      "Admins can create users, set roles, and reset credentials. This keeps access separated by responsibility and reduces operational risk.",
    ],
    models: [
      "Model Registry",
      "Model tools keep detection artifacts organized. Refresh/sync/register helps ensure live detection is using the right model version.",
    ],
  };

  const technical = {
    overview: [
      "Guided Popup: Technical",
      "Context engine maps hovered selectors to subsystem docs and runtime state. Use this to correlate UI controls with API surfaces, queue behavior, and model execution paths.",
    ],
    topology: [
      "Control Surface Telemetry",
      "Topology renders `controlSurfaceRealtime` devices/apps/vectors plus inferred links. Cisco-style cable paths include directional packet particles to indicate source-to-target packet traversal.",
    ],
    "mode-switch": [
      "Mode Runtime Semantics",
      "`realtime` polls live endpoints and job queue signals every second. `simulation` activates safe synthetic traffic with payload fields like `architecture_type`, `attacker_profile`, and retrain toggle.",
    ],
    simulation: [
      "Simulation Pipeline",
      "Submitting simulation posts to `/api/simulation/run` with deterministic seed/intensity parameters. Retrain mode extends flow to model handoff and registry visibility.",
    ],
    "surface-controls": [
      "Surface Control Hooks",
      "Buttons dispatch `data-device-action` handlers for model chooser, countermeasure mode, server jump, and topology reset. State syncs through settings endpoints and `refreshSystemInfo()`.",
    ],
    actions: [
      "Action Dispatcher",
      "Action cards are generated from `/api/menu`. Run submits `/api/run` with action id, params, mode, and timeout; status transitions are polled via `/api/jobs/{id}`.",
    ],
    logs: [
      "Job Telemetry",
      "Progress bar derives status plus stage markers (`STAGE A-D`) parsed from logs. Terminal states trigger notifications, history refresh, and packet/action log refresh.",
    ],
    settings: [
      "Settings Persistence",
      "Settings form serializes scalar and bool values to `/api/settings`. Values propagate to capture policy, countermeasure mode UI sync, and default run parameters.",
    ],
    "packet-log": [
      "Packet/Action Data Planes",
      "Action logs load from `/api/packet-logs`; packet rows load from `/api/packet-flow`. Row classes encode protocol heuristics and model/list-status overlays for triage.",
    ],
    toolbar: [
      "Runtime Control Plane",
      "Toolbar controls auth/session, scheduler, queue, API token, and viewport scaling. State indicators are refreshed from `/api/system` with role-aware visibility.",
    ],
    "history-audit": [
      "Forensics and Replay",
      "History reruns replay command strings through `/api/history/rerun`; audit filters query `/api/audit` with role/status/event/search dimensions for traceability.",
    ],
    users: [
      "RBAC Management",
      "Admin table actions call `/api/auth/users` endpoints for create/role/reset/delete. Password age and rotation flags enforce policy and first-login hardening.",
    ],
    models: [
      "Model Governance",
      "Registry view consumes `/api/models` plus `/api/models/db-status`. Sync/register operations preserve source metadata and update live selection options.",
    ],
  };

  const source = state.popupMode === "technical" ? technical : onboarding;
  return source[topic] || source.overview;
}

function refreshPopupModeUI() {
  if (!popupModeToggleBtn || !popupModePill || !contextPopupPanel) {
    return;
  }

  const onboardingMode = state.popupMode !== "technical";
  popupModeToggleBtn.textContent = onboardingMode ? "Popup Mode: New User" : "Popup Mode: Technical";
  popupModePill.textContent = onboardingMode ? "mode: onboarding" : "mode: technical";
  contextPopupPanel.classList.toggle("technical", !onboardingMode);
}

function updateContextPopupForTarget(target) {
  const topic = getPopupTopic(target);
  const [title, text] = getPopupText(topic);
  renderContextPopup(title, text);
}

function initContextPopupHandlers() {
  const interactiveSelector =
    "button, input, select, textarea, .menu-item, .action-card, .topology-node, .insight-panel, .timeline, .device-strip";

  document.addEventListener("mouseover", (event) => {
    const target = event.target.closest(interactiveSelector);
    if (!target) {
      return;
    }
    updateContextPopupForTarget(target);
  });

  document.addEventListener("focusin", (event) => {
    const target = event.target.closest(interactiveSelector);
    if (!target) {
      return;
    }
    updateContextPopupForTarget(target);
  });
}

function buildRealtimeTopologyModel() {
  const distributeLane = (count, minY = 16, maxY = 84) => {
    if (!count) {
      return [];
    }
    if (count === 1) {
      return [50];
    }
    const span = Math.max(10, maxY - minY);
    const step = span / (count - 1);
    return Array.from({ length: count }, (_, index) => Math.round((minY + step * index) * 10) / 10);
  };

  const surface = state.controlSurfaceRealtime || {};
  const interfaceName = surface.active_interface || state.activeInterface || state.settings?.last_interface || "eth0";
  const peers = (state.realtimeDevices || []).slice(0, 6);
  const apps = (surface.apps || []).slice(0, 4);
  const vectors = (surface.vectors || []).slice(0, 4);
  const threatSeverity = String(surface?.threat?.severity || "low");

  const coreNodes = [
    { id: "endpoint", label: `Host (${interfaceName})`, icon: "💻", x: 24, y: 52 },
    { id: "capture", label: "Capture", icon: "📡", x: 60, y: 52 },
    { id: "cnn", label: "CNN Model", icon: "🧠", x: 78, y: 40 },
    {
      id: "threat",
      label: `Threat (${threatSeverity})`,
      icon: threatSeverity === "high" ? "🚨" : threatSeverity === "medium" ? "⚠️" : "✅",
      x: 78,
      y: 66,
      statusClass: threatSeverity === "high" ? "blacklist" : threatSeverity === "medium" ? "greylist" : "whitelist",
    },
    { id: "reports", label: "Reports", icon: "📊", x: 94, y: 52 },
  ];

  const peerLane = distributeLane(peers.length, 18, 82);
  const peerNodes = peers.map((peer, index) => {
    const y = peerLane[index] || 50;
    const statusClass = getDeviceColorClass(peer);
    const icon = statusClass === "whitelist" ? "🟢" : statusClass === "intruder" ? "🔴" : statusClass === "blacklist" ? "🟥" : statusClass === "greylist" ? "🟡" : "⚪";
    return {
      id: `peer-${index}`,
      label: peer.ip || `peer-${index + 1}`,
      icon,
      x: 8,
      y,
      statusClass,
    };
  });

  const appLane = distributeLane(apps.length, 22, 78);
  const appNodes = apps.map((app, index) => {
    const normalized = String(app.name || `app-${index + 1}`).toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const category = String(app.category || "system");
    const y = appLane[index] || 50;
    const icon = category === "browser" ? "🌐" : category === "email" ? "✉️" : category === "usb" ? "🔌" : "⚙️";
    return {
      id: `app-${normalized}`,
      label: app.name || "app",
      icon,
      x: 40,
      y,
      statusClass: category === "usb" ? "greylist" : "unknown",
    };
  });

  const vectorLane = distributeLane(vectors.length, 24, 76);
  const vectorNodes = vectors.map((vector, index) => {
    const normalized = String(vector || "network").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const y = vectorLane[index] || 50;
    const icon = normalized === "web" ? "🕸️" : normalized === "email" ? "📧" : normalized === "usb" ? "🧷" : "🔗";
    return {
      id: `vector-${normalized}`,
      label: String(vector || "network").toUpperCase(),
      icon,
      x: 50,
      y,
      statusClass: normalized === "usb" ? "greylist" : "unknown",
    };
  });

  const nodes = [...peerNodes, ...appNodes, ...vectorNodes, ...coreNodes];
  const connections = [
    ...peerNodes.map((node) => [node.id, "endpoint"]),
    ...appNodes.map((node) => ["endpoint", node.id]),
    ...vectorNodes.map((node) => [node.id, "capture"]),
    ...appNodes.map((node, idx) => {
      const vectorNode = vectorNodes[idx % (vectorNodes.length || 1)];
      return vectorNode ? [node.id, vectorNode.id] : [node.id, "capture"];
    }),
    ["endpoint", "capture"],
    ["capture", "cnn"],
    ["cnn", "threat"],
    ["capture", "threat"],
    ["threat", "reports"],
    ["capture", "reports"],
    ["cnn", "reports"],
  ];

  return { nodes, connections };
}

function getTopologyModel() {
  if (state.mode === "simulation") {
    return { nodes: TOPOLOGY_NODE_DATA, connections: TOPOLOGY_CONNECTIONS };
  }
  return buildRealtimeTopologyModel();
}

function getVisibleTopologyNodes() {
  return getTopologyModel().nodes;
}

function getVisibleTopologyConnections(visibleNodes) {
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const allConnections = getTopologyModel().connections;
  return allConnections.filter(([source, target]) => visibleIds.has(source) && visibleIds.has(target));
}

function markDetectedNodes(nodeIds = []) {
  nodeIds.forEach((nodeId) => {
    if (TOPOLOGY_NODE_DATA.some((node) => node.id === nodeId)) {
      state.detectedNodes.add(nodeId);
    }
  });
}

function inferDetectedNodesFromText(textBlob = "") {
  const text = String(textBlob || "").toLowerCase();
  const inferred = [];

  if (/(iot|sensor|telemetry)/.test(text)) inferred.push("iot");
  if (/(device|host|endpoint|client)/.test(text)) inferred.push("endpoint");
  if (/(file|csv|dataset|archive)/.test(text)) inferred.push("fileserver");
  if (/(router|gateway)/.test(text)) inferred.push("router");
  if (/(switch|bridge)/.test(text)) inferred.push("switch");
  if (/(capture|pcap|wireshark|iface|interface)/.test(text)) inferred.push("capture");
  if (/(deep\s*scan|multi-pass)/.test(text)) inferred.push("deepScan");
  if (/(cnn|model|inference|predict|detection)/.test(text)) inferred.push("cnn");
  if (/(countermeasure|block|iptables|mitigation)/.test(text)) inferred.push("countermeasure");
  if (/(report|result|audit)/.test(text)) inferred.push("reports");

  markDetectedNodes(inferred);
}

function inferDetectedNodesFromJob(job) {
  if (!job) {
    return;
  }

  if (job.action_id && ACTION_NODE_HINTS[job.action_id]) {
    markDetectedNodes(ACTION_NODE_HINTS[job.action_id]);
  }

  const combined = [job.command || "", ...(job.logs || [])].join("\n");
  inferDetectedNodesFromText(combined);
}

function renderTopology() {
  if (!topologyNodes || !topologyLinks) {
    return;
  }

  const visibleNodes = getVisibleTopologyNodes();
  const visibleConnections = getVisibleTopologyConnections(visibleNodes);

  if (!visibleNodes.length) {
    topologyNodes.innerHTML = `<div class="topology-empty">No realtime devices detected yet. Run capture/detection jobs or switch to Simulation.</div>`;
    topologyLinks.innerHTML = "";
    return;
  }

  topologyNodes.innerHTML = visibleNodes
    .map(
      (node) => `
      <div class="topology-node ${node.statusClass || ""}" data-node-id="${node.id}" style="left:${node.x}%;top:${node.y}%;">
        <div class="topology-node-image">${node.icon}</div>
        <div class="topology-node-label">${node.label}</div>
      </div>
    `,
    )
    .join("");

  drawTopologyConnections(visibleConnections);
  updateTopologyTrafficState();
  applyTopologyPan();

  topologyNodes.querySelectorAll(".topology-node").forEach((nodeElement) => {
    nodeElement.addEventListener("mouseenter", (event) => {
      const nodeId = event.currentTarget.dataset.nodeId;
      const node = visibleNodes.find((item) => item.id === nodeId);
      const detailLines = getNodeInfo(nodeId);
      const details = detailLines.map((line) => `<div>• ${line}</div>`).join("");
      const intro =
        state.popupMode === "technical"
          ? `<div>Signal Path: ${nodeId} • Runtime state from control surface telemetry.</div>`
          : `<div>This node shows one step in traffic monitoring and response.</div>`;
      topologyTooltip.innerHTML = `<strong>${node?.label || nodeId}</strong>${intro}${details}`;
      topologyTooltip.classList.remove("hidden");
      updateContextPopupForTarget(event.currentTarget);
    });

    nodeElement.addEventListener("mousemove", (event) => {
      if (!topologyLayer || !topologyTooltip) {
        return;
      }
      const layerRect = topologyLayer.getBoundingClientRect();
      const x = event.clientX - layerRect.left + 10;
      const y = event.clientY - layerRect.top + 10;
      topologyTooltip.style.left = `${Math.min(x, layerRect.width - 220)}px`;
      topologyTooltip.style.top = `${Math.min(y, layerRect.height - 140)}px`;
    });

    nodeElement.addEventListener("mouseleave", () => {
      topologyTooltip.classList.add("hidden");
    });
  });
}

function applyTopologyPan() {
  if (!topologyNodes || !topologyLinks) {
    return;
  }
  const x = state.topologyPan?.x || 0;
  const y = state.topologyPan?.y || 0;
  const translate = `translate(${x}px, ${y}px)`;
  topologyNodes.style.transform = translate;
  topologyLinks.style.transform = translate;
}

function initTopologyPanHandlers() {
  if (!topologyLayer) {
    return;
  }

  const getPanLimits = () => {
    const rect = topologyLayer.getBoundingClientRect();
    const limitX = Math.max(180, Math.round(rect.width * 0.42));
    const limitY = Math.max(140, Math.round(rect.height * 0.42));
    return { limitX, limitY };
  };

  topologyLayer.addEventListener("mousedown", (event) => {
    if (event.button !== 0) {
      return;
    }
    state.topologyDrag.active = true;
    state.topologyDrag.lastX = event.clientX;
    state.topologyDrag.lastY = event.clientY;
    topologyLayer.style.cursor = "grabbing";
  });

  window.addEventListener("mousemove", (event) => {
    if (!state.topologyDrag.active) {
      return;
    }
    const dx = event.clientX - state.topologyDrag.lastX;
    const dy = event.clientY - state.topologyDrag.lastY;
    state.topologyDrag.lastX = event.clientX;
    state.topologyDrag.lastY = event.clientY;
    const { limitX, limitY } = getPanLimits();
    state.topologyPan.x = Math.max(-limitX, Math.min(limitX, (state.topologyPan.x || 0) + dx));
    state.topologyPan.y = Math.max(-limitY, Math.min(limitY, (state.topologyPan.y || 0) + dy));
    applyTopologyPan();
  });

  window.addEventListener("mouseup", () => {
    if (!state.topologyDrag.active) {
      return;
    }
    state.topologyDrag.active = false;
    topologyLayer.style.cursor = "grab";
  });
}

function resetTopologyView() {
  state.topologyPan.x = 0;
  state.topologyPan.y = 0;
  applyTopologyPan();
}

function drawTopologyConnections() {
  const visibleConnections = arguments[0] || getVisibleTopologyConnections(getVisibleTopologyNodes());
  if (!topologyLinks || !topologyNodes || !topologyLayer) {
    return;
  }

  const layerRect = topologyLayer.getBoundingClientRect();
  const status = getTrafficState();

  const points = {};
  topologyNodes.querySelectorAll(".topology-node").forEach((nodeElement) => {
    const rect = nodeElement.getBoundingClientRect();
    points[nodeElement.dataset.nodeId] = {
      x: ((rect.left + rect.width / 2 - layerRect.left) / layerRect.width) * 100,
      y: ((rect.top + rect.height / 2 - layerRect.top) / layerRect.height) * 100,
    };
  });

  const duration = status === "live" ? "1.6s" : status === "paused" ? "3.4s" : "0s";
  const renderFlowParticles = (pathId, lane) => {
    if (status === "stopped") {
      return "";
    }

    const count = status === "live" ? 2 : 1;
    return Array.from({ length: count }, (_, index) => {
      const begin = `${(index * 0.55 + lane * 0.2).toFixed(2)}s`;
      return `
        <circle class="topology-flow-dot ${status}" r="${status === "live" ? "0.32" : "0.26"}">
          <animateMotion dur="${duration}" begin="${begin}" repeatCount="indefinite" rotate="auto">
            <mpath href="#${pathId}" />
          </animateMotion>
        </circle>
      `;
    }).join("");
  };

  topologyLinks.innerHTML = visibleConnections
    .map(([source, target], index) => {
      const p1 = points[source];
      const p2 = points[target];
      if (!p1 || !p2) {
        return "";
      }

      const dx = p2.x - p1.x;
      const curveAmount = Math.max(2.2, Math.min(5.8, Math.abs(dx) * 0.22));
      const curveDirection = index % 2 === 0 ? 1 : -1;
      const c1x = p1.x + dx * 0.25;
      const c2x = p1.x + dx * 0.75;
      const c1y = p1.y + curveAmount * curveDirection;
      const c2y = p2.y - curveAmount * curveDirection;
      const pathData = `M ${p1.x} ${p1.y} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p2.x} ${p2.y}`;
      const pathId = `topology-link-path-${index}`;

      return `
        <g class="topology-cable-group" data-source="${source}" data-target="${target}">
          <path id="${pathId}" class="topology-cable-sheath ${status}" d="${pathData}" />
          <path class="topology-cable-core ${status}" d="${pathData}" />
          ${renderFlowParticles(pathId, index)}
        </g>
      `;
    })
    .join("");
}

function updateTopologyTrafficState() {
  if (!topologyNodes) {
    return;
  }

  if (!topologyNodes.querySelector(".topology-node")) {
    return;
  }

  const stateClass = getTrafficState();
  topologyNodes.querySelectorAll(".topology-node").forEach((nodeElement) => {
    nodeElement.classList.remove("live", "paused", "stopped");
    nodeElement.classList.add(stateClass);
  });
  drawTopologyConnections();
}

function renderMenu() {
  menuList.innerHTML = state.menu
    .map(
      (section) => `
      <button class="menu-item ${section.id === state.activeSectionId ? "active" : ""}" data-section-id="${section.id}">
        ${section.icon} ${section.title}
      </button>
    `,
    )
    .join("");

  const activeSection = getActiveSection();
  if (!activeSection) {
    return;
  }

  const actionsHtml = activeSection.actions
    .map(
      (action) => `
      <div class="action-card ${action.id === state.activeActionId ? "active" : ""}" data-action-id="${action.id}">
        <strong>${action.title}</strong><br>
        <small>${action.description}</small>
      </div>
    `,
    )
    .join("");

  actionDescription.innerHTML = actionsHtml;
}

function computeDefaultValue(paramName, fallback) {
  if (Object.prototype.hasOwnProperty.call(state.settings, paramName)) {
    return String(state.settings[paramName] ?? "");
  }
  return fallback || "";
}

function renderActionDetails() {
  const action = getActiveAction();
  const activeSection = getActiveSection();
  if (!action) {
    actionTitle.textContent = "Select an action";
    paramsForm.innerHTML = "";
    runBtn.disabled = true;
    return;
  }

  actionTitle.textContent = action.title;

  if (activeSection?.id === IDENTIFICATION_SECTION_ID) {
    paramsForm.innerHTML = `
      <div class="pill">Use submenu entries to filter list or run Identify.</div>
      <div class="pill">Use control-surface buttons below to add/remove/change-tag and return.</div>
    `;
    runBtn.disabled = true;
    return;
  }

  paramsForm.innerHTML = (action.params || [])
    .map(
      (param) => `
      <label for="param-${param.name}">${param.label}</label>
      <input id="param-${param.name}" name="${param.name}" value="${computeDefaultValue(param.name, param.default)}" ${param.required ? "required" : ""} />
    `,
    )
    .join("");

  paramsForm.innerHTML += `
    <label for="job-timeout">Job Timeout (seconds)</label>
    <input id="job-timeout" name="job_timeout" type="number" value="${state.timeoutSeconds}" min="5" />
  `;

  runBtn.disabled = false;
}

function applyRoleVisibility() {
  const isAdmin = state.auth.role === "admin";
  adminOnlyPanels.forEach((panel) => {
    panel.classList.toggle("hidden", !isAdmin);
  });
}

async function loadAuthSession() {
  const response = await apiFetch("/api/auth/session");
  if (!response.ok) {
    return;
  }
  state.auth = await response.json();
  applyRoleVisibility();
  rolePill.textContent = `role: ${state.auth.role}`;
  userPill.textContent = `user: ${state.auth.username}`;
  if (state.auth.must_change_password) {
    logsOutput.textContent = state.auth.password_rotation_due
      ? "Password expired by rotation policy. Change password now."
      : "Password change is required for this account.";
    jobStatus.textContent = "auth";
  }
  await loadUsers();
}

async function login() {
  const username = (authUserInput?.value || "").trim();
  const password = authPassInput?.value || "";
  if (!username || !password) {
    logsOutput.textContent = "Enter username and password.";
    jobStatus.textContent = "auth";
    return;
  }

  const response = await apiFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Login failed";
    jobStatus.textContent = "auth";
    return;
  }

  if (authPassInput) {
    authPassInput.value = "";
  }
  await loadAuthSession();
  logsOutput.textContent = data.must_change_password
    ? `Logged in as ${data.username} (${data.role}). Password change required.`
    : `Logged in as ${data.username} (${data.role})`;
  jobStatus.textContent = "auth";
}

async function changePassword() {
  const currentPassword = authPassInput?.value || "";
  const newPassword = authNewPassInput?.value || "";

  if (!currentPassword || !newPassword) {
    logsOutput.textContent = "Enter current and new password.";
    jobStatus.textContent = "auth";
    return;
  }

  const response = await apiFetch("/api/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Password change failed";
    jobStatus.textContent = "auth";
    return;
  }

  if (authNewPassInput) {
    authNewPassInput.value = "";
  }
  if (authPassInput) {
    authPassInput.value = "";
  }
  await loadAuthSession();
  logsOutput.textContent = "Password changed successfully.";
  jobStatus.textContent = "auth";
}

async function logout() {
  const response = await apiFetch("/api/auth/logout", { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Logout failed";
    jobStatus.textContent = "auth";
    return;
  }

  window.location.href = state.system?.login_path || "/login";
}

async function loadMenu() {
  const response = await apiFetch("/api/menu");
  const data = await response.json();
  state.menu = data.menu || [];

  if (state.menu.length) {
    state.activeSectionId = state.menu[0].id;
    if (state.menu[0].actions.length) {
      state.activeActionId = state.menu[0].actions[0].id;
    }
  }

  renderMenu();
  renderActionDetails();
}

async function loadSettings() {
  const response = await apiFetch("/api/settings");
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  state.settings = data.settings || {};
  state.packetCapture = data.packet_capture || state.packetCapture;
  state.settings.countermeasure_mode =
    String(state.settings.countermeasure_mode || "active").toLowerCase() === "passive" ? "passive" : "active";
  renderSettingsPanel();
  renderPacketCaptureStatus();
  await enforcePacketCapturePolicy();
}

function renderSettingsPanel() {
  if (!settingsForm) {
    return;
  }

  settingsForm.querySelectorAll("[name]").forEach((field) => {
    const key = field.getAttribute("name");
    if (!key) {
      return;
    }
    const value = state.settings[key];
    const type = String(field.getAttribute("data-setting-type") || field.type || "").toLowerCase();
    if (type === "bool" || field.type === "checkbox") {
      field.checked = Boolean(value);
      return;
    }
    field.value = value ?? "";
  });

  syncCountermeasureModeUI();
  renderLiveModelSelection();
}

function syncCountermeasureModeUI() {
  const normalized =
    String(state.settings?.countermeasure_mode || "active").toLowerCase() === "passive" ? "passive" : "active";
  state.settings.countermeasure_mode = normalized;
  if (simCountermeasureMode) {
    simCountermeasureMode.value = normalized;
  }
}

function renderLiveModelSelection() {
  if (!liveModelCurrent) {
    return;
  }

  const selectedMode = String(state.settings?.live_model_mode || "auto").toLowerCase() === "manual" ? "manual" : "auto";
  const selectedPath = state.settings?.live_model_path || "";
  const selectedBackend = state.settings?.live_backend || (selectedPath ? "auto" : "default");
  liveModelCurrent.textContent = selectedMode === "manual"
    ? (selectedPath ? `live model: manual ${selectedPath} (${selectedBackend})` : "live model: manual selection pending")
    : "live model: auto-detect";

  if (liveModelSelect) {
    liveModelSelect.value = selectedPath;
    liveModelSelect.disabled = selectedMode !== "manual";
  }

  if (liveModelModeAutoBtn) {
    liveModelModeAutoBtn.classList.toggle("active-switch", selectedMode === "auto");
  }

  if (liveModelModeManualBtn) {
    liveModelModeManualBtn.classList.toggle("active-switch", selectedMode === "manual");
  }

  if (modelChooserPanel) {
    modelChooserPanel.classList.toggle("hidden", !state.liveModelChooserVisible);
  }
}

function populateLiveModelOptions() {
  if (!liveModelSelect) {
    return;
  }

  const options = ['<option value="">Auto Default (built-in)</option>'];
  (state.models || []).forEach((model) => {
    const path = model.path || "";
    if (!path) {
      return;
    }
    options.push(`<option value="${path}">${model.model_name || path} (${model.model_format || "model"})</option>`);
  });

  liveModelSelect.innerHTML = options.join("");
  liveModelSelect.value = state.settings?.live_model_path || "";
}

async function loadHistoryPreview() {
  const response = await apiFetch("/api/history?limit=12");
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const history = data.history || [];
  if (state.mode === "realtime") {
    history.slice(0, 5).forEach((entry) => inferDetectedNodesFromText(entry.command || ""));
    renderTopology();
  }
  renderHistoryTable(history);
  logsOutput.textContent = history.length
    ? history.map((entry) => `${entry.timestamp} | ${entry.source} | ${entry.command}`).join("\n")
    : "No history entries.";
  jobStatus.textContent = "history";
}

function renderHistoryTable(history) {
  if (!historyBody) {
    return;
  }
  historyBody.innerHTML = history
    .map(
      (entry, index) => `
      <tr>
        <td>${entry.timestamp || "-"}</td>
        <td>${entry.source || "-"}</td>
        <td>${entry.command || "-"}</td>
        <td><button class="btn btn-compact history-rerun" data-history-index="${index}">Rerun</button></td>
      </tr>
    `,
    )
    .join("");
}

async function saveSettingsFromPanel() {
  const collectedSettings = {};
  settingsForm.querySelectorAll("[name]").forEach((field) => {
    const key = field.getAttribute("name");
    if (!key) {
      return;
    }
    const type = String(field.getAttribute("data-setting-type") || field.type || "").toLowerCase();
    if (type === "bool" || field.type === "checkbox") {
      collectedSettings[key] = Boolean(field.checked);
      return;
    }
    collectedSettings[key] = String(field.value ?? "").trim();
  });

  const payload = {
    settings: collectedSettings,
  };

  const response = await apiFetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Failed to save settings.";
    jobStatus.textContent = "error";
    return;
  }

  state.settings = data.settings || state.settings;
  renderSettingsPanel();
  logsOutput.textContent = (data.logs || ["Settings saved"]).join("\n");
  jobStatus.textContent = "settings";
}

async function saveLiveModelSelection() {
  const selectedMode = String(state.settings?.live_model_mode || "auto").toLowerCase() === "manual" ? "manual" : "auto";
  const modelPath = (liveModelSelect?.value || "").trim();
  const backend = selectedMode !== "manual" || !modelPath
    ? ""
    : /\.(pkl|pickle|joblib)$/i.test(modelPath)
      ? "unified"
      : "tf";

  const response = await apiFetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      settings: {
        live_model_mode: selectedMode,
        live_model_path: modelPath,
        live_backend: backend,
      },
    }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Failed to choose live model.";
    jobStatus.textContent = "models";
    return;
  }

  state.settings = data.settings || state.settings;
  renderLiveModelSelection();
  notify(
    "Model Selection",
    selectedMode === "manual" ? (modelPath || "Manual mode saved") : "Auto-detect mode enabled",
    "success",
    2600,
  );
}

function setLiveModelMode(mode) {
  state.settings = state.settings || {};
  state.settings.live_model_mode = mode === "manual" ? "manual" : "auto";
  renderLiveModelSelection();
}

async function toggleCountermeasureMode() {
  const currentMode =
    String(state.settings?.countermeasure_mode || "active").toLowerCase() === "passive" ? "passive" : "active";
  const nextMode = currentMode === "active" ? "passive" : "active";

  const response = await apiFetch("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: { countermeasure_mode: nextMode } }),
  });
  const data = await response.json();

  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Failed to update countermeasure mode.";
    jobStatus.textContent = "error";
    notify("Countermeasure Mode", "Update failed", "error", 2200);
    return;
  }

  state.settings = data.settings || state.settings;
  syncCountermeasureModeUI();
  state.packetCapture = data.packet_capture || state.packetCapture;
  renderPacketCaptureStatus();
  await enforcePacketCapturePolicy();
  renderDeviceStrip();
  notify("Countermeasure Mode", `Switched to ${state.settings.countermeasure_mode}`, "success", 1800);
}

async function schedulerControl(action) {
  const response = await apiFetch(`/api/scheduler/${action}`, { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || data.message || "Scheduler action failed";
    jobStatus.textContent = "error";
    return;
  }
  logsOutput.textContent = data.message;
  jobStatus.textContent = `scheduler-${data.scheduler}`;
  await refreshSystemInfo();
}

async function queueControl(action, payload = null) {
  const response = await apiFetch(`/api/queue/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Queue control failed";
    jobStatus.textContent = "error";
    return;
  }
  logsOutput.textContent = `Queue ${action}: ok`;
  jobStatus.textContent = `queue-${action}`;
  await refreshSystemInfo();
}

async function rerunHistoryCommand(command) {
  const response = await apiFetch("/api/history/rerun", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, mode: state.mode, timeout_seconds: state.timeoutSeconds }),
  });
  const data = await response.json();
  if (!response.ok) {
    logsOutput.textContent = `Error: ${data.error || "History rerun failed"}`;
    jobStatus.textContent = "error";
    return;
  }
  state.currentJobId = data.job_id;
  logsOutput.textContent = "Waiting for rerun output...";
  jobStatus.textContent = data.status;
}

async function cancelCurrentJob() {
  if (!state.currentJobId) {
    logsOutput.textContent = "No active job selected.";
    return;
  }
  const response = await apiFetch(`/api/jobs/${state.currentJobId}/cancel`, { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || data.message || "Cancel failed";
    jobStatus.textContent = "error";
    return;
  }
  jobStatus.textContent = data.status || "stopping";
  if ((data.status || "") === "stopping") {
    logsOutput.textContent = "Stop requested. Finalizing task from currently collected data...";
  }
  updateJobControlButtons(data.status || "stopping");
  await pollJob();
}

async function pauseCurrentJob() {
  if (!state.currentJobId) {
    logsOutput.textContent = "No active job selected.";
    return;
  }
  const response = await apiFetch(`/api/jobs/${state.currentJobId}/pause`, { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || data.message || "Pause failed";
    jobStatus.textContent = "error";
    return;
  }
  jobStatus.textContent = data.status || "paused";
  logsOutput.textContent = "Task paused.";
  updateJobControlButtons(data.status || "paused");
  await pollJob();
}

async function resumeCurrentJob() {
  if (!state.currentJobId) {
    logsOutput.textContent = "No active job selected.";
    return;
  }
  const response = await apiFetch(`/api/jobs/${state.currentJobId}/resume`, { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || data.message || "Resume failed";
    jobStatus.textContent = "error";
    return;
  }
  jobStatus.textContent = data.status || "running";
  logsOutput.textContent = "Task resumed.";
  updateJobControlButtons(data.status || "running");
  await pollJob();
}

function updateJobControlButtons(status = "idle") {
  if (jobPauseBtn) {
    jobPauseBtn.disabled = status !== "running";
  }
  if (jobResumeBtn) {
    jobResumeBtn.disabled = status !== "paused";
  }
  if (jobCancelBtn) {
    jobCancelBtn.disabled = ["idle", "completed", "failed", "cancelled", "timeout"].includes(status);
  }
  if (jobRetryBtn) {
    jobRetryBtn.disabled = !["failed", "cancelled", "timeout", "completed"].includes(status);
  }
}

async function retryCurrentJob() {
  if (!state.currentJobId) {
    logsOutput.textContent = "No job available to retry.";
    return;
  }
  const response = await apiFetch(`/api/jobs/${state.currentJobId}/retry`, { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Retry failed";
    jobStatus.textContent = "error";
    return;
  }
  state.currentJobId = data.job_id;
  logsOutput.textContent = "Retry queued...";
  jobStatus.textContent = data.status;
}

async function autoRetryIfSudoBlockedJob() {
  if (!state.currentJobId) {
    return false;
  }

  const response = await apiFetch(`/api/jobs/${state.currentJobId}`);
  if (!response.ok) {
    return false;
  }

  const job = await response.json();
  const isTerminal = ["failed", "timeout", "cancelled"].includes(job.status);
  const logBlob = (job.logs || []).join("\n");
  const sudoBlocked = /No cached sudo password|sudo: a password is required|a terminal is required to read the password/i.test(
    logBlob,
  );

  if (!isTerminal || !sudoBlocked) {
    return false;
  }

  const retryResponse = await apiFetch(`/api/jobs/${state.currentJobId}/retry`, { method: "POST" });
  const retryData = await retryResponse.json();
  if (!retryResponse.ok || !retryData.ok) {
    return false;
  }

  state.currentJobId = retryData.job_id;
  state.lastJobStatus = retryData.status;
  logsOutput.textContent = "[ok] Sudo password accepted. Relaunching the blocked command...";
  jobStatus.textContent = retryData.status || "queued";
  setGlobalProgress(retryData.status || "queued", []);
  notify("Sudo Validation", "Blocked command relaunched", "success", 2400);
  return true;
}

function collectParams() {
  const action = getActiveAction();
  if (!action) {
    return {};
  }

  const result = {};
  (action.params || []).forEach((param) => {
    const input = document.getElementById(`param-${param.name}`);
    result[param.name] = input ? input.value.trim() : "";
  });

  const timeoutInput = document.getElementById("job-timeout");
  if (timeoutInput) {
    const parsed = Number(timeoutInput.value);
    if (!Number.isNaN(parsed) && parsed > 0) {
      state.timeoutSeconds = Math.floor(parsed);
    }
  }

  return result;
}

async function runAction() {
  const action = getActiveAction();
  if (!action) {
    return;
  }

  if (IDENTIFICATION_REDIRECT_ACTIONS.has(action.id)) {
    const previousSection = state.activeSectionId;
    state.identification.previousSectionId = previousSection;
    state.activeSectionId = IDENTIFICATION_SECTION_ID;
    const identificationSection = getActiveSection();
    state.activeActionId = identificationSection?.actions?.[0]?.id || null;
    renderMenu();
    renderActionDetails();
    enterIdentificationSection();
    await loadIdentificationListing();
    notify("Identification Listing", "Redirected from legacy list action.", "success", 1800);
    return;
  }

  if (isIdentificationMode()) {
    handleIdentificationActionSelection(action.id);
    return;
  }

  const params = collectParams();
  runBtn.disabled = true;

  const response = await apiFetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action_id: action.id, params, mode: state.mode, timeout_seconds: state.timeoutSeconds }),
  });
  const data = await response.json();

  if (!response.ok) {
    logsOutput.textContent = `Error: ${data.error || "Unknown error"}`;
    jobStatus.textContent = "error";
    runBtn.disabled = false;
    return;
  }

  state.currentJobId = data.job_id;
  logsOutput.textContent = "Waiting for output...";
  jobStatus.textContent = data.status;
  state.lastJobStatus = data.status;
  setGlobalProgress(data.status, []);
  updateJobControlButtons(data.status);
  notify("Job Started", `${action.title} (${data.status})`, "success", 2600);
}

async function runSimulation() {
  if (state.mode !== "simulation") {
    logsOutput.textContent = "Switch to Simulation mode before launching simulation.";
    jobStatus.textContent = "simulation";
    return;
  }

  const payload = {
    architecture_type: (simArchitectureType?.value || "school").trim().toLowerCase(),
    attacker_profile: (simAttackerProfile?.value || "mixed").trim(),
    defender_profile: (simDefenderProfile?.value || "adaptive-ai").trim(),
    countermeasure_mode: (simCountermeasureMode?.value || state.settings?.countermeasure_mode || "active").trim(),
    intensity: (simIntensity?.value || "medium").trim(),
    attackers: Number(simAttackers?.value || 25),
    duration: Number(simDuration?.value || 90),
    seed: Number(simSeed?.value || 42),
    retrain: String(simRetrain?.value || "true") === "true",
    timeout_seconds: state.timeoutSeconds,
  };

  launchSimulationBtn.disabled = true;

  const response = await apiFetch("/api/simulation/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    logsOutput.textContent = `Simulation error: ${data.error || "Unknown error"}`;
    jobStatus.textContent = "error";
    launchSimulationBtn.disabled = false;
    return;
  }

  state.currentJobId = data.job_id;
  state.lastJobStatus = data.status;
  markDetectedNodes(ACTION_NODE_HINTS["simulate-ddos-training-loop"] || []);
  renderTopology();
  logsOutput.textContent = "Simulation queued. Waiting for output...";
  jobStatus.textContent = data.status;
  setGlobalProgress(data.status, []);
  updateJobControlButtons(data.status);
  notify(
    "Simulation Started",
    payload.retrain
      ? "Safe DDoS simulation + model handoff queued"
      : "Safe DDoS simulation queued",
    "success",
    3200,
  );
}

async function pollJob() {
  if (!state.currentJobId) {
    return;
  }

  const response = await apiFetch(`/api/jobs/${state.currentJobId}`);
  if (!response.ok) {
    return;
  }

  const job = await response.json();
  if (state.mode === "realtime") {
    inferDetectedNodesFromJob(job);
    renderTopology();
  }
  logsOutput.textContent = (job.logs || []).join("\n") || "No logs.";
  logsOutput.scrollTop = logsOutput.scrollHeight;
  jobStatus.textContent = job.status;
  setGlobalProgress(job.status, job.logs || []);
  updateJobControlButtons(job.status);

  if (state.lastJobStatus !== job.status) {
    const terminalStates = ["completed", "failed", "cancelled", "timeout"];
    if (terminalStates.includes(job.status)) {
      const tone = job.status === "completed" ? "success" : job.status === "failed" ? "error" : "warn";
      notify("Job Update", `${job.title || "Action"}: ${job.status}`, tone);
    }
    state.lastJobStatus = job.status;
  }

  const stageEvents = parseWorkflowStageEvents(job.logs || []);
  stageEvents.forEach((event) => {
    const tone = event.status === "COMPLETE" ? "success" : "warn";
    notify("Workflow Stage", `${event.stageCode}: ${event.stageName} → ${event.status}`, tone, 3200);
  });

  if (["completed", "failed", "cancelled", "timeout"].includes(job.status)) {
    runBtn.disabled = false;
    if (launchSimulationBtn) {
      launchSimulationBtn.disabled = false;
    }
    if (job.action_id && job.action_id.startsWith("history-")) {
      await loadHistoryPreview();
    }
    await loadActionLogs();
    await loadPacketFlow();
  }
}

async function refreshSystemInfo() {
  if (state.refreshInFlight) {
    state.refreshQueued = true;
    return;
  }

  state.refreshInFlight = true;
  const response = await apiFetch("/api/system");
  try {
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    state.system = data;
    state.packetCapture = data.packet_capture || state.packetCapture;
    schedulerPill.textContent = `scheduler: ${data.scheduler}`;
    rolePill.textContent = `role: ${data.current_role || state.auth.role}`;
    userPill.textContent = `user: ${data.current_user || state.auth.username}`;
    state.auth.role = data.current_role || state.auth.role;
    applyRoleVisibility();
    const queue = data.queue || {};
    queuePill.textContent = `queue: ${queue.running || 0} running / ${queue.pending || 0} pending / max ${queue.max_concurrent || 1}`;
    renderPacketCaptureStatus();
    updateTopologyTrafficState();
    await loadOverview();
    await loadControlSurfaceRealtime();
    if (isIdentificationMode()) {
      await loadIdentificationListing();
    }
  } finally {
    state.refreshInFlight = false;
    if (state.refreshQueued) {
      state.refreshQueued = false;
      setTimeout(() => {
        refreshSystemInfo();
      }, 50);
    }
  }
}

async function loadAuditEvents() {
  const params = new URLSearchParams({
    limit: "40",
    role: (auditRoleFilter?.value || "all").trim() || "all",
    status: (auditStatusFilter?.value || "all").trim() || "all",
    event: (auditEventFilter?.value || "all").trim() || "all",
    search: (auditSearchInput?.value || "").trim(),
  });

  const response = await apiFetch(`/api/audit?${params.toString()}`);
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const events = data.events || [];
  auditBody.innerHTML = events
    .map(
      (event) => `
      <tr>
        <td>${event.timestamp || "-"}</td>
        <td>${event.event || "-"}</td>
        <td>${event.status || "-"}</td>
        <td>${event.role || "-"}</td>
      </tr>
    `,
    )
    .join("");
}

async function exportAuditEvents() {
  const response = await apiFetch("/api/audit/export", { method: "POST" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Audit export failed";
    jobStatus.textContent = "error";
    return;
  }
  logsOutput.textContent = `Audit exported: ${data.path}`;
  jobStatus.textContent = "audit-export";
  await loadAuditEvents();
}

function renderUsersTable() {
  if (!usersBody) {
    return;
  }

  if (state.auth.role !== "admin") {
    usersBody.innerHTML = `<tr><td colspan="5">Admin role required.</td></tr>`;
    return;
  }

  if (!state.users.length) {
    usersBody.innerHTML = `<tr><td colspan="5">No users found.</td></tr>`;
    return;
  }

  usersBody.innerHTML = state.users
    .map((user) => {
      const statusBits = [];
      if (user.must_change_password) {
        statusBits.push("change-required");
      }
      if (user.rotation_due) {
        statusBits.push("rotation-due");
      }
      return `
      <tr>
        <td>${user.username}</td>
        <td>
          <select class="token-input role-select user-role" data-username="${user.username}">
            <option value="guest" ${user.role === "guest" ? "selected" : ""}>guest</option>
            <option value="viewer" ${user.role === "viewer" ? "selected" : ""}>viewer</option>
            <option value="operator" ${user.role === "operator" ? "selected" : ""}>operator</option>
            <option value="admin" ${user.role === "admin" ? "selected" : ""}>admin</option>
          </select>
        </td>
        <td>${user.password_age_days ?? "-"}</td>
        <td>${statusBits.length ? statusBits.join(", ") : "ok"}</td>
        <td>
          <button class="btn btn-compact user-set-role" data-username="${user.username}">Set Role</button>
          <button class="btn btn-compact user-reset-pass" data-username="${user.username}">Reset</button>
          <button class="btn btn-compact user-delete" data-username="${user.username}">Delete</button>
        </td>
      </tr>
    `;
    })
    .join("");
}

async function loadUsers() {
  if (!usersBody) {
    return;
  }

  if (state.auth.role !== "admin") {
    state.users = [];
    renderUsersTable();
    return;
  }

  const response = await apiFetch("/api/auth/users");
  const data = await response.json();
  if (!response.ok) {
    logsOutput.textContent = data.error || "Failed to load users";
    jobStatus.textContent = "auth";
    return;
  }

  state.users = data.users || [];
  renderUsersTable();
}

async function createUser() {
  const username = (userCreateNameInput?.value || "").trim();
  const role = (userCreateRoleInput?.value || "viewer").trim();
  const password = userCreatePassInput?.value || "";

  if (!username) {
    logsOutput.textContent = "Enter a username to create.";
    jobStatus.textContent = "auth";
    return;
  }

  const response = await apiFetch("/api/auth/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, role, password }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "User creation failed";
    jobStatus.textContent = "auth";
    return;
  }

  if (userCreateNameInput) {
    userCreateNameInput.value = "";
  }
  if (userCreatePassInput) {
    userCreatePassInput.value = "";
  }
  logsOutput.textContent = `User created: ${data.user.username}. Temporary password: ${data.temporary_password}`;
  jobStatus.textContent = "auth";
  await loadUsers();
}

async function updateUserRole(username) {
  const roleSelect = usersBody?.querySelector(`.user-role[data-username="${username}"]`);
  const role = (roleSelect?.value || "").trim();
  if (!role) {
    return;
  }

  const response = await apiFetch(`/api/auth/users/${encodeURIComponent(username)}/role`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Role update failed";
    jobStatus.textContent = "auth";
    return;
  }

  logsOutput.textContent = `Role updated for ${username}: ${role}`;
  jobStatus.textContent = "auth";
  await loadAuthSession();
}

async function resetUserPassword(username) {
  const response = await apiFetch(`/api/auth/users/${encodeURIComponent(username)}/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Password reset failed";
    jobStatus.textContent = "auth";
    return;
  }

  logsOutput.textContent = `Password reset for ${username}. Temporary password: ${data.temporary_password}`;
  jobStatus.textContent = "auth";
  await loadUsers();
}

async function deleteUser(username) {
  const response = await apiFetch(`/api/auth/users/${encodeURIComponent(username)}`, { method: "DELETE" });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Delete user failed";
    jobStatus.textContent = "auth";
    return;
  }

  logsOutput.textContent = `User deleted: ${username}`;
  jobStatus.textContent = "auth";
  await loadUsers();
}

function renderModelsTable() {
  if (!modelsBody) {
    return;
  }

  if (!state.models.length) {
    modelsBody.innerHTML = `<tr><td colspan="4">No models registered yet.</td></tr>`;
    return;
  }

  modelsBody.innerHTML = state.models
    .map(
      (model) => `
      <tr>
        <td>${model.model_name || "-"}</td>
        <td>${model.path || "-"}</td>
        <td>${model.model_format || "-"}</td>
        <td>${model.modified_at || "-"}</td>
      </tr>
    `,
    )
    .join("");
}

async function setPacketLogTab(tab = "action") {
  state.activePacketLogTab = tab;
  const showAction = tab !== "packet";

  actionlogsWrap?.classList.toggle("hidden", !showAction);
  packetflowWrap?.classList.toggle("hidden", showAction);
  actionlogsTable?.classList.toggle("hidden", !showAction);
  packetflowTable?.classList.toggle("hidden", showAction);
  showActionLogBtn?.classList.toggle("active-switch", showAction);
  showPacketLogBtn?.classList.toggle("active-switch", !showAction);

  if (showAction) {
    await loadActionLogs();
  } else {
    await loadPacketCaptureStatus();
    await loadPacketFlow();
  }
}

async function loadModelDbStatus() {
  if (!modelsDbPill) {
    return;
  }

  const response = await apiFetch("/api/models/db-status");
  const data = await response.json();
  if (!response.ok) {
    modelsDbPill.textContent = response.status === 403 ? "db: restricted" : "db: unavailable";
    return;
  }

  modelsDbPill.textContent = `db: ${data.total_models || 0} models`;
}

async function loadModels() {
  if (!modelsBody) {
    return;
  }

  const response = await apiFetch("/api/models?limit=80");
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 403) {
      state.models = [];
      modelsBody.innerHTML = `<tr><td colspan="4">Operator role required.</td></tr>`;
      return;
    }
    logsOutput.textContent = data.error || "Failed to load model registry.";
    jobStatus.textContent = "models";
    return;
  }

  state.models = data.models || [];
  renderModelsTable();
  populateLiveModelOptions();
  renderLiveModelSelection();
  await loadModelDbStatus();
}

async function syncModels() {
  const response = await apiFetch("/api/models/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: "webui-manual-sync" }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Model sync failed";
    jobStatus.textContent = "models";
    return;
  }

  logsOutput.textContent = `Model sync complete: ${data.updated}/${data.scanned} updated, total ${data.total_models}`;
  jobStatus.textContent = "models";
  await loadModels();
}

async function registerModelPath() {
  const path = (modelRegisterPathInput?.value || "").trim();
  if (!path) {
    logsOutput.textContent = "Enter a model path to register.";
    jobStatus.textContent = "models";
    return;
  }

  const response = await apiFetch("/api/models/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, source: "webui-manual-register" }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Model register failed";
    jobStatus.textContent = "models";
    return;
  }

  logsOutput.textContent = `Model registered: ${data.model?.path || path}`;
  jobStatus.textContent = "models";
  if (modelRegisterPathInput) {
    modelRegisterPathInput.value = "";
  }
  await loadModels();
}

function setMode(mode) {
  state.mode = mode;
  realtimeBtn.classList.toggle("active", mode === "realtime");
  simulationBtn.classList.toggle("active", mode === "simulation");
  if (simulationPanel) {
    simulationPanel.classList.toggle("hidden", mode !== "simulation");
  }
  if (mode === "simulation") {
    renderSimulationArchitectureSummary();
    markDetectedNodes(TOPOLOGY_NODE_DATA.map((node) => node.id));
  }
  renderTopology();
  updateTopologyTrafficState();
}

function saveApiToken() {
  state.apiToken = (apiTokenInput?.value || "").trim();
  localStorage.setItem("secids_api_token", state.apiToken);
  logsOutput.textContent = state.apiToken ? "API token saved." : "API token cleared.";
  jobStatus.textContent = "token";
}

function attachPressHighlights() {
  const highlightSelector = ".btn, .menu-item, .action-card, .mode-btn";
  const pressedClass = "pressed-highlight";
  let lastSelectedButton = null;

  document.addEventListener("click", (event) => {
    const target = event.target.closest(highlightSelector);
    if (!target) {
      return;
    }

    target.classList.remove(pressedClass);
    void target.offsetWidth;
    target.classList.add(pressedClass);
    setTimeout(() => {
      target.classList.remove(pressedClass);
    }, 240);

    if (target.classList.contains("btn")) {
      if (lastSelectedButton && lastSelectedButton !== target) {
        lastSelectedButton.classList.remove("selected-persistent");
      }
      target.classList.add("selected-persistent");
      lastSelectedButton = target;
    }

    const text = (target.textContent || "").trim();
    if (text) {
      notify("Action Event", text, "warn", 1800);
    }
  });
}

async function saveSudoPassword() {
  const sudoPassword = sudoPasswordInput?.value || "";
  const remember = Boolean(sudoRemember?.checked ?? true);

  const requirementChecks = [
    { ok: Boolean(state.auth?.authenticated), text: "User must be logged in" },
    { ok: sudoPassword.trim().length > 0, text: "Password cannot be empty" },
    { ok: true, text: remember ? "Session cache enabled" : "Session cache disabled" },
  ];

  logsOutput.textContent = [
    "[sudo-validation] Checking requirements...",
    ...requirementChecks.map((item) => `[${item.ok ? "ok" : "fail"}] ${item.text}`),
  ].join("\n");

  if (!requirementChecks.every((item) => item.ok)) {
    jobStatus.textContent = "auth";
    notify("Sudo Validation", "Requirements not met", "error", 2400);
    return;
  }

  if (!sudoPassword) {
    logsOutput.textContent = "Enter sudo password first.";
    jobStatus.textContent = "auth";
    return;
  }

  const response = await apiFetch("/api/auth/sudo-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sudo_password: sudoPassword, remember }),
  });

  const data = await response.json();
  if (!response.ok || !data.ok) {
    logsOutput.textContent = data.error || "Failed to store sudo password.";
    jobStatus.textContent = "error";
    notify("Sudo Validation", "Password rejected", "error", 2600);
    return;
  }

  if (sudoPasswordInput) {
    sudoPasswordInput.value = "";
  }
  const successMessage = remember
    ? "[ok] Sudo password validated and saved for current session."
    : "[ok] Sudo password validated for one-time use (not remembered).";
  logsOutput.textContent = successMessage;
  jobStatus.textContent = "auth";
  notify("Sudo Validation", "Password accepted", "success", 2200);

  const relaunched = await autoRetryIfSudoBlockedJob();
  if (!relaunched) {
    state.currentJobId = null;
    state.lastJobStatus = null;
  }
}

function startTimers() {
  setInterval(() => {
    const elapsed = Math.floor((Date.now() - state.timerStartedAt) / 1000);
    const hh = String(Math.floor(elapsed / 3600)).padStart(2, "0");
    const mm = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
    const ss = String(elapsed % 60).padStart(2, "0");
    uptime.textContent = `Time: ${hh}:${mm}:${ss}`;
    systemTime.textContent = new Date().toLocaleTimeString();
  }, 1000);

  setInterval(pollJob, 1000);
  setInterval(refreshSystemInfo, 1000);
  setInterval(async () => {
    if (state.activePacketLogTab === "packet") {
      await loadPacketFlow();
      return;
    }
    await loadActionLogs();
  }, 3000);
}

function attachEvents() {
  document.addEventListener("click", (event) => {
    const pickModelBtn = event.target.closest("[data-device-action='choose-model']");
    if (pickModelBtn) {
      state.liveModelChooserVisible = true;
      renderLiveModelSelection();
      notify("Model Picker", "Switch between auto-detect and manual mode, then apply.", "success", 2400);
      return;
    }

    const toggleCountermeasureBtn = event.target.closest("[data-device-action='toggle-countermeasure-mode']");
    if (toggleCountermeasureBtn) {
      toggleCountermeasureMode();
      return;
    }

    const resetViewBtn = event.target.closest("[data-device-action='reset-view']");
    if (resetViewBtn) {
      resetTopologyView();
      notify("Control Surface", "View reset to default position.", "success", 1600);
      return;
    }

    const openServerDbBtn = event.target.closest("[data-device-action='open-server-db']");
    if (openServerDbBtn) {
      if (state.auth.role !== "admin") {
        notify("Access Denied", "Admin role required to access server database.", "warn", 2200);
        return;
      }
      const accessPath = String(state.system?.access_path || "").trim();
      const targetPath = accessPath ? `${accessPath}/server` : "/server";
      window.location.href = targetPath;
      return;
    }

    const identAddBtn = event.target.closest("[data-device-action='ident-add']");
    if (identAddBtn) {
      addToIdentificationList();
      return;
    }

    const identRemoveBtn = event.target.closest("[data-device-action='ident-remove']");
    if (identRemoveBtn) {
      removeFromIdentificationList();
      return;
    }

    const identChangeTagBtn = event.target.closest("[data-device-action='ident-change-tag']");
    if (identChangeTagBtn) {
      changeIdentificationTag();
      return;
    }

    const identReturnBtn = event.target.closest("[data-device-action='ident-return']");
    if (identReturnBtn) {
      const targetSection =
        state.identification.previousSectionId && state.identification.previousSectionId !== IDENTIFICATION_SECTION_ID
          ? state.identification.previousSectionId
          : (state.menu || []).find((section) => section.id !== IDENTIFICATION_SECTION_ID)?.id;
      state.activeSectionId = targetSection || "detection";
      const section = getActiveSection();
      state.activeActionId = section?.actions?.[0]?.id || null;
      leaveIdentificationSection();
      renderMenu();
      renderActionDetails();
      renderDeviceStrip();
      return;
    }

    const identRow = event.target.closest("[data-identification-ip]");
    if (identRow) {
      state.identification.selectedIp = String(identRow.getAttribute("data-identification-ip") || "").trim();
      renderIdentificationListPanel();
      renderDeviceStrip();
    }
  });

  menuList.addEventListener("click", (event) => {
    const target = event.target.closest("[data-section-id]");
    if (!target) {
      return;
    }
    const previousSection = state.activeSectionId;
    state.activeSectionId = target.dataset.sectionId;
    const section = getActiveSection();
    state.activeActionId = section?.actions?.[0]?.id || null;
    if (state.activeSectionId === IDENTIFICATION_SECTION_ID) {
      state.identification.previousSectionId = previousSection && previousSection !== IDENTIFICATION_SECTION_ID ? previousSection : state.identification.previousSectionId;
      enterIdentificationSection();
      loadIdentificationListing();
    } else {
      leaveIdentificationSection();
    }
    renderMenu();
    renderActionDetails();
    renderDeviceStrip();
  });

  actionDescription.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action-id]");
    if (!target) {
      return;
    }

    if (IDENTIFICATION_REDIRECT_ACTIONS.has(target.dataset.actionId)) {
      const previousSection = state.activeSectionId;
      state.identification.previousSectionId = previousSection;
      state.activeSectionId = IDENTIFICATION_SECTION_ID;
      const identificationSection = getActiveSection();
      state.activeActionId = identificationSection?.actions?.[0]?.id || null;
      renderMenu();
      renderActionDetails();
      enterIdentificationSection();
      loadIdentificationListing();
      notify("Identification Listing", "Opened unified listing workspace.", "success", 1600);
      return;
    }

    state.activeActionId = target.dataset.actionId;
    renderMenu();
    renderActionDetails();
    if (isIdentificationMode()) {
      handleIdentificationActionSelection(state.activeActionId);
    }
  });

  historyBody.addEventListener("click", async (event) => {
    const rerunBtn = event.target.closest(".history-rerun");
    if (!rerunBtn) {
      return;
    }
    const index = Number(rerunBtn.dataset.historyIndex);
    if (Number.isNaN(index)) {
      return;
    }

    const response = await apiFetch("/api/history?limit=12");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    const entry = (data.history || [])[index];
    if (!entry || !entry.command) {
      return;
    }
    await rerunHistoryCommand(entry.command);
  });

  runBtn.addEventListener("click", runAction);
  zoomOutBtn?.addEventListener("click", () => zoomBy(-0.1));
  zoomInBtn?.addEventListener("click", () => zoomBy(0.1));
  zoomAutoBtn?.addEventListener("click", () => {
    state.autoAdjustWindow = !state.autoAdjustWindow;
    if (state.autoAdjustWindow) {
      autoAdjustToWindow();
      notify("Window Fit", "Auto Adjust enabled", "success", 1400);
    } else {
      applyPageZoom();
      notify("Window Fit", "Auto Adjust disabled", "warn", 1400);
    }
  });
  launchSimulationBtn?.addEventListener("click", runSimulation);
  simArchitectureType?.addEventListener("change", renderSimulationArchitectureSummary);
  realtimeBtn.addEventListener("click", () => setMode("realtime"));
  simulationBtn.addEventListener("click", () => setMode("simulation"));
  document.getElementById("refresh-system").addEventListener("click", refreshSystemInfo);

  settingsSaveBtn?.addEventListener("click", saveSettingsFromPanel);
  historyRefreshBtn?.addEventListener("click", loadHistoryPreview);
  schedulerStartBtn?.addEventListener("click", () => schedulerControl("start"));
  schedulerStopBtn?.addEventListener("click", () => schedulerControl("stop"));
  queuePauseBtn?.addEventListener("click", () => queueControl("pause"));
  queueResumeBtn?.addEventListener("click", () => queueControl("resume"));
  queueClearBtn?.addEventListener("click", () => queueControl("clear"));
  jobPauseBtn?.addEventListener("click", pauseCurrentJob);
  jobResumeBtn?.addEventListener("click", resumeCurrentJob);
  jobCancelBtn?.addEventListener("click", cancelCurrentJob);
  jobRetryBtn?.addEventListener("click", retryCurrentJob);
  sudoForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveSudoPassword();
  });
  saveTokenBtn?.addEventListener("click", saveApiToken);
  authLoginBtn?.addEventListener("click", login);
  authChangePassBtn?.addEventListener("click", changePassword);
  authLogoutBtn?.addEventListener("click", logout);
  auditRefreshBtn?.addEventListener("click", loadAuditEvents);
  auditExportBtn?.addEventListener("click", exportAuditEvents);
  auditApplyBtn?.addEventListener("click", loadAuditEvents);
  usersRefreshBtn?.addEventListener("click", loadUsers);
  userCreateBtn?.addEventListener("click", createUser);
  modelsRefreshBtn?.addEventListener("click", loadModels);
  modelsSyncBtn?.addEventListener("click", syncModels);
  modelRegisterBtn?.addEventListener("click", registerModelPath);
  packetCaptureStartBtn?.addEventListener("click", async () => {
    await controlPacketCapture("start", {
      interface: state.settings?.last_interface || state.activeInterface || "eth0",
      auto: false,
    });
  });
  packetCapturePauseBtn?.addEventListener("click", async () => {
    await controlPacketCapture("pause", {});
  });
  packetCaptureStopBtn?.addEventListener("click", async () => {
    await controlPacketCapture("stop", {});
  });
  packetlogsRefreshBtn?.addEventListener("click", async () => {
    await setPacketLogTab(state.activePacketLogTab || "action");
    await loadPacketCaptureStatus();
  });
  showActionLogBtn?.addEventListener("click", async () => {
    await setPacketLogTab("action");
  });
  showPacketLogBtn?.addEventListener("click", async () => {
    await setPacketLogTab("packet");
  });
  liveModelModeAutoBtn?.addEventListener("click", () => setLiveModelMode("auto"));
  liveModelModeManualBtn?.addEventListener("click", () => setLiveModelMode("manual"));
  liveModelSaveBtn?.addEventListener("click", saveLiveModelSelection);
  identificationDeepIdentify?.addEventListener("change", () => {
    state.identification.deepIdentify = Boolean(identificationDeepIdentify.checked);
  });
  identificationEditorSave?.addEventListener("click", submitIdentificationEditor);
  identificationEditorCancel?.addEventListener("click", closeIdentificationEditor);
  popupModeToggleBtn?.addEventListener("click", () => {
    state.popupMode = state.popupMode === "technical" ? "onboarding" : "technical";
    refreshPopupModeUI();
    updateContextPopupForTarget(document.activeElement || document.body);
    notify(
      "Popup Mode",
      state.popupMode === "technical" ? "Technical guidance enabled" : "New-user guidance enabled",
      "success",
      1500,
    );
  });

  usersBody?.addEventListener("click", async (event) => {
    const setRoleBtn = event.target.closest(".user-set-role");
    if (setRoleBtn) {
      await updateUserRole(setRoleBtn.dataset.username || "");
      return;
    }

    const resetBtn = event.target.closest(".user-reset-pass");
    if (resetBtn) {
      await resetUserPassword(resetBtn.dataset.username || "");
      return;
    }

    const deleteBtn = event.target.closest(".user-delete");
    if (deleteBtn) {
      await deleteUser(deleteBtn.dataset.username || "");
    }
  });
}

async function init() {
  applyDeviceProfile();
  renderSimulationArchitectureSummary();
  renderDeviceStrip();
  renderIdentificationListPanel();
  renderTopology();
  initTopologyPanHandlers();
  initContextPopupHandlers();
  attachPressHighlights();
  attachEvents();
  refreshPopupModeUI();
  updateContextPopupForTarget(document.body);
  setMode("realtime");
  await loadAuthSession();
  await loadSettings();
  await loadMenu();
  await loadIdentificationListing();
  await loadHistoryPreview();
  await loadAuditEvents();
  await loadModels();
  await setPacketLogTab("action");
  await refreshSystemInfo();
  await loadModelDbStatus();
  setGlobalProgress("idle", []);
  updateJobControlButtons("idle");
  window.addEventListener("resize", drawTopologyConnections);
  window.addEventListener("resize", () => {
    applyDeviceProfile();
    if (state.autoAdjustWindow) {
      autoAdjustToWindow();
    }
  });
  applyPageZoom();
  startTimers();
}

init();
