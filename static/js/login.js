function togglePassword() {
  const pwd = document.getElementById('password');
  const icon = document.getElementById('eyeIcon');
  if (pwd.type === 'password') {
    pwd.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
  } else {
    pwd.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
  }
}

async function refreshCaptcha() {
  const res = await fetch('/login/captcha/refresh', { method: 'POST' });
  if (!res.ok) return;
  const data = await res.json();
  document.getElementById('captchaId').value = data.id;
  const img = document.getElementById('captchaImg');
  img.src = data.url + '&t=' + Date.now();
  document.getElementById('captcha_code').value = '';
}

function initCaptcha() {
  const field = document.getElementById('captchaField');
  const img = document.getElementById('captchaImg');
  const refreshBtn = document.getElementById('captchaRefresh');
  if (!field || !img) return;

  if (window.LOGIN_CAPTCHA_REQUIRED) {
    field.classList.remove('hidden');
    document.getElementById('captcha_code').required = true;
  }

  img.addEventListener('click', refreshCaptcha);
  refreshBtn.addEventListener('click', refreshCaptcha);
}

document.getElementById('loginForm').addEventListener('submit', function () {
  const btn = document.getElementById('submitBtn');
  btn.classList.add('loading');
  btn.disabled = true;
});

initCaptcha();
