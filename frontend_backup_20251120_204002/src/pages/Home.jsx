import React, { useState } from "react";
import "./Home.css";
import Navbar from "../components/Navbar";
import { uploadPDF } from "../SupaBase/uploadPDF"; // adjust path if needed

const Home = () => {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState("");

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            alert("Please upload a PDF file.");
            return;
        }

        try {
            console.log("test");
            setStatus("Uploading...");

            // Use the JS helper to upload the PDF
            const result = await uploadPDF(file);

            console.log("Upload successful:", result);
            setStatus(`Upload successful! Doc ID: ${result.qdrant_doc_id}`);
        } catch (err) {
            setStatus("Upload failed.");
        }
    };

    return (
        <div className="home-container">
            <Navbar />

            <div className="home-content">
                <div className="home-left">
                    <h1>
                        XITM <span>RFP Analyzer</span>
                    </h1>
                    <p className="subtitle">
                        Upload your RFPs and ask questions about the document
                    </p>
                </div>

                <form className="upload-box" onSubmit={handleSubmit}>
                    <h2>Upload Your PDF</h2>
                    <input
                        id="file-upload"
                        type="file"
                        accept="application/pdf"
                        onChange={handleFileChange}
                        style={{ display: "none" }}
                    />

                    <label htmlFor="file-upload" className="upload-label">
                        Choose File
                    </label>
                    
                    <button type="submit">Upload</button>
                    {file && <p>Selected file: {file.name}</p>}

                    {status && <p className="upload-status">{status}</p>}
                </form>
            </div>
        </div>
    );
};

export default Home;