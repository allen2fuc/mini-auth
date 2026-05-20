let users = [];
let editingId = null;

// ============ API ============
function formatApiError(detail) {
  if (!detail) return 'request_failed';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(e => {
      const field = Array.isArray(e.loc) ? e.loc.filter(x => x !== 'body').join('.') : '';
      const prefix = field ? `${field}: ` : '';
      return prefix + (e.msg || 'validation_error');
    }).join('; ');
  }
  return String(detail);
}

async function api(method, url, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  if (r.status === 204) return null;
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const message = formatApiError(data.detail);
    const err = new Error(message);
    err.code = typeof data.detail === 'string' ? data.detail : message;
    throw err;
  }
  return data;
}

const ERR_MSG = {
  username_exists: '用户名已被占用',
  not_found: '用户不存在',
  last_admin: '系统至少需要保留一个启用的管理员',
  cannot_delete_self: '不能删除自己的账号',
  request_failed: '请求失败',
};

// ============ Toast ============
function toast(message, type = 'success') {
  const c = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icon = type === 'success'
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
  el.innerHTML = icon + '<span>' + escapeHtml(message) + '</span>';
  c.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(20px)';
    el.style.transition = 'all 0.2s';
    setTimeout(() => el.remove(), 200);
  }, 2800);
}

// ============ Helpers ============
function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function avatarColor(name) {
  const colors = [
    ['#6366f1', '#8b5cf6'], ['#ec4899', '#f43f5e'],
    ['#10b981', '#14b8a6'], ['#f59e0b', '#f97316'],
    ['#3b82f6', '#06b6d4']
  ];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) | 0;
  const [a, b] = colors[Math.abs(h) % colors.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function formatDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso + 'Z');
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ============ Render ============
function renderStats() {
  document.getElementById('statTotal').textContent = users.length;
  document.getElementById('statAdmin').textContent = users.filter(u => u.is_admin).length;
  document.getElementById('statActive').textContent = users.filter(u => u.is_active).length;
}

function renderTable() {
  const q = document.getElementById('searchInput').value.trim().toLowerCase();
  const filtered = q
    ? users.filter(u => u.username.toLowerCase().includes(q) || (u.email || '').toLowerCase().includes(q))
    : users;

  const tbody = document.getElementById('userTbody');
  const empty = document.getElementById('emptyState');
  const table = document.getElementById('userTable');

  if (filtered.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    if (users.length === 0) table.style.display = 'none';
    return;
  }
  empty.style.display = 'none';
  table.style.display = 'table';

  tbody.innerHTML = filtered.map(u => {
    const initial = u.username[0].toUpperCase();
    const isSelf = u.id === window.CURRENT_USER_ID;
    return `
      <tr>
        <td>
          <div class="user-cell">
            <div class="user-cell-avatar" style="background: ${avatarColor(u.username)}">${escapeHtml(initial)}</div>
            <div>
              <div class="user-cell-name">${escapeHtml(u.username)}${isSelf ? ' <span style="color: var(--text-muted); font-size: 11px; font-weight: 400;">(我)</span>' : ''}</div>
            </div>
          </div>
        </td>
        <td class="col-email" style="color: var(--text-secondary);">${escapeHtml(u.email || '-')}</td>
        <td>${u.is_admin
        ? '<span class="badge badge-admin"><span class="badge-dot"></span>管理员</span>'
        : '<span class="badge badge-user">普通用户</span>'}</td>
        <td>${u.is_active
        ? '<span class="badge badge-active"><span class="badge-dot"></span>启用</span>'
        : '<span class="badge badge-disabled"><span class="badge-dot"></span>停用</span>'}</td>
        <td class="col-created" style="color: var(--text-muted); font-size: 12px;">${formatDate(u.created_at)}</td>
        <td>
          <div class="actions">
            <button class="btn btn-sm" onclick="openEditModal(${u.id})">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              编辑
            </button>
            ${isSelf ? '' : `<button class="btn btn-sm btn-danger" onclick="confirmDelete(${u.id}, '${escapeHtml(u.username)}')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/></svg>
            </button>`}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function loadUsers() {
  try {
    const data = await api('GET', '/admin/api/users');
    users = data.users;
    renderStats();
    renderTable();
  } catch (e) {
    toast(ERR_MSG[e.code] || e.message, 'error');
  }
}

// ============ Modal ============
function openCreateModal() {
  editingId = null;
  document.getElementById('modalTitle').textContent = '新建用户';
  document.getElementById('formUserId').value = '';
  document.getElementById('formUsername').value = '';
  document.getElementById('formUsername').disabled = false;
  document.getElementById('formEmail').value = '';
  document.getElementById('formPassword').value = '';
  document.getElementById('formPassword').required = true;
  document.getElementById('passwordHint').textContent = '(至少 4 位)';
  document.getElementById('passwordEditHint').style.display = 'none';
  document.getElementById('formIsAdmin').checked = false;
  document.getElementById('formIsActive').checked = true;
  document.getElementById('modal').classList.add('show');
  setTimeout(() => document.getElementById('formUsername').focus(), 100);
}

function openEditModal(id) {
  const u = users.find(x => x.id === id);
  if (!u) return;
  editingId = id;
  document.getElementById('modalTitle').textContent = '编辑用户';
  document.getElementById('formUserId').value = id;
  document.getElementById('formUsername').value = u.username;
  document.getElementById('formUsername').disabled = true;
  document.getElementById('formEmail').value = u.email || '';
  document.getElementById('formPassword').value = '';
  document.getElementById('formPassword').required = false;
  document.getElementById('passwordHint').textContent = '';
  document.getElementById('passwordEditHint').style.display = 'block';
  document.getElementById('formIsAdmin').checked = u.is_admin;
  document.getElementById('formIsActive').checked = u.is_active;
  document.getElementById('modal').classList.add('show');
}

function closeModal() {
  document.getElementById('modal').classList.remove('show');
}

async function submitForm() {
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  const originalText = btn.textContent;
  btn.innerHTML = '<span class="loading"></span>';

  const username = document.getElementById('formUsername').value.trim();
  const email = document.getElementById('formEmail').value.trim();
  const password = document.getElementById('formPassword').value;
  const is_admin = document.getElementById('formIsAdmin').checked;
  const is_active = document.getElementById('formIsActive').checked;

  try {
    if (editingId === null) {
      if (!username) throw new Error('请输入用户名');
      if (!password || password.length < 4) throw new Error('密码至少 4 位');
      await api('POST', '/admin/api/users', {
        username, password, email: email || null, is_admin, is_active
      });
      toast('用户已创建');
    } else {
      const body = { email: email || null, is_admin, is_active };
      if (password) {
        if (password.length < 4) throw new Error('密码至少 4 位');
        body.password = password;
      }
      const data = await api('PATCH', '/admin/api/users/' + editingId, body);
      if (data.reauth_required) {
        toast('密码已修改，请重新登录');
        window.location.href = '/login?rd=' + encodeURIComponent('/admin/') + '&success=password_changed';
        return;
      }
      toast(password && editingId !== window.CURRENT_USER_ID
        ? '已保存，该用户需使用新密码重新登录'
        : '已保存');
    }
    closeModal();
    await loadUsers();
  } catch (e) {
    toast(ERR_MSG[e.code] || e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

async function confirmDelete(id, username) {
  if (!confirm(`确定删除用户 "${username}" 吗?此操作不可恢复。`)) return;
  try {
    await api('DELETE', '/admin/api/users/' + id);
    toast('用户已删除');
    await loadUsers();
  } catch (e) {
    toast(ERR_MSG[e.code] || e.message, 'error');
  }
}

document.getElementById('modal').addEventListener('click', e => {
  if (e.target.id === 'modal') closeModal();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});
document.getElementById('searchInput').addEventListener('input', renderTable);

loadUsers();
