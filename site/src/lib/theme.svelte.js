const STORAGE_KEY = 'theme-preference';

/** @type {'system' | 'light' | 'dark'} */
let preference = $state(loadPreference());

let resolved = $derived(
    preference === 'system' ? getSystemTheme() : preference
);

function loadPreference() {
    if (typeof localStorage === 'undefined') return 'system';
    return /** @type {'system' | 'light' | 'dark'} */ (
        localStorage.getItem(STORAGE_KEY) ?? 'system'
    );
}

function getSystemTheme() {
    if (typeof window === 'undefined') return 'dark';
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function applyTheme(theme) {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
}

export function setTheme(value) {
    preference = /** @type {'system' | 'light' | 'dark'} */ (value);
    localStorage.setItem(STORAGE_KEY, preference);
    applyTheme(preference === 'system' ? getSystemTheme() : preference);
}

export function initTheme() {
    applyTheme(resolved);

    const mql = window.matchMedia('(prefers-color-scheme: light)');
    mql.addEventListener('change', () => {
        if (preference === 'system') {
            applyTheme(getSystemTheme());
        }
    });
}

export function getPreference() {
    return preference;
}

export function getResolved() {
    return resolved;
}
