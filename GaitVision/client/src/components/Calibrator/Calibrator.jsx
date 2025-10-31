import { useRef, useEffect, useState } from "react";
import { useData } from "../DataContext/DataContext";
// import React, { useState } from 'react';

export default function Calibrator() {
    const fileInputRef = useRef();
    const { setCalibrationData, message, setMessage, setPcaSuggestions } = useData();
    const [processedFile, setProcessedFile] = useState("");

    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                setMessage("");
            }, 5000); // 5 seconds
            return () => clearTimeout(timer);
        }
    }, [message]);

    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                setMessage("");
            }, 5000); // 5 seconds
            return () => clearTimeout(timer);
        }
    }, [message]);

    function handleBigFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        setMessage(`Normalising ${file.name} and generating PCA suggestions...`);
        setProcessedFile("");

        const formData = new FormData();
        formData.append("file", file);
        
        fetch("http://localhost:5001/normalise", {
            method: "POST",
            body: formData,
        })
            .then((res) => {
                if (!res.ok) {
                    return res.text().then(text => {
                        let error = text;
                        try {
                            const jsonError = JSON.parse(text);
                            error = jsonError.error || text;
                        } catch (e) { /* Not a json error, use text */ }
                        throw new Error(error);
                    });
                }
                return res.json();
            })
            .then((json) => {
                try {
                    console.log("Raw API response:", json);
                    
                    const normalizationData = json.normalization_data;
                    const pcaSuggestions = json.pca_suggestions;

                    if (!normalizationData || !Array.isArray(normalizationData.variables)) {
                        console.error("Invalid response format:", json);
                        setMessage("Invalid data format received from API.");
                        return;
                    }
                    
                    console.log("=== Calibration Data Received ===");
                    setCalibrationData(normalizationData.variables);

                    console.log("=== PCA Suggestions Received ===");
                    setPcaSuggestions(pcaSuggestions);

                    setMessage(`'${file.name}' processed successfully!`);
                    setProcessedFile(file.name);
                } catch (err) {
                    console.error("Error processing data:", err);
                    setMessage("Failed to store data.");
                    setProcessedFile("");
                }
            })
            .catch((err) => {
                console.error("Upload error:", err);
                setMessage(`Upload failed: ${err.message}`);
                setProcessedFile("");
            });
    }

    return (
        <div>
            <input
                type="file"
                ref={fileInputRef}
                style={{ display: "none" }}
                accept=".csv"
                onChange={handleBigFileUpload}
            />
            <button 
                className="btn"
                onClick={() => fileInputRef.current.click()}
            >
                Calibrate and Suggest
                <span className="material-symbols-outlined">
                    upload
                </span>                             
            </button>
            
            {message ? (
                <div style={{ 
                    marginTop: "10px", 
                    color: message.includes("successful") ? "green" : message.includes("failed") || message.includes("Invalid") ? "red" : "inherit"
                }}>
                    {message}
                </div>
            ) : processedFile && (
                <div style={{ marginTop: "10px", color: "black" }}>
                    Current dataset: {processedFile}
                </div>
            )}
        </div>
    );
}