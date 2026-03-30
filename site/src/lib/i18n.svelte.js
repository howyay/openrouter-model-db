import en from './locales/en.json';
import zh from './locales/zh.json';
import ja from './locales/ja.json';

const translations = { en, zh, ja };

const STORAGE_KEY = 'locale-preference';

function detectLocale() {
    if (typeof localStorage !== 'undefined') {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && translations[saved]) return saved;
    }
    if (typeof navigator !== 'undefined') {
        const lang = navigator.language.slice(0, 2);
        if (translations[lang]) return lang;
    }
    return 'en';
}

let locale = $state(detectLocale());

export function t(key) {
    return (translations[locale] ?? translations.en)[key] ?? key;
}

export function getLocale() {
    return locale;
}

export function setLocale(l) {
    locale = l;
    if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, l);
    }
}

export const LOCALES = [
    { code: 'en', label: 'EN' },
    { code: 'zh', label: '中文' },
    { code: 'ja', label: '日本語' },
];
