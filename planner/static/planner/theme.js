(function () {
  const key = "app-theme";
  const root = document.documentElement;
  const btn = document.getElementById("themeToggle");

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    if (btn) btn.textContent = theme === "light" ? "☀️ Тема" : "🌙 Тема";
  }

  const saved = localStorage.getItem(key);
  const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  const initial = saved || (prefersLight ? "light" : "dark");
  apply(initial);

  if (btn) {
    btn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      localStorage.setItem(key, next);
      apply(next);
    });
  }
})();
