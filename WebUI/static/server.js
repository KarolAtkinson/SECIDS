const serverFoldersBody = document.getElementById("server-folders-body");
const serverCustomList = document.getElementById("server-custom-list");
const serverRootPill = document.getElementById("server-root-pill");
const serverTrashPill = document.getElementById("server-trash-pill");
const serverFolderSelect = document.getElementById("server-folder-select");
const serverFileSelect = document.getElementById("server-file-select");
const serverViewFileBtn = document.getElementById("server-view-file");
const serverViewReturnBtn = document.getElementById("server-view-return");
const serverFileViewWrap = document.getElementById("server-file-view-wrap");
const serverFilePath = document.getElementById("server-file-path");
const serverFileLines = document.getElementById("server-file-lines");
const serverFileContent = document.getElementById("server-file-content");
const returnMainBtn = document.getElementById("return-main");
const refreshBtn = document.getElementById("server-refresh");
const addBtn = document.getElementById("server-add");
const removeBtn = document.getElementById("server-remove");
const importBtn = document.getElementById("server-import");
const exportBtn = document.getElementById("server-export");
const syncDataBtn = document.getElementById("server-sync-data");
const syncSummary = document.getElementById("server-sync-summary");
const nistCswUpdateBtn = document.getElementById("nist-csw-update");
const nistCswStatus = document.getElementById("nist-csw-status");
const nistCswConvertBtn = document.getElementById("nist-csw-convert");
const nistCswConvertStatus = document.getElementById("nist-csw-convert-status");
const nistCswSummary = document.getElementById("nist-csw-summary");
const importFolderInput = document.getElementById("import-folder");
const importFlagInput = document.getElementById("import-flag");
const importDataInput = document.getElementById("import-data");
const serverFolderFiles = new Map();

function getApiToken() {
  return localStorage.getItem("secids_api_token") || "";
}

async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getApiToken();
  if (token) {
    headers["X-SECIDS-Token"] = token;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    window.location.href = "/login";
  }
  return response;
}

function renderOverview(data) {
  if (serverRootPill) {
    serverRootPill.textContent = `root: ${data.root || "--"}`;
  }
  if (serverTrashPill) {
    const retention = data.retention_trash || {};
    const parts = Object.entries(retention).map(([key, value]) => `${key}:${value}`);
    serverTrashPill.textContent = parts.length ? `trash: ${parts.join(" | ")}` : `trash: ${data.trash_root || "--"}`;
  }

  if (serverFoldersBody) {
    const folders = data.folders || [];
    const tagged = data.data_folders || [];
    serverFolderFiles.clear();
    if (!folders.length && !tagged.length) {
      serverFoldersBody.innerHTML = `<tr><td colspan="4">No folders found.</td></tr>`;
    } else {
      const coreRows = folders.map((folder) => {
          serverFolderFiles.set(folder.key || "", folder.files || []);
          const latest = (folder.files || []).slice(-5).join("<br>") || "-";
          return `
          <tr>
            <td>${folder.key || "-"}</td>
            <td>${folder.path || "-"}</td>
            <td>${folder.file_count || 0}</td>
            <td>${latest}</td>
          </tr>
        `;
        });

      const taggedRows = tagged.map((folder) => `
        <tr>
          <td>${folder.key || "-"}</td>
          <td>${folder.path || "-"}</td>
          <td>${folder.file_count || 0}</td>
          <td>tagged-data</td>
        </tr>
      `);

      serverFoldersBody.innerHTML = [...coreRows, ...taggedRows].join("");
    }
  }

  const customFolders = data.custom_folders || [];
  customFolders.forEach((name) => {
    const key = `custom/${name}`;
    serverFolderFiles.set(key, []);
  });

  if (serverFolderSelect) {
    const options = [];
    (data.folders || []).forEach((folder) => {
      options.push(`<option value="${folder.key}">${folder.key}</option>`);
    });
    customFolders.forEach((name) => {
      options.push(`<option value="custom/${name}">custom/${name}</option>`);
    });
    serverFolderSelect.innerHTML = options.join("");
    if (!serverFolderSelect.value && options.length) {
      serverFolderSelect.value = (data.folders || [])[0]?.key || "";
    }
  }

  renderFileSelect();

  if (serverCustomList) {
    serverCustomList.innerHTML = customFolders.length
      ? customFolders.map((name) => `<span class="pill">${name}</span>`).join(" ")
      : `<span class="pill">No custom folders</span>`;
  }
}

function renderFileSelect() {
  if (!serverFileSelect || !serverFolderSelect) {
    return;
  }
  const folder = serverFolderSelect.value || "";
  const files = serverFolderFiles.get(folder) || [];
  if (!files.length) {
    serverFileSelect.innerHTML = `<option value="">No files</option>`;
    return;
  }
  serverFileSelect.innerHTML = files.map((name) => `<option value="${name}">${name}</option>`).join("");
}

function showOverviewView() {
  serverFileViewWrap?.classList.add("hidden");
}

function showFileView() {
  serverFileViewWrap?.classList.remove("hidden");
}

async function loadOverview() {
  const response = await apiFetch("/api/server-db/overview");
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  renderOverview(data);
  await loadNistCswStatus();
}

function renderNistSummary(data) {
  if (!nistCswSummary) {
    return;
  }
  const latest = data.latest || {};
  const feedInfo = latest.feeds || {};
  const feedRows = Object.entries(feedInfo)
    .map(([name, details]) => {
      const ok = details?.ok ? "ok" : "failed";
      const count = details?.count || 0;
      return `<li>${name}: ${ok} (${count})</li>`;
    })
    .join("");

  nistCswSummary.innerHTML = `
    <div class="pill">folder: ${data.folder || "ServerDB/NIST-CSW"}</div>
    <div class="pill">files: ${data.file_count || 0}</div>
    <div class="pill">recent: ${(data.recent_files || []).slice(-4).join(", ") || "none"}</div>
    <div class="pill">converted rows: ${latest.converted_rows || latest?.conversion?.converted_rows || 0}</div>
    <div class="pill">dataset: ${latest.dataset_file || latest?.conversion?.dataset_file || "--"}</div>
    <ul class="quick-guide">${feedRows || "<li>No feed update data yet.</li>"}</ul>
  `;
}

async function loadNistCswStatus() {
  const response = await apiFetch("/api/server-db/nist-csw/status");
  const data = await response.json();
  if (!response.ok || !data.ok) {
    if (nistCswStatus) {
      nistCswStatus.textContent = "status: failed";
    }
    return;
  }
  const latest = data.latest || {};
  if (nistCswStatus) {
    nistCswStatus.textContent = `status: ${latest.ok === false ? "degraded" : "ready"}`;
  }
  if (nistCswConvertStatus) {
    const convertedRows = latest.converted_rows || latest?.conversion?.converted_rows || 0;
    nistCswConvertStatus.textContent = `convert: ${convertedRows > 0 ? `ready (${convertedRows})` : "pending"}`;
  }
  renderNistSummary(data);
}

async function updateNistCswFeeds() {
  if (nistCswStatus) {
    nistCswStatus.textContent = "status: updating...";
  }
  const response = await apiFetch("/api/server-db/nist-csw/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feeds: ["cisa_kev", "nvd_recent"], auto_convert: true }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    if (nistCswStatus) {
      nistCswStatus.textContent = "status: update failed";
    }
    alert(data?.result?.error || data?.error || "NIST-CSW update failed");
    await loadNistCswStatus();
    return;
  }
  if (nistCswStatus) {
    nistCswStatus.textContent = "status: updated";
  }
  await loadOverview();
}

async function convertNistCswFeeds() {
  if (nistCswConvertStatus) {
    nistCswConvertStatus.textContent = "convert: running...";
  }
  const response = await apiFetch("/api/server-db/nist-csw/convert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    if (nistCswConvertStatus) {
      nistCswConvertStatus.textContent = "convert: failed";
    }
    alert(data?.result?.error || data?.error || "NIST-CSW conversion failed");
    await loadNistCswStatus();
    return;
  }
  const rows = data?.result?.converted_rows || 0;
  if (nistCswConvertStatus) {
    nistCswConvertStatus.textContent = `convert: ready (${rows})`;
  }
  await loadOverview();
}

async function viewSelectedFile() {
  const folder = (serverFolderSelect?.value || "").trim();
  const name = (serverFileSelect?.value || "").trim();
  if (!folder || !name) {
    alert("Select folder and file first");
    return;
  }

  const response = await apiFetch(`/api/server-db/file?folder=${encodeURIComponent(folder)}&name=${encodeURIComponent(name)}&lines=400`);
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(data.error || "Failed to load file");
    return;
  }

  if (serverFilePath) {
    serverFilePath.textContent = data.path || `${folder}/${name}`;
  }
  if (serverFileLines) {
    serverFileLines.textContent = `lines: ${data.line_count || 0}`;
  }
  if (serverFileContent) {
    serverFileContent.textContent = data.content || "(empty file)";
    serverFileContent.scrollTop = 0;
  }
  showFileView();
}

async function addFolder() {
  const folder = (prompt("New custom folder name:") || "").trim();
  if (!folder) {
    return;
  }
  const response = await apiFetch("/api/server-db/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(data.error || "Failed to add folder");
    return;
  }
  renderOverview(data.overview || {});
}

async function removeFolder() {
  const folder = (prompt("Custom folder name to remove:") || "").trim();
  if (!folder) {
    return;
  }
  const response = await apiFetch("/api/server-db/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(data.error || "Failed to remove folder");
    return;
  }
  renderOverview(data.overview || {});
}

async function importData() {
  const folder = (importFolderInput?.value || "").trim() || (prompt("Folder for import:") || "").trim();
  const dataRaw = (importDataInput?.value || "").trim() || (prompt("Data to import:") || "").trim();
  const flag = (importFlagInput?.value || "").trim() || "SERVER_IMPORT";
  if (!folder || !dataRaw) {
    alert("Folder and import data are required");
    return;
  }

  let payloadData = dataRaw;
  try {
    payloadData = JSON.parse(dataRaw);
  } catch {
    payloadData = dataRaw;
  }

  const response = await apiFetch("/api/server-db/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder, flag, data: payloadData }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(data.error || "Import failed");
    return;
  }
  renderOverview(data.overview || {});
}

async function exportData() {
  const response = await apiFetch("/api/server-db/export", {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    alert(data.error || "Export failed");
    return;
  }
  alert(`Export created: ${data.path}`);
  await loadOverview();
}

async function syncProjectData() {
  if (syncSummary) {
    syncSummary.textContent = "data sync: running...";
  }
  const response = await apiFetch("/api/server-db/sync-project-data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ execute: true }),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    if (syncSummary) {
      syncSummary.textContent = `data sync: failed`;
    }
    alert(data.error || "Project data sync failed");
    return;
  }

  const summary = data.summary || {};
  if (syncSummary) {
    syncSummary.textContent = `data sync: synced ${summary.synced || 0}, skipped ${summary.skipped || 0}, errors ${summary.errors || 0}`;
  }
  renderOverview(data.overview || {});
}

function attachEvents() {
  returnMainBtn?.addEventListener("click", () => {
    const indexPath = returnMainBtn.dataset.indexPath || "/";
    window.location.href = indexPath;
  });
  refreshBtn?.addEventListener("click", loadOverview);
  serverFolderSelect?.addEventListener("change", renderFileSelect);
  serverViewFileBtn?.addEventListener("click", viewSelectedFile);
  serverViewReturnBtn?.addEventListener("click", showOverviewView);
  addBtn?.addEventListener("click", addFolder);
  removeBtn?.addEventListener("click", removeFolder);
  importBtn?.addEventListener("click", importData);
  exportBtn?.addEventListener("click", exportData);
  syncDataBtn?.addEventListener("click", syncProjectData);
  nistCswUpdateBtn?.addEventListener("click", updateNistCswFeeds);
  nistCswConvertBtn?.addEventListener("click", convertNistCswFeeds);
}

async function init() {
  attachEvents();
  await loadOverview();
}

init();
