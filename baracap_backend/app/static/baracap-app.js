// Backward-compatible entrypoint for older exported BARACAP pages.
// The canonical frontend is implemented in baracap-ui.js.
(function () {
  if (window.BARACAP_UI_LOADED) return;
  window.BARACAP_UI_LOADED = true;
  var script = document.createElement("script");
  script.src = "/baracap-ui.js?v=20260629a";
  script.defer = true;
  document.head.appendChild(script);
})();
