export async function submitFeedback(feedback) {
  const res = await fetch("http://localhost:8000/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedback),
  });
  return res.json();
}

export async function getRecommendations(file) {
  const form = new FormData();
  form.append("file", file);
  
  const res = await fetch("http://localhost:8000/recommend", {
    method: "POST",
    body: form,
  });
  
  if (!res.ok) {
    throw new Error(`Server returned ${res.status}`);
  }
  
  return res.json();
}
