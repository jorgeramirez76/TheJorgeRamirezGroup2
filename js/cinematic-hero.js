(() => {
  const hero = document.querySelector('.cinema-hero');
  if (!hero) return;
  const video = hero.querySelector('video');
  const toggle = hero.querySelector('.cinema-toggle');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  let userPaused = false;
  let inView = true;
  let loaded = false;
  let frame = 0;
  function load() {
    if (loaded) return;
    loaded = true;
    video.src = video.dataset.src;
    video.load();
  }
  function label() {
    toggle.textContent = video.paused ? 'Play background film' : 'Pause background film';
  }
  function play() {
    load();
    video.play().catch(() => { label(); });
  }
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    userPaused = !video.paused;
    if (video.paused) play(); else video.pause();
  });
  video.addEventListener('playing', () => { hero.classList.add('is-playing'); label(); });
  video.addEventListener('pause', label);
  video.addEventListener('error', () => { hero.classList.remove('is-playing'); toggle.hidden = true; });
  function resume() {
    if (inView && !document.hidden && !userPaused && !reduced.matches && !connection?.saveData) play();
    else video.pause();
  }
  const observer = new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; resume(); });
  observer.observe(hero);
  document.addEventListener('visibilitychange', resume);
  reduced.addEventListener('change', () => { if (reduced.matches) hero.style.setProperty('--cinema-offset','0px'); resume(); });
  function update() {
    frame = 0;
    const rect = hero.getBoundingClientRect();
    const progress = Math.min(1, Math.max(0, -rect.top / rect.height));
    hero.style.setProperty('--cinema-progress', String(progress));
    if (!reduced.matches) hero.style.setProperty('--cinema-offset', `${Math.min(35,progress * 60)}px`);
  }
  window.addEventListener('scroll', () => { if (!frame && inView) frame = requestAnimationFrame(update); }, {passive:true});
  update();
})();
