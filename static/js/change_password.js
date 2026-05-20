const EYE_OPEN = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
const EYE_CLOSED = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';

document.querySelectorAll('.toggle-password').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.target);
    const icon = btn.querySelector('svg');
    if (!input || !icon) return;
    if (input.type === 'password') {
      input.type = 'text';
      icon.innerHTML = EYE_CLOSED;
    } else {
      input.type = 'password';
      icon.innerHTML = EYE_OPEN;
    }
  });
});

document.getElementById('changePasswordForm').addEventListener('submit', function (e) {
  const newPwd = document.getElementById('new_password').value;
  const confirmPwd = document.getElementById('confirm_password').value;
  if (newPwd !== confirmPwd) {
    e.preventDefault();
    alert('两次输入的新密码不一致');
    return;
  }
  if (newPwd.length < 4) {
    e.preventDefault();
    alert('新密码至少 4 位');
    return;
  }
  const btn = document.getElementById('submitBtn');
  btn.classList.add('loading');
  btn.disabled = true;
});
