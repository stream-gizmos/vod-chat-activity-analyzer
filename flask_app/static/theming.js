/**
 * @return {boolean}
 */
function isDarkSchemePreferred() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
}

const themeChangeListeners = []

/**
 * @param {function} callback
 */
function onThemeChange(callback) {
    if (typeof callback !== 'function') {
        return
    }

    themeChangeListeners.push(callback)
}

/**
 * @param {string} newTheme
 */
function emitThemeChange(newTheme) {
    themeChangeListeners.forEach(callback => setTimeout(
        callback.apply(this, [newTheme]), 0
    ))
}

/**
 * @return {string}
 */
function getCurrentTheme() {
    return window.localStorage.getItem('theme') || (isDarkSchemePreferred() ? 'dark' : 'light')
}

/**
 * @param {string} value
 */
function setTheme(value) {
    if (value !== 'light') {
        value = 'dark'
    }

    window.localStorage.setItem('theme', value)

    if (value === 'light') {
        document.documentElement.classList.remove('dark-theme')
    } else {
        document.documentElement.classList.add('dark-theme')
    }

    emitThemeChange(value)
}

/**
 * @return {string}
 */
function getOppositeTheme() {
    return getCurrentTheme() === 'light' ? 'dark' : 'light'
}

document.addEventListener('DOMContentLoaded', () => {
    emitThemeChange(getCurrentTheme())
})
