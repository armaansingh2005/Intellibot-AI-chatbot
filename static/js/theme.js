(() => {
  const button = document.getElementById("theme-toggle");
  if (!button) return;
  const icon = button.querySelector(".theme-toggle-icon");
  const label = button.querySelector(".theme-toggle-label");
  const storageKey = "intellibot-theme";

  function applyTheme(theme, persist) {
    document.documentElement.dataset.theme = theme;
    const dark = theme === "dark";
    button.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} mode`);
    button.setAttribute("aria-pressed", String(dark));
    button.title = `Switch to ${dark ? "light" : "dark"} mode`;
    icon.textContent = dark ? "☼" : "☾";
    label.textContent = dark ? "Light" : "Dark";
    document.querySelector('meta[name="theme-color"]').content = dark ? "#121722" : "#f5f7fb";
    if (persist) {
      try {
        localStorage.setItem(storageKey, theme);
      } catch {
        button.setAttribute("aria-label", "Theme changed for this page only");
      }
    }
    document.dispatchEvent(new CustomEvent("intellibot:themechange", { detail: { theme } }));
  }

  button.addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
  });
  applyTheme(document.documentElement.dataset.theme || "light", false);
})();
