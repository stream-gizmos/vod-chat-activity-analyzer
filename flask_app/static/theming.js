/**
 * @return {boolean}
 */
function isDarkSchemePreferred() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

class SiteTheme {
    #changeListeners = []

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.#emitChangeEvent(this.getCurrentTheme())
        })
    }

    /**
     * @return {string}
     */
    getCurrentTheme() {
        return window.localStorage.getItem('theme') || (isDarkSchemePreferred() ? 'dark' : 'light')
    }

    /**
     * @return {string}
     */
    getOppositeTheme() {
        return this.getCurrentTheme() === 'light' ? 'dark' : 'light'
    }

    /**
     * @param {string} value
     */
    setTheme(value) {
        if (value !== 'light') {
            value = 'dark'
        }

        window.localStorage.setItem('theme', value)

        if (value === 'light') {
            document.documentElement.classList.remove('dark-theme')
        } else {
            document.documentElement.classList.add('dark-theme')
        }

        this.#emitChangeEvent(value)
    }

    applyCurrentTheme() {
        this.setTheme(this.getCurrentTheme())
    }

    /**
     * @param {function} callback
     */
    onChange(callback) {
        if (typeof callback !== 'function') {
            return
        }

        this.#changeListeners.push(callback)
    }

    /**
     * @param {string} newTheme
     */
    #emitChangeEvent(newTheme) {
        this.#changeListeners.forEach(callback => setTimeout(
            callback.apply(this, [newTheme]), 0
        ))
    }
}

window.siteTheme = new SiteTheme()
window.siteTheme.init()
