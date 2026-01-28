/**
 * Auto-Save Manager for OppNDA Configuration
 * Handles silent auto-saving of changes without user notifications
 */

class AutoSaveManager {
    constructor(options = {}) {
        this.debounceDelay = options.debounceDelay || 1500; // 1.5 seconds
        this.autoSaveEndpoint = options.endpoint || '/api/save-config';
        this.debounceTimers = new Map();
        this.pendingChanges = new Map();
        this.isSaving = false;
        this.lastSaveTime = new Map();
        this.saveHistory = [];
        this.maxHistorySize = options.maxHistory || 10;
    }
    
    /**
     * Register a form or input element for auto-save
     */
    registerElement(element, configName, fieldName) {
        if (!element) return;
        
        element.addEventListener('change', (e) => {
            this.markDirty(configName, fieldName, e.target.value);
        });
        
        element.addEventListener('input', (e) => {
            this.markDirty(configName, fieldName, e.target.value);
        });
    }
    
    /**
     * Mark a field as dirty and schedule auto-save
     */
    markDirty(configName, fieldName, value) {
        const key = `${configName}:${fieldName}`;
        
        // Store pending change
        if (!this.pendingChanges.has(configName)) {
            this.pendingChanges.set(configName, {});
        }
        this.pendingChanges.get(configName)[fieldName] = value;
        
        // Clear existing debounce timer
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }
        
        // Set new debounce timer
        const timer = setTimeout(() => {
            this.saveConfig(configName);
            this.debounceTimers.delete(key);
        }, this.debounceDelay);
        
        this.debounceTimers.set(key, timer);
    }
    
    /**
     * Manually trigger auto-save for a config
     */
    async saveConfig(configName) {
        if (!this.pendingChanges.has(configName) || this.isSaving) {
            return;
        }
        
        this.isSaving = true;
        const changes = this.pendingChanges.get(configName);
        
        try {
            const response = await fetch(this.autoSaveEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    config: configName,
                    changes: changes
                })
            });
            
            if (response.ok) {
                // Record successful save
                this.recordSave(configName, changes);
                this.pendingChanges.delete(configName);
            } else {
                console.warn(`Auto-save failed for ${configName}:`, response.statusText);
                // Retry later
                setTimeout(() => this.saveConfig(configName), this.debounceDelay * 2);
            }
        } catch (error) {
            console.warn(`Auto-save error for ${configName}:`, error.message);
            // Retry later
            setTimeout(() => this.saveConfig(configName), this.debounceDelay * 2);
        } finally {
            this.isSaving = false;
        }
    }
    
    /**
     * Record a successful save in history
     */
    recordSave(configName, changes) {
        this.lastSaveTime.set(configName, new Date());
        this.saveHistory.push({
            timestamp: new Date(),
            config: configName,
            changes: changes
        });
        
        // Keep history size limited
        if (this.saveHistory.length > this.maxHistorySize) {
            this.saveHistory.shift();
        }
    }
    
    /**
     * Force save all pending changes immediately
     */
    async saveAll() {
        const configs = Array.from(this.pendingChanges.keys());
        await Promise.all(configs.map(config => this.saveConfig(config)));
    }
    
    /**
     * Get last save time for a config
     */
    getLastSaveTime(configName) {
        return this.lastSaveTime.get(configName);
    }
    
    /**
     * Get save history
     */
    getHistory() {
        return [...this.saveHistory];
    }
    
    /**
     * Get pending changes for a config
     */
    getPendingChanges(configName) {
        return this.pendingChanges.get(configName) || {};
    }
    
    /**
     * Clear pending changes
     */
    clearPending(configName) {
        this.pendingChanges.delete(configName);
        
        // Clear related debounce timers
        for (let key of this.debounceTimers.keys()) {
            if (key.startsWith(configName + ':')) {
                clearTimeout(this.debounceTimers.get(key));
                this.debounceTimers.delete(key);
            }
        }
    }
}

// Global auto-save manager instance
let autoSaveManager = null;

/**
 * Initialize the auto-save manager
 */
function initAutoSave(options = {}) {
    autoSaveManager = new AutoSaveManager(options);
    return autoSaveManager;
}

/**
 * Register element for auto-save
 */
function registerAutoSave(element, configName, fieldName) {
    if (!autoSaveManager) {
        autoSaveManager = new AutoSaveManager();
    }
    autoSaveManager.registerElement(element, configName, fieldName);
}

/**
 * Mark a field as dirty (convenience function)
 */
function markDirty(configName, fieldName, value) {
    if (!autoSaveManager) {
        autoSaveManager = new AutoSaveManager();
    }
    autoSaveManager.markDirty(configName, fieldName, value);
}

/**
 * Trigger save for a config
 */
async function triggerSave(configName) {
    if (!autoSaveManager) {
        autoSaveManager = new AutoSaveManager();
    }
    await autoSaveManager.saveConfig(configName);
}

/**
 * Save all pending changes
 */
async function saveAllChanges() {
    if (!autoSaveManager) {
        autoSaveManager = new AutoSaveManager();
    }
    await autoSaveManager.saveAll();
}

// Export for use in other modules
window.AutoSaveManager = AutoSaveManager;
window.autoSaveManager = autoSaveManager;
window.initAutoSave = initAutoSave;
window.registerAutoSave = registerAutoSave;
window.markDirty = markDirty;
window.triggerSave = triggerSave;
window.saveAllChanges = saveAllChanges;
