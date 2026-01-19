let mediaRecorder = null;
let chunks = [];
let startTime = null;

function setStatus(msg) {
  const el = document.getElementById("recStatus");
  if (el) el.textContent = msg;
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    startTime = Date.now();

    const opts = {};
    // Algunos navegadores no aceptan mimeType explícito
    try { opts.mimeType = "audio/webm"; } catch(e) {}

    mediaRecorder = new MediaRecorder(stream, opts);

    mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    mediaRecorder.onstop = () => stream.getTracks().forEach(t => t.stop());

    mediaRecorder.start();
    setStatus("Grabando…");
  } catch (err) {
    console.error(err);
    alert("No se pudo acceder al micrófono. Revisa permisos.");
  }
}

function stopRecording() {
  if (!mediaRecorder) return;
  mediaRecorder.stop();
  setStatus("Grabación detenida. Ahora puedes subirla.");
}

async function uploadRecording(uploadUrl) {
  if (!chunks.length) return alert("No hay audio grabado.");
  const blob = new Blob(chunks, { type: "audio/webm" });
  const secs = startTime ? Math.round((Date.now() - startTime) / 1000) : "";

  const fd = new FormData();
  fd.append("audio", blob, "recording.webm");
  fd.append("audio_seconds", String(secs));

  setStatus("Subiendo audio…");
  const res = await fetch(uploadUrl, { method: "POST", body: fd });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    setStatus("Error al subir.");
    alert(data.error || "Error");
    return;
  }
  setStatus("Audio subido ✅");
}
