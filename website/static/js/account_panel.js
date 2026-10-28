document.addEventListener("DOMContentLoaded", function () {
    const panel = document.getElementById("accountPanel");
    const backdrop = document.getElementById("accountPanelBackdrop");
    const closeButton = document.getElementById("closeAccountPanel");

    if (!panel || !backdrop || !closeButton) {
        return;
    }

    let previousFocus = null;

    function openAccountPanel(event) {
        if (event) {
            event.preventDefault();
        }

        previousFocus = document.activeElement;

        panel.inert = false;
        panel.setAttribute("aria-hidden", "false");

        panel.classList.add("is-open");
        backdrop.classList.add("is-visible");

        document.body.classList.add("account-panel-open");

        closeButton.focus();
    }

    function closeAccountPanel() {
        panel.classList.remove("is-open");
        backdrop.classList.remove("is-visible");

        document.body.classList.remove("account-panel-open");

        panel.setAttribute("aria-hidden", "true");
        panel.inert = true;

        if (previousFocus && typeof previousFocus.focus === "function") {
            previousFocus.focus();
        }
    }

    // Open from any account trigger.
    document.querySelectorAll("[data-account-panel-trigger]").forEach(function (trigger) {
        trigger.addEventListener("click", openAccountPanel);
    });

    // Close button.
    closeButton.addEventListener("click", closeAccountPanel);

    // Close when the backdrop is clicked.
    backdrop.addEventListener("click", closeAccountPanel);

    // Close with Escape.
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && panel.classList.contains("is-open")) {
            closeAccountPanel();
        }
    });

    // Close the panel when a real navigation link is selected.
    panel.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            if (
                link.hasAttribute("data-account-link") ||
                link.getAttribute("href") === "#"
            ) {
                return;
            }

            closeAccountPanel();
        });
    });
})