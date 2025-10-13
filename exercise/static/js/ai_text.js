// ESM helpers for rendering streamed AI text safely with simple Markdown

export function escapeHtml(text) {
  return (text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Replace **bold** sections with <strong>bold</strong>
export function applyMarkdownBold(text) {
  return (text || '').replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');
}

// Convert leading # / ## headings to simple block headings
function applyHeadings(text) {
  const lines = (text || '').split('\n');
  const out = [];
  for (const line of lines) {
    if (/^\s*##\s+/.test(line)) {
      const content = line.replace(/^\s*##\s+/, '');
      out.push(`<div class=\"ai-h2\"><strong>${content}</strong></div>`);
    } else if (/^\s*#\s+/.test(line)) {
      const content = line.replace(/^\s*#\s+/, '');
      out.push(`<div class=\"ai-h1\"><strong>${content}</strong></div>`);
    } else {
      out.push(line);
    }
  }
  return out.join('\n');
}

// Decode SSE chunk token to actual newlines
export function decodeSseChunk(data) {
  return (data || '').replace(/\|\|NEWLINE\|\|/g, '\n');
}

// Format the full accumulated text into safe HTML
export function formatAiText(text) {
  const escaped = escapeHtml(text || '');
  const withBold = applyMarkdownBold(escaped);
  const withHeadings = applyHeadings(withBold);
  return withHeadings.replace(/\n/g, '<br>');
}
