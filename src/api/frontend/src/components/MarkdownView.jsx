// MarkdownView.tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";      // tables, strikethrough, task lists
import rehypeRaw from "rehype-raw";      // render inline HTML in md (be careful)

export default function MarkdownView( { md } ) {
  return (
    <div className="prose">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
        {md}
      </ReactMarkdown>
    </div>
  );
}
