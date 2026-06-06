export function saveAvatarRect(rect) {
  try {
    sessionStorage.setItem('cortex_avatar_rect', JSON.stringify(rect));
  } catch (e) {}
}

export function consumeAvatarRect() {
  try {
    const raw = sessionStorage.getItem('cortex_avatar_rect');
    if (!raw) return null;
    sessionStorage.removeItem('cortex_avatar_rect');
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

export function getElementRect(el) {
  const r = el.getBoundingClientRect();
  return { x: r.x, y: r.y, width: r.width, height: r.height, scrollX: window.scrollX, scrollY: window.scrollY };
}
