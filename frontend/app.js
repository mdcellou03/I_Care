(() => {
  const API_URL = `${window.ICHECK_API_URL || ""}/api/v1/analyze`;
  const input = document.querySelector("#file-input");
  const cameraInput = document.querySelector("#camera-input");
  const dropzone = document.querySelector("#dropzone");
  const chooseButton = document.querySelector("#choose-button");
  const analyzeButton = document.querySelector("#analyze-button");
  const analyzeLabel = document.querySelector("#analyze-label");
  const errorMessage = document.querySelector("#upload-error");
  const previewRow = document.querySelector("#preview-row");
  const previewImage = document.querySelector("#preview-image");
  const nearbyButton = document.querySelector("#find-nearby-button");
  const nearbyMapSection = document.querySelector("#nearby-map-section");
  const locationStatus = document.querySelector("#location-status");
  const providerList = document.querySelector("#provider-list");
  const googleMapsSearch = document.querySelector("#google-maps-search");
  const MAX_BYTES = 15 * 1024 * 1024;
  const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
  // Some browsers report HEIC files with an empty type, so fall back to the extension.
  const isAccepted = (file) => ACCEPTED.includes(file.type) || /\.(heic|heif)$/i.test(file.name);
  let selectedFile = null;
  let previewUrl = null;

  const setError = (message = "") => {
    errorMessage.textContent = message;
    errorMessage.hidden = !message;
  };

  function selectFile(file) {
    setError();
    if (!file) return;
    if (!isAccepted(file)) return setError("Please choose a JPG, PNG, WEBP or HEIC image.");
    if (file.size > MAX_BYTES) return setError("This image is over 15 MB. Please choose a smaller file.");
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
  // Phones (touch screens) use the native camera app via capture="environment", which gives the
  // best photo. Laptops ignore that attribute, so they get a webcam preview dialog instead.
  // getUserMedia only exists on secure pages (https or localhost); otherwise fall back to a file picker.
  const cameraDialog = document.querySelector("#camera-dialog");
  const cameraVideo = document.querySelector("#camera-video");
  const cameraCapture = document.querySelector("#camera-capture");
  const cameraError = document.querySelector("#camera-error");
  const isTouchDevice = window.matchMedia("(pointer: coarse)").matches;
  const canUseWebcam = Boolean(navigator.mediaDevices?.getUserMedia) && typeof cameraDialog.showModal === "function";
  let cameraStream = null;

  const setCameraError = (message = "") => {
    cameraError.textContent = message;
    cameraError.hidden = !message;
  };

  function stopCamera() {
    cameraStream?.getTracks().forEach((track) => track.stop());
    cameraStream = null;
    cameraVideo.srcObject = null;
    cameraCapture.disabled = true;
  }

  // Turn the camera off explicitly instead of relying only on the dialog's "close" event,
  // which some browsers don't fire reliably.
  function closeCamera() {
    stopCamera();
    if (cameraDialog.open) cameraDialog.close();
  }

  async function openWebcam() {
    setCameraError();
    cameraDialog.showModal();
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      // The dialog may have been closed while the permission prompt was open.
      if (!cameraDialog.open) return stopCamera();
      cameraVideo.srcObject = cameraStream;
      await cameraVideo.play();
      cameraCapture.disabled = false;
    } catch (error) {
      stopCamera();
      const messages = {
        NotAllowedError: "Camera access was blocked. Allow it from the camera icon in your address bar, or use Choose image.",
        NotFoundError: "No camera was found on this device. Please use Choose image instead.",
        NotReadableError: "Your camera is being used by another app. Close it and try again.",
      };
      setCameraError(messages[error.name] || "The camera couldn't be started. Please use Choose image instead.");
    }
  }

  function captureFrame() {
    if (!cameraVideo.videoWidth) return;
    cameraCapture.disabled = true; // encoding can take a moment; avoid double captures
    const canvas = document.createElement("canvas");
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    // Draw the raw frame (not the mirrored preview), so the photo matches what the camera sees.
    canvas.getContext("2d").drawImage(cameraVideo, 0, 0);
    canvas.toBlob((blob) => {
      if (!blob) {
        cameraCapture.disabled = false;
        return setCameraError("The photo couldn't be captured. Please try again.");
      }
      closeCamera();
      selectFile(new File([blob], `webcam-${Date.now()}.jpg`, { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  }

  document.querySelector("#camera-button").addEventListener("click", (event) => {
    event.stopPropagation();
    if (!isTouchDevice && canUseWebcam) openWebcam();
    else cameraInput.click();
  });
  cameraInput.addEventListener("change", () => selectFile(cameraInput.files?.[0]));
  cameraCapture.addEventListener("click", captureFrame);
  document.querySelector("#camera-cancel").addEventListener("click", closeCamera);
  // Escape closes the dialog without our buttons; "cancel" and "close" cover that case.
  cameraDialog.addEventListener("cancel", stopCamera);
  cameraDialog.addEventListener("close", stopCamera);
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.remove("dragging"); }));
  dropzone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files?.[0]));
  document.querySelector("#remove-button").addEventListener("click", () => {
    selectedFile = null;
    input.value = "";
    cameraInput.value = "";
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
    scores.forEach(([label, value]) => {
      const row = document.createElement("div"); row.className = "score-row";
      const name = document.createElement("span"); name.textContent = label.replaceAll("_", " ");
      const percentage = document.createElement("strong"); percentage.textContent = `${Math.round(value * 100)}%`;
      const track = document.createElement("div"); track.className = "score-track";
      const bar = document.createElement("span"); bar.style.width = `${Math.max(0, Math.min(100, value * 100))}%`; track.append(bar);
      row.append(name, percentage, track); scoresList.append(row);
    });
    document.querySelector("#scores-wrap").hidden = !scores.length;
    document.querySelector("#low-confidence").hidden = !data.low_confidence;
    const urgent = document.querySelector("#urgent-warning");
    urgent.textContent = recommendation.urgent_warning || "";
    urgent.hidden = !urgent.textContent;
    document.querySelector("#result-disclaimer").textContent = data.disclaimer || recommendation.disclaimer || "This educational screening is not a medical diagnosis.";
    document.querySelector("#result-status").innerHTML = '<span class="status-dot"></span> Analysis complete';
  }

  let nearbyMap = null;
  let providerLayer = null;
  let userMarker = null;

  function googleMapsUrl(name, address, latitude, longitude) {
    const query = [name, address].filter(Boolean).join(" ") || `optometrist near ${latitude},${longitude}`;
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
  }

  function ensureNearbyMap(latitude, longitude) {
    if (!window.L) throw new Error("The map library did not load. Check your internet connection and try again.");
    if (!nearbyMap) {
      nearbyMap = L.map("nearby-map", { scrollWheelZoom: false }).setView([latitude, longitude], 13);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(nearbyMap);
      providerLayer = L.layerGroup().addTo(nearbyMap);
    } else {
      nearbyMap.setView([latitude, longitude], 13);
      providerLayer.clearLayers();
    }
    if (userMarker) nearbyMap.removeLayer(userMarker);
    userMarker = L.circleMarker([latitude, longitude], {
      radius: 8, color: "#ffffff", weight: 3, fillColor: "#5595df", fillOpacity: 1,
    }).addTo(nearbyMap).bindPopup("Your approximate location");
    window.setTimeout(() => nearbyMap.invalidateSize(), 120);
  }

  function providerAddress(tags) {
    const street = [tags["addr:housenumber"], tags["addr:street"]].filter(Boolean).join(" ");
    return [street, tags["addr:city"], tags["addr:postcode"]].filter(Boolean).join(", ");
  }

  function renderProviders(elements, userLatitude, userLongitude) {
    providerLayer.clearLayers();
    providerList.replaceChildren();
    const providers = elements.map((element) => {
      const tags = element.tags || {};
      const point = element.center || element;
      const latitude = Number(point.lat);
      const longitude = Number(point.lon);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
      const name = tags.name || tags.operator || (tags.healthcare === "optometrist" ? "Optometrist" : "Eye-care provider");
      const address = providerAddress(tags);
      const distanceKm = L.latLng(userLatitude, userLongitude).distanceTo(L.latLng(latitude, longitude)) / 1000;
      return { name, address, latitude, longitude, distanceKm };
    }).filter(Boolean).sort((a, b) => a.distanceKm - b.distanceKm);

    providers.forEach((provider) => {
      const mapsUrl = googleMapsUrl(provider.name, provider.address, provider.latitude, provider.longitude);
      const popup = document.createElement("div");
      const popupName = document.createElement("strong");
      popupName.textContent = provider.name;
      const popupAddress = document.createElement("p");
      popupAddress.textContent = provider.address || "Address not listed";
      const popupLink = document.createElement("a");
      popupLink.href = mapsUrl;
      popupLink.target = "_blank";
      popupLink.rel = "noopener noreferrer";
      popupLink.textContent = "Open in Google Maps";
      popup.append(popupName, popupAddress, popupLink);
      L.marker([provider.latitude, provider.longitude]).addTo(providerLayer).bindPopup(popup);

      const card = document.createElement("article");
      card.className = "provider-card";
      const details = document.createElement("div");
      const title = document.createElement("h4");
      title.textContent = provider.name;
      const address = document.createElement("p");
      address.textContent = provider.address || "Address not listed";
      const distance = document.createElement("span");
      distance.className = "provider-distance";
      distance.textContent = `${provider.distanceKm.toFixed(1)} km away`;
      details.append(title, address, distance);
      const link = document.createElement("a");
      link.href = mapsUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.className = "provider-directions";
      link.textContent = "Google Maps ↗";
      card.append(details, link);
      providerList.append(card);
    });

    if (providers.length) {
      locationStatus.textContent = `Found ${providers.length} nearby eye-care ${providers.length === 1 ? "provider" : "providers"}. Listings may be incomplete.`;
      nearbyMap.fitBounds(L.featureGroup([
        userMarker,
        ...providers.map((provider) => L.marker([provider.latitude, provider.longitude])),
      ]).getBounds().pad(0.18), { maxZoom: 14 });
    } else {
      locationStatus.textContent = "No nearby eye-care providers were found in OpenStreetMap. Try Google Maps for more listings.";
      nearbyMap.setView([userLatitude, userLongitude], 13);
    }
    googleMapsSearch.href = googleMapsUrl("", "", userLatitude, userLongitude);
    googleMapsSearch.hidden = false;
  }

  async function loadNearbyProviders(latitude, longitude) {
    ensureNearbyMap(latitude, longitude);
    locationStatus.textContent = "Looking for nearby optometrists and ophthalmologists…";
    const query = `[out:json][timeout:20];(nwr(around:5000,${latitude},${longitude})["healthcare"~"^(optometrist|ophthalmologist)$"];nwr(around:5000,${latitude},${longitude})["healthcare:speciality"~"(ophthalmology|optometry)"];);out center tags;`;
    const response = await fetch("/api/nearby-optometrists", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
      body: new URLSearchParams({ data: query }),
    });
    if (!response.ok) throw new Error("Nearby provider search is temporarily unavailable.");
    const data = await response.json();
    renderProviders(data.elements || [], latitude, longitude);
  }

  nearbyButton.addEventListener("click", () => {
    nearbyMapSection.hidden = false;
    providerList.replaceChildren();
    googleMapsSearch.hidden = true;
    locationStatus.textContent = "Requesting your location…";
    nearbyMapSection.scrollIntoView({ behavior: "smooth", block: "start" });
    nearbyButton.disabled = true;
    nearbyButton.textContent = "Finding nearby eye care…";

    if (!navigator.geolocation) {
      locationStatus.textContent = "Location is unavailable in this browser. Open this page on localhost or HTTPS to use the map.";
      nearbyButton.disabled = false;
      nearbyButton.textContent = "Try again";
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        googleMapsSearch.href = googleMapsUrl("", "", coords.latitude, coords.longitude);
        googleMapsSearch.hidden = false;
        loadNearbyProviders(coords.latitude, coords.longitude).catch((error) => {
          locationStatus.textContent = `${error.message} You can still use Google Maps for nearby options.`;
        }).finally(() => {
          nearbyButton.disabled = false;
          nearbyButton.textContent = "Optometrist near me";
        });
      },
      () => {
        locationStatus.textContent = "We couldn’t access your location. Allow location access in your browser and try again.";
        nearbyButton.disabled = false;
        nearbyButton.textContent = "Try again";
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  });

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
      if (!response.ok) throw new Error(data.message || data.detail || "The image could not be analyzed. Please try a different photo.");
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
