/* ============================================================
   Kepler 404 · Interactions
   Custom cursor · particle network · mobile nav · theme toggle
   FAQ accordion · scroll reveal · upload demo · 3-way compare
   ============================================================ */
(function () {
  "use strict";

  const body = document.body;
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = window.matchMedia("(hover: none)").matches;

  /* ---------- Element refs ---------- */
  const cursorDot = document.querySelector(".cursor-dot");
  const cursorOutline = document.querySelector(".cursor-outline");
  const scrollProgress = document.getElementById("scrollProgress");
  const header = document.getElementById("header");
  const hamburger = document.getElementById("hamburger");
  const navMenu = document.getElementById("navMenu");
  const navOverlay = document.getElementById("navOverlay");
  const navLinks = navMenu ? navMenu.querySelectorAll("a") : [];
  const navDesktopLinks = document.querySelectorAll(".nav-desktop a");
  const themeToggle = document.getElementById("themeToggle");
  const backToTop = document.getElementById("backToTop");
  const toastHost = document.getElementById("toastHost");

  /* ============================================================
     Custom cursor (desktop only)
     ============================================================ */
  function initCursor() {
    if (isTouch || !cursorDot || !cursorOutline) return;

    let mouseX = 0, mouseY = 0;
    let outlineX = 0, outlineY = 0;

    document.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      cursorDot.style.left = mouseX + "px";
      cursorDot.style.top = mouseY + "px";
    });

    // Smooth lerp for the outer ring
    function animateOutline() {
      outlineX += (mouseX - outlineX) * 0.18;
      outlineY += (mouseY - outlineY) * 0.18;
      cursorOutline.style.left = outlineX + "px";
      cursorOutline.style.top = outlineY + "px";
      requestAnimationFrame(animateOutline);
    }
    animateOutline();

    // Grow on hoverable elements
    const hoverSelector = "a, button, .upload-area, .faq-question, .compare-handle, .sample-chip, [role='button']";
    document.querySelectorAll(hoverSelector).forEach((el) => {
      el.addEventListener("mouseenter", () => cursorOutline.classList.add("hovering"));
      el.addEventListener("mouseleave", () => cursorOutline.classList.remove("hovering"));
    });

    // Hide cursor when leaving window
    document.addEventListener("mouseleave", () => {
      cursorDot.classList.add("hidden-c");
      cursorOutline.classList.add("hidden-c");
    });
    document.addEventListener("mouseenter", () => {
      cursorDot.classList.remove("hidden-c");
      cursorOutline.classList.remove("hidden-c");
    });
  }

  /* ============================================================
     Particle network (hero canvas)
     ============================================================ */
  function initParticles() {
    const canvas = document.getElementById("particleCanvas");
    if (!canvas || prefersReduced) return;
    const ctx = canvas.getContext("2d");

    let particles = [];
    let width = 0, height = 0;
    let mouseX = -9999, mouseY = -9999;
    let raf;

    function resize() {
      const parent = canvas.parentElement;
      width = canvas.width = parent.offsetWidth;
      height = canvas.height = parent.offsetHeight;
      buildParticles();
    }

    function buildParticles() {
      const count = Math.min(90, Math.floor((width * height) / 14000));
      particles = [];
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          r: Math.random() * 1.6 + 0.5,
        });
      }
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);
      const accent = "0, 255, 136";

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around edges
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Mouse repulsion
        const mdx = p.x - mouseX;
        const mdy = p.y - mouseY;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 120) {
          const force = (120 - mdist) / 120;
          p.x += (mdx / mdist) * force * 1.6;
          p.y += (mdy / mdist) * force * 1.6;
        }

        // Particle dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${accent}, 0.5)`;
        ctx.fill();

        // Connection lines
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(${accent}, ${0.22 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(draw);
    }

    canvas.parentElement.addEventListener("mousemove", (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    });
    canvas.parentElement.addEventListener("mouseleave", () => {
      mouseX = -9999;
      mouseY = -9999;
    });

    window.addEventListener("resize", () => {
      cancelAnimationFrame(raf);
      resize();
      draw();
    });

    resize();
    draw();
  }

  /* ============================================================
     Mobile navigation
     ============================================================ */
  function initNav() {
    if (!hamburger || !navMenu) return;

    function open() {
      hamburger.classList.add("active");
      navMenu.classList.add("open");
      navOverlay.classList.add("open");
      hamburger.setAttribute("aria-expanded", "true");
      body.style.overflow = "hidden";
    }
    function close() {
      hamburger.classList.remove("active");
      navMenu.classList.remove("open");
      navOverlay.classList.remove("open");
      hamburger.setAttribute("aria-expanded", "false");
      body.style.overflow = "";
    }
    function toggle() {
      navMenu.classList.contains("open") ? close() : open();
    }

    hamburger.addEventListener("click", toggle);
    navOverlay.addEventListener("click", close);
    navLinks.forEach((link) => link.addEventListener("click", close));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && navMenu.classList.contains("open")) close();
    });
  }

  /* ============================================================
     Theme toggle (persisted)
     ============================================================ */
  function initTheme() {
    if (!themeToggle) return;

    const saved = localStorage.getItem("kepler-theme");
    if (saved) applyTheme(saved);

    function applyTheme(theme) {
      body.setAttribute("data-theme", theme);
      themeToggle.innerHTML = theme === "light"
        ? '<i class="fa-solid fa-sun"></i>'
        : '<i class="fa-solid fa-moon"></i>';
    }

    themeToggle.addEventListener("click", () => {
      const next = body.getAttribute("data-theme") === "light" ? "dark" : "light";
      applyTheme(next);
      localStorage.setItem("kepler-theme", next);
    });
  }

  /* ============================================================
     Scroll: progress bar, header shadow, back-to-top, active link
     ============================================================ */
  function initScroll() {
    const sections = document.querySelectorAll("section[id]");

    function onScroll() {
      const scrollY = window.scrollY;
      const docH = document.documentElement.scrollHeight - window.innerHeight;
      const pct = docH > 0 ? (scrollY / docH) * 100 : 0;
      if (scrollProgress) scrollProgress.style.width = pct + "%";

      if (header) header.classList.toggle("scrolled", scrollY > 20);
      if (backToTop) backToTop.classList.toggle("visible", scrollY > 500);

      // Active section highlight
      let current = "";
      sections.forEach((sec) => {
        if (scrollY >= sec.offsetTop - 120) current = sec.id;
      });
      [...navDesktopLinks, ...navLinks].forEach((link) => {
        const href = link.getAttribute("href");
        link.classList.toggle("active", href === "#" + current);
      });
    }

    if (backToTop) {
      backToTop.addEventListener("click", () =>
        window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" })
      );
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ============================================================
     FAQ accordion
     ============================================================ */
  function initFAQ() {
    const items = document.querySelectorAll(".faq-item");
    items.forEach((item) => {
      const btn = item.querySelector(".faq-question");
      btn.addEventListener("click", () => {
        const isOpen = item.classList.contains("open");
        items.forEach((i) => i.classList.remove("open"));
        if (!isOpen) item.classList.add("open");
      });
    });
  }

  /* ============================================================
     Scroll reveal
     ============================================================ */
  function initReveal() {
    const els = document.querySelectorAll(".reveal");
    if (prefersReduced || !("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("visible"));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );
    els.forEach((el) => observer.observe(el));
  }

  /* ============================================================
     Toast helper
     ============================================================ */
  function showToast(message, icon = "fa-circle-check") {
    if (!toastHost) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
    toastHost.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("leaving");
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  /* ============================================================
     Upload demo + simulated inference
     ============================================================ */
  function initDemo() {
    const uploadArea = document.getElementById("uploadArea");
    const fileInput = document.getElementById("fileInput");
    const processing = document.getElementById("processing");
    const procLabel = document.getElementById("procLabel");
    const procFill = document.getElementById("procFill");
    const resultsWrap = document.getElementById("resultsWrap");
    const samples = document.getElementById("samples");

    if (!uploadArea || !fileInput) return;

    // Click to browse
    uploadArea.addEventListener("click", () => fileInput.click());
    uploadArea.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fileInput.click();
      }
    });

    // Drag & drop styling
    ["dragenter", "dragover"].forEach((evt) =>
      uploadArea.addEventListener(evt, (e) => {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      uploadArea.addEventListener(evt, (e) => {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");
      })
    );

    // Handle dropped file
    uploadArea.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    });

    // Handle browsed file
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) handleFile(file);
    });

    // Sample chips — fetch the sample image and send it through the real backend
    if (samples) {
      samples.querySelectorAll(".sample-chip").forEach((chip) => {
        chip.addEventListener("click", async () => {
          const seed = chip.dataset.seed;
          try {
            showToast("Fetching sample scene…", "fa-satellite");
            const res = await fetch(`https://picsum.photos/seed/${seed}/900/600`);
            const blob = await res.blob();
            const file = new File([blob], `${seed}.png`, { type: "image/png" });
            handleFile(file);
          } catch (err) {
            showToast("Could not load sample. Check your connection.", "fa-triangle-exclamation");
          }
        });
      });
    }

    /* Validate and route the file to the real backend pipeline */
    function handleFile(file) {
      if (!file) return;
      if (!file.type.startsWith("image/") && !/\.(tif|tiff|png|jpe?g)$/i.test(file.name)) {
        showToast("Please upload an image (.png/.jpg) or GeoTIFF (.tif).", "fa-triangle-exclamation");
        return;
      }
      triggerBackendInference(file);
    }

    let progressTimer = null;

    /* Drive the progress bar while awaiting the server response.
       We can't know real % without streaming, so we ease toward a 90% cap
       and snap to 100% the moment the response resolves. */
    function startProgress() {
      stopProgress();
      let p = 5;
      procFill.style.width = "5%";
      procLabel.textContent = "Uploading to inference server…";
      progressTimer = setInterval(() => {
        // Ease toward 90% with diminishing steps so it never completes early
        p += (90 - p) * 0.08;
        procFill.style.width = p + "%";
        if (p > 30 && p < 60) procLabel.textContent = "Running super-resolution (200m → 100m)…";
        else if (p >= 60 && p < 85) procLabel.textContent = "Predicting RGB colorization…";
      }, 280);
    }

    function stopProgress() {
      if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
      }
    }

    /* Real end-to-end call to the Flask backend */
    async function triggerBackendInference(file) {
      processing.hidden = false;
      resultsWrap.hidden = true;
      procFill.style.width = "0%";
      startProgress();

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/api/infer", { method: "POST", body: formData });
        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.error || "Inference failed on the server.");
        }

        // Server finished — complete the bar
        stopProgress();
        procFill.style.width = "100%";
        procLabel.textContent = "Geospatial export complete!";

        showResults(data);
      } catch (err) {
        stopProgress();
        // If the backend is unreachable (e.g. file:// preview), fall back to a
        // clearly-labeled offline mock so the UI still demonstrates the flow.
        if (isLikelyOffline(err)) {
          showToast("Backend offline — showing offline preview.", "fa-triangle-exclamation");
          offlineMock(file);
        } else {
          processing.hidden = true;
          showToast("Error: " + err.message, "fa-triangle-exclamation");
          console.error("API Error:", err);
        }
      }
    }

    function isLikelyOffline(err) {
      return (
        err instanceof TypeError &&
        /fetch|network|Failed to fetch/i.test(err.message)
      ) || location.protocol === "file:";
    }

    /* Offline fallback: keeps the demo usable without the Flask server */
    function offlineMock(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const src = e.target.result;
        const ts = Date.now();
        showResults({
          images: {
            input: src,
            sr: `https://picsum.photos/seed/sr-${ts}/900/600`,
            colorized: `https://picsum.photos/seed/color-${ts}/900/600`,
          },
          download: null,
          download_tif: null,
          meta: { offline: true },
        });
      };
      reader.readAsDataURL(file);
    }

    /* Render the backend response into the results UI */
    function showResults(data) {
      const cacheBust = (url) =>
        typeof url === "string" && url.startsWith("/") ? url + "?t=" + Date.now() : url;

      setSrc("imgOriginal", cacheBust(data.images.input));
      setSrc("imgSR", cacheBust(data.images.sr));
      setSrc("imgColor", cacheBust(data.images.colorized));
      setSrc("compOriginal", cacheBust(data.images.input));
      setSrc("compSR", cacheBust(data.images.sr));
      setSrc("compColor", cacheBust(data.images.colorized));

      // Download buttons (optional — guarded so it works if absent)
      setHref("downloadBtn", data.download);
      setHref("downloadTifBtn", data.download_tif);

      // Telemetry line (optional)
      const meta = data.meta || {};
      const metaEl = document.getElementById("resultsMeta");
      if (metaEl) {
        const parts = [];
        if (meta.offline) parts.push("OFFLINE PREVIEW");
        if (meta.input_size) parts.push(`Input ${meta.input_size}`);
        if (meta.output_size) parts.push(`Output ${meta.output_size}`);
        if (meta.crs) parts.push(meta.crs);
        if (meta.elapsed) parts.push(`${meta.elapsed}s`);
        metaEl.textContent = parts.join("  ·  ");
      }

      setTimeout(() => {
        processing.hidden = true;
        resultsWrap.hidden = false;
        showToast(
          meta.offline
            ? "Offline preview ready."
            : "Inference complete — real GeoTIFF processed."
        );
        setTimeout(() => resultsWrap.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "start" }), 80);
        setTimeout(initCompareSlider, 150);
      }, 400);
    }

    function setSrc(id, src) {
      const el = document.getElementById(id);
      if (el) el.src = src;
    }
    function setHref(id, href) {
      const el = document.getElementById(id);
      if (el && href) {
        el.href = href;
        el.style.display = "";
      } else if (el && !href) {
        el.style.display = "none";
      }
    }
  }

  /* ============================================================
     3-way comparison slider
     ============================================================ */
  let compareBound = false;
  function initCompareSlider() {
    const container = document.getElementById("compareContainer");
    const handle = document.getElementById("compareHandle");
    const layerColor = document.getElementById("layerColor");
    const layerSR = document.getElementById("layerSR");
    if (!container || !handle || !layerColor || !layerSR || compareBound) return;
    compareBound = true;

    let pos = 0.34; // 0..1
    let dragging = false;

    function updateMasks(x) {
      pos = Math.min(1, Math.max(0, x));
      const pct = pos * 100;
      const pct2 = Math.min(100, pct + 34);
      const colorMask = `linear-gradient(to right, black 0%, black ${pct}%, transparent ${pct}%, transparent 100%)`;
      const srMask = `linear-gradient(to right, transparent 0%, transparent ${pct}%, black ${pct}%, black ${pct2}%, transparent ${pct2}%, transparent 100%)`;

      layerColor.style.webkitMaskImage = colorMask;
      layerColor.style.maskImage = colorMask;
      layerSR.style.webkitMaskImage = srMask;
      layerSR.style.maskImage = srMask;
      handle.style.left = pct + "%";
    }

    function getPos(e) {
      const rect = container.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    }

    // Pointer (mouse + touch unified)
    handle.addEventListener("pointerdown", (e) => {
      dragging = true;
      handle.setPointerCapture(e.pointerId);
    });
    handle.addEventListener("pointermove", (e) => {
      if (dragging) updateMasks(getPos(e));
    });
    handle.addEventListener("pointerup", () => (dragging = false));
    handle.addEventListener("pointercancel", () => (dragging = false));

    // Click anywhere on container to move handle
    container.addEventListener("click", (e) => {
      if (e.target === handle || handle.contains(e.target)) return;
      updateMasks(getPos(e));
    });

    // Keyboard support
    handle.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") { updateMasks(pos - 0.05); e.preventDefault(); }
      if (e.key === "ArrowRight") { updateMasks(pos + 0.05); e.preventDefault(); }
    });

    updateMasks(pos);
  }

  /* ============================================================
     Init
     ============================================================ */
  function init() {
    initCursor();
    initParticles();
    initNav();
    initTheme();
    initScroll();
    initFAQ();
    initReveal();
    initDemo();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
