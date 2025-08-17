export async function submitFeedback(feedback) {
  const res = await fetch("/submit_feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(feedback),
  });
  return res.json();
}
