import { useThemeStore } from '../src/store/themeStore';

describe('ThemeStore', () => {
  it('defaults to dark mode', () => {
    expect(useThemeStore.getState().isDark).toBe(true);
  });

  it('toggles theme', () => {
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().isDark).toBe(false);
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().isDark).toBe(true);
  });
});
