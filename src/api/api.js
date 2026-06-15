export const getAIMessage = async (userQuery, history = [], rememberedModel = null) => {
  const cleanHistory = history
    .filter(m => (m.role === "user" || m.role === "assistant") && m.content)
    .map(m => ({ role: m.role, content: m.content }));

  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userQuery, history: cleanHistory, remembered_model: rememberedModel }),
  });

  const data = await res.json();

  return {
    role: "assistant",
    content: data.response,
    parts: data.parts || [],
    chips: data.chips || [],
    detected_model: data.detected_model || null,
  };
};
