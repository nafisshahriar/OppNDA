/**
 * Modern Directory Browser Component
 * Provides an intuitive file/folder navigation UI with absolute path support
 */

class DirectoryBrowser {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with ID "${containerId}" not found`);
            return;
        }
        
        this.currentPath = options.initialPath || '';
        this.filterType = options.filterType || 'dirs'; // 'dirs', 'files', 'all'
        this.onSelectPath = options.onSelectPath || (() => {});
        this.allowMultiSelect = options.allowMultiSelect || false;
        this.selectedPaths = new Set();
        
        this.isLoading = false;
        this.history = [];
        
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="directory-browser">
                <!-- Navigation Bar -->
                <div class="db-nav-bar">
                    <button class="db-btn db-btn-icon" id="dbBtnBack" title="Go back">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <button class="db-btn db-btn-icon" id="dbBtnUp" title="Go to parent">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <button class="db-btn db-btn-icon" id="dbBtnRefresh" title="Refresh">
                        <i class="fas fa-redo"></i>
                    </button>
                    <input 
                        type="text" 
                        id="dbPathInput" 
                        class="db-path-input" 
                        placeholder="Enter path or paste absolute path..."
                        value="${this.currentPath}"
                    >
                    <button class="db-btn db-btn-primary" id="dbBtnGo">Go</button>
                </div>
                
                <!-- Breadcrumb Navigation -->
                <div class="db-breadcrumb" id="dbBreadcrumb"></div>
                
                <!-- Content Area -->
                <div class="db-content">
                    <div class="db-listing" id="dbListing">
                        <div class="db-loading">
                            <i class="fas fa-spinner fa-spin"></i> Loading...
                        </div>
                    </div>
                </div>
                
                <!-- Footer with Current Selection -->
                <div class="db-footer">
                    <div class="db-selected-info">
                        <span id="dbSelectedCount">No selection</span>
                    </div>
                    <div class="db-footer-buttons">
                        <button class="db-btn db-btn-secondary" id="dbBtnCancel">Cancel</button>
                        <button class="db-btn db-btn-primary" id="dbBtnSelect" disabled>Select</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        document.getElementById('dbBtnBack').addEventListener('click', () => this.goBack());
        document.getElementById('dbBtnUp').addEventListener('click', () => this.goUp());
        document.getElementById('dbBtnRefresh').addEventListener('click', () => this.refresh());
        document.getElementById('dbBtnGo').addEventListener('click', () => this.navigateTo());
        document.getElementById('dbPathInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.navigateTo();
        });
        document.getElementById('dbBtnSelect').addEventListener('click', () => this.confirmSelection());
        document.getElementById('dbBtnCancel').addEventListener('click', () => this.cancel());
    }
    
    async browse(path = '') {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const listing = document.getElementById('dbListing');
        listing.innerHTML = '<div class="db-loading"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
        
        try {
            const response = await fetch('/api/browse-directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: path || this.currentPath,
                    filter_type: this.filterType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPath = data.current_path;
                document.getElementById('dbPathInput').value = this.currentPath;
                
                this.renderBreadcrumb(data.current_path);
                this.renderListing(data);
            } else {
                listing.innerHTML = `<div class="db-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error: ${data.error}</p>
                </div>`;
            }
        } catch (error) {
            listing.innerHTML = `<div class="db-error">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load directory: ${error.message}</p>
            </div>`;
        }
        
        this.isLoading = false;
    }
    
    renderBreadcrumb(path) {
        const breadcrumb = document.getElementById('dbBreadcrumb');
        const parts = path.split(require('path').sep || '/');
        
        let html = '<button class="db-breadcrumb-item" data-path="">Home</button>';
        let accumulated = '';
        
        for (let part of parts) {
            if (!part) continue;
            accumulated = accumulated ? accumulated + (require('path').sep || '/') + part : part;
            html += `<span class="db-breadcrumb-sep">/</span>
                    <button class="db-breadcrumb-item" data-path="${accumulated}">${part}</button>`;
        }
        
        breadcrumb.innerHTML = html;
        breadcrumb.querySelectorAll('.db-breadcrumb-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const newPath = e.target.dataset.path;
                this.browse(newPath);
            });
        });
    }
    
    renderListing(data) {
        const listing = document.getElementById('dbListing');
        let html = '';
        
        // Render directories first (if filter allows)
        if (this.filterType !== 'files') {
            for (let dir of data.directories) {
                const isSelected = this.selectedPaths.has(dir.path);
                html += `
                    <div class="db-item db-item-dir ${isSelected ? 'selected' : ''}" data-path="${dir.path}">
                        <div class="db-item-icon"><i class="fas fa-folder"></i></div>
                        <div class="db-item-name">${this.escapeHtml(dir.name)}</div>
                        <div class="db-item-actions">
                            <button class="db-item-open" title="Open directory">
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </div>
                    </div>
                `;
            }
        }
        
        // Render files (if filter allows)
        if (this.filterType !== 'dirs') {
            for (let file of data.files) {
                const isSelected = this.selectedPaths.has(file.path);
                const size = this.formatFileSize(file.size);
                html += `
                    <div class="db-item db-item-file ${isSelected ? 'selected' : ''}" data-path="${file.path}">
                        <div class="db-item-icon"><i class="fas fa-file"></i></div>
                        <div class="db-item-info">
                            <div class="db-item-name">${this.escapeHtml(file.name)}</div>
                            <div class="db-item-size">${size}</div>
                        </div>
                    </div>
                `;
            }
        }
        
        if (!html) {
            html = '<div class="db-empty"><i class="fas fa-inbox"></i><p>Empty directory</p></div>';
        }
        
        listing.innerHTML = html;
        
        // Attach event listeners
        listing.querySelectorAll('.db-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.db-item-open')) {
                    this.browse(item.dataset.path);
                } else {
                    this.selectItem(item, item.dataset.path);
                }
            });
        });
    }
    
    selectItem(element, path) {
        if (this.allowMultiSelect) {
            element.classList.toggle('selected');
            if (element.classList.contains('selected')) {
                this.selectedPaths.add(path);
            } else {
                this.selectedPaths.delete(path);
            }
        } else {
            // Single select
            document.querySelectorAll('.db-item.selected').forEach(item => {
                item.classList.remove('selected');
            });
            element.classList.add('selected');
            this.selectedPaths.clear();
            this.selectedPaths.add(path);
        }
        
        this.updateSelectionInfo();
    }
    
    updateSelectionInfo() {
        const count = this.selectedPaths.size;
        const info = document.getElementById('dbSelectedCount');
        const selectBtn = document.getElementById('dbBtnSelect');
        
        if (count === 0) {
            info.textContent = 'No selection';
            selectBtn.disabled = true;
        } else {
            info.textContent = `${count} item${count !== 1 ? 's' : ''} selected`;
            selectBtn.disabled = false;
        }
    }
    
    confirmSelection() {
        if (this.selectedPaths.size > 0) {
            const paths = Array.from(this.selectedPaths);
            this.onSelectPath(this.allowMultiSelect ? paths : paths[0]);
        }
    }
    
    navigateTo() {
        const path = document.getElementById('dbPathInput').value.trim();
        if (path) {
            this.browse(path);
        }
    }
    
    goBack() {
        if (this.history.length > 0) {
            this.browse(this.history.pop());
        }
    }
    
    goUp() {
        if (this.currentPath && this.currentPath !== '/') {
            this.browse('..');
        }
    }
    
    refresh() {
        this.browse(this.currentPath);
    }
    
    cancel() {
        this.container.innerHTML = '';
        this.selectedPaths.clear();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Export for use in other scripts
window.DirectoryBrowser = DirectoryBrowser;
