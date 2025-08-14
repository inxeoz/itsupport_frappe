function loadCSS(href) {
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.onload = resolve;
    link.onerror = reject;
    document.head.appendChild(link);
  });
}

frappe.pages["it_support"].on_page_load = async function (wrapper) {
  // Show loading UI
  $(wrapper).html(`
    <div id="loading-ui" style="padding:2rem;font-size:1.2rem">
      🚀 Loading IT Support Dashboard...
      (npx vite build)
    </div>
    <div id="root_itsupport" style="min-height:400px"></div>
  `);

  try {
    // Step 1: Build static UI from backend
    await frappe.call({
      method: "itsupport_frappe.itsupport_frappe.api.dev.build_static_ui",
    });

    console.log("✅ Static UI build complete");
  } catch (err) {
    frappe.msgprint("❌ Failed to build static UI");
    console.error(err);
    return;
  }

  const version = Date.now(); // cache busting for dev

  try {
    //?v=${version}
    // Corrected path for CSS
    // await loadCSS(`/assets/itsupport_frappe/static_ui/assets/index.css`);
    await loadCSS(
      `/assets/itsupport_frappe/static_ui/assets/index.css?v=${version}`,
    );
  } catch (err) {
    frappe.msgprint("❌ Failed to load CSS");
    console.error("Failed to load CSS:", err);
  }

  try {
    //?v=${version}
    // Corrected path for JS
    // const mod = await import(`/assets/itsupport_frappe/static_ui/assets/main.js`);

    const mod = await import(
      `/assets/itsupport_frappe/static_ui/assets/main.js?v=${version}`
    );

    // Remove loading UI
    document.getElementById("loading-ui").remove();

    // Mount your app if exported
    if (mod.mountReact) {
      mod.mountReact(document.getElementById("root_itsupport"));
    }
  } catch (err) {
    frappe.msgprint("❌ Failed to load JS bundle");
    console.error("Failed to load main.js:", err);
  }
};
