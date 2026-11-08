(() => {
  const API_URL = `${window.ICHECK_API_URL || ""}/api/v1/analyze`;
  const input = document.querySelector("#file-input");
  const dropzone = document.querySelector("#dropzone");
  const chooseButton = document.querySelector("#choose-button");
  const analyzeButton = document.querySelector("#analyze-button");
  const analyzeLabel = document.querySelector("#analyze-label");
  const errorMessage = document.querySelector("#upload-error");
  const previewRow = document.querySelector("#preview-row");
  const previewImage = document.querySelector("#preview-image");
  const MAX_BYTES = 10 * 1024 * 1024;
  const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
  let selectedFile = null;
  let previewUrl = null;

  const setError = (message = "") => {
    errorMessage.textContent = message;
    errorMessage.hidden = !message;
  };

  function selectFile(file) {
    setError();
    if (!file) return;
    if (!ACCEPTED.includes(file.type)) return setError("Please choose a JPG, PNG or WEBP image.");
    if (file.size > MAX_BYTES) return setError("This image is over 10 MB. Please choose a smaller file.");
    selectedFile = file;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    previewImage.src = previewUrl;
    document.querySelector("#file-name").textContent = file.name;
    document.querySelector("#file-size").textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    document.querySelector("#drop-title").textContent = "Image ready to analyze";
    previewRow.hidden = false;
    analyzeButton.disabled = false;
    document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Ready to analyze';
  }

  chooseButton.addEventListener("click", (event) => { event.stopPropagation(); input.click(); });
  dropzone.addEventListener("click", (event) => { if (event.target !== chooseButton) input.click(); });
  dropzone.addEventListener("keydown", (event) => {
    if (event.target === dropzone && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); input.click(); }
  });
  input.addEventListener("change", () => selectFile(input.files?.[0]));
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.remove("dragging"); }));
  dropzone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files?.[0]));
  document.querySelector("#remove-button").addEventListener("click", () => {
    selectedFile = null;
    input.value = "";
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
    previewImage.removeAttribute("src");
    previewRow.hidden = true;
    document.querySelector("#drop-title").textContent = "Drag & drop your image here";
    analyzeButton.disabled = true;
    setError();
    document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Awaiting image';
  });

  function showResults(data) {
    document.querySelector("#empty-results").hidden = true;
    document.querySelector("#api-hint").hidden = true;
    const result = document.querySelector("#result-content");
    result.hidden = false;
    const recommendation = data.recommendation || {};
    document.querySelector("#prediction-title").textContent = recommendation.title || data.predicted_class || "Screening result";
    document.querySelector("#confidence-value").textContent = `${Math.round((data.confidence || 0) * 100)}%`;
    document.querySelector("#recommendation-description").textContent = recommendation.description || `The model classified this image as ${data.predicted_class || "unknown"}.`;
    const steps = document.querySelector("#next-steps");
    steps.replaceChildren();
    (recommendation.next_steps || []).forEach((step) => { const item = document.createElement("li"); item.textContent = step; steps.append(item); });
    document.querySelector("#next-steps-wrap").hidden = !steps.children.length;
    const scores = Object.entries(data.scores || {}).sort((a, b) => b[1] - a[1]);
    const scoresList = document.querySelector("#scores-list");
    scoresList.replaceChildren();
    scores.slice(0, 4).forEach(([label, value]) => {
      const row = document.createElement("div"); row.className = "score-row";
      const name = document.createElement("span"); name.textContent = label.replaceAll("_", " ");
      const percentage = document.createElement("strong"); percentage.textContent = `${Math.round(value * 100)}%`;
      const track = document.createElement("div"); track.className = "score-track";
      const bar = document.createElement("span"); bar.style.width = `${Math.max(0, Math.min(100, value * 100))}%`; track.append(bar);
      row.append(name, percentage, track); scoresList.append(row);
    });
    document.querySelector("#scores-wrap").hidden = !scores.length;
    const urgent = document.querySelector("#urgent-warning");
    urgent.textContent = recommendation.urgent_warning || "";
    urgent.hidden = !urgent.textContent;
    document.querySelector("#result-disclaimer").textContent = data.disclaimer || recommendation.disclaimer || "This educational screening is not a medical diagnosis.";
    document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Analysis complete';
  }

  analyzeButton.addEventListener("click", async () => {
    if (!selectedFile || analyzeButton.disabled) return;
    setError();
    document.querySelector("#api-hint").hidden = true;
    analyzeButton.disabled = true;
    analyzeButton.classList.add("is-loading");
    analyzeLabel.textContent = "Analyzing image";
    document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Analyzing';
    const form = new FormData(); form.append("file", selectedFile);
    try {
      const response = await fetch(API_URL, { method: "POST", body: form });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "The image could not be analyzed. Please try a different photo.");
      showResults(data);
    } catch (error) {
      document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Unable to analyze';
      if (error instanceof TypeError) document.querySelector("#api-hint").hidden = false;
      else setError(error.message);
    } finally {
      analyzeButton.disabled = !selectedFile;
      analyzeButton.classList.remove("is-loading");
      analyzeLabel.textContent = "Analyze image";
    }
  });
})();
