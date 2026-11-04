// A minimal reveal.js plugin: proves Quarto loads custom plugins and calls init(deck).
window.RevealPing = { id: "ping", init: (deck) => { window.__pingSlides = deck.getTotalSlides(); } };
