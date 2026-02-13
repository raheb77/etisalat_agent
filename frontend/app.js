const DEFAULT_BASE = "http://localhost:8000";

const form = document.getElementById("queryForm");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submitBtn");
const sampleBtn = document.getElementById("sampleBtn");
const apiBaseInput = document.getElementById("apiBase");
const backendStatus = document.getElementById("backendStatus");

const emptyState = document.getElementById("emptyState");
const responseContent = document.getElementById("responseContent");
const answerText = document.getElementById("answerText");
const confidenceBar = document.getElementById("confidenceBar");
const confidenceValue = document.getElementById("confidenceValue");
const categoryValue = document.getElementById("categoryValue");
const handoffValue = document.getElementById("handoffValue");
const handoffReason = document.getElementById("handoffReason");
const stepsBlock = document.getElementById("stepsBlock");
const stepsList = document.getElementById("stepsList");
const citationsList = document.getElementById("citationsList");
const citationsEmpty = document.getElementById("citationsEmpty");

const storedBase = localStorage.getItem("csr_api_base") || DEFAULT_BASE;
apiBaseInput.value = storedBase;

apiBaseInput.addEventListener("change", () => {
  const value = apiBaseInput.value.trim() || DEFAULT_BASE;
  apiBaseInput.value = value;
  localStorage.setItem("csr_api_base", value);
  pingBackend();
});

sampleBtn.addEventListener("click", () => {
  form.question.value =
    "How long does it take to port a mobile number and what is the maximum wait time?";
  form.categoryHint.value = "number_porting";
  form.locale.value = "en-US";
});

const setStatus = (message, tone = "") => {
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
};

const showResponse = () => {
  emptyState.hidden = true;
  responseContent.hidden = false;
};

const resetResponse = () => {
  responseContent.hidden = true;
  emptyState.hidden = false;
  answerText.textContent = "";
  confidenceBar.style.width = "0%";
  confidenceValue.textContent = "";
  categoryValue.textContent = "";
  handoffValue.textContent = "";
  handoffReason.textContent = "";
  stepsList.innerHTML = "";
  stepsBlock.hidden = true;
  citationsList.innerHTML = "";
  citationsEmpty.hidden = false;
};

const formatPercent = (value) => `${Math.round(value * 100)}%`;

const renderCitations = (citations) => {
  citationsList.innerHTML = "";
  if (!citations || citations.length === 0) {
    citationsEmpty.hidden = false;
    return;
  }
  citationsEmpty.hidden = true;

  citations.forEach((item) => {
    const card = document.createElement("div");
    card.className = "citation";

    const source = document.createElement("span");
    const sourceLabel = document.createElement("span");
    sourceLabel.className = "label";
    sourceLabel.textContent = "Source";
    const sourceValue = document.createElement("span");
    sourceValue.textContent = item.source;
    source.append(sourceLabel, sourceValue);

    const chunk = document.createElement("span");
    const chunkLabel = document.createElement("span");
    chunkLabel.className = "label";
    chunkLabel.textContent = "Chunk";
    const chunkValue = document.createElement("span");
    chunkValue.textContent = item.chunk_id;
    chunk.append(chunkLabel, chunkValue);

    const score = document.createElement("span");
    const scoreLabel = document.createElement("span");
    scoreLabel.className = "label";
    scoreLabel.textContent = "Score";
    const scoreValue = document.createElement("span");
    scoreValue.textContent = Number(item.score).toFixed(3);
    score.append(scoreLabel, scoreValue);

    card.append(source, chunk, score);
    citationsList.appendChild(card);
  });
};

const renderSteps = (steps) => {
  stepsList.innerHTML = "";
  if (!steps || steps.length === 0) {
    stepsBlock.hidden = true;
    return;
  }
  stepsBlock.hidden = false;
  steps.forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    stepsList.appendChild(li);
  });
};

const pingBackend = async () => {
  const base = apiBaseInput.value.trim() || DEFAULT_BASE;
  try {
    const response = await fetch(`${base}/health`);
    backendStatus.textContent = response.ok ? "Online" : "Degraded";
  } catch (error) {
    backendStatus.textContent = "Offline";
  }
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = form.question.value.trim();
  if (!question) {
    setStatus("Please enter a question.", "error");
    return;
  }

  const payload = {
    question,
    category_hint: form.categoryHint.value.trim() || undefined,
    locale: form.locale.value,
    channel: "csr_ui",
  };

  const base = apiBaseInput.value.trim() || DEFAULT_BASE;
  submitBtn.disabled = true;
  setStatus("Running query...", "loading");

  try {
    const response = await fetch(`${base}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed (${response.status}).`);
    }

    const data = await response.json();
    showResponse();

    answerText.textContent = data.answer || "";
    const confidence = Number(data.confidence ?? 0);
    confidenceBar.style.width = `${Math.round(confidence * 100)}%`;
    confidenceValue.textContent = formatPercent(confidence);
    categoryValue.textContent = data.category || "Unknown";
    handoffValue.textContent = data.handoff ? "Yes" : "No";
    handoffReason.textContent = data.handoff_reason || "-";

    renderSteps(data.steps || []);
    renderCitations(data.citations || []);

    setStatus("Query complete.");
  } catch (error) {
    resetResponse();
    setStatus(`Error: ${error.message}`, "error");
  } finally {
    submitBtn.disabled = false;
  }
});

resetResponse();
pingBackend();
