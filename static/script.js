document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab");
    const items = document.querySelectorAll(".menu-item");

    if (!tabs.length) return;

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");

            const category = tab.dataset.category;
            items.forEach((item) => {
                const match = category === "all" || item.dataset.category === category;
                item.style.display = match ? "flex" : "none";
            });
        });
    });
});
