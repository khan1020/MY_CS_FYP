const fs = require('fs');
const path = 'c:/xampp/htdocs/backend_latest/chatscreenui.html';

let content = fs.readFileSync(path, 'utf8');

// 1. FIX the regex bug in simpleMarkdownParser
content = content.replace(
    ".replace(/(<li>.*<\\ /li >) / gs, '<ul>$1</ul>')",
    ".replace(/(<li>.*<\\/li>)/gs, '<ul>$1</ul>')"
);

// 2. UPDATE sidebar CSS for dynamic resizing
const oldSidebarCSS = `    /* Sidebar - FIXED for mobile */
    .sidebar {
      width: 13rem;
      min-width: 13rem;
      background: rgba(15, 23, 42, 0.9);
      backdrop-filter: blur(10px);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      transition: transform 0.3s ease;
      flex-shrink: 0;
    }`;

const newSidebarCSS = `    /* Sidebar - DYNAMIC RESIZING */
    .sidebar {
      width: var(--sidebar-width, 13rem);
      min-width: 200px;
      max-width: 400px;
      background: rgba(15, 23, 42, 0.9);
      backdrop-filter: blur(10px);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      transition: transform 0.3s ease;
      flex-shrink: 0;
      position: relative;
    }
    
    /* Sidebar Resizer Handle */
    .sidebar-resizer {
      width: 6px;
      background: transparent;
      cursor: col-resize;
      position: absolute;
      right: -3px;
      top: 0;
      bottom: 0;
      z-index: 50;
      transition: background 0.2s;
    }
    .sidebar-resizer:hover,
    .sidebar-resizer.resizing {
      background: var(--primary);
    }`;

content = content.replace(oldSidebarCSS, newSidebarCSS);

// 3. UPDATE sidebar-header CSS to add search styles
const oldSidebarHeaderCSS = `    .sidebar-header {
      padding: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .light-mode .sidebar-header {
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }`;

const newSidebarHeaderCSS = `    .sidebar-header {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar-header-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .light-mode .sidebar-header {
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    /* Search Container */
    .search-container {
      position: relative;
      width: 100%;
    }
    .search-container input {
      width: 100%;
      padding: 10px 35px 10px 12px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(15, 23, 42, 0.5);
      color: var(--light);
      font-size: 0.9rem;
      outline: none;
      transition: var(--transition);
    }
    .search-container input:focus {
      border-color: var(--primary);
    }
    .search-container .search-icon {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--gray);
    }
    .search-container .clear-search {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: var(--gray);
      cursor: pointer;
      display: none;
    }
    .search-container.has-value .clear-search { display: block; }
    .search-container.has-value .search-icon { display: none; }
    .no-results {
      text-align: center;
      color: var(--gray);
      padding: 20px;
      font-size: 0.9rem;
    }`;

content = content.replace(oldSidebarHeaderCSS, newSidebarHeaderCSS);

// 4. Add message timestamp and code block CSS before /* Modal for Rename */
const modalCSS = '    /* Modal for Rename */';
const additionalCSS = `    /* Message Timestamps */
    .message-timestamp {
      font-size: 0.75rem;
      color: var(--gray);
      margin-top: 8px;
      opacity: 0.7;
    }
    .message:hover .message-timestamp { opacity: 1; }
    
    /* Code Block Styling */
    .message pre {
      background: rgba(0, 0, 0, 0.3) !important;
      border-radius: 8px;
      padding: 15px;
      overflow-x: auto;
      margin: 10px 0;
    }
    .message pre code {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.9rem;
    }
    .message code:not(pre code) {
      background: rgba(99, 102, 241, 0.2);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Consolas', monospace;
    }
    .code-block-wrapper { position: relative; margin: 10px 0; }
    .code-block-header {
      display: flex;
      justify-content: space-between;
      background: rgba(0, 0, 0, 0.4);
      padding: 8px 12px;
      border-radius: 8px 8px 0 0;
      font-size: 0.8rem;
      color: var(--gray);
    }
    .code-copy-btn {
      background: none;
      border: none;
      color: var(--gray);
      cursor: pointer;
    }
    .code-block-wrapper pre { margin-top: 0 !important; border-radius: 0 0 8px 8px !important; }
    
    /* Keyboard Shortcuts */
    .shortcuts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .shortcut-item {
      display: flex;
      justify-content: space-between;
      padding: 10px;
      background: rgba(99, 102, 241, 0.1);
      border-radius: 8px;
    }
    .shortcut-key {
      background: rgba(255, 255, 255, 0.1);
      padding: 4px 8px;
      border-radius: 4px;
      font-family: 'Consolas', monospace;
      font-size: 0.8rem;
    }
    .shortcuts-hint {
      position: fixed;
      bottom: 20px;
      left: 20px;
      background: rgba(15, 23, 42, 0.8);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 0.8rem;
      color: var(--gray);
      cursor: pointer;
      z-index: 100;
    }
    @media (max-width: 768px) {
      .shortcuts-grid { grid-template-columns: 1fr; }
      .shortcuts-hint { display: none; }
    }

    ${modalCSS}`;

content = content.replace(modalCSS, additionalCSS);

// 5. UPDATE sidebar HTML to add resizer and search
const oldSidebarHTML = `  <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
      <div class="sidebar-overlay"></div>
      <div class="sidebar-header">
        <h3>Chat History</h3>
      </div>`;

const newSidebarHTML = `  <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
      <div class="sidebar-resizer" id="sidebarResizer"></div>
      <div class="sidebar-overlay"></div>
      <div class="sidebar-header">
        <div class="sidebar-header-top">
          <h3>Chat History</h3>
        </div>
        <div class="search-container" id="searchContainer">
          <input type="text" id="searchInput" placeholder="Search chats... (Ctrl+K)">
          <i class="fas fa-search search-icon"></i>
          <button class="clear-search" id="clearSearch"><i class="fas fa-times"></i></button>
        </div>
      </div>`;

content = content.replace(oldSidebarHTML, newSidebarHTML);

// 6. ADD keyboard shortcuts modal after rename modal
const renameModalEnd = `      </div>
    </div>
  </div>



  <!-- Microphone Button -->`;

const shortcutsModalHTML = `      </div>
    </div>
  </div>

  <!-- Keyboard Shortcuts Modal -->
  <div class="modal" id="shortcutsModal">
    <div class="modal-content" style="max-width: 600px;">
      <div class="modal-header">
        <h3 class="modal-title">Keyboard Shortcuts</h3>
        <button class="close-modal" id="closeShortcutsModal">&times;</button>
      </div>
      <div class="modal-body">
        <div class="shortcuts-grid">
          <div class="shortcut-item"><div><span class="shortcut-key">Ctrl</span> <span class="shortcut-key">K</span></div><span>Search chats</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">Ctrl</span> <span class="shortcut-key">N</span></div><span>New chat</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">Ctrl</span> <span class="shortcut-key">Enter</span></div><span>Send message</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">Ctrl</span> <span class="shortcut-key">/</span></div><span>Toggle sidebar</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">Ctrl</span> <span class="shortcut-key">D</span></div><span>Toggle theme</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">Esc</span></div><span>Close modals</span></div>
          <div class="shortcut-item"><div><span class="shortcut-key">?</span></div><span>Show shortcuts</span></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn" id="closeShortcutsBtn">Got it!</button>
      </div>
    </div>
  </div>
  
  <!-- Keyboard Shortcuts Hint -->
  <div class="shortcuts-hint" id="shortcutsHint">
    <i class="fas fa-keyboard"></i> Press ? for shortcuts
  </div>

  <!-- Microphone Button -->`;

content = content.replace(renameModalEnd, shortcutsModalHTML);

// 7. ADD JavaScript enhancements before // Init app
const initApp = '    // Init app\n    init();';

const jsEnhancements = `    // ============================================
    // ENHANCEMENT 1: DYNAMIC SIDEBAR RESIZING
    // ============================================
    const sidebarResizer = document.getElementById('sidebarResizer');
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;

    // Load saved sidebar width
    const savedSidebarWidth = localStorage.getItem('sidebarWidth');
    if (savedSidebarWidth) {
      sidebar.style.width = savedSidebarWidth + 'px';
    }

    if (sidebarResizer) {
      sidebarResizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
      });
    }

    document.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const width = startWidth + (e.clientX - startX);
      if (width >= 200 && width <= 400) {
        sidebar.style.width = width + 'px';
      }
    });

    document.addEventListener('mouseup', () => {
      if (isResizing) {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        localStorage.setItem('sidebarWidth', sidebar.offsetWidth);
      }
    });

    // ============================================
    // ENHANCEMENT 2: SEARCH FUNCTIONALITY
    // ============================================
    const searchInput = document.getElementById('searchInput');
    const searchContainer = document.getElementById('searchContainer');
    const clearSearchBtn = document.getElementById('clearSearch');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (query) {
          searchContainer.classList.add('has-value');
        } else {
          searchContainer.classList.remove('has-value');
        }
        filterChats(query);
      });
    }

    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchContainer.classList.remove('has-value');
        filterChats('');
      });
    }

    function filterChats(query) {
      if (!query) {
        renderChatHistory();
        return;
      }
      const filtered = chats.filter(chat => 
        chat.title.toLowerCase().includes(query) ||
        (chat.messages && chat.messages.some(m => m.text && m.text.toLowerCase().includes(query)))
      );
      renderFilteredHistory(filtered, query);
    }

    function renderFilteredHistory(filteredChats, query) {
      chatHistory.innerHTML = '';
      if (filteredChats.length === 0) {
        chatHistory.innerHTML = '<div class="no-results"><i class="fas fa-search"></i><p>No chats found</p></div>';
        return;
      }
      filteredChats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item';
        chatItem.dataset.chatId = chat.id;
        if (chat.id === currentChatId) chatItem.classList.add('active');
        chatItem.innerHTML = '<div class="chat-title">' + chat.title + '</div><div class="chat-actions"><button class="chat-menu-btn">...</button><div class="chat-menu"><button class="chat-menu-btn rename-chat">Rename</button><button class="chat-menu-btn export-chat">Export</button><button class="chat-menu-btn delete-chat">Delete</button></div></div>';
        chatItem.addEventListener('click', (e) => {
          if (!e.target.closest('.chat-actions')) {
            loadChat(chat.id);
            searchInput.value = '';
            searchContainer.classList.remove('has-value');
            renderChatHistory();
          }
        });
        chatHistory.appendChild(chatItem);
      });
    }

    // ============================================
    // ENHANCEMENT 3: KEYBOARD SHORTCUTS
    // ============================================
    const shortcutsModal = document.getElementById('shortcutsModal');
    const closeShortcutsModal = document.getElementById('closeShortcutsModal');
    const closeShortcutsBtn = document.getElementById('closeShortcutsBtn');
    const shortcutsHint = document.getElementById('shortcutsHint');

    if (closeShortcutsModal) closeShortcutsModal.addEventListener('click', () => shortcutsModal.classList.remove('show'));
    if (closeShortcutsBtn) closeShortcutsBtn.addEventListener('click', () => shortcutsModal.classList.remove('show'));
    if (shortcutsHint) shortcutsHint.addEventListener('click', () => shortcutsModal.classList.add('show'));

    document.addEventListener('keydown', (e) => {
      const isInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
      
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (searchInput) { searchInput.focus(); if (sidebar.classList.contains('hidden')) sidebar.classList.remove('hidden'); }
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); createNewChat(); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && document.activeElement === messageInput) { e.preventDefault(); sendMessage(); }
      if ((e.ctrlKey || e.metaKey) && e.key === '/') { e.preventDefault(); sidebar.classList.toggle('hidden'); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') { e.preventDefault(); themeToggle.click(); }
      if (e.key === 'Escape') { renameModal.classList.remove('show'); if (shortcutsModal) shortcutsModal.classList.remove('show'); }
      if (e.key === '?' && !isInput && shortcutsModal) { e.preventDefault(); shortcutsModal.classList.add('show'); }
    });

    // ============================================
    // ENHANCEMENT 4 & 5: MESSAGE TIMESTAMP & ENHANCED MARKDOWN
    // ============================================
    function formatTimestamp(date) {
      const now = new Date();
      const diff = now - date;
      const mins = Math.floor(diff / 60000);
      if (mins < 1) return 'Just now';
      if (mins < 60) return mins + ' min ago';
      const hrs = Math.floor(mins / 60);
      if (hrs < 24) return hrs + ' hr ago';
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    // Override addMessageToUI for timestamps
    const _origAddMessageToUI = addMessageToUI;
    addMessageToUI = function(text, sender, timestamp) {
      const el = document.createElement('div');
      el.className = 'message ' + sender;
      const ts = timestamp ? new Date(timestamp) : new Date();
      
      if (sender === 'ai') {
        el.innerHTML = '<div class="message-content">' + simpleMarkdownParser(text) + '</div><div class="message-timestamp">' + formatTimestamp(ts) + '</div><button class="copy-btn" title="Copy"><i class="fas fa-copy"></i></button>';
        el.querySelector('.copy-btn').addEventListener('click', () => { navigator.clipboard.writeText(text).then(() => showToast('Copied!', 'success')); });
        const cb = el.querySelector('.copy-btn');
        cb.style.cssText = 'position:absolute;top:8px;right:8px;background:rgba(99,102,241,0.2);border:none;color:var(--gray);padding:6px 10px;border-radius:6px;cursor:pointer;opacity:0;transition:opacity 0.2s;';
        el.style.position = 'relative';
        el.addEventListener('mouseenter', () => cb.style.opacity = '1');
        el.addEventListener('mouseleave', () => cb.style.opacity = '0');
        // Apply Prism highlighting
        setTimeout(() => { if (typeof Prism !== 'undefined') el.querySelectorAll('pre code').forEach(block => Prism.highlightElement(block)); }, 0);
      } else {
        el.innerHTML = '<div class="message-text">' + text + '</div><div class="message-timestamp">' + formatTimestamp(ts) + '</div>';
      }
      chatMessages.appendChild(el);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Init app
    init();`;

content = content.replace(initApp, jsEnhancements);

fs.writeFileSync(path, content, 'utf8');
console.log('All enhancements applied successfully!');
