// static/admin/schemas/column_constraints_toggle.js
(function () {
  function toggleConstraints() {
    var dt = document.getElementById("id_data_type");
    if (!dt) return;
    var val = dt.value;

    var decRows = ["id_decimal_places", "id_dec_min", "id_dec_max"];
    var strRows = ["id_character_minimum", "id_character_limit", "id_all_caps"];

    function show(id, show) {
      var el = document.getElementById(id);
      if (!el) return;
      var row =
        el.closest(".form-row") || el.closest(".fieldBox") || el.parentElement;
      if (row) row.style.display = show ? "" : "none";
    }

    if (val === "decimal" || val === "number") {
      // treat number like decimal
      decRows.forEach(function (id) {
        show(id, true);
      });
      strRows.forEach(function (id) {
        show(id, false);
      });
    } else if (val === "string") {
      decRows.forEach(function (id) {
        show(id, false);
      });
      strRows.forEach(function (id) {
        show(id, true);
      });
    } else {
      decRows.forEach(function (id) {
        show(id, false);
      });
      strRows.forEach(function (id) {
        show(id, false);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var dt = document.getElementById("id_data_type");
    if (dt) {
      dt.addEventListener("change", toggleConstraints);
      toggleConstraints();
    }
  });
})();
