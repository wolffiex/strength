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

// Decode SSE chunk token to actual newlines
export function decodeSseChunk(data) {
  return (data || '').replace(/\|\|NEWLINE\|\|/g, '\n');
}

// Format the full accumulated text into safe HTML
export function formatAiText(text) {
  const escaped = escapeHtml(text || '');
  const withBold = applyMarkdownBold(escaped);
  return withBold.replace(/\n/g, '<br>');
}

