async function runProbe() {
  const out = document.getElementById("out");
  const report = {
    hasRequire: typeof require === "function",
    premierepro: null,
    error: null
  };
  try {
    const ppro = require("premierepro");
    const app = ppro.app;
    report.premierepro = {
      appKeys: Object.keys(app || {}).sort(),
      hasProject: Boolean(app && app.project),
      projectKeys: app && app.project ? Object.keys(app.project).sort() : []
    };
  } catch (error) {
    report.error = String(error && error.stack ? error.stack : error);
  }
  out.textContent = JSON.stringify(report, null, 2);
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("run").addEventListener("click", runProbe);
});

