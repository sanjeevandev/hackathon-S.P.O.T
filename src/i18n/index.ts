import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import hi from './locales/hi.json';
import mr from './locales/mr.json';
import ta from './locales/ta.json';

const STORAGE_LANG_KEY = 'spot_language';

function getInitialLanguage(): string {
  try {
    const saved = localStorage.getItem(STORAGE_LANG_KEY);
    if (saved && ['en', 'hi', 'mr', 'ta'].includes(saved)) {
      return saved;
    }
  } catch {
    // Ignore localStorage access issues
  }
  return 'en'; // Safe default language is English
}

const initialLang = getInitialLanguage();

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
      mr: { translation: mr },
      ta: { translation: ta },
    },
    lng: initialLang,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

i18n.on('languageChanged', (lng) => {
  try {
    localStorage.setItem(STORAGE_LANG_KEY, lng);
  } catch {
    // Ignore
  }
});

export default i18n;
