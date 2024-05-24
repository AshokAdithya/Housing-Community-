var tl = gsap.timeline();
const buttons = document.querySelectorAll(".button");

tl.from(".heading", {
  y: -30,
  opacity: 0,
  duration: 0.8,
  delay: 0.3,
});

tl.from(".quote", {
  x: 100,
  opacity: 0,
  duration: 1,
});

tl.from(".button", {
  x: 100,
  opacity: 0,
  delay: 0,
  duration: 1,
});

buttons.forEach((button) => {
  button.addEventListener("mouseenter", () => {
    gsap.to(button, { scaleX: 1.05, scaleY: 1.05, duration: 0.1 });
  });

  button.addEventListener("mouseleave", () => {
    gsap.to(button, { scaleX: 1, scaleY: 1, duration: 0.1 });
  });
});

var overlay = document.querySelector(".overlay");
var detailsView = document.querySelector(".details-view");

function openModal() {
  overlay.style.display = "flex";
  detailsView.style.display = "flex";
}

function closeModal() {
  overlay.style.display = "none";
  detailsView.style.display = "none";
}
