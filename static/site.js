(function () {
  "use strict";

  document.documentElement.classList.add("js-enabled");

  var OUT_QUART = "cubic-bezier(0.165, 0.84, 0.44, 1)";
  var IN_QUART = "cubic-bezier(0.895, 0.03, 0.685, 0.22)";
  var MOTION_DURATION = 1000;
  var pageId = document.documentElement.getAttribute("data-wf-page");
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /*
   * Native equivalents of the active Webflow IX2 events captured on 2026-10-16.
   * The page ID is part of Webflow's target, so the repeated element ID on an
   * obsolete page does not accidentally receive an animation.
   */
  var scrollEffects = {
    "6042c212f919e93f282c3a28": [
      ["4374b62e-4c83-2ad1-6e15-c8cef3e787d9", "fade", 0],
      ["29ceec38-ac18-d23c-d8d3-48279ad5c8b3", "fade", 24],
      ["9f575feb-3831-4ae4-b279-d96fb9dfa5fc", "fade", 0],
    ],
    "60b009ad0883d90c30d58c34": [
      ["7d855c64-69b8-cd13-ac2e-ba0f5abcf244", "fade", 0],
    ],
    "5daf4a741c624d59f55be4a1": [
      ["0befc76b-828c-2822-f9fa-f2c6de040bbc", "slide", 0],
    ],
    "60c3fb866bf40011149328be": [
      ["0befc76b-828c-2822-f9fa-f2c6de040bbc", "slide", 0],
    ],
    "60d9233c0848bb3e1148209e": [
      ["0befc76b-828c-2822-f9fa-f2c6de040bbc", "slide", 0],
    ],
    "60deda14bb05b218a266a589": [
      ["0befc76b-828c-2822-f9fa-f2c6de040bbc", "slide", 0],
    ],
  };

  function targetById(id) {
    return document.querySelector('[data-w-id="' + id + '"]');
  }

  function finishEffect(element, kind) {
    element.style.opacity = "1";
    if (kind === "slide") element.style.transform = "translate3d(0, 0, 0)";
    element.style.removeProperty("will-change");
  }

  function playScrollEffect(element, kind, delay) {
    if (reducedMotion) {
      finishEffect(element, kind);
      return;
    }

    var start = { opacity: 0 };
    var end = { opacity: 1 };
    if (kind === "slide") {
      start.transform = "translate3d(0, 100px, 0)";
      end.transform = "translate3d(0, 0, 0)";
    }

    if (typeof element.animate === "function") {
      var animation = element.animate([start, end], {
        duration: MOTION_DURATION,
        delay: delay,
        easing: OUT_QUART,
        fill: "forwards",
      });
      animation.addEventListener("finish", function () {
        finishEffect(element, kind);
        animation.cancel();
      });
      return;
    }

    element.style.transition =
      "opacity " + MOTION_DURATION + "ms " + OUT_QUART +
      (kind === "slide"
        ? ", transform " + MOTION_DURATION + "ms " + OUT_QUART
        : "");
    window.setTimeout(function () {
      finishEffect(element, kind);
    }, delay);
  }

  function initializeScrollEffects() {
    var effects = scrollEffects[pageId] || [];
    if (!effects.length) return;

    var observed = [];
    effects.forEach(function (effect) {
      var element = targetById(effect[0]);
      if (!element) return;
      element.style.opacity = "0";
      element.style.willChange = effect[1] === "slide" ? "opacity, transform" : "opacity";
      if (effect[1] === "slide") {
        element.style.transform = "translate3d(0, 100px, 0)";
      }
      observed.push({ element: element, kind: effect[1], delay: effect[2] });
    });

    if (reducedMotion || !("IntersectionObserver" in window)) {
      observed.forEach(function (effect) {
        playScrollEffect(effect.element, effect.kind, 0);
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var effect = observed.find(function (candidate) {
            return candidate.element === entry.target;
          });
          if (!effect) return;
          observer.unobserve(entry.target);
          playScrollEffect(effect.element, effect.kind, effect.delay);
        });
      },
      { threshold: 0 }
    );
    observed.forEach(function (effect) {
      observer.observe(effect.element);
    });
  }

  function initializeAboutHover() {
    if (pageId !== "5daf4a741c624de1495be4a0") return;
    var portrait = targetById("f7ba8d4a-8c80-0304-3bdb-a907245da887");
    var desktop = window.matchMedia("(min-width: 992px)");
    var currentAnimation = null;

    if (!portrait || !desktop.matches || reducedMotion) return;
    portrait.style.opacity = "0";

    function fadeTo(opacity, easing) {
      var start = Number(window.getComputedStyle(portrait).opacity);
      if (currentAnimation) currentAnimation.cancel();
      if (typeof portrait.animate !== "function") {
        portrait.style.transition = "opacity " + MOTION_DURATION + "ms " + easing;
        portrait.style.opacity = String(opacity);
        return;
      }
      var animation = portrait.animate(
        [{ opacity: start }, { opacity: opacity }],
        { duration: MOTION_DURATION, easing: easing, fill: "forwards" }
      );
      currentAnimation = animation;
      animation.addEventListener("finish", function () {
        if (currentAnimation !== animation) return;
        portrait.style.opacity = String(opacity);
        animation.cancel();
        currentAnimation = null;
      });
    }

    portrait.addEventListener("mouseenter", function () {
      fadeTo(1, OUT_QUART);
    });
    portrait.addEventListener("mouseleave", function () {
      fadeTo(0, IN_QUART);
    });
  }

  initializeScrollEffects();
  initializeAboutHover();

  document.querySelectorAll(".navigation").forEach(function (navigation) {
    var button = navigation.querySelector(".menu-button");
    var menu = navigation.querySelector(".w-nav-menu");
    if (!button || !menu) return;

    button.setAttribute("role", "button");
    button.setAttribute("tabindex", "0");
    button.setAttribute("aria-label", "Toggle navigation menu");
    button.setAttribute("aria-expanded", "false");

    function setOpen(open) {
      menu.classList.toggle("is-open", open);
      button.classList.toggle("is-open", open);
      button.setAttribute("aria-expanded", String(open));
    }

    function toggle() {
      setOpen(!menu.classList.contains("is-open"));
    }

    button.addEventListener("click", toggle);
    button.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
      if (event.key === "Escape") setOpen(false);
    });
    menu.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 991) setOpen(false);
    });
  });

})();

