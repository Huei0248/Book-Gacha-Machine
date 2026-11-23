/* 前端只使用 localStorage 記錄書籍，不需後端資料庫。 */
const HISTORY_KEY = 'book-gacha-history-v1';
const FAVORITES_KEY = 'book-gacha-favorites-v1';
let selectedSubject = 'random';
let currentBook = null;
const $ = (selector) => document.querySelector(selector);

function readStorage(key) {
  try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch { return []; }
}
function writeStorage(key, value) { localStorage.setItem(key, JSON.stringify(value)); }
function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}
function renderHistory() {
  const history = readStorage(HISTORY_KEY);
  $('#emptyHistory').hidden = history.length > 0;
  $('#history').innerHTML = history.map((book, index) => `<li>
    ${book.cover_url ? `<img class="history-cover" src="${escapeHtml(book.cover_url)}" alt="" onerror="this.outerHTML='<div class=\'history-cover placeholder\'>📖</div>'">` : '<div class="history-cover placeholder">📖</div>'}
    <div class="history-info"><strong>${escapeHtml(book.title)}</strong><span>${escapeHtml(book.subject_label || '')}</span></div>
    <button class="remove-history" data-index="${index}" aria-label="刪除此筆紀錄">×</button></li>`).join('');
}
function addHistory(book) { writeStorage(HISTORY_KEY, [book, ...readStorage(HISTORY_KEY)].slice(0, 10)); renderHistory(); }
function coverMarkup(book) {
  return book.cover_url
    ? `<img class="cover" src="${escapeHtml(book.cover_url)}" alt="《${escapeHtml(book.title)}》封面" onerror="this.outerHTML='<div class=\'cover-placeholder\'><b>📖</b><span>${escapeHtml(book.title)}</span></div>'">`
    : `<div class="cover-placeholder"><b>📖</b><span>${escapeHtml(book.title)}</span></div>`;
}
function showBook(book) {
  currentBook = book;
  const favorite = readStorage(FAVORITES_KEY).some((item) => item.key === book.key);
  const authorText = book.authors.length ? book.authors.join('、') : '作者資料未提供';
  const tags = book.subjects.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('');
  const detailsUrl = book.key ? `https://openlibrary.org${book.key}` : 'https://openlibrary.org/';
  $('#result').innerHTML = `${coverMarkup(book)}<div class="book-info"><span class="eyebrow">${escapeHtml(book.subject_label)}</span><h3>${escapeHtml(book.title)}</h3><p>作者｜${escapeHtml(authorText)}</p><p>首次出版｜${book.first_publish_year || '未提供'}</p><div class="tags">${tags}</div><a class="book-link" href="${escapeHtml(detailsUrl)}" target="_blank" rel="noopener noreferrer">前往 Open Library 查看詳情 ↗</a><div class="book-actions"><button id="favoriteButton" class="small-button">${favorite ? '♥ 已收藏' : '♡ 收藏這本書'}</button></div></div>`;
  $('#result').hidden = false;
  $('#favoriteButton').addEventListener('click', toggleFavorite);
  $('#message').hidden = true;
}
function toggleFavorite() {
  const favorites = readStorage(FAVORITES_KEY);
  const found = favorites.some((book) => book.key === currentBook.key);
  writeStorage(FAVORITES_KEY, found ? favorites.filter((book) => book.key !== currentBook.key) : [currentBook, ...favorites]);
  $('#favoriteButton').textContent = found ? '♡ 收藏這本書' : '♥ 已收藏';
}

document.querySelectorAll('.subject').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.subject').forEach((item) => item.classList.remove('selected'));
  button.classList.add('selected');
  selectedSubject = button.dataset.subject;
}));
$('#drawButton').addEventListener('click', async () => {
  const button = $('#drawButton');
  const capsule = $('#capsule');
  button.disabled = true;
  $('#result').hidden = true;
  $('#message').hidden = true;
  $('#hint').textContent = '扭蛋正在尋找你的下一本書…';
  capsule.classList.add('spinning');
  try {
    const response = await fetch('/api/draw', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({subject:selectedSubject})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '暫時無法取得書籍資料，請再試一次。');
    await new Promise((resolve) => setTimeout(resolve, 450));
    capsule.classList.remove('spinning'); capsule.classList.add('opened');
    $('#hint').textContent = '噹！你的閱讀靈感來了。';
    showBook(data.book); addHistory(data.book);
    setTimeout(() => capsule.classList.remove('opened'), 600);
  } catch (error) {
    capsule.classList.remove('spinning');
    $('#hint').textContent = '扭蛋沒有轉成功，再試一次吧。';
    $('#message').textContent = `${error.message} 點擊「再轉一次」即可重試。`;
    $('#message').hidden = false;
  } finally { button.disabled = false; button.innerHTML = '再轉一次 <span>↗</span>'; }
});
$('#history').addEventListener('click', (event) => {
  const button = event.target.closest('[data-index]');
  if (!button) return;
  const history = readStorage(HISTORY_KEY); history.splice(Number(button.dataset.index), 1);
  writeStorage(HISTORY_KEY, history); renderHistory();
});
$('#clearHistory').addEventListener('click', () => { writeStorage(HISTORY_KEY, []); renderHistory(); });
renderHistory();
