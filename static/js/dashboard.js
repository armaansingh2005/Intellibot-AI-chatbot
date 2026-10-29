(() => {
  const rows = document.getElementById("conversation-rows");
  if (!rows) return;
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let page = 1;
  let activityChart;
  let intentChart;
  const colors = ["#5758d8", "#33a58e", "#f0a14a", "#df6b7d", "#4f9dc6", "#8e71c9", "#73a673", "#d37d42"];

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  async function getJSON(url) {
    const response = await fetch(url, { headers: { Accept: "application/json", "X-CSRFToken": csrf } });
    if (!response.ok) {
      if (response.status === 401) location.href = "/admin/login";
      throw new Error("Dashboard data could not be loaded. Please try again.");
    }
    return response.json();
  }

  function empty(target, message) {
    target.replaceChildren(element("p", message, "empty-inline"));
  }

  function drawCharts(data) {
    if (typeof Chart === "undefined") return;
    const styles = getComputedStyle(document.documentElement);
    const chartText = styles.getPropertyValue("--chart-text").trim();
    const chartGrid = styles.getPropertyValue("--chart-grid").trim();
    const activity = document.getElementById("activity-chart");
    const intent = document.getElementById("intent-chart");
    activityChart?.destroy();
    intentChart?.destroy();
    activityChart = new Chart(activity, {
      type: "line",
      data: {
        labels: data.daily.map((item) => new Date(`${item.date}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })),
        datasets: [
          { label: "Conversations", data: data.daily.map((item) => item.conversations), borderColor: colors[0], backgroundColor: "rgba(87,88,216,.10)", fill: true, tension: .35 },
          { label: "Messages", data: data.daily.map((item) => item.messages), borderColor: colors[1], backgroundColor: "transparent", tension: .35 },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { color: chartText } } }, scales: { x: { ticks: { color: chartText }, grid: { color: chartGrid } }, y: { beginAtZero: true, ticks: { precision: 0, color: chartText }, grid: { color: chartGrid } } } },
    });
    if (data.intent_distribution.length) {
      intentChart = new Chart(intent, {
        type: "doughnut",
        data: { labels: data.intent_distribution.map((item) => item.intent.replaceAll("_", " ")), datasets: [{ data: data.intent_distribution.map((item) => item.count), backgroundColor: colors, borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: "68%", plugins: { legend: { position: "bottom", labels: { usePointStyle: true, padding: 15, color: chartText } } } },
      });
    } else {
      intent.parentElement.textContent = "Intent data will appear after your first message.";
    }
  }

  async function loadAnalytics() {
    const data = await getJSON("/api/admin/analytics");
    const kpis = data.kpis;
    document.getElementById("kpi-conversations").textContent = kpis.total_conversations.toLocaleString();
    document.getElementById("kpi-messages").textContent = kpis.total_messages.toLocaleString();
    document.getElementById("kpi-average").textContent = kpis.average_messages_per_conversation.toFixed(1);
    document.getElementById("kpi-intent").textContent = kpis.most_frequent_intent.replaceAll("_", " ");
    document.getElementById("kpi-fallback").textContent = `${(kpis.fallback_rate * 100).toFixed(1)}%`;
    document.getElementById("kpi-response").textContent = `${kpis.average_response_time_ms.toFixed(1)} ms`;
    drawCharts(data);
    const faqTarget = document.getElementById("frequent-questions");
    faqTarget.replaceChildren();
    if (!data.frequent_questions.length) empty(faqTarget, "Frequently asked questions will appear as visitors chat.");
    data.frequent_questions.forEach((item) => {
      const line = element("div", undefined, "compact-row");
      line.append(element("span", item.question), element("b", String(item.count)));
      faqTarget.append(line);
    });
    const fallbackTarget = document.getElementById("fallback-questions");
    fallbackTarget.replaceChildren();
    if (!data.fallback_queries.length) empty(fallbackTarget, "No unanswered questions yet. Great work!");
    data.fallback_queries.forEach((item) => {
      const line = element("div", undefined, "compact-row fallback-row");
      line.append(element("span", item.question), element("time", new Date(item.created_at).toLocaleDateString()));
      fallbackTarget.append(line);
    });
  }

  async function loadConversations() {
    const query = new URLSearchParams({
      page: String(page),
      q: document.getElementById("search-query").value.trim(),
      intent: document.getElementById("intent-filter").value.trim(),
      date_from: document.getElementById("date-from").value,
      date_to: document.getElementById("date-to").value,
    });
    const data = await getJSON(`/api/admin/conversations?${query}`);
    rows.replaceChildren();
    document.getElementById("conversation-total").textContent = `${data.total} conversations found`;
    document.getElementById("page-indicator").textContent = `Page ${data.page} of ${Math.max(data.pages, 1)}`;
    document.getElementById("page-previous").disabled = data.page <= 1;
    document.getElementById("page-next").disabled = data.page >= data.pages;
    if (!data.conversations.length) {
      const row = element("tr");
      const cell = element("td", "No conversations match this filter yet.", "empty-inline");
      cell.colSpan = 5;
      row.append(cell);
      rows.append(row);
    }
    data.conversations.forEach((item) => {
      const row = element("tr");
      row.append(element("td", `#${item.id}`, "conversation-number"));
      row.append(element("td", item.preview || "—", "preview-cell"));
      row.append(element("td", String(item.message_count)));
      row.append(element("td", new Date(item.last_activity).toLocaleString()));
      const cell = element("td");
      const link = element("a", "Open →", "table-link");
      link.href = `/admin/conversations/${item.id}`;
      cell.append(link);
      row.append(cell);
      rows.append(row);
    });
  }

  function showError(error) {
    const target = document.getElementById("dashboard-error");
    target.textContent = error.message;
    target.classList.remove("hidden");
  }

  document.getElementById("conversation-search").addEventListener("submit", (event) => {
    event.preventDefault();
    page = 1;
    loadConversations().catch(showError);
  });
  document.getElementById("page-previous").addEventListener("click", () => { page -= 1; loadConversations().catch(showError); });
  document.getElementById("page-next").addEventListener("click", () => { page += 1; loadConversations().catch(showError); });
  document.addEventListener("intellibot:themechange", () => loadAnalytics().catch(showError));
  Promise.all([loadAnalytics(), loadConversations()]).catch(showError);
})();
