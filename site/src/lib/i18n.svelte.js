import en from './locales/en.json';
import zh from './locales/zh.json';
import ja from './locales/ja.json';
import ar from './locales/ar.json';
import bn from './locales/bn.json';
import de from './locales/de.json';
import es from './locales/es.json';
import fr from './locales/fr.json';
import hi from './locales/hi.json';
import id from './locales/id.json';
import it from './locales/it.json';
import ko from './locales/ko.json';
import nl from './locales/nl.json';
import pl from './locales/pl.json';
import pt from './locales/pt.json';
import ru from './locales/ru.json';
import th from './locales/th.json';
import tr from './locales/tr.json';
import uk from './locales/uk.json';
import vi from './locales/vi.json';

const translations = { en, zh, ja, ar, bn, de, es, fr, hi, id, it, ko, nl, pl, pt, ru, th, tr, uk, vi };

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
    { code: 'ar', label: 'العربية' },
    { code: 'bn', label: 'বাংলা' },
    { code: 'de', label: 'Deutsch' },
    { code: 'es', label: 'Español' },
    { code: 'fr', label: 'Français' },
    { code: 'hi', label: 'हिन्दी' },
    { code: 'id', label: 'Indonesia' },
    { code: 'it', label: 'Italiano' },
    { code: 'ja', label: '日本語' },
    { code: 'ko', label: '한국어' },
    { code: 'nl', label: 'Nederlands' },
    { code: 'pl', label: 'Polski' },
    { code: 'pt', label: 'Português' },
    { code: 'ru', label: 'Русский' },
    { code: 'th', label: 'ไทย' },
    { code: 'tr', label: 'Türkçe' },
    { code: 'uk', label: 'Українська' },
    { code: 'vi', label: 'Tiếng Việt' },
    { code: 'zh', label: '中文' },
];
