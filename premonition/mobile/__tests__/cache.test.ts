import { useCacheStore } from '../src/store/cacheStore';

describe('CacheStore', () => {
  it('starts with empty cache', () => {
    expect(useCacheStore.getState().patients).toEqual({});
    expect(useCacheStore.getState().alerts).toEqual([]);
  });

  it('stores patients', () => {
    useCacheStore.getState().setPatients({ 'p-1': { risk: 0.5 } });
    expect(useCacheStore.getState().patients['p-1']).toEqual({ risk: 0.5 });
  });
});
