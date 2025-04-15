import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file first.");
      return;
    }

    setProcessing(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        "http://localhost:5000/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      if (response.data.error) {
        setError(response.data.error);
      } else {
        setResult(response.data);
      }
    } catch (err) {
      setError("Error processing file. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="App">
      <h1>🎤 Audio Noise Filtering & Speech Detection</h1>
      <input type="file" accept="audio/*" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={processing}>
        {processing ? "⏳ Processing..." : "🚀 Upload & Process"}
      </button>

      {error && <p className="error">⚠️ {error}</p>}

      {processing && <p className="loading">🔄 Processing your audio...</p>}

      {result && (
        <div className="result">
          <p>
            <strong>🗣️ Human Voice Detected:</strong>{" "}
            {result.human_voice ? "✅ Yes" : "❌ No"}
          </p>
          <p>
            <strong>📜 Transcription:</strong> {result.transcription || "N/A"}
          </p>
          {result.download_url && (
            <a href={`http://localhost:5000${result.download_url}`} download>
              🎧 Download Processed Audio
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
