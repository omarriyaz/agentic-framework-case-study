export const streamAIMessage = async (userQuery, history = [], rememberedModel = null, mode = "homeowner", onToken, onDone) => {
  const cleanHistory = history
    .filter(m => (m.role === "user" || m.role === "assistant") && m.content)
    .map(m => ({ role: m.role, content: m.content }));

  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userQuery, history: cleanHistory, remembered_model: rememberedModel, mode }),
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(part.slice(6));
        if (data.type === "token") onToken(data.content);
        else if (data.type === "done") onDone(data);
      } catch {}
    }
  }
};
