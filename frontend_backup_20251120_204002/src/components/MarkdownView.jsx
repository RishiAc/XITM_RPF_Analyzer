import React from "react";

const MarkdownView = ({ md }) => {
  // Simple markdown rendering - you can enhance this with a library like react-markdown
  const formatMarkdown = (text) => {
    if (!text) return "";
    
    // Ensure text is a string
    if (typeof text !== "string") {
      // If it's an object, try to stringify it or get a meaningful representation
      if (typeof text === "object") {
        text = JSON.stringify(text, null, 2);
      } else {
        text = String(text);
      }
    }
    
    // Convert markdown-like formatting to HTML
    let formatted = text
      // Bold
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      // Italic
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      // Code blocks
      .replace(/`(.*?)`/g, "<code>$1</code>")
      // Line breaks
      .replace(/\n/g, "<br />");
    
    return formatted;
  };

  return (
    <div
      className="markdown-view"
      dangerouslySetInnerHTML={{ __html: formatMarkdown(md) }}
    />
  );
};

export default MarkdownView;

