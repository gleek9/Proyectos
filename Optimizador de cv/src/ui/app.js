/**
 * Cuva - Lógica de Interfaz de Usuario
 * Conexión bidireccional con backend Python (PyWebView API)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elementos de la interfaz
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const apiStatusDot = document.getElementById("api-status-dot");
  const apiStatusText = document.getElementById("api-status-text");

  const settingsModal = document.getElementById("settings-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCancelModal = document.getElementById("btn-cancel-modal");
  const btnSaveKey = document.getElementById("btn-save-key");
  const btnRemoveKey = document.getElementById("btn-remove-key");
  const inputApiKey = document.getElementById("input-api-key");
  const modalErrorMsg = document.getElementById("modal-error-msg");
  const linkGetApiKey = document.getElementById("link-get-api-key");

  const profileEmptyState = document.getElementById("profile-empty-state");
  const profileLoadedState = document.getElementById("profile-loaded-state");
  const btnUploadCv = document.getElementById("btn-upload-cv");
  const btnChangeCv = document.getElementById("btn-change-cv");
  const profileName = document.getElementById("profile-name");
  const profileInitials = document.getElementById("profile-initials");
  const profileFileInfo = document.getElementById("profile-file-info");

  const jobForm = document.getElementById("job-analysis-form");
  const jobUrlInput = document.getElementById("job-url-input");
  const tabDirectText = document.getElementById("tab-direct-text");
  const tabUrlMode = document.getElementById("tab-url-mode");
  const panelDirectText = document.getElementById("panel-direct-text");
  const panelUrlMode = document.getElementById("panel-url-mode");
  const btnPasteClipboard = document.getElementById("btn-paste-clipboard");
  const btnClearTextarea = document.getElementById("btn-clear-textarea");
  const btnAnalyzeDirect = document.getElementById("btn-analyze-direct");
  const btnAnalyzeUrl = document.getElementById("btn-analyze-url");
  const jobManualTextarea = document.getElementById("job-manual-textarea");
  let currentMinMatch = 75;

  const progressCard = document.getElementById("analysis-progress-card");
  const progressStatusText = document.getElementById("progress-status-text");

  const resultsSection = document.getElementById("results-section");
  const matchScoreValue = document.getElementById("match-score-value");
  const jobTitleDetected = document.getElementById("job-title-detected");
  const listMatchedSkills = document.getElementById("list-matched-skills");
  const listTransferableSkills = document.getElementById("list-transferable-skills");
  const listMissingSkills = document.getElementById("list-missing-skills");
  const mentorFeedbackText = document.getElementById("mentor-feedback-text");
  const btnGenerateCv = document.getElementById("btn-generate-cv");
  const btnGenerateText = document.getElementById("btn-generate-text");
  const actionHintText = document.getElementById("action-hint-text");

  const cvSuccessCard = document.getElementById("cv-success-card");
  const cvGeneratedFilename = document.getElementById("cv-generated-filename");
  const btnOpenPdf = document.getElementById("btn-open-pdf");
  const btnOpenFolder = document.getElementById("btn-open-folder");

  // --- Inicialización con PyWebView ---

  function initApp() {
    if (window.pywebview && window.pywebview.api) {
      loadAppState();
    } else {
      window.addEventListener("pywebviewready", loadAppState);
    }
  }

  async function loadAppState() {
    try {
      const state = await window.pywebview.api.get_app_state();
      updateUIState(state);
    } catch (err) {
      console.error("Error al cargar estado:", err);
    }
  }

  function updateUIState(state) {
    if (state.min_match_threshold) {
      currentMinMatch = state.min_match_threshold;
    }

    // 1. Estado de API Key
    if (state.has_api_key) {
      apiStatusDot.className = "status-dot active";
      apiStatusText.textContent = "Clave Activa";
      btnRemoveKey.classList.remove("hidden");
    } else {
      apiStatusDot.className = "status-dot warning";
      apiStatusText.textContent = "Sin Clave API";
      btnRemoveKey.classList.add("hidden");
    }

    // 2. Estado de Perfil Profesional
    if (state.has_profile) {
      profileEmptyState.classList.add("hidden");
      profileLoadedState.classList.remove("hidden");
      profileName.textContent = state.user_name || "Perfil Profesional Guardado";
      profileInitials.textContent = (state.user_name || "P").charAt(0).toUpperCase();
      profileFileInfo.textContent = state.original_cv_file 
        ? `Archivo base: ${state.original_cv_file}` 
        : "Datos estructurados en SQLite local";
    } else {
      profileEmptyState.classList.remove("hidden");
      profileLoadedState.classList.add("hidden");
    }
  }

  const modalSuccessMsg = document.getElementById("modal-success-msg");

  // --- Modal de Ajustes / API Key ---

  btnOpenSettings.addEventListener("click", () => {
    modalErrorMsg.classList.add("hidden");
    modalSuccessMsg.classList.add("hidden");
    inputApiKey.value = "";
    settingsModal.classList.remove("hidden");
    inputApiKey.focus();
  });

  function closeModal() {
    settingsModal.classList.add("hidden");
    modalErrorMsg.classList.add("hidden");
    modalSuccessMsg.classList.add("hidden");
  }

  btnCloseModal.addEventListener("click", closeModal);
  btnCancelModal.addEventListener("click", closeModal);

  btnSaveKey.addEventListener("click", async () => {
    const key = inputApiKey.value.trim();
    modalErrorMsg.classList.add("hidden");
    modalSuccessMsg.classList.add("hidden");

    if (!key) {
      modalErrorMsg.textContent = "Por favor ingresa tu clave API de Google AI Studio.";
      modalErrorMsg.classList.remove("hidden");
      return;
    }

    btnSaveKey.disabled = true;
    btnSaveKey.textContent = "Verificando con Google...";

    try {
      const res = await window.pywebview.api.save_api_key(key);
      if (res.success) {
        modalSuccessMsg.textContent = res.message || "Clave verificada y conectada exitosamente.";
        modalSuccessMsg.classList.remove("hidden");
        setTimeout(async () => {
          closeModal();
          await loadAppState();
        }, 750);
      } else {
        modalErrorMsg.textContent = res.error || "No se pudo validar la clave con Google.";
        modalErrorMsg.classList.remove("hidden");
      }
    } catch (err) {
      modalErrorMsg.textContent = "Error al comunicar con la aplicación de escritorio.";
      modalErrorMsg.classList.remove("hidden");
    } finally {
      btnSaveKey.disabled = false;
      btnSaveKey.textContent = "Guardar Clave";
    }
  });

  btnRemoveKey.addEventListener("click", async () => {
    if (confirm("¿Deseas desvincular tu clave API de la base de datos local?")) {
      await window.pywebview.api.remove_api_key();
      closeModal();
      await loadAppState();
    }
  });

  linkGetApiKey.addEventListener("click", (e) => {
    e.preventDefault();
    // Abrir navegador externo o avisar
    alert("Ingresa a https://aistudio.google.com/app/apikey para obtener tu clave gratuita.");
  });

  // --- Carga y Procesamiento de CV (Paso 1) ---

  async function handleSelectCv() {
    // 1. Validar que exista clave API antes de procesar
    try {
      const currentState = await window.pywebview.api.get_app_state();
      if (!currentState.has_api_key) {
        alert("Antes de cargar tu currículum, ingresa tu API Key de Google en el botón superior derecho 'Clave API'.");
        btnOpenSettings.click();
        return;
      }
    } catch (e) {
      console.warn("No se pudo verificar el estado previo:", e);
    }

    const originalUploadText = btnUploadCv.innerHTML;
    const originalChangeText = btnChangeCv.innerHTML;

    btnUploadCv.disabled = true;
    btnUploadCv.innerHTML = `<span>Extrayendo y estructurando con IA...</span>`;
    btnChangeCv.disabled = true;
    btnChangeCv.innerHTML = `<span>Procesando...</span>`;

    try {
      const res = await window.pywebview.api.select_and_process_cv();
      if (res.success) {
        await loadAppState();
      } else if (!res.cancelled) {
        alert(res.error || "Ocurrió un error al procesar el archivo.");
      }
    } catch (err) {
      console.error("Error al procesar CV:", err);
      alert("Error al procesar el archivo del currículum.");
    } finally {
      btnUploadCv.disabled = false;
      btnUploadCv.innerHTML = originalUploadText;
      btnChangeCv.disabled = false;
      btnChangeCv.innerHTML = originalChangeText;
    }
  }

  btnUploadCv.addEventListener("click", handleSelectCv);
  btnChangeCv.addEventListener("click", handleSelectCv);

  // --- Arrastrar y Soltar (Drag & Drop) de CV (PDF o DOCX) ---

  // 1. Prevenir que el navegador abra el archivo por defecto
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    window.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
    document.body.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  // 2. Resaltar la zona de subida al arrastrar
  ['dragenter', 'dragover'].forEach(eventName => {
    profileEmptyState.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      profileEmptyState.classList.add("drag-over");
    }, false);

    profileLoadedState.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      profileLoadedState.classList.add("drag-over");
    }, false);
  });

  ['dragleave', 'dragend'].forEach(eventName => {
    profileEmptyState.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      profileEmptyState.classList.remove("drag-over");
    }, false);

    profileLoadedState.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      profileLoadedState.classList.remove("drag-over");
    }, false);
  });

  // 3. Manejar el archivo soltado
  async function handleFileDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    profileEmptyState.classList.remove("drag-over");
    profileLoadedState.classList.remove("drag-over");

    const dt = e.dataTransfer;
    if (!dt || !dt.files || dt.files.length === 0) return;

    const file = dt.files[0];
    const fileName = file.name || "Curriculum.pdf";
    const lowerName = fileName.toLowerCase();

    if (!lowerName.endsWith('.pdf') && !lowerName.endsWith('.docx')) {
      alert("Formato no compatible. Por favor arrastra un archivo en formato PDF o Word (.docx).");
      return;
    }

    // Comprobación de API Key
    try {
      const currentState = await window.pywebview.api.get_app_state();
      if (!currentState.has_api_key) {
        alert("Antes de cargar tu currículum, ingresa tu API Key de Google en el botón superior derecho 'Clave API'.");
        btnOpenSettings.click();
        return;
      }
    } catch (err) {
      console.warn("No se pudo comprobar el estado previo:", err);
    }

    const originalUploadText = btnUploadCv.innerHTML;
    const originalChangeText = btnChangeCv.innerHTML;

    btnUploadCv.disabled = true;
    btnUploadCv.innerHTML = `<span>Extrayendo y estructurando con IA...</span>`;
    btnChangeCv.disabled = true;
    btnChangeCv.innerHTML = `<span>Procesando...</span>`;

    const reader = new FileReader();
    reader.onload = async (evt) => {
      const base64Data = evt.target.result;
      const localPath = file.path || null;

      try {
        const res = await window.pywebview.api.process_dropped_file(fileName, base64Data, localPath);
        if (res.success) {
          await loadAppState();
        } else {
          alert(res.error || "Ocurrió un error al procesar el archivo arrastrado.");
        }
      } catch (err) {
        console.error("Error al procesar archivo arrastrado:", err);
        alert("Error de comunicación al procesar el archivo arrastrado.");
      } finally {
        btnUploadCv.disabled = false;
        btnUploadCv.innerHTML = originalUploadText;
        btnChangeCv.disabled = false;
        btnChangeCv.innerHTML = originalChangeText;
      }
    };

    reader.onerror = () => {
      alert("No se pudo leer el archivo arrastrado desde tu equipo.");
      btnUploadCv.disabled = false;
      btnUploadCv.innerHTML = originalUploadText;
      btnChangeCv.disabled = false;
      btnChangeCv.innerHTML = originalChangeText;
    };

    reader.readAsDataURL(file);
  }

  profileEmptyState.addEventListener("drop", handleFileDrop, false);
  profileLoadedState.addEventListener("drop", handleFileDrop, false);

  // --- Pestañas y Acciones de Entrada de Vacante (Paso 2) ---

  if (tabDirectText && tabUrlMode) {
    tabDirectText.addEventListener("click", () => {
      tabDirectText.classList.add("active");
      tabUrlMode.classList.remove("active");
      panelDirectText.classList.remove("hidden");
      panelDirectText.classList.add("active");
      panelUrlMode.classList.add("hidden");
      panelUrlMode.classList.remove("active");
      jobManualTextarea.focus();
    });

    tabUrlMode.addEventListener("click", () => {
      tabUrlMode.classList.add("active");
      tabDirectText.classList.remove("active");
      panelUrlMode.classList.remove("hidden");
      panelUrlMode.classList.add("active");
      panelDirectText.classList.add("hidden");
      panelDirectText.classList.remove("active");
      jobUrlInput.focus();
    });
  }

  if (btnPasteClipboard) {
    btnPasteClipboard.addEventListener("click", async () => {
      try {
        let text = "";
        // 1. Intentar API moderna de portapapeles del navegador
        if (navigator.clipboard && navigator.clipboard.readText) {
          try {
            text = await navigator.clipboard.readText();
          } catch (e) {
            console.warn("navigator.clipboard no disponible directamente:", e);
          }
        }
        // 2. Fallback a método nativo de Python en PyWebView
        if (!text && window.pywebview && window.pywebview.api && window.pywebview.api.get_clipboard_text) {
          const clipRes = await window.pywebview.api.get_clipboard_text();
          if (clipRes && clipRes.success) {
            text = clipRes.text;
          }
        }

        if (text && text.trim()) {
          jobManualTextarea.value = text.trim();
          jobManualTextarea.focus();
        } else {
          alert("No se detectó texto en el portapapeles. Copia la descripción de la vacante e inténtalo de nuevo.");
        }
      } catch (err) {
        console.error("Error al pegar del portapapeles:", err);
        alert("Puedes pegar directamente el texto usando el atajo Ctrl + V.");
      }
    });
  }

  if (btnClearTextarea) {
    btnClearTextarea.addEventListener("click", () => {
      jobManualTextarea.value = "";
      jobManualTextarea.focus();
    });
  }

  // --- Función de Auditoría de Vacante (Entrada Directa o URL) ---

  async function executeJobAudit(mode) {
    let url = "";
    let manualText = "";

    if (mode === "direct") {
      manualText = jobManualTextarea.value.trim();
      if (!manualText) {
        alert("Por favor pega o escribe la descripción de la vacante en el cuadro de texto.");
        jobManualTextarea.focus();
        return;
      }
    } else if (mode === "url") {
      url = jobUrlInput.value.trim();
      if (!url) {
        alert("Por favor ingresa la URL de la vacante.");
        jobUrlInput.focus();
        return;
      }
    } else {
      url = jobUrlInput.value.trim();
      manualText = jobManualTextarea.value.trim();
      if (!url && !manualText) {
        alert("Por favor ingresa la descripción o la URL de la vacante.");
        return;
      }
    }

    // Comprobación de estado previo
    try {
      const state = await window.pywebview.api.get_app_state();
      if (!state.has_api_key) {
        alert("Configura tu API Key de Google antes de analizar vacantes.");
        btnOpenSettings.click();
        return;
      }
      if (!state.has_profile) {
        alert("Primero debes cargar tu currículum en el Paso 1.");
        return;
      }
    } catch (e) {
      console.warn("Error al verificar estado:", e);
    }

    // Iniciar indicador de progreso determinista
    progressCard.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    if (btnAnalyzeDirect) btnAnalyzeDirect.disabled = true;
    if (btnAnalyzeUrl) btnAnalyzeUrl.disabled = true;

    progressStatusText.textContent = "1. Estructurando requisitos y competencias de la oferta...";

    const stepTimer = setTimeout(() => {
      progressStatusText.textContent = "2. Cruzando perfil con estándares ATS en Gemini Flash 3.0+...";
    }, 1200);

    const stepTimer2 = setTimeout(() => {
      progressStatusText.textContent = "3. Validando residencia y calculando viabilidad objetiva (≥ 75%)...";
    }, 2800);

    try {
      const res = await window.pywebview.api.analyze_job_offer(url, manualText);
      clearTimeout(stepTimer);
      clearTimeout(stepTimer2);

      if (res.success && res.analysis) {
        renderAnalysisResults(res.analysis);
      } else if (res.requires_manual) {
        // Fallback para sitios protegidos por login (LinkedIn, Indeed, etc.)
        alert(res.error || "El portal requiere autenticación o captcha. Te transferimos a la pestaña 'Descripción Directa' para que pegues el texto.");
        if (tabDirectText) tabDirectText.click();
        jobManualTextarea.focus();
      } else {
        alert(res.error || "No se pudo realizar el análisis de la vacante.");
      }
    } catch (err) {
      clearTimeout(stepTimer);
      clearTimeout(stepTimer2);
      console.error("Error al auditar vacante:", err);
      alert("Error inesperado durante la auditoría de la vacante.");
    } finally {
      progressCard.classList.add("hidden");
      if (btnAnalyzeDirect) btnAnalyzeDirect.disabled = false;
      if (btnAnalyzeUrl) btnAnalyzeUrl.disabled = false;
    }
  }

  if (btnAnalyzeDirect) {
    btnAnalyzeDirect.addEventListener("click", () => executeJobAudit("direct"));
  }
  if (btnAnalyzeUrl) {
    btnAnalyzeUrl.addEventListener("click", () => executeJobAudit("url"));
  }
  if (jobForm) {
    jobForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const isDirect = tabDirectText && tabDirectText.classList.contains("active");
      executeJobAudit(isDirect ? "direct" : "url");
    });
  }

  // Renderizado dinámico del diagnóstico (principios de diseño de AGENTS.md)
  function renderAnalysisResults(analysis) {
    resultsSection.classList.remove("hidden");
    if (cvSuccessCard) cvSuccessCard.classList.add("hidden");
    const score = analysis.match_percentage || 0;
    matchScoreValue.textContent = `${score}%`;

    const jobTitle = analysis.job_title || "Vacante Analizada";
    const company = analysis.company ? ` en ${analysis.company}` : "";
    jobTitleDetected.textContent = `Puesto detectado: ${jobTitle}${company}`;

    // Lógica estricta de activación de optimización (≥ 75%)
    if (score >= currentMinMatch) {
      matchScoreValue.className = "score-value high-score";
      btnGenerateCv.disabled = false;
      btnGenerateCv.className = "btn-action-unlocked";
      actionHintText.textContent = `¡Afinidad superior al ${currentMinMatch}%! Desbloqueado para adaptar y generar nuevo CV.`;
    } else {
      matchScoreValue.className = "score-value medium-score";
      btnGenerateCv.disabled = true;
      btnGenerateCv.className = "btn-action-locked";
      actionHintText.textContent = `Requiere ≥ ${currentMinMatch}% de afinidad para desbloquear adaptación (tu afinidad actual es ${score}%).`;
    }

    // Columna 1: Requisitos cubiertos (incluye residencia y ubicación)
    const matched = analysis.matched_skills || [];
    listMatchedSkills.innerHTML = matched.length > 0 
      ? matched.map(s => `<li>${escapeHtml(s)}</li>`).join("")
      : "<li>No se identificaron coincidencias directas explícitas.</li>";

    // Columna 2: Habilidades transferibles
    const transferable = analysis.transferable_skills || [];
    listTransferableSkills.innerHTML = transferable.length > 0
      ? transferable.map(s => `<li>${escapeHtml(s)}</li>`).join("")
      : "<li>No se identificaron habilidades secundarias afines.</li>";

    // Columna 3: Brechas detectadas (sin penalización por residencia)
    const missing = analysis.missing_skills || [];
    listMissingSkills.innerHTML = missing.length > 0
      ? missing.map(s => `<li>${escapeHtml(s)}</li>`).join("")
      : "<li>¡Excelente! No se detectaron brechas críticas en tu perfil.</li>";

    // Feedback de mentor ejecutivo
    mentorFeedbackText.textContent = analysis.mentor_feedback || 
      "El análisis concluyó la evaluación de competencias frente a la vacante.";

    // Guardar último análisis en memoria de sesión para la Fase 5 (Generación de PDF)
    window._lastJobAnalysis = analysis;

    // Desplazar suavemente hacia los resultados
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // --- Generación y Descarga de CV Adaptado (Fase 5) ---

  btnGenerateCv.addEventListener("click", async () => {
    if (!window._lastJobAnalysis) {
      alert("No hay ningún análisis de vacante activo.");
      return;
    }

    if ((window._lastJobAnalysis.match_percentage || 0) < currentMinMatch) {
      alert(`Se requiere un mínimo de ${currentMinMatch}% de afinidad para generar el currículum adaptado.`);
      return;
    }

    const originalText = btnGenerateText.textContent;
    btnGenerateCv.disabled = true;
    btnGenerateText.textContent = "Adaptando con IA y generando PDF ATS...";

    try {
      const res = await window.pywebview.api.generate_adapted_cv(window._lastJobAnalysis);

      if (res.success) {
        window._lastGeneratedPdfPath = res.file_path;
        cvGeneratedFilename.textContent = res.filename || "Curriculum_Adaptado.pdf";
        cvSuccessCard.classList.remove("hidden");
        cvSuccessCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else if (!res.cancelled) {
        alert(res.error || "Ocurrió un error al generar el currículum adaptado.");
      }
    } catch (err) {
      console.error("Error al generar CV adaptado:", err);
      alert("Error al comunicarse con el motor de generación de PDF.");
    } finally {
      btnGenerateCv.disabled = false;
      btnGenerateText.textContent = originalText;
    }
  });

  btnOpenPdf.addEventListener("click", async () => {
    if (!window._lastGeneratedPdfPath) return;
    try {
      const res = await window.pywebview.api.open_file(window._lastGeneratedPdfPath);
      if (!res.success) {
        alert(res.error || "No se pudo abrir el archivo PDF.");
      }
    } catch (err) {
      console.error("Error al abrir archivo:", err);
    }
  });

  btnOpenFolder.addEventListener("click", async () => {
    if (!window._lastGeneratedPdfPath) return;
    try {
      const res = await window.pywebview.api.open_containing_folder(window._lastGeneratedPdfPath);
      if (!res.success) {
        alert(res.error || "No se pudo abrir la carpeta en el explorador.");
      }
    } catch (err) {
      console.error("Error al abrir carpeta:", err);
    }
  });

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Iniciar la aplicación
  initApp();
});
