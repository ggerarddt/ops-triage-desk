// Populate form fields when a quick-load example button is clicked.
// Uses data-* attributes on each button so the browser does all the work
// — no server round-trip required.

document.addEventListener("DOMContentLoaded", function () {
  var buttons = document.querySelectorAll(".example-btn");
  for (var i = 0; i < buttons.length; i++) {
    (function (btn) {
      btn.addEventListener("click", function () {
        document.getElementById("title").value = btn.dataset.title || "";
        document.getElementById("description").value = btn.dataset.description || "";
        document.getElementById("business_area").value = btn.dataset.business_area || "";
        document.getElementById("system_affected").value = btn.dataset.system_affected || "";
        document.getElementById("impact_level").value = btn.dataset.impact_level || "";
        document.getElementById("urgency").value = btn.dataset.urgency || "";
        document.getElementById("customer_impact").value = btn.dataset.customer_impact || "";
      });
    })(buttons[i]);
  }
});
