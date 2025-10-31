import { useRef, useState, useEffect } from "react";
import { useData } from "../DataContext/DataContext";

export default function CsvUploader() {
    const fileInputRef = useRef();
    const { setCsvData, deleteMessage } = useData();
    const [message, setMessage] = useState("");
    const [processedFile, setProcessedFile] = useState("");

    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                setMessage("");
            }, 5000); // 5 seconds
            return () => clearTimeout(timer);
        }
    }, [message]);

    
    function handleFileUpload(event) {
        const file = event.target.files[0];  
        if (!file) return;

        setMessage(`Uploading ${file.name}...`);
        setProcessedFile("");

        const formData = new FormData();
        formData.append("file", file);
        
        fetch("http://localhost:5001/upload", {   
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
                        } catch (e) {
                            // Not a json error, use text
                        }
                        throw new Error(error);
                    });
                }
                return res.json();
            })
            .then((json) => {
                console.log("Received JSON from Flask:", json);
                setCsvData(json); // pass data to DataContext
                deleteMessage(); // clear any previous messages
                setMessage(`Upload of '${file.name}' successful!`);
                setProcessedFile(file.name);
            })
            .catch((err) => {
                console.error("Upload error:", err);
                setMessage(`Upload failed: ${err.message}`);
                setProcessedFile("");
            });
    }

    return(
        <div>
            <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".csv"
            onChange={handleFileUpload}
            />
            <div>
            <button 
                className="btn"
                onClick={ () => fileInputRef.current.click() }
            >
                Upload patient CSV
                <span class="material-symbols-outlined">
                    upload
                </span>                
            </button>

            </div>


            {message ? (
                <div style={{ 
                    marginTop: "10px", 
                    color: message.includes("successful") ? "green" : message.includes("failed") ? "red" : "inherit"
                }}>
                    {message}
                </div>
            ) : processedFile && (
                <div style={{ marginTop: "10px", color: "black" }}>
                    Current patient: {processedFile}
                </div>
            )}
        </div>
    );
}



