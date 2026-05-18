(function () {
  // 初始化:读 localStorage 或系统偏好
  let saved = null;
  try { saved = localStorage.getItem('auth-theme'); } catch (e) {}
  if (saved) {
    document.documentElement.dataset.theme = saved;
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.dataset.theme = 'dark';
  } else {
    document.documentElement.dataset.theme = 'light';
  }
})();

function toggleTheme() {
  const root = document.documentElement;
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  try { localStorage.setItem('auth-theme', next); } catch (e) {}
}
