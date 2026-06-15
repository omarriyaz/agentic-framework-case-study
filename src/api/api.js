export const getAIMessage = async (userQuery, history = []) => {
  const res = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userQuery, history }),
  });

  const data = await res.json();

  return {
    role: "assistant",
    content: data.response,
    parts: data.parts || [],
  };
};
