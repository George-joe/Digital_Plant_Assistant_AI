const cards = document.querySelectorAll(".feature-card");

window.addEventListener("load", () => {
  cards.forEach((card, index) => {
    setTimeout(() => {
      card.style.opacity = 1;
      card.style.transform = "translateY(0)";
    }, index * 150);
  });
});
