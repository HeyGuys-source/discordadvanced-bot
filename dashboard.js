// Dashboard JavaScript functionality
class Dashboard {
    constructor() {
        this.currentGuildId = null;
        this.settings = {};
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTheme();
    }

    bindEvents() {
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#general-settings-form')) {
                e.preventDefault();
                this.saveGeneralSettings(e.target);
            } else if (e.target.matches('#automod-settings-form')) {
                e.preventDefault();
                this.saveAutoModSettings(e.target);
            } else if (e.target.matches('#welcome-settings-form')) {
                e.preventDefault();
                this.saveWelcomeSettings(e.target);
            } else if (e.target.matches('#starboard-settings-form')) {
                e.preventDefault();
                this.saveStarboardSettings(e.target);
            } else if (e.target.matches('#logging-settings-form')) {
                e.preventDefault();
                this.saveLoggingSettings(e.target);
            }
        });

        // Tab switches
        document.addEventListener('shown.bs.tab', (e) => {
            const target = e.target.getAttribute('data-bs-target');
            this.onTabSwitch(target);
        });

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    async initializeGuildConfig(guildId) {
        this.currentGuildId = guildId;
        
        try {
            // Load guild settings
            await this.loadGuildSettings();
            
            // Load guild stats
            await this.loadGuildStats();
            
            // Populate dropdown options
            await this.loadChannelOptions();
            await this.loadRoleOptions();
            
        } catch (error) {
            console.error('Error initializing guild config:', error);
            this.showAlert('Error loading guild configuration', 'danger');
        }
    }

    async loadGuildSettings() {
        try {
            const response = await fetch(`/api/guild/${this.currentGuildId}/settings`);
            if (!response.ok) throw new Error('Failed to load settings');
            
            this.settings = await response.json();
            this.populateSettingsForms();
            
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showAlert('Failed to load settings', 'danger');
        }
    }

    async loadGuildStats() {
        try {
            const response = await fetch(`/api/guild/${this.currentGuildId}/stats`);
            if (!response.ok) throw new Error('Failed to load stats');
            
            const stats = await response.json();
            this.updateStatsDisplay(stats);
            
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    async loadChannelOptions() {
        // This would typically fetch from Discord API via backend
        // For now, we'll simulate it
        const channelSelects = document.querySelectorAll('select[name$="_channel_id"]');
        
        channelSelects.forEach(select => {
            // Clear existing options except first
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add sample channels (in real implementation, fetch from API)
            const sampleChannels = [
                { id: '123456789', name: 'general' },
                { id: '123456790', name: 'mod-logs' },
                { id: '123456791', name: 'welcome' },
                { id: '123456792', name: 'starboard' }
            ];
            
            sampleChannels.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.id;
                option.textContent = `#${channel.name}`;
                select.appendChild(option);
            });
        });
    }

    async loadRoleOptions() {
        const roleSelects = document.querySelectorAll('select[name$="_role_id"]');
        
        roleSelects.forEach(select => {
            // Clear existing options except first
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add sample roles (in real implementation, fetch from API)
            const sampleRoles = [
                { id: '123456789', name: 'Member' },
                { id: '123456790', name: 'Verified' },
                { id: '123456791', name: 'VIP' }
            ];
            
            sampleRoles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.id;
                option.textContent = role.name;
                select.appendChild(option);
            });
        });
    }

    populateSettingsForms() {
        // Populate general settings
        const prefixInput = document.getElementById('prefix');
        if (prefixInput && this.settings.prefix) {
            prefixInput.value = this.settings.prefix;
        }

        // Populate automod settings
        const automodEnabled = document.getElementById('automod_enabled');
        if (automodEnabled) {
            automodEnabled.checked = this.settings.automod_enabled || false;
        }

        // Populate welcome settings
        const welcomeChannelSelect = document.getElementById('welcome_channel_id');
        const welcomeMessage = document.getElementById('welcome_message');
        const farewellMessage = document.getElementById('farewell_message');
        const autoRoleSelect = document.getElementById('auto_role_id');

        if (welcomeChannelSelect && this.settings.welcome_channel_id) {
            welcomeChannelSelect.value = this.settings.welcome_channel_id;
        }
        if (welcomeMessage && this.settings.welcome_message) {
            welcomeMessage.value = this.settings.welcome_message;
        }
        if (farewellMessage && this.settings.farewell_message) {
            farewellMessage.value = this.settings.farewell_message;
        }
        if (autoRoleSelect && this.settings.auto_role_id) {
            autoRoleSelect.value = this.settings.auto_role_id;
        }

        // Populate starboard settings
        const starboardChannelSelect = document.getElementById('starboard_channel_id');
        const starboardThreshold = document.getElementById('starboard_threshold');

        if (starboardChannelSelect && this.settings.starboard_channel_id) {
            starboardChannelSelect.value = this.settings.starboard_channel_id;
        }
        if (starboardThreshold && this.settings.starboard_threshold) {
            starboardThreshold.value = this.settings.starboard_threshold;
        }

        // Populate logging settings
        const logChannelSelect = document.getElementById('log_channel_id');
        if (logChannelSelect && this.settings.log_channel_id) {
            logChannelSelect.value = this.settings.log_channel_id;
        }
    }

    updateStatsDisplay(stats) {
        const memberCount = document.getElementById('member-count');
        const channelCount = document.getElementById('channel-count');

        if (memberCount) memberCount.textContent = stats.member_count || 'N/A';
        if (channelCount) channelCount.textContent = stats.channel_count || 'N/A';
    }

    async saveGeneralSettings(form) {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData);
        
        await this.saveSettings(settings, 'General settings saved successfully!');
    }

    async saveAutoModSettings(form) {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData);
        
        // Convert checkbox to boolean
        settings.automod_enabled = form.automod_enabled.checked;
        
        await this.saveSettings(settings, 'AutoMod settings saved successfully!');
    }

    async saveWelcomeSettings(form) {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData);
        
        // Convert empty strings to null
        Object.keys(settings).forEach(key => {
            if (settings[key] === '') settings[key] = null;
        });
        
        await this.saveSettings(settings, 'Welcome settings saved successfully!');
    }

    async saveStarboardSettings(form) {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData);
        
        // Convert empty strings to null
        Object.keys(settings).forEach(key => {
            if (settings[key] === '') settings[key] = null;
        });
        
        // Convert threshold to integer
        if (settings.starboard_threshold) {
            settings.starboard_threshold = parseInt(settings.starboard_threshold);
        }
        
        await this.saveSettings(settings, 'Starboard settings saved successfully!');
    }

    async saveLoggingSettings(form) {
        const formData = new FormData(form);
        const settings = Object.fromEntries(formData);
        
        // Convert empty strings to null
        Object.keys(settings).forEach(key => {
            if (settings[key] === '') settings[key] = null;
        });
        
        await this.saveSettings(settings, 'Logging settings saved successfully!');
    }

    async saveSettings(settings, successMessage) {
        try {
            const response = await fetch(`/api/guild/${this.currentGuildId}/settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });

            if (!response.ok) {
                throw new Error('Failed to save settings');
            }

            const result = await response.json();
            
            if (result.success) {
                this.showAlert(successMessage, 'success');
                // Update local settings
                Object.assign(this.settings, settings);
            } else {
                throw new Error(result.error || 'Unknown error');
            }

        } catch (error) {
            console.error('Error saving settings:', error);
            this.showAlert('Failed to save settings: ' + error.message, 'danger');
        }
    }

    onTabSwitch(target) {
        // Handle any tab-specific initialization
        switch (target) {
            case '#v-pills-general':
                // General tab specific code
                break;
            case '#v-pills-moderation':
                // Moderation tab specific code
                break;
            case '#v-pills-automod':
                // AutoMod tab specific code
                break;
            case '#v-pills-welcome':
                // Welcome tab specific code
                break;
            case '#v-pills-starboard':
                // Starboard tab specific code
                break;
            case '#v-pills-logging':
                // Logging tab specific code
                break;
        }
    }

    showAlert(message, type = 'info', duration = 5000) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert.fade');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }

        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
                alert.close();
            }, duration);
        }
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('dashboard-theme');
        if (savedTheme) {
            document.body.setAttribute('data-theme', savedTheme);
        }
    }

    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('dashboard-theme', newTheme);
    }

    // Utility methods
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        return isValid;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Global function for guild config initialization
function initializeGuildConfig(guildId) {
    if (window.dashboard) {
        window.dashboard.initializeGuildConfig(guildId);
    }
}

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.dashboard && window.dashboard.currentGuildId) {
        // Refresh data when page becomes visible again
        window.dashboard.loadGuildStats();
    }
});

// Handle connection status
window.addEventListener('online', () => {
    if (window.dashboard) {
        window.dashboard.showAlert('Connection restored', 'success', 3000);
    }
});

window.addEventListener('offline', () => {
    if (window.dashboard) {
        window.dashboard.showAlert('No internet connection', 'warning', 0);
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}
