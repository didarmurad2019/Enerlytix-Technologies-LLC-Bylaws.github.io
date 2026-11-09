(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Mobile menu
  var menu = $(".menu"), nav = $("#nav");
  if (menu && nav) {
    menu.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", open);
    });
    $$("a", nav).forEach(function (a) { a.addEventListener("click", function () { nav.classList.remove("open"); }); });
  }

  var doc = $("#doc");
  if (!doc) return;

  // Print / Save as PDF
  var pr = $("#print");
  if (pr) pr.addEventListener("click", function () { window.print(); });

  // Copy link
  var sh = $("#share");
  if (sh) sh.addEventListener("click", function () {
    var url = location.href.split("#")[0], done = function () { sh.textContent = "Link copied"; setTimeout(function () { sh.textContent = "Copy link"; }, 1800); };
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link:", url); });
    else window.prompt("Copy this link:", url);
  });

  // Scroll-spy
  var links = $$(".toc nav a"), map = {};
  links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { links.forEach(function (l) { l.classList.remove("on"); }); var a = map[e.target.id]; if (a) a.classList.add("on"); }
      });
    }, { rootMargin: "-90px 0px -70% 0px" });
    $$(".article").forEach(function (s) { io.observe(s); });
  }

  // Search
  var q = $("#q"), count = $("#count"), none = $("#none"), clauses = $$(".clause"), arts = $$(".article");
  var orig = new Map();
  clauses.forEach(function (c) { orig.set(c, c.innerHTML); });
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function run() {
    var term = q.value.trim(), shown = 0;
    clauses.forEach(function (c) { c.innerHTML = orig.get(c); });
    if (!term) {
      clauses.forEach(function (c) { c.hidden = false; });
      arts.forEach(function (a) { a.hidden = false; });
      links.forEach(function (l) { l.parentNode.hidden = false; });
      count.textContent = ""; none.hidden = true; return;
    }
    var re = new RegExp("(" + esc(term) + ")", "gi");
    clauses.forEach(function (c) {
      var hit = c.textContent.toLowerCase().indexOf(term.toLowerCase()) > -1;
      c.hidden = !hit;
      if (hit) {
        shown++;
        var w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT), nodes = [], n;
        while ((n = w.nextNode())) nodes.push(n);
        nodes.forEach(function (t) {
          if (!re.test(t.nodeValue)) return; re.lastIndex = 0;
          var span = document.createElement("span"); span.innerHTML = t.nodeValue.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(re, "<mark>$1</mark>");
          t.parentNode.replaceChild(span, t);
        });
      }
    });
    arts.forEach(function (a) {
      var any = $$(".clause", a).some(function (c) { return !c.hidden; }) || (!$(".clause", a) && a.textContent.toLowerCase().indexOf(term.toLowerCase()) > -1);
      a.hidden = !any; if (map[a.id]) map[a.id].parentNode.hidden = !any; if (!any) return;
    });
    count.textContent = shown + (shown === 1 ? " clause" : " clauses") + " found";
    none.hidden = shown > 0 || arts.some(function (a) { return !a.hidden; });
  }
  var t; q.addEventListener("input", function () { clearTimeout(t); t = setTimeout(run, 140); });

  // Highlight clause targeted by hash
  function hl() { var c = location.hash && $(location.hash); if (c && c.classList.contains("clause")) { c.classList.remove("hit"); void c.offsetWidth; c.classList.add("hit"); } }
  window.addEventListener("hashchange", hl); hl();
  window.addEventListener("beforeprint", function () { q.value = ""; run(); });
})();
