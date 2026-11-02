const fileInput = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const chooseButton = document.querySelector("#choose-button");
const clearButton = document.querySelector("#clear-button");
const convertButton = document.querySelector("#convert-button");
const fileList = document.querySelector("#file-list");
const emptyState = document.querySelector("#empty-state");
const fileCount = document.querySelector("#file-count");
const totalNumber = document.querySelector("#total-number");
const statusMessage = document.querySelector("#status-message");
const allowedExtensions = new Set([".xlsx", ".xls", ".xlsm", ".xlsb"]);
const maxBytes = 100 * 1024 * 1024;
let selectedFiles = [];
let busy = false;

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderFiles() {
  fileList.replaceChildren();
  emptyState.hidden = selectedFiles.length > 0;
  clearButton.hidden = selectedFiles.length === 0;
  convertButton.disabled = selectedFiles.length === 0 || busy;
  fileCount.textContent = `${selectedFiles.length} FILE`;
  totalNumber.textContent = String(selectedFiles.length).padStart(2, "0");

  selectedFiles.forEach((file, index) => {
    const item = document.createElement("li");
    item.className = "file-item";

    const type = document.createElement("span");
    type.className = "file-type";
    type.textContent = `.${file.name.split(".").pop().toUpperCase()}`;

    const name = document.createElement("span");
    name.className = "file-name";
    name.title = file.name;
    name.textContent = file.name;

    const size = document.createElement("span");
    size.className = "file-size";
    size.textContent = formatSize(file.size);

    const remove = document.createElement("button");
    remove.className = "remove-button";
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Rimuovi ${file.name}`);
    remove.addEventListener("click", () => {
      selectedFiles.splice(index, 1);
      renderFiles();
      statusMessage.textContent = selectedFiles.length
        ? "File pronto per la conversione."
        : "Aggiungi almeno un file per iniziare.";
    });

    item.append(type, name, size, remove);
    fileList.append(item);
  });
}

function addFiles(fileCollection) {
  const incoming = Array.from(fileCollection);
  const invalid = incoming.filter((file) => !allowedExtensions.has(`.${file.name.split(".").pop().toLowerCase()}`));
  const valid = incoming.filter((file) => !invalid.includes(file));
  const identities = new Set(selectedFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`));
  const fresh = valid.filter((file) => !identities.has(`${file.name}:${file.size}:${file.lastModified}`));
  const total = [...selectedFiles, ...fresh].reduce((sum, file) => sum + file.size, 0);

  if (invalid.length) {
    statusMessage.textContent = `Formato non supportato: ${invalid.map((file) => file.name).join(", ")}`;
  } else if (total > maxBytes) {
    statusMessage.textContent = "La selezione supera il limite di 100 MB.";
    fileInput.value = "";
    return;
  } else if (fresh.length) {
    statusMessage.textContent = "File pronti per la conversione.";
  }

  selectedFiles.push(...fresh);
  renderFiles();
  fileInput.value = "";
}

chooseButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => addFiles(fileInput.files));
clearButton.addEventListener("click", () => {
  selectedFiles = [];
  renderFiles();
  statusMessage.textContent = "Aggiungi almeno un file per iniziare.";
});

dropzone.addEventListener("click", (event) => {
  if (event.target !== chooseButton) fileInput.click();
});
dropzone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    fileInput.click();
  }
});
for (const eventName of ["dragenter", "dragover"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
  });
}
dropzone.addEventListener("drop", (event) => addFiles(event.dataTransfer.files));

convertButton.addEventListener("click", async () => {
  if (busy || selectedFiles.length === 0) return;
  const form = new FormData();
  selectedFiles.forEach((file) => form.append("files", file, file.name));
  busy = true;
  convertButton.disabled = true;
  convertButton.querySelector("span").textContent = "Conversione in corso...";
  statusMessage.textContent = "Sto preparando i PDF. Attendi il download.";
  document.querySelector(".converter").setAttribute("aria-busy", "true");

  try {
    const response = await fetch("/convert", { method: "POST", body: form });
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Conversione non riuscita.");
    }
    const archive = await response.blob();
    const url = URL.createObjectURL(archive);
    const link = document.createElement("a");
    link.href = url;
    link.download = "file-convertiti.zip";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    statusMessage.textContent = `Completato: ${selectedFiles.length} PDF scaricati nello ZIP.`;
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    busy = false;
    convertButton.querySelector("span").textContent = "Converti e scarica";
    convertButton.disabled = selectedFiles.length === 0;
    document.querySelector(".converter").setAttribute("aria-busy", "false");
  }
});

renderFiles();
