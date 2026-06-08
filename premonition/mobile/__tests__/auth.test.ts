import { useAuthStore } from '../src/store/authStore';

describe('AuthStore', () => {
  it('starts unauthenticated', () => {
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('has null email initially', () => {
    expect(useAuthStore.getState().email).toBeNull();
  });
});
