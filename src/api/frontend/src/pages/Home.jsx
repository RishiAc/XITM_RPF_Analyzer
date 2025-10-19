import React, { useState } from "react";
import "./Home.css";
import Navbar from "../components/Navbar";

const Home = () => {
	const [file, setFile] = useState(null);

	const handleFileChange = (e) => {
		setFile(e.target.files[0]);
	};

	const handleSubmit = (e) => {
		e.preventDefault();
		if (file) {
			console.log("Uploaded PDF:", file.name);
			// insert backend call here
		} else {
			alert("Please upload a PDF file.");
		}
	};

	return (
		<div className="home-container">
			<Navbar />

			<form className="upload-box" onSubmit={handleSubmit}>
				<h2>Upload Your PDF</h2>
				<input
				type="file"
				accept="application/pdf"
				onChange={handleFileChange}
				/>
				<button type="submit">Upload</button>
				{file && <p>Selected file: {file.	name}</p>}
			</form>
		</div>
	);
}
export default Home;
